from __future__ import annotations

import ast
from pathlib import Path
import unittest


class FrontBadgePositionTest(unittest.TestCase):
    def test_badge_anchor_is_left_and_above_front_slope_lower_edge(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "generate_macintosh_case.py"
        source = script.read_text(encoding="utf-8")
        tree = ast.parse(source)

        assignments = {
            target.id: node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name) and target.id in {"badge_x", "badge_z"}
        }

        self.assertIn("badge_x", assignments)
        self.assertIn("badge_z", assignments)

        badge_x = assignments["badge_x"]
        self.assertIsInstance(badge_x, ast.BinOp)
        self.assertIsInstance(badge_x.op, ast.Add)
        self.assertIsInstance(badge_x.right, ast.Constant)
        self.assertLessEqual(badge_x.right.value, 47)

        badge_z = assignments["badge_z"]
        self.assertIsInstance(badge_z, ast.BinOp)
        self.assertIsInstance(badge_z.left, ast.Attribute)
        self.assertIsInstance(badge_z.left.value, ast.Name)
        self.assertEqual(badge_z.left.value.id, "P")
        self.assertEqual(badge_z.left.attr, "io_z")
        self.assertIsInstance(badge_z.op, ast.Sub)
        self.assertIsInstance(badge_z.right, ast.Constant)
        self.assertEqual(badge_z.right.value, 4)


if __name__ == "__main__":
    unittest.main()
