from __future__ import annotations

import ast
from pathlib import Path
import unittest


class FrontScreenFrameTest(unittest.TestCase):
    def test_flat_lcd_frame_is_integrated_into_main_shell(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "generate_macintosh_case.py"
        source = script.read_text(encoding="utf-8")
        tree = ast.parse(source)

        call_names = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        assigned_names = {
            target.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Assign)
            for target in node.targets
            if isinstance(target, ast.Name)
        }

        self.assertNotIn("slanted_rect_frame", call_names)
        self.assertNotIn("screen_recess_cut", assigned_names)
        self.assertNotIn("flat_frame", assigned_names)


if __name__ == "__main__":
    unittest.main()
