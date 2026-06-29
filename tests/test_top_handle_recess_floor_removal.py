from __future__ import annotations

import ast
from pathlib import Path
import unittest


class TopHandleRecessFloorRemovalTest(unittest.TestCase):
    def test_top_handle_recess_floor_is_not_generated(self) -> None:
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

        self.assertNotIn("top_handle_recess_floor", generated_names)
        self.assertNotIn('"top_handle_recess_floor"', source)
        self.assertNotIn("顶部提手凹槽底面", source)


if __name__ == "__main__":
    unittest.main()
