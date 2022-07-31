import json
from pathlib import Path
import random
from typing import Any, Dict, List, Tuple

import click


ASCII_OFFSET: int = ord('a') - 1


def get_equivalence_classes(word: str, mod: int) -> Tuple[int, int]:
    face_value = get_numeric_value(word) % mod
    hidden_value = get_numeric_value(word, hidden=True) % mod
    return face_value, hidden_value

def get_numeric_value(word: str, hidden: bool = False) -> int:
    # get_numeric_value('abc') = 6
    # get_numeric_value('abc', hidden=True) = 321
    def ord_offset(char: str) -> int:
        return ord(char) - ASCII_OFFSET

    if hidden:
        return sum([10**i * ord_offset(char) for i, char in enumerate(word)])
    return sum([ord_offset(char) for char in word])

def get_vocab(vocab_size: int, vocab_input_file: str) -> List[str]:
    with open(vocab_input_file, 'r') as fh:
        full_vocab_list: List[str] = [word.strip() for word in fh.readlines()]
    vocab_list = random.sample(full_vocab_list, vocab_size)
    vocab_list.sort()
    return vocab_list

def write_json(name: str, value: Dict[Any, Any], output_path: str) -> None:
    path = Path(output_path, f'{name}.json')
    with open(path, 'w') as fh:
        json.dump(value, fh, indent=4, sort_keys=True)

@click.command()
@click.option('-m', '--mod', type=int, default=7, help='Words / mod Words. Defaults to |days of the week|')
@click.option('--vocab_size',
    type=int,
    default=8679,
    help=('Number of words to sample from a list of English words. Defaults to the number of unique words in the torah')
    )
@click.option('--vocab_input_file',
    type=str,
    default='data/corncob_lowercase.txt',
    help=('Path to a file containing a list of (lowercase) words')
    )
@click.option('--output_path', type=str, default='data', help='Path to output json blobs')
@click.option('--seed', type=int, default=42, help='Random seed value')
def main(mod: int, vocab_size: int, vocab_input_file: str, output_path: str, seed:int) -> None:
    random.seed(seed)

    vocab_list: List[str] = get_vocab(vocab_size, vocab_input_file)
    vocab: Dict[str, Dict[str, int]] = {}
    face: Dict[int, List[str]] = {}
    hidden: Dict[int, List[str]] = {}

    for word in vocab_list:
        class_values: Tuple[int, int] = get_equivalence_classes(word, mod)
        face_value:int = class_values[0]
        hidden_value:int = class_values[1]
        word = word.capitalize()
        vocab[word]: Dict[str, int] = {}
        vocab[word]['face']: int = face_value
        vocab[word]['hidden']: int = hidden_value
        if not face_value in face:
            face[face_value]: List[str] = []
        face[face_value].append(word)
        if not hidden_value in hidden:
            hidden[hidden_value]: List[str] = []
        hidden[hidden_value].append(word)

    for mod in face.keys():
        face[mod].sort()
        hidden[mod].sort()

    write_json('vocab', vocab, output_path)
    write_json('face', face, output_path)
    write_json('hidden', hidden, output_path)


if __name__ == '__main__':
    main()