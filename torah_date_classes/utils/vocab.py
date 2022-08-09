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
    spelling: str
    strongs: int

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
    diacritics: Dict[str, int] = {metadata['lemma']: strongs[1:] for strongs, metadata in input_dict.items()}
    return diacritics

def make_words(diacritics: Dict[str, int]) -> Dict[str, Word]:
    """Turns the words (w/ vowels) to Strong's map and returns a map from words (w/out vowels) to Word objects

    Args:
        diacritics (Dict[str, int]): A map from words (w/ vowels) to Strong's

    Returns:
        (Dict[str, Word]) a map from words (w/out vowels) to Word objects
    """
    words: Dict[str, Word] = {}
    for diacritic, strongs in diacritics.items():
        word: str = strip_vowels(diacritic)
        if word not in words:
            word_numbers: WordNumbers = get_word_numbers(word)
            words[word]: Word = Word(word_numbers, [Diacritic(diacritic, strongs)])
        else:
            old_word: Word = words[word]
            word_numbers: WordNumbers = old_word.word_numbers
            diacritics: List[Diacritic] = old_word.diacritics
            diacritics.append(Diacritic(diacritic, strongs))
            new_word: Word = Word(word_numbers, diacritics)
            words[word]: Word = new_word
    return words


def write_json(name: str, value: Dict[Any, Any], output_path: str) -> None:
    path = Path(output_path, f'{name}.json')
    with open(path, 'w') as fh:
        json.dump(value, fh, indent=4, sort_keys=True)

@click.command()
@click.option('-m', '--mod', type=int, default=7, help='Words / mod Words. Defaults to |days of the week|')
@click.option('--vocab_input_file',
    type=str,
    default='../data/strongs-hebrew-dictionary.json',
    help=('Path to a file containing a list of (lowercase) words')
    )
@click.option('--output_path', type=str, default='../data', help='Path to output json blobs')
def main(mod: int, vocab_input_file: str, output_path: str) -> None:

    vocab: Dict[str, Word] = {}
    face: Dict[str, Dict[int, List[str]]] = {}
    hidden: Dict[str, Dict[int, List[str]]] = {}

    diacritics: Dict[str, int] = get_diacritics(vocab_input_file)

    for word, strongs in vocab_input.items():
        values: Tuple[int, int, int, int] = get_equivalence_classes(word, mod)
        face_value: int = values[0]
        face_mod: int = values[1]
        hidden_value: int = values[2]
        hidden_mod: int = values[3]
        vocab[word]: Dict[str, Any] = {}
        vocab[word]['strongs']: str = strongs
        vocab[word]['face_value']: int = face_value
        vocab[word]['face_mod']: int = face_mod
        vocab[word]['hidden_value']: int = hidden_value
        vocab[word]['hidden_mod']: int = hidden_mod
        letter = word[0]
        if not letter in face:
            face[letter]: Dict[str, Dict[int, List[str]]] = {}
        if not face_mod in face[letter]:
            face[letter][face_mod]: List[str] = []
        face[letter][face_mod].append(word)
        if not letter in hidden:
            hidden[letter]: Dict[str, Dict[int, List[str]]] = {}
        if not hidden_mod in hidden[letter]:
            hidden[letter][hidden_mod]: List[str] = []
        hidden[letter][hidden_mod].append(word)

    for letter in face.keys():
        for mod in face[letter].keys():
            try:
                face[letter][mod].sort()
            except KeyError:
                pass
            try:
                hidden[letter][mod].sort()
            except KeyError:
                pass

    write_json('vocab', vocab, output_path)
    write_json('face', face, output_path)
    write_json('hidden', hidden, output_path)


if __name__ == '__main__':
    main()