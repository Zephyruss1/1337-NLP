import unittest
from core_nlp.src.dataloader import load_aff, load_dic
from pathlib import Path

_ROOT_PATH: Path = Path(__file__).parent.parent

class TestDataloader(unittest.TestCase):
    @unittest.expectedFailure
    def test_load_aff(self) -> None:
        self.assertEqual(load_aff(_ROOT_PATH / "data" / "tr_TR.aff"), {})

    @unittest.expectedFailure
    def test_load_dic(self) -> None:
        self.assertEqual(load_dic(_ROOT_PATH / "data" / "tr_TR.dic"), {})


