from __future__ import annotations

import ast
from pathlib import Path
import unittest


class FrontTiltTest(unittest.TestCase):
    def test_front_tilt_is_seven_degrees(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "generate_macintosh_case.py"
        source = script.read_text(encoding="utf-8")
        tree = ast.parse(source)

        params = next(node for node in ast.walk(tree) if isinstance(node, ast.ClassDef) and node.name == "Params")
        tilt_assignment = next(
            node for node in params.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "front_tilt_deg"
        )

        value = tilt_assignment.value
        self.assertIsInstance(value, ast.UnaryOp)
        self.assertIsInstance(value.op, ast.USub)
        self.assertIsInstance(value.operand, ast.Constant)
        self.assertEqual(value.operand.value, 7.0)

    def test_front_y_at_uses_front_tilt_angle(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "generate_macintosh_case.py"
        source = script.read_text(encoding="utf-8")

        self.assertIn("math.tan(math.radians(abs(P.front_tilt_deg)))", source)
        self.assertNotIn("* 0.212", source)


if __name__ == "__main__":
    unittest.main()
