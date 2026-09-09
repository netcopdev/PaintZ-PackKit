# Fonts

PaintZ PackKit does not require font binaries to be committed to a paint pack.

For the canonical PaintZ typography, place these local font files here:

- `BarlowCondensed-Black.ttf`
- `BarlowCondensed-SemiBold.ttf`

The generator also accepts explicit local font paths through:

- `PAINTZ_PACKKIT_FONT`
- `PAINTZ_PACKKIT_FONT_TEXT`

For compatibility with the original PaintZ generator it also recognizes `PAINTZ_FONT`, `PAINTZ_FONT_DISPLAY`, and `PAINTZ_FONT_TEXT`.

If no local Barlow files are present, PackKit falls back to Arial Bold on Windows or DejaVu Sans Condensed Bold on common Linux installations. This makes the generator usable without shipping font binaries, but canonical release artwork should use the intended fonts.
