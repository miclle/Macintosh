from __future__ import annotations

import ast
from pathlib import Path
import unittest


class BodyDimensionsTest(unittest.TestCase):
    def test_body_depth_is_reduced_by_one_fifth(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "generate_macintosh_case.py"
        source = script.read_text(encoding="utf-8")
        tree = ast.parse(source)

        params = next(node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name == "Params")
        depth_assignment = next(
            node for node in params.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "body_depth"
        )

        self.assertIsInstance(depth_assignment.value, ast.Constant)
        self.assertEqual(depth_assignment.value.value, 228.0)


if __name__ == "__main__":
    unittest.main()
