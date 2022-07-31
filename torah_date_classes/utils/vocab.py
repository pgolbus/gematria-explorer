import json
import random
from typing import List

from PyDictionary import PyDictionary

ASCII_OFFSET: int = ord('a') - 1
RANDOM_SEED: int = 42
VOCAB_SIZE: int = 8679
VOCAB_FILE: str = 'utils/corncob_lowercase.txt'


def get_vocab(vocab_size: int = VOCAB_SIZE, vocab_file: str = VOCAB_FILE) -> List[str]:
    with open(vocab_file, 'r') as fh:
        full_vocab_list: List[str] = [word.strip() for word in fh.readlines()]
    vocab_list = random.sample(full_vocab_list, vocab_size)
    vocab_list.sort()
    return vocab_list

def get_numeric_value(word: str, hidden: bool = False) -> int:
    # get_numeric_value('abc') = 6
    # get_numeric_value('abc', hidden=True) = 321
    def ord_offset(char: str) -> int:
        return ord(char) - ASCII_OFFSET

    if hidden:
        return sum([10**i * ord_offset(char) for i, char in enumerate(word)])
    return sum([ord_offset(char) for char in word])


if __name__ == '__main__':
    random.seed(RANDOM_SEED)
    vocab_list = get_vocab()
