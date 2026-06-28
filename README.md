# Macintosh iPad LCD Case

FreeCAD model for a compact retro iPad LCD enclosure. The current version
follows the latest reference photos: a slanted front face, lower front lip that
projects forward, clean deep side body, slightly lowered rear top with clipped
rear corners, deep recessed top carry handle, inset LCD opening, rainbow badge,
modern front I/O, side vents, and a removable bottom plate. It intentionally
does not include a separate keyboard, mouse, stand, or dock.

## Generated files

- `models/macintosh_ipad_lcd_case.FCStd` - native FreeCAD model.
- `exports/macintosh_ipad_lcd_case.step` - STEP export for other CAD/CAM tools.
- `scripts/generate_macintosh_case.py` - parameterized model generator.

## Current dimensions

The mechanical constraint is the salvaged iPad LCD:

- LCD opening: 210 x 160 mm
- LCD depth allowance: 8 mm
- HDMI driver-board keep-out: 105 x 70 mm

The generated enclosure is:

- Body: 226 x 285 x 275 mm
- Front face tilt: 12 degrees
- Shell wall: 3 mm
- Soft edge radius: 0.45 mm
- Removable bottom plate: 4 mm

## Included model features

- Single-piece printable main shell with a separate removable bottom plate.
- Slanted front face; the lower screen/control area projects forward like the
  reference photos.
- The top-front transition is a short rear-facing bevel instead of a sharp
  peak.
- The lower front transition is a rear-set step instead of a continuous slope.
- The LCD installs from the removable bottom opening, so the top/front shell
  above the LCD bay stays closed.
- Deep side body with one continuous main top slope, a small top-front bevel,
  and clipped rear top corners.
- Clean top surface with a deeper 126 x 128 x 34 mm recessed carry-handle
  pocket and finger clearance.
- Inset 210 x 160 mm LCD opening with the LCD visual recessed inside the shell
  instead of protruding from the front.
- Rainbow badge and modern front I/O strip with USB-A, SD, USB-C, and status
  slit placeholders.
- Clean lower front access panel, soft integrated front feet, and long side
  lower vents.
- Reference-style rear shell with paired top vent fields, a small Macintosh
  badge/nameplate area, regulatory-label plate, right-side service column, and
  low legacy-port bay.
- LCD retaining rails, bars, and four M3-style mounting bosses.
- 105 x 70 mm HDMI driver-board keep-out with standoffs.
- Internal keep-out for a battery pack.

## Regenerate

Run the generator inside FreeCAD's Python environment:

```sh
freecadcmd scripts/generate_macintosh_case.py
```

Measure the real LCD metal frame, HDMI driver board, battery, and any optional modules
before fabrication. Adjust the `Params` values in
`scripts/generate_macintosh_case.py`, regenerate, then export/slice the main
shell and bottom plate for your printer and material.
