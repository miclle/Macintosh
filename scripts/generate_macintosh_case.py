"""Generate a compact retro iPad LCD enclosure for 3D printing.

The model follows the user's latest reference photos: a clean one-piece main
shell, slanted front face, lower front lip that projects forward, slightly
lower rear top with clipped back corners, a recessed top carry handle, side
vents, modern front I/O, and a removable bottom plate for installing the LCD,
HDMI driver board, speakers, and battery.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import FreeCAD as App
import Part


@dataclass(frozen=True)
class Params:
    lcd_width: float = 210.0
    lcd_height: float = 160.0
    lcd_depth_allowance: float = 8.0

    body_width: float = 230.0
    body_depth: float = 285.0
    body_height: float = 275.0
    body_corner_radius: float = 2.0
    edge_soft_radius: float = 0.45
    wall: float = 3.0
    front_tilt_deg: float = -12.0

    screen_z: float = 92.0
    screen_flat_frame_width: float = 5.0
    screen_bezel_slope_width: float = 3.0
    screen_bezel_recess_depth: float = 3.0
    screen_lower_forward_y: float = -28.0

    io_z: float = 50.0
    bottom_plate_thickness: float = 4.0
    lower_service_panel_height: float = 42.0

    driver_board_width: float = 105.0
    driver_board_height: float = 70.0
    battery_width: float = 92.0
    battery_depth: float = 68.0


P = Params()


def add_shape(doc, name: str, shape, color):
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape
    if hasattr(obj, "ViewObject"):
        obj.ViewObject.ShapeColor = color[:3]
        obj.ViewObject.Transparency = int(color[3]) if len(color) > 3 else 0
    return obj


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


def slanted_rect_frame(
    outer_width: float,
    outer_height: float,
    inner_width: float,
    inner_height: float,
    depth: float,
    x_center: float,
    y: float,
    z: float,
):
    """Flat rectangular frame on the tilted front plane."""
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
        [v(outer_left, 0, 0), v(outer_right, 0, 0), v(inner_right, 0, inner_bottom), v(inner_left, 0, inner_bottom)],
        [v(outer_right, 0, outer_height), v(outer_left, 0, outer_height), v(inner_left, 0, inner_top), v(inner_right, 0, inner_top)],
        [v(outer_left, 0, outer_height), v(outer_left, 0, 0), v(inner_left, 0, inner_bottom), v(inner_left, 0, inner_top)],
        [v(outer_right, 0, 0), v(outer_right, 0, outer_height), v(inner_right, 0, inner_top), v(inner_right, 0, inner_bottom)],
    ]
    for quad in quads:
        faces.append(Part.Face(Part.makePolygon(quad + [quad[0]])))

    shape = Part.makeCompound(faces)
    shape.Placement = App.Placement(
        App.Vector(x_center, y, z),
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


def front_y_at(z: float) -> float:
    # Approximate the slanted front plane. The lower front is forward, while
    # the screen top recedes toward the body like the reference photo.
    return P.screen_lower_forward_y + (z - 58.0) * 0.212


def make_main_shell():
    screen_margin = P.screen_flat_frame_width + P.screen_bezel_slope_width
    front_top_z = P.screen_z + P.lcd_height + screen_margin + 2
    front_bottom_z = 58
    front_lower_y = front_y_at(front_bottom_z)
    front_step_rear_y = -11
    top_front_bevel_y = front_y_at(front_top_z) + 26
    top_front_bevel_z = front_top_z + 3
    side_profile = [
        (-10, 0),
        (P.body_depth - 8, 0),
        (P.body_depth - 3, P.body_height - 42),
        (P.body_depth - 25, P.body_height - 20),
        (top_front_bevel_y, top_front_bevel_z),
        (front_y_at(front_top_z), front_top_z),
        (front_lower_y, front_bottom_z),
        (front_lower_y, 47),
        (front_step_rear_y, 47),
        (front_step_rear_y, 0),
        (-10, 0),
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

    recess_w = P.lcd_width + 2 * screen_margin
    recess_h = P.lcd_height + 2 * screen_margin
    screen_cut = slanted_box(
        P.lcd_width + 3,
        42,
        P.lcd_height + 3,
        -P.lcd_width / 2.0 - 1.5,
        front_y_at(P.screen_z) - 24,
        P.screen_z - 1.5,
    )
    screen_recess_cut = slanted_box(
        recess_w,
        16,
        recess_h,
        -recess_w / 2.0,
        front_y_at(P.screen_z - screen_margin) - 10,
        P.screen_z - screen_margin,
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
    for cutter in (bottom_service_opening, screen_recess_cut, screen_cut, io_cut, handle_cut):
        shell = shell.cut(cutter)

    # Actual side vent openings, cut through both side walls.
    for x in (-P.body_width / 2.0 - 1.2, P.body_width / 2.0 - 1.2):
        for row in range(6):
            shell = shell.cut(box(3.0, 145, 2.4, x, 72, 32 + row * 7))

    # Rear features following the reference: paired top vents, a narrow right
    # service column, and a low recessed legacy-port bay.
    for x in (-P.body_width / 2.0 + 18, P.body_width / 2.0 - 52):
        for row in range(6):
            shell = shell.cut(rounded_box(34, 8, 2.2, 0.7, App.Vector(x, P.body_depth - 10, P.body_height - 78 + row * 7)))

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

    return soft_edges(shell)


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
    metal = colors["metal"]

    total_margin = P.screen_flat_frame_width + P.screen_bezel_slope_width
    outer_w = P.lcd_width + 2 * total_margin
    outer_h = P.lcd_height + 2 * total_margin
    slope_outer_w = P.lcd_width + 2 * P.screen_bezel_slope_width
    slope_outer_h = P.lcd_height + 2 * P.screen_bezel_slope_width
    outer_y = front_y_at(P.screen_z - total_margin) + 0.6
    outer_z = P.screen_z - total_margin

    flat_frame = slanted_rect_frame(
        outer_w,
        outer_h,
        slope_outer_w,
        slope_outer_h,
        0.8,
        0,
        outer_y,
        outer_z,
    )
    add_shape(doc, "flat_white_screen_frame_surface", flat_frame, white)

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
    add_shape(doc, "sloped_white_screen_bezel_surface", bevel, shadow)
    inner_y = front_y_at(P.screen_z) + P.screen_bezel_recess_depth
    add_shape(doc, "sloped_black_lcd_bezel_visual", slanted_box(P.lcd_width, 0.9, P.lcd_height, -P.lcd_width / 2.0, inner_y, P.screen_z), black)
    add_shape(doc, "lcd_dark_glass_visual", slanted_box(P.lcd_width - 12, 0.8, P.lcd_height - 12, -P.lcd_width / 2.0 + 6, inner_y + 0.8, P.screen_z + 6), glass)

    add_shape(doc, "front_io_recess_shadow", slanted_box(126, 0.8, 26, -20, front_y_at(P.io_z) - 1.8, P.io_z - 3), shadow)
    add_shape(doc, "front_usb_a_left", slanted_box(22, 0.45, 10, -12, front_y_at(P.io_z + 4) - 2.4, P.io_z + 4), black)
    add_shape(doc, "front_usb_a_right", slanted_box(22, 0.45, 10, 21, front_y_at(P.io_z + 4) - 2.4, P.io_z + 4), black)
    add_shape(doc, "front_sd_slot", slanted_box(34, 0.45, 5.5, 54, front_y_at(P.io_z + 5) - 2.5, P.io_z + 5), black)
    add_shape(doc, "front_usb_c_slot", slanted_box(15, 0.45, 6, 92, front_y_at(P.io_z + 15) - 2.5, P.io_z + 15), black)
    add_shape(doc, "front_small_status_slit", slanted_box(12, 0.45, 3.5, 82, front_y_at(P.io_z + 17) - 2.6, P.io_z + 17), black)

    badge_x = -P.body_width / 2.0 + 57
    badge_z = 41
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

    add_shape(doc, "lower_front_clean_access_panel", rounded_box(142, 2.0, P.lower_service_panel_height, 1.0, App.Vector(-72, -11.0, 4)), (0.78, 0.79, 0.74, 0))
    add_shape(doc, "lower_panel_small_led", cyl_y(2.0, 1.0, 50, -12.2, 24), (0.95, 0.96, 0.90, 0))
    add_shape(doc, "lower_panel_round_button", cyl_y(4.0, 1.0, 84, -12.2, 24), black)

    # Soft lower feet only; no extra stand.
    add_shape(doc, "front_left_integral_foot", rounded_box(30, 18, 46, 1.0, App.Vector(-P.body_width / 2.0 + 10, -10, 0)), white)
    add_shape(doc, "front_right_integral_foot", rounded_box(30, 18, 46, 1.0, App.Vector(P.body_width / 2.0 - 40, -10, 0)), white)


def add_top_side_back_visuals(doc, colors):
    white = colors["white"]
    shadow = colors["shadow"]
    black = colors["black"]
    gray = colors["gray"]
    metal = colors["metal"]

    add_shape(doc, "top_handle_recess_floor", rounded_box(112, 108, 1.2, 2.0, App.Vector(-56, P.body_depth * 0.49, P.body_height - 34.8)), shadow)

    for side_name, x in (("left", -P.body_width / 2.0 - 0.6), ("right", P.body_width / 2.0 - 0.6)):
        for row in range(6):
            add_shape(doc, f"{side_name}_side_vent_shadow_{row + 1}", box(1.0, 145, 2.0, x, 72, 32 + row * 7), black)

    # Slightly proud visual faces keep the rear details legible in STEP/viewer
    # exports while the shell cutters above define the actual recesses.
    rear_y = P.body_depth - 0.8

    # Top rear vent fields, left and right of the carry handle.
    for side_name, x in (("left", -P.body_width / 2.0 + 18), ("right", P.body_width / 2.0 - 52)):
        for row in range(6):
            add_shape(doc, f"rear_{side_name}_top_vent_slit_{row + 1}", rounded_box(34, 0.65, 2.6, 0.6, App.Vector(x, P.body_depth + 0.15, P.body_height - 77 + row * 7)), black)

    # Small Macintosh badge on the upper rear-left corner.
    badge_x = -P.body_width / 2.0 + 21
    badge_z = 190
    badge_colors = [
        (0.33, 0.52, 0.88, 0),
        (0.83, 0.20, 0.24, 0),
        (0.93, 0.42, 0.18, 0),
        (0.93, 0.72, 0.18, 0),
        (0.43, 0.70, 0.23, 0),
    ]
    add_shape(doc, "rear_badge_base", rounded_box(12, 0.8, 14, 0.5, App.Vector(badge_x, rear_y - 0.2, badge_z)), shadow)
    for i, color in enumerate(badge_colors):
        add_shape(doc, f"rear_badge_stripe_{i + 1}", box(9, 0.5, 2.2, badge_x + 1.5, rear_y - 0.5, badge_z + 1.5 + i * 2.2), color)
    add_shape(doc, "rear_macintosh_nameplate", rounded_box(44, 0.8, 14, 0.6, App.Vector(badge_x + 15, rear_y - 0.2, badge_z)), gray)

    # Regulatory label block with shallow engraved line hints.
    label_x = -17
    label_z = 74
    add_shape(doc, "rear_regulatory_label_plate", rounded_box(47, 0.8, 66, 1.0, App.Vector(label_x, rear_y - 0.2, label_z),), metal)
    for row in range(8):
        add_shape(doc, f"rear_regulatory_label_text_line_{row + 1}", box(33 - (row % 3) * 5, 0.45, 1.0, label_x + 7, rear_y - 0.55, label_z + 54 - row * 5), gray)
    add_shape(doc, "rear_rohs_mark_block", box(28, 0.45, 5, label_x + 8, rear_y - 0.6, label_z + 7), black)

    # Tall right rear service column: vertical door, switch, and USB-C opening.
    column_x = P.body_width / 2.0 - 42
    add_shape(doc, "rear_right_service_column_floor", rounded_box(22, 0.8, 94, 1.0, App.Vector(column_x, rear_y, 72)), shadow)
    add_shape(doc, "rear_right_vertical_cover", rounded_box(15, 0.7, 43, 0.8, App.Vector(column_x + 3.5, rear_y - 0.35, 122)), metal)
    add_shape(doc, "rear_right_small_switch_recess", rounded_box(14, 0.7, 17, 0.8, App.Vector(column_x + 4, rear_y - 0.4, 99)), metal)
    add_shape(doc, "rear_right_small_switch_tab", rounded_box(8, 0.7, 10, 0.6, App.Vector(column_x + 7, rear_y - 0.7, 102)), (0.78, 0.70, 0.52, 0))
    add_shape(doc, "rear_right_usb_c_port", rounded_box(9, 0.7, 17, 1.5, App.Vector(column_x + 6.5, rear_y - 0.8, 77)), black)

    # Bottom rear legacy-port bay.
    bay_x = -P.body_width / 2.0 + 18
    add_shape(doc, "rear_bottom_port_bay_floor", rounded_box(P.body_width - 36, 0.8, 28, 1.0, App.Vector(bay_x, rear_y, 19)), shadow)
    for i, x in enumerate((bay_x + 34, bay_x + 70, bay_x + 106), start=1):
        add_shape(doc, f"rear_dsub_connector_shell_{i}", rounded_box(25, 0.7, 10, 0.8, App.Vector(x, rear_y - 0.45, 28)), metal)
        add_shape(doc, f"rear_dsub_connector_dark_face_{i}", rounded_box(17, 0.5, 5, 0.5, App.Vector(x + 4, rear_y - 0.75, 30.5)), black)
    add_shape(doc, "rear_round_audio_port", cyl_y(4.0, 0.8, bay_x + P.body_width - 62, rear_y - 0.7, 32), black)
    add_shape(doc, "rear_small_round_port", cyl_y(2.6, 0.8, bay_x + P.body_width - 43, rear_y - 0.7, 32), black)
    for i, x in enumerate((bay_x + 6, bay_x + P.body_width - 48), start=1):
        add_shape(doc, f"rear_bottom_bay_screw_{i}", cyl_y(2.5, 0.8, x, rear_y - 0.7, 49), black)

    add_shape(doc, "rear_bottom_plate_seam", box(P.body_width - 64, 1.0, 1.2, -P.body_width / 2.0 + 32, P.body_depth - 5, 48), gray)


def add_internal_mounts(doc, colors):
    white = colors["white"]
    board = colors["board"]
    glass = colors["glass"]
    battery = colors["battery"]

    lcd_panel = slanted_box(
        P.lcd_width,
        P.lcd_depth_allowance,
        P.lcd_height,
        -P.lcd_width / 2.0,
        front_y_at(P.screen_z) + 8,
        P.screen_z,
    )
    add_shape(doc, "lcd_panel_envelope_210x160x8", lcd_panel, glass)

    for name, x in (("left", -P.lcd_width / 2.0 - 3), ("right", P.lcd_width / 2.0)):
        add_shape(doc, f"lcd_{name}_side_retaining_rail", slanted_box(3, 12, P.lcd_height + 18, x, front_y_at(P.screen_z - 9) + 16, P.screen_z - 9), white)

    for i, (x, y) in enumerate(
        [
            (-P.body_width / 2.0 + 36, 44),
            (P.body_width / 2.0 - 36, 44),
            (-P.body_width / 2.0 + 36, P.body_depth - 46),
            (P.body_width / 2.0 - 36, P.body_depth - 46),
        ],
        start=1,
    ):
        boss = cyl_z(5.5, 22, x, y, 0).cut(cyl_z(1.8, 24, x, y, -1))
        add_shape(doc, f"bottom_plate_m3_boss_{i}", boss, white)

    board_y = 82
    board_z = 26
    add_shape(doc, "hdmi_driver_board_keepout_105x70", box(P.driver_board_width, 3, P.driver_board_height, -P.driver_board_width / 2.0, board_y, board_z), board)
    for i, (x, z) in enumerate(
        [
            (-P.driver_board_width / 2.0 + 8, board_z + 8),
            (P.driver_board_width / 2.0 - 8, board_z + 8),
            (-P.driver_board_width / 2.0 + 8, board_z + P.driver_board_height - 8),
            (P.driver_board_width / 2.0 - 8, board_z + P.driver_board_height - 8),
        ],
        start=1,
    ):
        add_shape(doc, f"driver_board_m2_5_standoff_{i}", cyl_z(3.5, 18, x, board_y, z), white)

    add_shape(doc, "battery_pack_keepout", rounded_box(P.battery_width, P.battery_depth, 16, 1.0, App.Vector(-P.battery_width / 2.0, 150, 16)), battery)


def save_preview(preview_path: str) -> None:
    try:
        import FreeCADGui as Gui

        Gui.ActiveDocument.ActiveView.viewIsometric()
        Gui.SendMsgToActiveView("ViewFit")
        Gui.ActiveDocument.ActiveView.saveImage(preview_path, 1400, 1000, "White")
        print(f"Saved {preview_path}")
    except Exception as exc:
        print(f"Preview not saved: {exc}")


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

    colors = {
        "white": (0.88, 0.90, 0.86, 0),
        "shadow": (0.66, 0.69, 0.65, 0),
        "black": (0.012, 0.012, 0.014, 0),
        "glass": (0.18, 0.22, 0.30, 30),
        "metal": (0.74, 0.76, 0.72, 0),
        "gray": (0.46, 0.48, 0.46, 0),
        "board": (0.05, 0.32, 0.18, 35),
        "battery": (0.16, 0.20, 0.24, 45),
    }

    add_shape(doc, "single_piece_slanted_main_shell", make_main_shell(), colors["white"])
    add_shape(doc, "removable_bottom_plate", make_bottom_plate(), colors["white"])
    add_front_visuals(doc, colors)
    add_top_side_back_visuals(doc, colors)
    add_internal_mounts(doc, colors)

    params_obj = doc.addObject("App::FeaturePython", "design_parameters")
    params_obj.addProperty("App::PropertyFloat", "LcdWidthMm", "LCD").LcdWidthMm = P.lcd_width
    params_obj.addProperty("App::PropertyFloat", "LcdHeightMm", "LCD").LcdHeightMm = P.lcd_height
    params_obj.addProperty("App::PropertyFloat", "FrontTiltDeg", "Case").FrontTiltDeg = abs(P.front_tilt_deg)
    params_obj.addProperty("App::PropertyFloat", "BodyWidthMm", "Case").BodyWidthMm = P.body_width
    params_obj.addProperty("App::PropertyFloat", "BodyDepthMm", "Case").BodyDepthMm = P.body_depth
    params_obj.addProperty("App::PropertyFloat", "BodyHeightMm", "Case").BodyHeightMm = P.body_height

    doc.recompute()
    App.setActiveDocument(doc.Name)
    doc.saveAs(model_path)

    import Import

    Import.export([obj for obj in doc.Objects if hasattr(obj, "Shape")], step_path)
    print(f"Saved {model_path}")
    print(f"Saved {step_path}")
    print(f"Body: {P.body_width:.1f} x {P.body_depth:.1f} x {P.body_height:.1f} mm")
    print(f"LCD opening: {P.lcd_width:.1f} x {P.lcd_height:.1f} mm")
    print(f"Front tilt: {abs(P.front_tilt_deg):.1f} deg")
    save_preview(preview_path)


if __name__ == "__main__":
    main()
