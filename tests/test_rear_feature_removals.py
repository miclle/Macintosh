from __future__ import annotations

import ast
from pathlib import Path
import unittest


REMOVED_REAR_FEATURES = {
    "rear_macintosh_nameplate",
    "rear_badge_base",
    "rear_right_service_column_floor",
    "rear_regulatory_label_plate",
    "rear_bottom_port_bay_floor",
    "rear_rohs_mark_block",
    "rear_right_vertical_cover",
    "rear_right_small_switch_recess",
    "rear_right_small_switch_tab",
    "rear_right_usb_c_port",
    "rear_round_audio_port",
    "rear_small_round_port",
    "lcd_panel_envelope_210x160x8",
    "lcd_left_side_retaining_rail",
    "lcd_right_side_retaining_rail",
    "hdmi_driver_board_keepout_105x70",
    "battery_pack_keepout",
    "lower_front_clean_access_panel",
    "front_left_integral_foot",
    "front_right_integral_foot",
    "rear_bottom_plate_seam",
}

REMOVED_REAR_FEATURE_PREFIXES = (
    "rear_badge_stripe_",
    "rear_regulatory_label_text_line_",
    "rear_dsub_connector_shell_",
    "rear_dsub_connector_dark_face_",
    "rear_bottom_bay_screw_",
    "bottom_plate_m3_boss_",
    "driver_board_m2_5_standoff_",
    "rear_left_top_vent_slit_",
    "right_side_vent_shadow_",
    "left_side_vent_shadow_",
    "rear_right_top_vent_slit_",
)


class RemovedFeatureTest(unittest.TestCase):
    def test_removed_features_are_not_generated(self) -> None:
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

        self.assertTrue(generated_names.isdisjoint(REMOVED_REAR_FEATURES))
        for feature_prefix in REMOVED_REAR_FEATURE_PREFIXES:
            self.assertNotIn(f'add_shape(doc, f"{feature_prefix}', source)
        self.assertNotIn('("left", -P.body_width / 2.0 + 18)', source)
        self.assertNotIn('("right", P.body_width / 2.0 - 0.6)', source)
        self.assertNotIn("P.body_width / 2.0 - 52", source)


if __name__ == "__main__":
    unittest.main()
