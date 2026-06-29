"""Generate a compact retro iPad LCD enclosure for 3D printing.

The model follows the user's latest reference photos: a clean one-piece main
shell, slanted front face, lower front lip that projects forward, slightly
lower rear top with clipped back corners, a recessed top carry handle, side
vents, modern front I/O, and a removable bottom plate for installing the LCD,
HDMI driver board, speakers, and battery.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
import math
import xml.etree.ElementTree as ET

import FreeCAD as App
import Part


@dataclass(frozen=True)
class Params:
    lcd_width: float = 210.0
    lcd_height: float = 160.0
    body_width: float = 230.0
    body_depth: float = 228.0
    body_height: float = 275.0
    body_corner_radius: float = 2.0
    edge_soft_radius: float = 0.45
    wall: float = 3.0
    front_tilt_deg: float = -7.0

    screen_z: float = 92.0
    screen_flat_frame_width: float = 5.0
    screen_bezel_slope_width: float = 3.0
    screen_bezel_recess_depth: float = 3.0
    screen_lower_forward_y: float = -28.0

    io_z: float = 50.0
    bottom_plate_thickness: float = 4.0
    lower_service_panel_height: float = 42.0


P = Params()


def screen_frame_margin() -> float:
    return P.screen_flat_frame_width + P.screen_bezel_slope_width


DOCUMENT_LABEL_ZH = "Macintosh iPad LCD 外壳"

OBJECT_LABELS_ZH = {
    "single_piece_slanted_main_shell": "一体式倾斜主外壳",
    "removable_bottom_plate": "可拆卸底板",
    "sloped_white_screen_bezel_surface": "白色屏幕斜面边框",
    "sloped_black_lcd_bezel_visual": "黑色 LCD 斜面边框",
    "lcd_dark_glass_visual": "LCD 深色玻璃",
    "front_io_recess_shadow": "前侧接口凹槽阴影",
    "front_usb_a_left": "前侧左 USB-A 口",
    "front_usb_a_right": "前侧右 USB-A 口",
    "front_sd_slot": "前侧 SD 卡槽",
    "front_usb_c_slot": "前侧 USB-C 槽",
    "front_small_status_slit": "前侧小状态灯缝",
    "front_badge_white_backing": "前侧徽标白色底板",
    "lower_panel_small_led": "下方面板小 LED",
    "lower_panel_round_button": "下方面板圆形按钮",
    "design_parameters": "设计参数",
}


def chinese_label_for(name: str) -> str:
    if name in OBJECT_LABELS_ZH:
        return OBJECT_LABELS_ZH[name]

    numbered_prefixes = (
        ("front_rainbow_badge_stripe_", "前侧彩虹徽标条"),
    )
    for prefix, label in numbered_prefixes:
        if name.startswith(prefix):
            return f"{label} {name.removeprefix(prefix)}"

    return name


def add_shape(doc, name: str, shape, color):
    obj = doc.addObject("Part::Feature", name)
    obj.Label = chinese_label_for(name)
    obj.Shape = shape
    view = getattr(obj, "ViewObject", None)
    if view is not None:
        view.ShapeColor = color[:3]
        view.Transparency = int(color[3]) if len(color) > 3 else 0
    return obj


def capture_gui_metadata(model_path: str) -> dict[str, bytes]:
    """Read GUI/view metadata from an existing FCStd before headless save."""
    if not os.path.exists(model_path):
        return {}
    try:
        with zipfile.ZipFile(model_path, "r") as archive:
            if "GuiDocument.xml" not in archive.namelist():
                return {}
            return {
                name: archive.read(name)
                for name in archive.namelist()
                if name == "GuiDocument.xml"
                or name.startswith("thumbnails/")
                or name.startswith("LineColorArray")
                or name.startswith("PointColorArray")
                or name.startswith("ShapeAppearance")
            }
    except zipfile.BadZipFile:
        return {}


def filter_gui_document(gui_document: bytes, object_names: set[str]) -> bytes:
    root = ET.fromstring(gui_document)
    provider_data = root.find("ViewProviderData")
    if provider_data is None:
        return gui_document

    for provider in list(provider_data):
        if provider.tag == "ViewProvider" and provider.get("name") not in object_names:
            provider_data.remove(provider)
    provider_data.set("Count", str(sum(1 for child in provider_data if child.tag == "ViewProvider")))
    ET.indent(root, space="    ")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def restore_gui_metadata(model_path: str, gui_metadata: dict[str, bytes], object_names: set[str]) -> None:
    if not gui_metadata:
        return

    filtered_metadata = dict(gui_metadata)
    filtered_metadata["GuiDocument.xml"] = filter_gui_document(gui_metadata["GuiDocument.xml"], object_names)

    fd, temp_path = tempfile.mkstemp(suffix=".FCStd")
    os.close(fd)
    try:
        with zipfile.ZipFile(model_path, "r") as source, zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED) as target:
            metadata_names = set(filtered_metadata)
            for item in source.infolist():
                if item.filename in metadata_names:
                    continue
                target.writestr(item, source.read(item.filename))
            for name, data in filtered_metadata.items():
                target.writestr(name, data)
        shutil.move(temp_path, model_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def rounded_box(width: float, depth: float, height: float, radius: float, base: App.Vector):
    shape = Part.makeBox(width, depth, height, base)
    if radius <= 0:
        return shape
    try:
        return shape.makeFillet(radius, shape.Edges)
    except Exception:
        return shape


def soft_edges(shape, radius: float | None = None):
    radius = P.edge_soft_radius if radius is None else radius
    if radius <= 0:
        return shape
    try:
        return shape.makeFillet(radius, shape.Edges)
    except Exception:
        return shape


def box(width: float, depth: float, height: float, x: float, y: float, z: float):
    return Part.makeBox(width, depth, height, App.Vector(x, y, z))


def cyl_y(radius: float, length: float, x: float, y: float, z: float):
    return Part.makeCylinder(radius, length, App.Vector(x, y, z), App.Vector(0, 1, 0))


def cyl_z(radius: float, height: float, x: float, y: float, z: float):
    return Part.makeCylinder(radius, height, App.Vector(x, y, z), App.Vector(0, 0, 1))


def prism_from_yz(width: float, yz_points: list[tuple[float, float]], x_center: float = 0):
    x0 = x_center - width / 2.0
    points = [App.Vector(x0, y, z) for y, z in yz_points]
    if yz_points[0] != yz_points[-1]:
        points.append(App.Vector(x0, yz_points[0][0], yz_points[0][1]))
    poly = Part.makePolygon(points)
    return Part.Face(poly).extrude(App.Vector(width, 0, 0))


def slanted_box(width: float, depth: float, height: float, x: float, y: float, z: float):
    """Box whose local vertical face follows the tilted front panel."""
    shape = Part.makeBox(width, depth, height)
    shape.Placement = App.Placement(
        App.Vector(x, y, z),
        App.Rotation(App.Vector(1, 0, 0), P.front_tilt_deg),
    )
    return shape


def slanted_bezel_frame(
    outer_width: float,
    outer_height: float,
    inner_width: float,
    inner_height: float,
    recess_depth: float,
    x: float,
    y: float,
    z: float,
):
    """Four equal-width faces that slope inward to the LCD opening."""
    outer_left = -outer_width / 2.0
    outer_right = outer_width / 2.0
    inner_left = -inner_width / 2.0
    inner_right = inner_width / 2.0
    margin_z = (outer_height - inner_height) / 2.0
    inner_bottom = margin_z
    inner_top = margin_z + inner_height

    def v(px: float, py: float, pz: float) -> App.Vector:
        return App.Vector(px, py, pz)

    faces = []
    quads = [
        # bottom, top, left, right
        [v(outer_left, 0, 0), v(outer_right, 0, 0), v(inner_right, recess_depth, inner_bottom), v(inner_left, recess_depth, inner_bottom)],
        [v(outer_right, 0, outer_height), v(outer_left, 0, outer_height), v(inner_left, recess_depth, inner_top), v(inner_right, recess_depth, inner_top)],
        [v(outer_left, 0, outer_height), v(outer_left, 0, 0), v(inner_left, recess_depth, inner_bottom), v(inner_left, recess_depth, inner_top)],
        [v(outer_right, 0, 0), v(outer_right, 0, outer_height), v(inner_right, recess_depth, inner_top), v(inner_right, recess_depth, inner_bottom)],
    ]
    for quad in quads:
        faces.append(Part.Face(Part.makePolygon(quad + [quad[0]])))

    shape = Part.makeCompound(faces)
    shape.Placement = App.Placement(
        App.Vector(x, y, z),
        App.Rotation(App.Vector(1, 0, 0), P.front_tilt_deg),
    )
    return shape


def make_screen_frame_surfaces():
    slope_outer_w = P.lcd_width + 2 * P.screen_bezel_slope_width
    slope_outer_h = P.lcd_height + 2 * P.screen_bezel_slope_width

    bevel = slanted_bezel_frame(
        slope_outer_w,
        slope_outer_h,
        P.lcd_width,
        P.lcd_height,
        P.screen_bezel_recess_depth,
        0,
        front_y_at(P.screen_z - P.screen_bezel_slope_width) + 0.6,
        P.screen_z - P.screen_bezel_slope_width,
    )
    return bevel


def front_y_at(z: float) -> float:
    # Approximate the slanted front plane. The lower front is forward, while
    # the screen top recedes toward the body like the reference photo.
    front_tilt_slope = math.tan(math.radians(abs(P.front_tilt_deg)))
    return P.screen_lower_forward_y + (z - 58.0) * front_tilt_slope


def make_main_shell():
    screen_margin = screen_frame_margin()
    front_top_z = P.screen_z + P.lcd_height + screen_margin + 2
    front_bottom_z = P.io_z - 8
    front_lower_y = front_y_at(front_bottom_z)
    front_step_rear_y = -10
    side_profile = [
        (-10, 0),
        (P.body_depth - 8, 0),
        (P.body_depth - 3, P.body_height - 42),
        (P.body_depth - 25, P.body_height - 20),
        (front_y_at(front_top_z), front_top_z),
        (front_lower_y, front_bottom_z),
        (front_step_rear_y, front_bottom_z),
        (front_step_rear_y, 0),
    ]
    outer = prism_from_yz(P.body_width, side_profile)
    try:
        outer = outer.makeFillet(P.body_corner_radius, outer.Edges)
    except Exception:
        pass

    inner = box(
        P.body_width - 2 * P.wall,
        P.body_depth - 34,
        214,
        -P.body_width / 2.0 + P.wall,
        18,
        14,
    )

    bottom_service_opening = rounded_box(
        P.body_width - 42,
        P.body_depth - 54,
        24,
        1.0,
        App.Vector(-P.body_width / 2.0 + 21, 24, -8),
    )

    screen_cut = slanted_box(
        P.lcd_width + 3,
        42,
        P.lcd_height + 3,
        -P.lcd_width / 2.0 - 1.5,
        front_y_at(P.screen_z) - 24,
        P.screen_z - 1.5,
    )

    io_cut = slanted_box(126, 18, 27, -20, front_y_at(P.io_z) - 12, P.io_z - 4)

    handle_cut = rounded_box(
        126,
        128,
        34,
        2.0,
        App.Vector(-63, P.body_depth * 0.47, P.body_height - 34),
    )

    shell = outer.cut(inner)
    for cutter in (bottom_service_opening, screen_cut, io_cut, handle_cut):
        shell = shell.cut(cutter)

    # Actual side vent openings, cut through both side walls.
    for x in (-P.body_width / 2.0 - 1.2, P.body_width / 2.0 - 1.2):
        for row in range(6):
            shell = shell.cut(box(3.0, 145, 2.4, x, 72, 32 + row * 7))

    rear_io_column_cut = rounded_box(
        22,
        9,
        94,
        1.0,
        App.Vector(P.body_width / 2.0 - 42, P.body_depth - 10, 72),
    )
    rear_port_bay_cut = rounded_box(
        P.body_width - 36,
        9,
        28,
        1.0,
        App.Vector(-P.body_width / 2.0 + 18, P.body_depth - 10, 19),
    )
    for cutter in (rear_io_column_cut, rear_port_bay_cut):
        shell = shell.cut(cutter)

    shell = soft_edges(shell)
    bevel = make_screen_frame_surfaces()
    return Part.makeCompound([shell, bevel])


def make_bottom_plate():
    plate = rounded_box(
        P.body_width - 48,
        P.body_depth - 58,
        P.bottom_plate_thickness,
        1.0,
        App.Vector(-P.body_width / 2.0 + 24, 28, -P.bottom_plate_thickness),
    )
    for x in (-P.body_width / 2.0 + 44, P.body_width / 2.0 - 44):
        for y in (48, P.body_depth - 44):
            plate = plate.cut(cyl_z(1.9, P.bottom_plate_thickness + 2, x, y, -P.bottom_plate_thickness - 1))
    for i in range(4):
        plate = plate.cut(box(30, 1.8, P.bottom_plate_thickness + 2, -75 + i * 40, P.body_depth - 80, -P.bottom_plate_thickness - 1))
    return soft_edges(plate, 0.45)


def add_front_visuals(doc, colors):
    white = colors["white"]
    shadow = colors["shadow"]
    black = colors["black"]
    glass = colors["glass"]

    inner_y = front_y_at(P.screen_z) + P.screen_bezel_recess_depth
    add_shape(doc, "sloped_black_lcd_bezel_visual", slanted_box(P.lcd_width, 0.9, P.lcd_height, -P.lcd_width / 2.0, inner_y, P.screen_z), black)
    add_shape(doc, "lcd_dark_glass_visual", slanted_box(P.lcd_width - 12, 0.8, P.lcd_height - 12, -P.lcd_width / 2.0 + 6, inner_y + 0.8, P.screen_z + 6), glass)

    add_shape(doc, "front_io_recess_shadow", slanted_box(126, 0.8, 26, -20, front_y_at(P.io_z) - 1.8, P.io_z - 3), shadow)
    add_shape(doc, "front_usb_a_left", slanted_box(22, 0.45, 10, -12, front_y_at(P.io_z + 4) - 2.4, P.io_z + 4), black)
    add_shape(doc, "front_usb_a_right", slanted_box(22, 0.45, 10, 21, front_y_at(P.io_z + 4) - 2.4, P.io_z + 4), black)
    add_shape(doc, "front_sd_slot", slanted_box(34, 0.45, 5.5, 54, front_y_at(P.io_z + 5) - 2.5, P.io_z + 5), black)
    add_shape(doc, "front_usb_c_slot", slanted_box(15, 0.45, 6, 92, front_y_at(P.io_z + 15) - 2.5, P.io_z + 15), black)
    add_shape(doc, "front_small_status_slit", slanted_box(12, 0.45, 3.5, 82, front_y_at(P.io_z + 17) - 2.6, P.io_z + 17), black)

    badge_x = -P.body_width / 2.0 + 47
    badge_z = P.io_z - 4
    add_shape(doc, "front_badge_white_backing", slanted_box(23, 0.7, 28, badge_x - 2, front_y_at(badge_z) - 2.4, badge_z - 2), (0.80, 0.81, 0.78, 0))
    rainbow = [
        (0.43, 0.70, 0.23, 0),
        (0.93, 0.72, 0.18, 0),
        (0.93, 0.42, 0.18, 0),
        (0.83, 0.20, 0.24, 0),
        (0.33, 0.52, 0.88, 0),
    ]
    for i, color in enumerate(rainbow):
        add_shape(doc, f"front_rainbow_badge_stripe_{i + 1}", slanted_box(19, 0.45, 4.4, badge_x, front_y_at(badge_z + i * 4.4) - 3.0, badge_z + i * 4.4), color)

    lower_front_y = front_y_at(47) - 0.8
    add_shape(doc, "lower_panel_small_led", cyl_y(2.0, 1.0, 50, lower_front_y - 1.2, 24), (0.95, 0.96, 0.90, 0))
    add_shape(doc, "lower_panel_round_button", cyl_y(4.0, 1.0, 84, lower_front_y - 1.2, 24), black)


def save_preview(preview_path: str) -> None:
    try:
        import FreeCADGui as Gui

        Gui.ActiveDocument.ActiveView.viewIsometric()
        Gui.SendMsgToActiveView("ViewFit")
        Gui.ActiveDocument.ActiveView.saveImage(preview_path, 1400, 1000, "White")
        print(f"Saved {preview_path}")
    except Exception as exc:
        print(f"Preview not saved: {exc}")


def set_default_front_view(doc) -> None:
    try:
        import FreeCADGui as Gui

        App.setActiveDocument(doc.Name)
        Gui.ActiveDocument = Gui.getDocument(doc.Name)
        view = Gui.ActiveDocument.ActiveView
        for obj in doc.Objects:
            if hasattr(obj, "ViewObject"):
                obj.ViewObject.Visibility = True
        view.viewFront()
        Gui.runCommand("Std_ViewFront", 0)
        Gui.SendMsgToActiveView("ViewFit")
        Gui.runCommand("Std_ViewFitAll", 0)
        Gui.updateGui()
    except Exception:
        pass


def main() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_dir = os.path.dirname(script_dir)
    model_path = os.path.join(repo_dir, "models", "macintosh_ipad_lcd_case.FCStd")
    step_path = os.path.join(repo_dir, "exports", "macintosh_ipad_lcd_case.step")
    preview_path = os.path.join(repo_dir, "exports", "macintosh_ipad_lcd_case_preview.png")

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    os.makedirs(os.path.dirname(step_path), exist_ok=True)

    doc_name = "Compact_Retro_iPad_LCD_Case"
    if doc_name in App.listDocuments():
        App.closeDocument(doc_name)
    doc = App.newDocument(doc_name)
    doc.Label = DOCUMENT_LABEL_ZH

    colors = {
        "white": (0.88, 0.90, 0.86, 0),
        "shadow": (0.66, 0.69, 0.65, 0),
        "black": (0.012, 0.012, 0.014, 0),
        "glass": (0.18, 0.22, 0.30, 30),
        "metal": (0.74, 0.76, 0.72, 0),
        "gray": (0.46, 0.48, 0.46, 0),
    }

    add_shape(doc, "single_piece_slanted_main_shell", make_main_shell(), colors["white"])
    add_shape(doc, "removable_bottom_plate", make_bottom_plate(), colors["white"])
    add_front_visuals(doc, colors)
    gui_metadata = capture_gui_metadata(model_path)

    params_obj = doc.addObject("App::FeaturePython", "design_parameters")
    params_obj.Label = chinese_label_for("design_parameters")
    params_obj.addProperty("App::PropertyFloat", "LcdWidthMm", "LCD").LcdWidthMm = P.lcd_width
    params_obj.addProperty("App::PropertyFloat", "LcdHeightMm", "LCD").LcdHeightMm = P.lcd_height
    params_obj.addProperty("App::PropertyFloat", "FrontTiltDeg", "Case").FrontTiltDeg = abs(P.front_tilt_deg)
    params_obj.addProperty("App::PropertyFloat", "BodyWidthMm", "Case").BodyWidthMm = P.body_width
    params_obj.addProperty("App::PropertyFloat", "BodyDepthMm", "Case").BodyDepthMm = P.body_depth
    params_obj.addProperty("App::PropertyFloat", "BodyHeightMm", "Case").BodyHeightMm = P.body_height

    doc.recompute()
    set_default_front_view(doc)
    doc.saveAs(model_path)
    restore_gui_metadata(model_path, gui_metadata, {obj.Name for obj in doc.Objects})

    import Import

    Import.export([obj for obj in doc.Objects if hasattr(obj, "Shape")], step_path)
    print(f"Saved {model_path}")
    print(f"Saved {step_path}")
    print(f"Body: {P.body_width:.1f} x {P.body_depth:.1f} x {P.body_height:.1f} mm")
    print(f"LCD opening: {P.lcd_width:.1f} x {P.lcd_height:.1f} mm")
    print(f"Front tilt: {abs(P.front_tilt_deg):.1f} deg")
    save_preview(preview_path)
    set_default_front_view(doc)
    doc.save()
    restore_gui_metadata(model_path, gui_metadata, {obj.Name for obj in doc.Objects})


if __name__ == "__main__":
    main()
