import dataclasses
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Dict, List

import click
from gematria_engine import Mispar, MisparHechrechi, MisparGadol, MisparhaAkhor

# The UTF value for א, which we use for a vowel / punctuation cutoff
ALEF: int = ord("א")  # 1488


class EnhancedJSONEncoder(json.JSONEncoder):
    """A JSON encoder that can handle dataclasses

    https://stackoverflow.com/a/51286749/1779707
    """

    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


# I'm calling the form w/out vowels a word and the form w/ vowels a "diacritic"
# One word has 1 or more diacrtitics associated with it
@dataclass
class Diacritic:
    strongs: int
    diacritic: str

    def __lt__(self, obj):
        return (self.diacritic) < (obj.diacritic)


@dataclass
class Strongs:
    diacritic: str
    word: str


@dataclass
class WordNumber:
    value: int
    mod: int


@dataclass
class Word:
    word: str
    hechrechi: WordNumber
    gadol: WordNumber
    haakhor: WordNumber
    diacritics: List[Diacritic]

    def __lt__(self, obj):
        return (self.word) < (obj.word)


def get_word_numbers(word: str, mod: int, mispar: Mispar) -> WordNumber:
    """Take a word and get it's numeric values according to a mispar and equivalence classes mod a given number

    Args:
        word      (str): The word to convert
        mod       (int): The base used for equivalence classes
        mispar (Mispar): The gematria encoding we're using

    Returns:
        (WordNumber) The numeric value and equivalence classe of that word for that base
    """
    word_value: int = mispar.mispar(word)
    word_mod: int = word_value % mod
    return WordNumber(word_value, word_mod)


def strip_vowels(word: str) -> str:
    """Remove vowels from a word

    args:
        word (str): The word to strip

    returns:
        (str) the word w/out vowels
    """
    output_word: List[str] = [char for char in word if ord(char) >= ALEF]
    return "".join(output_word)


def get_diacritics(vocab_input_file: str) -> Dict[int, Strongs]:
    """Read the input file and spit out a dict from strongs values to their word strings

    Args:
        vocab_input_file (str): The path to the input file

    Returns:
        (Dict[int, Strongs]) The map from Strongs numbers to their word strings
    """
    with open(vocab_input_file, "r") as fh:
        input_dict: Dict[str, Any] = json.load(fh)
    diacritics: Dict[int, Strongs] = {
        int(strongs[1:]): Strongs(metadata["lemma"], strip_vowels(metadata["lemma"]))
        for strongs, metadata in input_dict.items()
    }
    return diacritics


def make_words(diacritics: Dict[int, Strongs], mod: int) -> Dict[str, Word]:
    """Turns the words (w/ vowels) to Strong's map and returns a map from words (w/out vowels) to Word objects

    Args:
        diacritics (Dict[int, Strongs]): A map Strongs numbers to word strings
        mod                       (int): The base for the equivalence classes

    Returns:
        (Dict[str, Word]) a map from words (w/out vowels) to Word objects
    """
    mispar_hechrechi: Mispar = MisparHechrechi()
    mispar_gadol: Mispar = MisparGadol()
    mispar_haakhor: Mispar = MisparhaAkhor()

    words: Dict[str, Word] = {}
    for strongs, diacritic in diacritics.items():
        word: str = diacritic.word
        hechrechi: WordNumber
        gadol: WordNumber
        haakhor: WordNumber
        if word not in words:
            hechrechi = get_word_numbers(word, mod, mispar_hechrechi)
            gadol = get_word_numbers(word, mod, mispar_gadol)
            haakhor = get_word_numbers(word, mod, mispar_haakhor)
            words[word] = Word(
                word,
                hechrechi,
                gadol,
                haakhor,
                [Diacritic(strongs, diacritic.diacritic)],
            )
        else:
            old_word: Word = words[word]
            diacritics_list: List[Diacritic] = old_word.diacritics
            diacritics_list.append(Diacritic(strongs, diacritic.diacritic))
            new_word: Word = Word(word, hechrechi, gadol, haakhor, diacritics_list)
            words[word] = new_word
    for word in words:
        words[word].diacritics.sort()
    return words


def write_js_var(name: str, value: Dict[Any, Any], output_path: str) -> None:
    """Write dictionary to js variable containing a json blob, DESTRUCTIVELY!

    args:
        name             (str): file name, as in f'{name}.json
        value (Dict[Any, Any]): the dictionary you are writing
        output_path      (str): the path to the directory where we're writing the variables
    """
    path = Path(output_path, f"{name}.js")
    blob = json.dumps(value, cls=EnhancedJSONEncoder)
    with open(path, "w") as fh:
        fh.write(f"export const {name} = {blob}")


@click.command()
@click.option(
    "-m",
    "--mod",
    type=int,
    default=7,
    help="Words / mod Words. Defaults to |days of the week|",
)
@click.option(
    "--vocab_input_file",
    type=str,
    default="data/strongs-hebrew-dictionary.json",
    help=("Path to my Strong's JSON file"),
)
@click.option(
    "--output_path", type=str, default="data", help="Path to output json blobs"
)
def main(mod: int, vocab_input_file: str, output_path: str) -> None:
    """Main function. Persists maps to disk, DESTRUCTIVELY!

    Main function:
        1) Read dictionary file
        2) Create maps
        3) Persist them

    Maps:
        strongs -> [diacritic, word str]
        word str -> Word object
        hechrechi: letter -> day number -> [Word]
        gadol: letter -> day number -> [Word]
        haakhor: letter -> day number -> [Word]

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

    hechrechi: Dict[str, Dict[int, List[Word]]] = {}
    gadol: Dict[str, Dict[int, List[Word]]] = {}
    haakhor: Dict[str, Dict[int, List[Word]]] = {}

    for word_str, word_object in words.items():
        letter: str = word_str[0]
        if letter not in hechrechi:
            hechrechi[letter] = {}
            gadol[letter] = {}
            haakhor[letter] = {}
        # TODO: you can make this a function
        word_mod: int = word_object.hechrechi.mod
        if word_mod not in hechrechi[letter]:
            hechrechi[letter][word_mod] = []
        hechrechi[letter][word_mod].append(word_object)
        word_mod = word_object.gadol.mod
        if word_mod not in gadol[letter]:
            gadol[letter][word_mod] = []
        gadol[letter][word_mod].append(word_object)
        word_mod = word_object.haakhor.mod
        if word_mod not in haakhor[letter]:
            haakhor[letter][word_mod] = []
        haakhor[letter][word_mod].append(word_object)

    # TODO: ditto
    for letter in hechrechi.keys():
        for day in hechrechi[letter].keys():
            hechrechi[letter][day].sort()
    for letter in gadol.keys():
        for day in gadol[letter].keys():
            gadol[letter][day].sort()
    for letter in haakhor.keys():
        for day in haakhor[letter].keys():
            haakhor[letter][day].sort()

    write_js_var("diacritics", diacritics, output_path)
    write_js_var("words", words, output_path)
    write_js_var("hechrechi", hechrechi, output_path)
    write_js_var("gadol", gadol, output_path)
    write_js_var("haakhor", haakhor, output_path)


if __name__ == "__main__":
    main()
