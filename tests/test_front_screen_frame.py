from __future__ import annotations

import ast
from pathlib import Path
import unittest


class FrontScreenFrameTest(unittest.TestCase):
    def _tree(self) -> ast.AST:
        script = Path(__file__).resolve().parents[1] / "scripts" / "generate_macintosh_case.py"
        return ast.parse(script.read_text(encoding="utf-8"))

    def test_flat_lcd_frame_is_integrated_into_main_shell(self) -> None:
        tree = self._tree()

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

    def test_lcd_glass_visual_fills_inner_opening_without_black_backing(self) -> None:
        tree = self._tree()
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
        self.assertNotIn("sloped_black_lcd_bezel_visual", generated_names)

        add_shape_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "add_shape"
            and len(node.args) >= 3
            and isinstance(node.args[1], ast.Constant)
            and node.args[1].value == "lcd_dark_glass_visual"
        ]
        self.assertEqual(len(add_shape_calls), 1)

        visual_shape = add_shape_calls[0].args[2]
        self.assertIsInstance(visual_shape, ast.Call)
        self.assertIsInstance(visual_shape.func, ast.Name)
        self.assertEqual(visual_shape.func.id, "slanted_box")

        glass_width = visual_shape.args[0]
        self.assertIsInstance(glass_width, ast.Attribute)
        self.assertIsInstance(glass_width.value, ast.Name)
        self.assertEqual(glass_width.value.id, "P")
        self.assertEqual(glass_width.attr, "lcd_width")

        glass_x = visual_shape.args[3]
        self.assertIsInstance(glass_x, ast.BinOp)
        self.assertIsInstance(glass_x.left, ast.UnaryOp)
        self.assertIsInstance(glass_x.left.op, ast.USub)
        self.assertIsInstance(glass_x.left.operand, ast.Attribute)
        self.assertEqual(glass_x.left.operand.attr, "lcd_width")

        glass_z = visual_shape.args[5]
        self.assertIsInstance(glass_z, ast.Attribute)
        self.assertIsInstance(glass_z.value, ast.Name)
        self.assertEqual(glass_z.value.id, "P")
        self.assertEqual(glass_z.attr, "screen_z")

        glass_height = visual_shape.args[2]
        self.assertIsInstance(glass_height, ast.Attribute)
        self.assertIsInstance(glass_height.value, ast.Name)
        self.assertEqual(glass_height.value.id, "P")
        self.assertEqual(glass_height.attr, "lcd_height")

    def test_screen_bezel_is_cut_into_front_shell_instead_of_added_as_surface(self) -> None:
        tree = self._tree()
        function_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        self.assertIn("make_screen_bezel_recess_cut", function_names)

        make_main_shell = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "make_main_shell"
        )
        source_names = {node.id for node in ast.walk(make_main_shell) if isinstance(node, ast.Name)}
        self.assertIn("screen_bezel_recess_cut", source_names)

        script = Path(__file__).resolve().parents[1] / "scripts" / "generate_macintosh_case.py"
        source = script.read_text(encoding="utf-8")
        self.assertNotIn("make_screen_frame_surfaces()", source)
        self.assertNotIn("Part.makeCompound([shell, bevel])", source)

    def test_screen_bezel_uses_uniform_slope_width_on_all_sides(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "generate_macintosh_case.py"
        source = script.read_text(encoding="utf-8")
        self.assertNotIn("screen_bezel_vertical_slope_width", source)
        self.assertIn("slope_outer_h = P.lcd_height + 2 * P.screen_bezel_slope_width", source)
        self.assertIn("screen_bezel_recess_origin_z()", source)

    def test_screen_bezel_uses_thirty_degree_inward_slope(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "generate_macintosh_case.py"
        source = script.read_text(encoding="utf-8")
        self.assertIn("screen_bezel_slope_angle_deg: float = 30.0", source)
        self.assertIn("def screen_bezel_recess_depth() -> float:", source)
        self.assertIn(
            "return P.screen_bezel_slope_width * math.tan(math.radians(P.screen_bezel_slope_angle_deg))",
            source,
        )

    def test_screen_bezel_boolean_overlap_extends_along_same_slope_planes(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "generate_macintosh_case.py"
        source = script.read_text(encoding="utf-8")
        self.assertIn("screen_bezel_boolean_overlap: float = 0.6", source)
        self.assertIn("front_overlap = P.screen_bezel_boolean_overlap", source)
        self.assertIn("front_y = -front_overlap", source)
        self.assertIn("overlap_inset = front_overlap * P.screen_bezel_slope_width / recess_depth", source)
        self.assertIn("outer_bottom_left = v(outer_left - overlap_inset, front_y, -overlap_inset)", source)
        self.assertIn("outer_top_right = v(outer_right + overlap_inset, front_y, slope_outer_h + overlap_inset)", source)
        self.assertIn("front_y_at(screen_bezel_recess_origin_z())", source)
        self.assertNotIn("front_y_at(P.screen_z - P.screen_bezel_slope_width) + 0.6", source)

    def test_screen_bezel_recess_origin_aligns_inner_bottom_to_lcd_bottom(self) -> None:
        tree = self._tree()
        function_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        self.assertIn("screen_bezel_recess_origin_z", function_names)

        script = Path(__file__).resolve().parents[1] / "scripts" / "generate_macintosh_case.py"
        source = script.read_text(encoding="utf-8")
        self.assertIn("rotation = math.radians(P.front_tilt_deg)", source)
        self.assertIn("recess_depth = screen_bezel_recess_depth()", source)
        self.assertIn("P.screen_z - recess_depth * math.sin(rotation) - P.screen_bezel_slope_width * math.cos(rotation)", source)

    def test_screen_cut_preserves_bezel_inner_edge(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "generate_macintosh_case.py"
        source = script.read_text(encoding="utf-8")
        self.assertIn("screen_cut = slanted_box(", source)
        self.assertIn("P.lcd_width,", source)
        self.assertIn("P.lcd_height,", source)
        self.assertIn("P.screen_z,", source)
        self.assertNotIn("P.lcd_width + 0.2", source)
        self.assertNotIn("P.lcd_height + 0.2", source)
        self.assertNotIn("P.screen_z - 0.1", source)

    def test_screen_through_cut_starts_behind_bezel_to_keep_bottom_slope_continuous(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "generate_macintosh_case.py"
        source = script.read_text(encoding="utf-8")
        self.assertIn("screen_cut_bezel_overlap: float = 0.2", source)
        self.assertIn("screen_cut_y = front_y_at(P.screen_z) + screen_bezel_recess_depth() - P.screen_cut_bezel_overlap", source)
        self.assertIn("screen_cut_depth = P.front_inner_relief_depth - screen_bezel_recess_depth() + P.screen_cut_bezel_overlap", source)
        self.assertIn("screen_cut_y,", source)
        self.assertIn("screen_cut_depth,", source)
        self.assertNotIn("front_y_at(P.screen_z) - 24", source)


if __name__ == "__main__":
    unittest.main()
