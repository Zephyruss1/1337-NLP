import sys
from pathlib import Path
from pprint import pprint

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core_nlp.src.engine import MorphAnalyzer

morph_analyzer = MorphAnalyzer()

pprint(morph_analyzer.analyze("görebiliyorum"))
print()
pprint(morph_analyzer.analyze("geldim"))