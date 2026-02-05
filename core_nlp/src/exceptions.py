from enum import Enum


class MorphologicalException(Enum):
  ANALYZE_ERROR = "Something happened during analyzing  {data}"
  ANALYZE_NOT_FOUND = "No analysis found for '{word}'"


class SpellingException(Enum):
  DICTIONARY_LOAD_ERROR = "Dictionary or rules could not be loaded"
  SUGGESTION_NOT_FOUND = "No suggestion found for '{word}'"
  CHECK_ERROR = "Error occurred while checking spelling for '{word}'"
  INVALID_INPUT = "Invalid input provided: '{input}'"
  UNKNOWN_ERROR = "An unknown error occurred"
