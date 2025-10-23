from error_messages import TokenizerErrorMessages

class TokenizerException(Exception):
    """Custom exception for BPE Tokenizer errors."""

    def __init__(self, message: TokenizerErrorMessages, **kwargs):
        # Support formatting placeholders like {error}
        self.message = message.value.format(**kwargs)
        super().__init__(self.message)
