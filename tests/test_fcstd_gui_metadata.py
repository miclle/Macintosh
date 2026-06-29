from __future__ import annotations

from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
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

    def test_model_opens_with_every_component_visible(self) -> None:
        model = Path(__file__).resolve().parents[1] / "models" / "macintosh_ipad_lcd_case.FCStd"

        with zipfile.ZipFile(model) as archive:
            document = ET.fromstring(archive.read("Document.xml"))
            gui_document = ET.fromstring(archive.read("GuiDocument.xml"))

        object_names = {
            item.get("name")
            for item in document.find("Objects")
            if item.tag == "Object"
        }
        providers = {
            item.get("name"): item
            for item in gui_document.find("ViewProviderData")
            if item.tag == "ViewProvider"
        }

        self.assertEqual(object_names, set(providers))
        for name, provider in providers.items():
            visibility = provider.find("./Properties/Property[@name='Visibility']/Bool")
            self.assertIsNotNone(visibility, name)
            self.assertEqual(visibility.get("value"), "true", name)


if __name__ == "__main__":
    unittest.main()
