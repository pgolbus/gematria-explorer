from datetime import timedelta
import json
import random
from typing import Dict, List


ASCII_OFFSET: int = ord('a') - 1
MOD: int = 7
RANDOM_SEED: int = 42
VOCAB_SIZE: int = 8679
VOCAB_INPUT_FILE: str = 'data/corncob_lowercase.txt'
OUTPUT_FILE_PATH: str = 'data/{}.json'


def get_numeric_value(word: str, hidden: bool = False) -> int:
    # get_numeric_value('abc') = 6
    # get_numeric_value('abc', hidden=True) = 321
    def ord_offset(char: str) -> int:
        return ord(char) - ASCII_OFFSET

    if hidden:
        return sum([10**i * ord_offset(char) for i, char in enumerate(word)])
    return sum([ord_offset(char) for char in word])

def get_vocab(vocab_size: int = VOCAB_SIZE, vocab_input_file: str = VOCAB_INPUT_FILE) -> List[str]:
    with open(vocab_input_file, 'r') as fh:
        full_vocab_list: List[str] = [word.strip() for word in fh.readlines()]
    vocab_list = random.sample(full_vocab_list, vocab_size)
    vocab_list.sort()
    return vocab_list


if __name__ == '__main__':
    random.seed(RANDOM_SEED)
    vocab_list: List[str] = get_vocab()
    vocab: Dict[str, Dict[str, int]] = {}
    face: Dict[int, List[str]] = {}
    hidden: Dict[int, List[str]] = {}

    for word in vocab_list:
        face_value: int = get_numeric_value(word)
        face_mod: int = face_value % MOD
        hidden_value: int = get_numeric_value(word, hidden=True)
        hidden_mod: int = hidden_value % MOD
        word = word.capitalize()
        vocab[word]: Dict[str, int] = {}
        vocab[word]['face']: int = face_mod
        vocab[word]['hidden']: int = hidden_mod
        if not face_mod in face:
            face[face_mod]: List[str] = []
        face[face_mod].append(word)
        if not hidden_mod in hidden:
            hidden[hidden_mod]: List[str] = []
        hidden[hidden_mod].append(word)

    for mod in face.keys():
        face[mod].sort()
        hidden[mod].sort()

    with open(OUTPUT_FILE_PATH.format('face'), 'w') as fh:
        json.dump(face, fh, indent=4, sort_keys=True)
    with open(OUTPUT_FILE_PATH.format('hidden'), 'w') as fh:
        json.dump(hidden, fh, indent=4, sort_keys=True)
    with open(OUTPUT_FILE_PATH.format('vocab'), 'w') as fh:
        json.dump(vocab, fh, indent=4, sort_keys=True)