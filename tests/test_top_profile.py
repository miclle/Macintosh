from __future__ import annotations

import ast
from pathlib import Path
import unittest


class TopProfileTest(unittest.TestCase):
    def test_top_surface_has_no_separate_front_bevel_segment(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "generate_macintosh_case.py"
        source = script.read_text(encoding="utf-8")
        tree = ast.parse(source)

        side_profile_assignments = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "side_profile" for target in node.targets)
        ]

        self.assertEqual(len(side_profile_assignments), 1)
        side_profile = side_profile_assignments[0].value
        self.assertIsInstance(side_profile, ast.List)

        top_segment_names = {
            name.id
            for item in side_profile.elts
            for name in ast.walk(item)
            if isinstance(name, ast.Name) and name.id.startswith("top_front_bevel")
        }

        self.assertEqual(top_segment_names, set())

    def test_front_slope_extends_below_front_io_recess_shadow(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "generate_macintosh_case.py"
        source = script.read_text(encoding="utf-8")
        tree = ast.parse(source)

        assignments = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "front_bottom_z" for target in node.targets)
        ]

        self.assertEqual(len(assignments), 1)
        value = assignments[0].value
        self.assertIsInstance(value, ast.BinOp)
        self.assertIsInstance(value.left, ast.Attribute)
        self.assertIsInstance(value.left.value, ast.Name)
        self.assertEqual(value.left.value.id, "P")
        self.assertEqual(value.left.attr, "io_z")
        self.assertIsInstance(value.op, ast.Sub)
        self.assertIsInstance(value.right, ast.Constant)
        self.assertGreater(value.right.value, 3)

    def test_lower_wall_below_front_slope_is_set_back(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "generate_macintosh_case.py"
        source = script.read_text(encoding="utf-8")
        tree = ast.parse(source)

        assignments = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "front_step_rear_y" for target in node.targets)
        ]

        self.assertEqual(len(assignments), 1)
        value = assignments[0].value
        self.assertIsInstance(value, ast.UnaryOp)
        self.assertIsInstance(value.op, ast.USub)
        self.assertIsInstance(value.operand, ast.Constant)
        self.assertEqual(value.operand.value, 10)

        side_profile = next(
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "side_profile" for target in node.targets)
        )
        self.assertIsInstance(side_profile, ast.List)
        self.assertEqual(len(side_profile.elts), 8)


if __name__ == "__main__":
    unittest.main()
