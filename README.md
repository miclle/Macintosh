# Macintosh iPad LCD Case

FreeCAD model for a compact retro iPad LCD enclosure. The current version
follows the latest reference photos: a slanted front face, lower front lip that
projects forward, clean deep side body, slightly lowered rear top with clipped
rear corners, deep recessed top carry handle, inset LCD opening, rainbow badge,
modern front I/O, side vents, and separate front/rear shell parts with a
removable bottom plate. It intentionally does not include a separate keyboard,
mouse, stand, or dock.

## Generated files

- `models/macintosh_ipad_lcd_case.FCStd` - native FreeCAD model.
- `exports/macintosh_ipad_lcd_case.step` - STEP export for other CAD/CAM tools.
- `scripts/generate_macintosh_case.py` - parameterized model generator.

## Current dimensions

The mechanical constraint is the salvaged iPad LCD:

- LCD opening: 210 x 160 mm

The generated enclosure is:

- Body: 230 x 228 x 275 mm
- Front face tilt: 7 degrees
- Shell wall: 3 mm
- Soft edge radius: 0.45 mm
- Removable bottom plate: 4 mm

## Included model features

- Printable front and rear main shell parts with a separate removable bottom
  plate.
- Side split line with a lower vertical section parallel to the recessed front
  step, a short horizontal jog, and an upper section parallel to the front
  slope.
- Slanted front face that continues below the front I/O recess; the lower
  screen/control area projects forward like the reference photos.
- The top surface is one continuous main plane from the front edge to the rear
  clipped section instead of a segmented top-front bevel.
- The lower front transition is a rear-set step below the front I/O recess
  instead of ending the slope at the LCD frame.
- The LCD installs from inside the enclosure against the front shell, using
  four integral screw bosses around the LCD opening; the removable bottom
  opening remains the service access path.
- Deep side body with one continuous main top plane and clipped rear top
  corners.
- Clean top surface with a deeper 126 x 128 x 34 mm recessed carry-handle
  pocket and finger clearance.
- Inset 210 x 160 mm LCD opening with a flush 5 mm front-shell border followed
  by a 3 mm wide, 30 degree inward-sloping bevel toward the LCD center before
  the LCD visual plane.
- Internal LCD retaining bosses: 4.2 mm boss radius, 1.35 mm screw pilot hole
  radius, 9 mm boss depth, positioned just outside the LCD opening.
- Rainbow badge and modern front I/O strip with USB-A, SD, USB-C, and status
  slit placeholders.
- Lower front LED/button details.
- Unsupported rear decorative parts are omitted.

## Regenerate

Run the generator inside FreeCAD's Python environment:

```sh
freecadcmd scripts/generate_macintosh_case.py
```

Measure the real LCD metal frame and any optional modules before fabrication.
Adjust the `Params` values in `scripts/generate_macintosh_case.py`, regenerate,
then export/slice the main shell and bottom plate for your printer and material.
