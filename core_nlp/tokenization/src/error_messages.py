from enum import Enum

class TokenizerErrorMessages(Enum):
    """Custom error messages for Tokenizers"""
    INVALID_METHOD_FOR_CURRENT_CLASS = "Error choosing Tokenizer class: Invalid method selected for current Tokenizer"
    EMPTY_SENTENCE_ERROR = "Error tokenizing data: No sentence."
    UNEXPECTED_ERROR = "An unexpected error occurred while loading data: {error}"