from typing import Any
from dataloader import load_aff, load_dic
from exceptions import MorphologicalException
from pathlib import Path
import re

_ROOT_PATH: Path = Path(__file__).parent.parent


class MorphAnalyzer:
  def __init__(self):
    try:
      self.dictionary: dict = load_dic(_ROOT_PATH / "data" / "tr_TR.dic")
      self.rules: dict = load_aff(_ROOT_PATH / "data" / "tr_TR.aff")
      if self.dictionary is None or self.rules is None:
        raise ValueError("Dictionary or rules could not be loaded")
      self._build_reverse_rules()
      print("Data loaded successfully")
    except Exception as e:
      print(f"Error loading data: {e}")
      raise

  def _build_reverse_rules(self) -> None:
    """Index rules by their 'add' string for fast lookup."""
    self.rules_by_add = {}
    if not self.rules:
      return
    for flag, rules in self.rules.items():
      for rule in rules:
        add = rule["add"]
        if add not in self.rules_by_add:
          self.rules_by_add[add] = []
        self.rules_by_add[add].append(rule)

  def _recursive_split(self, stem: str, suffix: str) -> list[list[str]]:
    """
    Recursively decompose a suffix string into a list of valid suffixes.
    stem: The word part before this suffix (used for condition checking).
    suffix: The suffix string to split.
    Returns: A list of possible splits (each split is a list of suffix strings).
    """
    if not suffix:
      return [[]]

    results: list = []
    # Try all possible prefixes of the suffix
    for i in range(1, len(suffix) + 1):
      part = suffix[:i]
      rest = suffix[i:]
      print(part)
      print(rest)

      # Check if 'part' is a valid suffix in our rules
      if part in self.rules_by_add:
        # Check if valid for the current stem
        valid = False
        for rule in self.rules_by_add[part]:
          cond = rule["cond"]
          # Existing logic for condition: if '.' or match
          if cond == "." or re.match(cond, stem):
            valid = True
            break

        if valid:
          # Recurse on the rest
          sub_results = self._recursive_split(stem + part, rest)
          for res in sub_results:
            results.append([part] + res)
    return results

  def _select_best_match(self, list_of_possible_matches: list[list[str]]) -> list[list[str]]:
    """
    Selects the most probable morphological parse based on known suffixes.
    Prioritizes the analysis where the most parts are recognized suffixes.
    """
    # TODO: Research a way to parse morphological structures more accurately.
    if not list_of_possible_matches:
      return []

    # Build a quick lookup set of all valid suffix strings from self.rules
    known_suffixes: set[str] = set()
    for flag_rules in self.rules.values():
      for rule in flag_rules:
        # Add the suffix string (the 'add' part) to our known list
        if rule["add"]:
          known_suffixes.add(rule["add"])

    # Add common single-letter buffers/suffixes that might not be explicit in rules
    # (Turkish specific: y, n, s, ş, t for buffering or causality)
    known_suffixes.update({"y", "n", "s", "m", "k", "z", "l"})

    scored_candidates: list[tuple[float, list[str]]] = []

    for candidate in list_of_possible_matches:
      score = 0
      valid_parts_count = 0

      for part in candidate:
        if part in known_suffixes:
          score += 10  # High reward for known suffix
          valid_parts_count += 1
        elif len(part) == 1:
          # Single letters are risky unless known, give small penalty
          score -= 1
        else:
          # Unknown multi-letter string: high penalty
          # likely a bad split like 'emed'
          score -= 5

      # GRANULARITY TIE-BREAKER:
      # If we have two valid lists: ['eme', 'di', 'm'] and ['e', 'me', 'di', 'm']
      # And assuming 'eme', 'e', 'me' are all known suffixes:
      # We prefer the one with MORE parts (higher granularity).
      score += len(candidate) * 0.5

      scored_candidates.append((score, candidate))

    # Sort by score descending
    scored_candidates.sort(key=lambda x: x[0], reverse=True)

    # Return the best candidates (there might be ties, return all ties)
    if not scored_candidates:
      return []

    best_score = scored_candidates[0][0]
    return [cand for s, cand in scored_candidates if s == best_score]

  def analyze(self, sentences: str) -> list[dict[str, Any] | str]:
    """
    Perform morphological analysis on Turkish words to identify their roots and suffixes.
    Args:
        sentences: A space-separated string of Turkish words to analyze (lowercase conversion applied)

    Returns:
        A list where each element is either:
        - dict: A valid morphological analysis containing:
            - 'root': The base dictionary form of the word
            - 'stem': The combined suffix string applied to the root
            - 'suffixes': A list of individual suffix components (recursively split)
            - 'flag_number': The morphological rule flag that was applied
        - str: An error message if no valid analysis was found for a word

    Example:
        >>> MorphAnalyzer().analyze("göremedim")
        [{'root': 'gör', 'stem': 'emedim', 'suffixes': ['e', 'me', 'di', 'm'], 'flag_number': '19944'}]

    Raises:
        MorphologicalException.ANALYZE_ERROR: If an analysis error occurs during processing
    """
    analyses: list[dict[str, Any] | str] = []
    list_of_sentences: list[str] = [word.lower() for word in sentences.split(" ")]
    word: str = ""

    try:
      # Check if the word is a root word itself
      for word in list_of_sentences:
        # Try to find roots that could form this word with suffixes
        for root, flags in self.dictionary.items():
          # Skip if root is longer than the word
          if len(root) >= len(word):
            continue

          # Check if word starts with this root
          if not word.startswith(root):
            continue

          # TODO: Remove dueue unused variable
          suffix_list: list = []
          suffix = word[len(root) :]
          suffix_list.append(suffix)

          # Check each flag associated with this root
          for flag in flags.get("flags", set()):
            if flag not in self.rules:
              continue

            # Check each rule for this flag
            for rule in self.rules[flag]:
              strip = rule["strip"]
              add = rule["add"]
              condition = rule["cond"]

              # Check if root ends with the condition pattern
              if condition != "." and not re.match(condition, root):
                continue

              # Calculate what the word should be if this rule applies
              modified_root = root
              if strip and re.match(strip, modified_root):
                modified_root = modified_root[: -len(strip)]

              expected_word = modified_root + add

              # If it matches our word, we found an analysis
              if expected_word == word:
                # Now try to granularly split the 'add' part
                possible_splits = self._recursive_split(modified_root, add)
                best_match = self._select_best_match(possible_splits)
                if not best_match:
                  best_match = [[add]]

                # Add analysis for each valid split
                for possible_split in possible_splits:
                  analyses.append({
                    "root": root,
                    "stem": add,
                    "suffixes": possible_split,
                    "flag_number": flag,
                  })

      return analyses if analyses else [f"No analysis found for '{word}'"]

    except MorphologicalException.ANALYZE_ERROR:
      raise MorphologicalException.ANALYZE_ERROR.value.format(data=word)
