import os
from pathlib import Path


def load_dic(path: str | Path) -> dict:
  """Load dictionary from a file."""
  dictionary: dict = {}

  if not os.path.exists(path):
    print(f"Error: Dictionary file not found at {path}")

  try:
    with open(path, encoding="utf-8") as f:
      next(f)
      for line in f:
        line = line.strip()
        if not line:
          continue

        parts = line.split("/")
        word = parts[0]
        if len(parts) > 1:
          flags = parts[1].split(",")
          dictionary[word] = {
            "type": "root",
            "flags": set(flags),
            "bool": True,
          }
        else:
          dictionary[word] = {
            "type": "root",
            "flags": set(),
            "bool": True,
          }
    return dictionary
  except OSError as e:
    print(f"Error loading dictionary from {path}: {e}")
    return {}


def load_aff(path: str | Path) -> dict:
  """Load affix rules from a file."""
  rules: dict = {}
  if not os.path.exists(path):
    print(f"Error: Affix file not found at {path}")

  try:
    with open(path, encoding="utf-8") as f:
      for line in f:
        parts = line.split()
        if not parts:
          continue

        if parts[0] == "SFX":
          if len(parts) < 5:
            continue

          flag = parts[1]
          strip = parts[2]
          add = parts[3]
          condition = parts[4]

          if strip == "0":
            strip = ""
          if add == "0":
            add = ""

          if flag not in rules:
            rules[flag] = []

          rules[flag].append({"strip": strip, "add": add, "cond": condition})
    return rules
  except OSError as e:
    print(f"Error loading affix rules from {path}: {e}")
    return {}
