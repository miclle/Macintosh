from __future__ import annotations

import ast
from pathlib import Path
import unittest


class CaseSplitTest(unittest.TestCase):
    def _constant_value(self, node: ast.AST, constants: dict[str, float]) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -self._constant_value(node.operand, constants)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "P":
            return constants[node.attr]
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return self._constant_value(node.left, constants) + self._constant_value(node.right, constants)
        raise AssertionError(f"Unsupported profile value: {ast.dump(node)}")

    def _params_constants(self, tree: ast.AST) -> dict[str, float]:
        params = next(node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name == "Params")
        constants: dict[str, float] = {}
        for node in params.body:
            if (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, (int, float))
            ):
                constants[node.target.id] = float(node.value.value)
        return constants

    def _split_profile_points(self, tree: ast.AST) -> list[tuple[float, float]]:
        constants = self._params_constants(tree)
        profile_function = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "case_split_profile"
        )
        returned_list = next(
            node.value
            for node in ast.walk(profile_function)
            if isinstance(node, ast.Return) and isinstance(node.value, ast.List)
        )

        points: list[tuple[float, float]] = []
        for item in returned_list.elts:
            self.assertIsInstance(item, ast.Tuple)
            self.assertEqual(len(item.elts), 2)
            points.append((
                self._constant_value(item.elts[0], constants),
                self._constant_value(item.elts[1], constants),
            ))
        return points

    def test_case_is_generated_as_front_and_rear_shells(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "generate_macintosh_case.py"
        source = script.read_text(encoding="utf-8")
        tree = ast.parse(source)

        generated_names = {
            node.args[1].value
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "add_shape"
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Constant)
            and isinstance(node.args[1].value, str)
        }

        self.assertIn("front_case_shell", generated_names)
        self.assertIn("rear_case_shell", generated_names)
        self.assertNotIn("single_piece_slanted_main_shell", generated_names)

    def test_split_profile_is_parallel_to_front_slope_and_lower_setback(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "generate_macintosh_case.py"
        source = script.read_text(encoding="utf-8")
        tree = ast.parse(source)

        function_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        self.assertIn("case_split_profile", function_names)
        self.assertIn("split_mask_from_profile", function_names)

        self.assertIn("split_jog_z = P.io_z + 8", source)
        self.assertIn("initial_upper_split_y = 8", source)
        self.assertIn("forward_shift_fraction = 2 / 3", source)
        self.assertIn("upper_split_y = initial_upper_split_y - (lower_split_y - initial_upper_split_y) * forward_shift_fraction", source)
        self.assertIn("split_offset = upper_split_y - front_y_at(split_jog_z)", source)
        self.assertIn("(lower_split_y, split_jog_z)", source)
        self.assertIn("(front_y_at(split_jog_z) + split_offset, split_jog_z)", source)
        self.assertIn("(front_y_at(front_top_z) + split_offset, front_top_z)", source)
        self.assertIn("(front_y_at(P.body_height + 20) + split_offset, P.body_height + 20)", source)


if __name__ == "__main__":
    unittest.main()
