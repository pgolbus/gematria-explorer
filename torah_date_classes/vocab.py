from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Dict, List

import click

from utils import EnhancedJSONEncoder

# The UTF value for א that we will be indexing characters off of
ALEF: int = 1488


# I'm calling the form w/out vowels a word and the form w/ vowels a "diacritic"
# One word has 1 or more diacrtitics associated with it
@dataclass
class Diacritic:
    strongs: int
    diacritic: str

    def __lt__(self, obj):
        return ((self.diacritic) < (obj.diacritic))

@dataclass
class Strongs:
    diacritic: str
    word: str

@dataclass
class WordNumbers:
    face_value: int
    face_mod: int
    hidden_value: int
    hidden_mod: int

@dataclass
class Word:
    word: str
    word_numbers: WordNumbers
    diacritics: List[Diacritic]

    def __lt__(self, obj):
        return ((self.word) < (obj.word))


def get_word_numbers(word: str, mod: int) -> WordNumbers:
    """Take a word and get it's numeric values and equivalence classes mod a given number

    Args:
        word (str): The word to convert
        mod  (int): The base used for equivalence classes

    Returns:
        (WordNumbers) The numeric values and equivalence classes of that word for that base
    """
    face_value: int = get_numeric_value(word)
    face_mod: int  = face_value % mod
    hidden_value: int = get_numeric_value(word, hidden=True)
    hidden_mod:int = hidden_value % mod
    return WordNumbers(face_value, face_mod, hidden_value, hidden_mod)

def get_numeric_value(word: str, hidden: bool = False) -> int:
    """Convert a word to its numeric value

    Convert a word to its numeric value by adding up the numeric value of it's letters.
    A word's "hidden" value is obtained by treating it as a number rather than a sum of digits.

    Examples:
        get_numeric_value('אב') = 3
        get_numeric_value('אב', hidden=True) = 21

    Args:
        word    (str): The word to convert
        hidden (bool): Whether to return the hidden number. Defaults to False

    Returns:
        (int) The (hidden) numeric value of the word
    """
    def ord_offset(char: str) -> int:
        return ord(char) - ALEF + 1

    if hidden:
        return sum([10**i * ord_offset(char) for i, char in enumerate(word)])
    return sum([ord_offset(char) for char in word])

def strip_vowels(word: str) -> str:
    """Remove vowels from a word

    args:
        word (str): The word to strip

    returns:
        (str) the word w/out vowels
    """
    output_word: List[str] = [char for char in word if ord(char) >= ALEF]
    return ''.join(output_word)

def get_diacritics(vocab_input_file: str) -> Dict[int, Strongs]:
    """Read the input file and spit out a dict from strongs values to their word strings

    Args:
        vocab_input_file (str): The path to the input file

    Returns:
        (Dict[int, Strongs]) The map from Strongs numbers to their word strings
    """
    with open(vocab_input_file, 'r') as fh:
        input_dict: Dict[str, Any] = json.load(fh)
    diacritics: Dict[int, Strongs] = {int(strongs[1:]): Strongs(metadata['lemma'],
                                                                strip_vowels(metadata['lemma']))
                                      for strongs, metadata in input_dict.items()}
    return diacritics

def make_words(diacritics: Dict[int, Strongs], mod: int) -> Dict[str, Word]:
    """Turns the words (w/ vowels) to Strong's map and returns a map from words (w/out vowels) to Word objects

    Args:
        diacritics (Dict[int, Strongs]): A map Strongs numbers to word strings
        mod                       (int): The base for the equivalence classes

    Returns:
        (Dict[str, Word]) a map from words (w/out vowels) to Word objects
    """
    words: Dict[str, Word] = {}
    for strongs, diacritic in diacritics.items():
        word: str = diacritic.word
        word_numbers: WordNumbers
        if word not in words:
            word_numbers = get_word_numbers(word, mod)
            words[word] = Word(word, word_numbers, [Diacritic(strongs, diacritic.diacritic)])
        else:
            old_word: Word = words[word]
            word_numbers = old_word.word_numbers
            diacritics_list: List[Diacritic] = old_word.diacritics
            diacritics_list.append(Diacritic(strongs, diacritic.diacritic))
            new_word: Word = Word(word, word_numbers, diacritics_list)
            words[word] = new_word
    for word in words:
        words[word].diacritics.sort()
    return words

def write_json(name: str, value: Dict[Any, Any], output_path: str) -> None:
    """Write dictionary to JSON blob, DESTRUCTIVELY!

    args:
        name             (str): file name, as in f'{name}.json
        value (Dict[Any, Any]): the dictionary you are writing
        output_path      (str): the path to the directory where we're writing the blobs
    """
    path = Path(output_path, f'{name}.json')
    with open(path, 'w') as fh:
        json.dump(value, fh, indent=4, sort_keys=True, cls=EnhancedJSONEncoder)

@click.command()
@click.option('-m', '--mod', type=int, default=7, help='Words / mod Words. Defaults to |days of the week|')
@click.option('--vocab_input_file',
    type=str,
    default='data/strongs-hebrew-dictionary.json',
    help=('Path to my Strong\'s JSON file')
    )
@click.option('--output_path', type=str, default='data', help='Path to output json blobs')
def main(mod: int, vocab_input_file: str, output_path: str) -> None:
    """Main function. Persists maps to disk, DESTRUCTIVELY!

    Main function:
        1) Read dictionary file
        2) Create maps
        3) Persist them

    Maps:
        strongs -> [diacritic, word str]
        word str -> Word object
        face: letter -> day number -> [Word]
        hidden: letter -> day number -> [Word]

    Args:
        mod              (int): The base number for equivalence classes
        vocab_input_file (str): Path to input dictionary
        output_path      (str): Path to output directory

    Side-effects:
        Persists maps to disk, DESTRUCTIVELY!
    """
    # get the "diacritics" and "words" from the strong's dictionary
    # We'll go from diacritic str -> word str dynamically on the javascript side
    diacritics: Dict[int, Strongs] = get_diacritics(vocab_input_file)
    words: Dict[str, Word] = make_words(diacritics, mod)

    face: Dict[str, Dict[int, List[Word]]] = {}
    hidden: Dict[str, Dict[int, List[Word]]] ={}

    for word_str, word_object in words.items():
        letter: str = word_str[0]
        if letter not in face:
            face[letter] = {}
            hidden[letter] = {}
        face_mod: int = word_object.word_numbers.face_mod
        if face_mod not in face[letter]:
            face[letter][face_mod] = []
        face[letter][face_mod].append(word_object)
        hidden_mod: int = word_object.word_numbers.hidden_mod
        if hidden_mod not in hidden[letter]:
            hidden[letter][hidden_mod] = []
        hidden[letter][hidden_mod].append(word_object)

    for letter in face.keys():
        for day in face[letter].keys():
            face[letter][day].sort()

    for letter in hidden.keys():
        for day in hidden[letter].keys():
            hidden[letter][day].sort()

    write_json('diacritics', diacritics, output_path)
    write_json('words', words, output_path)
    write_json('face', face, output_path)
    write_json('hidden', hidden, output_path)


if __name__ == '__main__':
    main()