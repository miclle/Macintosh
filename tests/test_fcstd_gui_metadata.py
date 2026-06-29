from __future__ import annotations

from pathlib import Path
import unittest
import zipfile


REMOVED_REAR_LABELS = (
    "后侧 Macintosh 铭牌",
    "后侧徽标底座",
    "后侧右服务栏底面",
    "后侧认证标签底板",
    "后侧底部接口舱底面",
)


class FcstdGuiMetadataTest(unittest.TestCase):
    def test_model_keeps_gui_metadata_without_removed_rear_features(self) -> None:
        model = Path(__file__).resolve().parents[1] / "models" / "macintosh_ipad_lcd_case.FCStd"

        with zipfile.ZipFile(model) as archive:
            names = set(archive.namelist())
            self.assertIn("GuiDocument.xml", names)
            gui_document = archive.read("GuiDocument.xml").decode("utf-8")

        for label in REMOVED_REAR_LABELS:
            self.assertNotIn(label, gui_document)


if __name__ == "__main__":
    unittest.main()
