from dataclasses import dataclass
from distutils.dep_util import newer_pairwise
import json
from pathlib import Path
from typing import Any, Dict, List

import click


# The UTF value for א (plus one) that we will be indexing characters off of
UTF_OFFSET: int = int("0x05D0", 0) + 1


# I'm calling the form w/out vowels a word and the form w/ vowels a "diacritic"
# One word has 1 or more diacrtitics associated with it
@dataclass
class Diacritic:
    strongs: int
    diacritic: str

@dataclass
class WordNumbers:
    face_value: int
    face_mod: int
    hidden_value: int
    hidden_mod: int

@dataclass
class Word:
    word_numbers: WordNumbers
    diacritics: List[Diacritic]



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
        return ord(char) - UTF_OFFSET

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
    output_word: List[str] = [ord(char) for char in word if ord(char) >= UTF_OFFSET - 1]
    return ''.join(output_word)

def get_diacritics(vocab_input_file: str) -> Dict[str, int]:
    """Read the input file and spit out a list of words (w/ vowels) to their Strong's numbers

    Args:
        vocab_input_file (str): The path to the input file

    Returns:
        (Dict[str, int]) The map from words (w/ vowels) to their Strong's numbers
    """
    with open(vocab_input_file, 'r') as fh:
        input_dict: Dict[str, Any] = json.load(fh)
    diacritics: Dict[int, str] = {strongs[1:]: metadata['lemma'] for strongs, metadata in input_dict.items()}
    return diacritics

def make_words(diacritics: Dict[int, str]) -> Dict[str, Word]:
    """Turns the words (w/ vowels) to Strong's map and returns a map from words (w/out vowels) to Word objects

    Args:
        diacritics (Dict[str, int]): A map from words (w/ vowels) to Strong's

    Returns:
        (Dict[str, Word]) a map from words (w/out vowels) to Word objects
    """
    words: Dict[str, Word] = {}
    for strongs, diacritic in diacritics.items():
        word: str = strip_vowels(diacritic)
        if word not in words:
            word_numbers: WordNumbers = get_word_numbers(word)
            words[word]: Word = Word(word_numbers, [Diacritic(strongs, diacritic)])
        else:
            old_word: Word = words[word]
            word_numbers: WordNumbers = old_word.word_numbers
            diacritics: List[Diacritic] = old_word.diacritics
            diacritics.append(Diacritic(strongs, diacritic))
            new_word: Word = Word(word_numbers, diacritics)
            words[word]: Word = new_word
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
        json.dump(value, fh, indent=4, sort_keys=True)

@click.command()
@click.option('-m', '--mod', type=int, default=7, help='Words / mod Words. Defaults to |days of the week|')
@click.option('--vocab_input_file',
    type=str,
    default='../data/strongs-hebrew-dictionary.json',
    help=('Path to my Strong\'s JSON file')
    )
@click.option('--output_path', type=str, default='../data', help='Path to output json blobs')
def main(mod: int, vocab_input_file: str, output_path: str) -> None:
    """Main function. Persists maps to disk, DESTRUCTIVELY!

    Main function:
        1) Read dictionary file
        2) Create maps
        3) Persist them

    Maps:
        strongs -> diacritic
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
    diacritics: Dict[int, str] = get_diacritics(vocab_input_file)
    words: Dict[str, Word] = make_words(diacritics)

    face: Dict[str, Dict[int, List[Word]]] = {}
    hidden: Dict[str, Dict[int, List[Word]]] ={}

    for word_str, word_object in words.items:
        letter: str = word_str[0]
        if letter not in face:
            face[letter]: Dict[int, List[Word]] = {}
            hidden[letter]: Dict[int, List[Word]] = {}
        face_mod: int = word_object.word_numbers.face_mod
        if face_mod not in face[letter]:
            face[letter][face_mod]: List[Word] = []
        face[letter][face_mod].append(word_object)
        hidden_mod: int = word_object.word_numbers.hidden_mod
        if hidden_mod not in hidden[letter]:
            hidden[letter][hidden_mod]: List[Word] = []
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