from __future__ import annotations

import ast
from pathlib import Path
import unittest


class LcdInternalMountingTest(unittest.TestCase):
    def _tree(self) -> ast.AST:
        script = Path(__file__).resolve().parents[1] / "scripts" / "generate_macintosh_case.py"
        return ast.parse(script.read_text(encoding="utf-8"))

    def test_front_shell_has_internal_lcd_screw_mount_parameters(self) -> None:
        tree = self._tree()
        params = next(node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name == "Params")
        param_names = {
            node.target.id
            for node in params.body
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
        }

        self.assertIn("lcd_mount_boss_radius", param_names)
        self.assertIn("lcd_mount_screw_hole_radius", param_names)
        self.assertIn("lcd_mount_boss_depth", param_names)
        self.assertIn("lcd_mount_screw_inset", param_names)

    def test_internal_lcd_mounts_are_fused_before_case_split(self) -> None:
        tree = self._tree()
        function_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        self.assertIn("make_lcd_internal_mounts", function_names)
        self.assertIn("make_front_inner_relief_cut", function_names)

        make_main_shell = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "make_main_shell"
        )
        source_names = {node.id for node in ast.walk(make_main_shell) if isinstance(node, ast.Name)}
        self.assertIn("front_inner_relief_cut", source_names)
        self.assertIn("lcd_mounts", source_names)

        cutter_tuples = [
            node
            for node in ast.walk(make_main_shell)
            if isinstance(node, ast.Tuple)
            and any(isinstance(elt, ast.Name) and elt.id == "front_inner_relief_cut" for elt in node.elts)
        ]
        self.assertTrue(cutter_tuples)

        fuse_calls = [
            node
            for node in ast.walk(make_main_shell)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "fuse"
            and any(isinstance(arg, ast.Name) and arg.id == "lcd_mounts" for arg in node.args)
        ]
        self.assertTrue(fuse_calls)

    def test_four_lcd_mount_bosses_have_screw_holes(self) -> None:
        tree = self._tree()
        function_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        self.assertIn("make_lcd_internal_mounts", function_names)

        mount_function = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "make_lcd_internal_mounts"
        )
        source_names = {node.id for node in ast.walk(mount_function) if isinstance(node, ast.Name)}
        self.assertIn("bosses", source_names)
        self.assertIn("holes", source_names)

        constants = [
            node.value
            for node in ast.walk(mount_function)
            if isinstance(node, ast.Constant) and isinstance(node.value, int)
        ]
        self.assertIn(4, constants)


if __name__ == "__main__":
    unittest.main()
