from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rpmatrix.config import expand_conditions, load_matrix_config

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class MatrixConfigTest(unittest.TestCase):
    def test_base_config_expands_expected_conditions(self) -> None:
        config = load_matrix_config(PROJECT_ROOT / "configs" / "matrix.base.yaml")
        conditions = expand_conditions(config)
        self.assertEqual(len(conditions), 27)
        self.assertEqual(conditions[0]["benchmark"], "osworld_subset")
        self.assertEqual(conditions[0]["policy"], "react")
        self.assertEqual(conditions[0]["seed"], 13)


if __name__ == "__main__":
    unittest.main()
