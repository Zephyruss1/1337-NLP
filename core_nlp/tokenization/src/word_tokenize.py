"""
Core file, all tokenizer methods contains here. 
"""

import json
import re
from collections import defaultdict, Counter
from enum import Enum
from functools import lru_cache
from dataclasses import dataclass
from typing import Optional, Dict, Union, List

from error_messages import TokenizerErrorMessages
from exceptions import TokenizerException

END_OF_TEXT = "<|endoftext|>"


class TokenizationMethod(str, Enum):
    BPE = "BPE"
    WORDPIECE = "WordPiece"
    SENTENCEPIECE = "SentencePiece"

@dataclass
class TurkishTokenizerParameters:
    vocab_size: int = 50257
    method: TokenizationMethod = TokenizationMethod.BPE


class TurkishBPETokenizer:
    """Byte-Pair Tokenizer for Turkish sentences"""
    def __init__(self, params: TurkishTokenizerParameters) -> None:
        if params.method != TokenizationMethod.BPE:
            raise TokenizerException(
                TokenizerErrorMessages.INVALID_METHOD_FOR_CURRENT_CLASS
            )

        self.vocab_size = params.vocab_size
        self.vocab: dict[str, int] = {}
        self.inverse_vocab: dict[int, str] = {}
        self.bpe_merges: dict[int] = {}

    def train(self, text: str, vocab_size, allowed_special=END_OF_TEXT) -> None:
        """
        Train the BPE tokenizer from scratch.

        Args:
            text (str): The training text.
            vocab_size (int): The desired vocabulary size.
            allowed_special (set): A set of special tokens to include.
        """
        if not text:
            raise TokenizerException(TokenizerErrorMessages.EMPTY_TEXT)

        processed_text: list[str] = []

        for i, char in enumerate(text):
            if char == " ":
                processed_text.append(char)
        processed_text = "".join(processed_text)

        unique_chars = [chr(i) for i in range(256)]
        unique_chars.extend(
            char for char in sorted(set(processed_text))
            if char not in unique_chars
        )
        
        self.vocab = {char: i for i, char in enumerate(unique_chars)}
        self.inverse_vocab = {i: char for char, i in self.vocab.items()}

        # Add allowed special tokens
        if allowed_special:
            for special_token in allowed_special:
                if special_token not in self.vocab:
                    new_id = len(self.vocab)
                    self.vocab[new_id] = special_token
                    self.inverse_vocab[special_token] = new_id

        # Tokenize the processed_text into token IDs
        token_ids = [self.inverse_vocab[char] for char in processed_text] 
        
        # BPE steps 1-3: Repeatedly find and replace frequent pairs
        for new_id in range(len(self.vocab), vocab_size):
            pair_id = self.find_freq_pair(token_ids, mode="most")
            if pair_id is None:
                break
            token_ids = self.replace_pair(token_ids, pair_id, new_id)
            self.bpe_merges[pair_id] = new_id
        
        # Build the vocabulary with merged tokens
        for (p0, p1), new_id in self.bpe_merges.items():
            merged_token = self.vocab[p0] + self.vocab[p1]
            self.vocab[new_id] = merged_token
            self.inverse_vocab[merged_token] = new_id

    def load_vocab_and_merges_from_openai(self, vocab_path: str, bpe_merges_path: str) -> None:
        """
        Load pre-trained vocabulary and BPE merges from OpenAI's GPT-2 files.

        Args:
            vocab_path (str): Path to the vocab file (GPT-2 calls it 'encoder.json').
            bpe_merges_path (str): Path to the bpe_merges file  (GPT-2 calls it 'vocab.bpe').
        """
        # Load vocabulary
        with open(vocab_path, 'r', encoding='utf-8') as file:
            loaded_vocab = json.load(file)
            # Convert loaded vocabulary to correct format
            self.vocab = {int(v): k for k, v in loaded_vocab.items()}
            self.inverse_vocab = {k: int(v) for k, v in loaded_vocab.items()}

        # Handle newline character without adding a new token
        if "\n" not in self.inverse_vocab:
            fallback_token = next((token for token in ["<|endoftext|>", "<|startoftext|>"] if token in self.inverse_vocab), None)
            if fallback_token is not None:
                newline_token_id = self.inverse_vocab[fallback_token]
            else:
                raise KeyError("no suitable fallback token found for newline character")
        
        self.inverse_vocab["\n"] = newline_token_id
        self.vocab[newline_token_id] = "\n"

        self.bpe_ranks: dict = {}

        with open("bpe_ranks_path", 'r', encoding='utf-8') as file:
            lines = file.readlines()
            if lines[0].startswith("#"):
                lines = lines[1:]
            
            rank = 0

            for line in lines:
                pair = tuple(line.strip().split())
                if len(pair) == 2:
                    token1, token2 = pair
                    if token1 in self.inverse_vocab and token2 in self.inverse_vocab:
                        self.bpe_ranks[(token1, token2)] = rank
                        rank += 1
                    else:
                        print(f"Skipping pair {pair} as one of the tokens is not in the vocabulary.")
    
    def encode(self, text: str, allowed_special=None):
        """
        Encode the input text into a list of token IDs, with tiktoken-style handling of special tokens.
    
        Args:
            text (str): The input text to encode.
            allowed_special (set or None): Special tokens to allow passthrough. If None, special handling is disabled.
    
        Returns:
            List of token IDs.
        """
        import re

        token_ids: list[int] = []

        # If special handling is enabled, split the text accordingly
        if allowed_special is not None and len(allowed_special) > 0:
            # Create a regex pattern to match special tokens
            special_pattern = re.compile(
                "(" + "|".join(re.escape(tok) for tok in sorted(allowed_special, key=len, reverse=True)) + ")"
            )
            last_index: int = 0

            for match in re.finditer(special_pattern, text):
                prefix = text[last_index:match.start()]
                token_ids.extend(self.encode(prefix, allowed_special=None))

                special_token = match.group(0)
                if special_token in self.inverse_vocab:
                    token_ids.append(self.inverse_vocab[special_token])
                else:
                    raise TokenizerException(
                        f"Special token '{special_token}' not in vocabulary."
                    )
                last_index = match.end()
            
            text = text[last_index:]

            disallowed =[
                tok for tok in self.inverse_vocab
                if tok.startswith("</") and tok.endswith(">") and tok in text and tok not in allowed_special
            ]
            if disallowed:
                raise TokenizerException(
                    f"Disallowed special tokens found in text: {disallowed}"
                )
        tokens = []
        lines = text.split("\n")
        
if __name__ == "__main__":
    params = TurkishTokenizerParameters()
    tok = TurkishBPETokenizer(params)
    DUMMY_TEXT = "bu akşam güzel bir yemek yiyeceğim !"

    tok.fit(text=DUMMY_TEXT)
    print("Vocab:", tok.vocab)
    print("---" * 30)
    print("Merges:", tok.merges)
    print("---" * 30)
    print("Encode 'lowest':", tok.encode(DUMMY_TEXT))
