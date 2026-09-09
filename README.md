# PaintZ PackKit

PaintZ PackKit is the offline authoring/generation toolkit for [PaintZ](https://github.com/netcopdev/PaintZ).

The initial `0.1.x` line is intentionally conservative: it extracts and rebrands the proven `PaintZ/tools/paintzgen` pipeline with minimal functional change. It reads the existing v1 paint manifest format and generates can textures, finish surfaces, previews, a machine-readable catalogue, and the same style of DayZ integration fragments.

PackKit contains **no paint catalogue and no finish/pattern artwork**. Paint content belongs to the pack being authored.

## What is included

- Python generator package: `src/paintz_packkit/`
- compatibility entry point: `tools/generate_paints.py`
- canonical PaintZ can label template: `assets/templates/can_design3.svg`
- font lookup contract/documentation: `assets/fonts/README.md`
- default appearance profiles: `config/appearance_profiles.json`
- v1 manifest JSON Schema: `schemas/paints.schema.json`
- tests for IDs, validation, solid rendering, and generated DayZ output

Reusable legacy grime/scratch/rust/edge-wear overlays are **optional**. If a pack workspace provides them under `assets/overlays/`, PackKit uses them. Without them, generation still works and retains the deterministic grain layer. This removes the old public-repository dependency on an unavailable binary artwork bundle.

## Requirements

- Python 3.10+
- Pillow
- `resvg_py` for SVG rendering

Install in a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

The CLI then becomes:

```powershell
paintz-packkit --manifest E:\MyPaintPack\paints.json --check
paintz-packkit --manifest E:\MyPaintPack\paints.json --clean
```

The original workflow remains available:

```powershell
python tools\generate_paints.py --manifest E:\MyPaintPack\paints.json --check
```

## Pack workspace

PackKit does not require a paint pack to live inside this repository. A basic external workspace can be:

```text
MyPaintPack/
  paints.json
  assets/
    pattern_sources/     # only when the pack contains patterns/camouflage
    overlays/            # optional legacy appearance overlays
  config/
    appearance_profiles.json   # optional pack-specific override
```

Generation writes only to the manifest directory's `generated/` tree:

```text
generated/
  labels/
  surfaces/
  previews/
  dayz/
  catalog.json
  preview_catalog.png
```

`--clean` removes that generated directory before rebuilding. Source artwork is not cleaned.

## Manifest compatibility

Version 0.1 intentionally uses the existing PaintZ generator schema:

```json
{
  "schema_version": 1,
  "generator": {
    "label_size": [1024, 1024],
    "surface_size": [1024, 1024],
    "pattern_scales": [0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
  },
  "dayz": {
    "emit_config_fragment": true,
    "base_class": "PaintZ_SprayCanBase",
    "class_prefix": "MyPack_SprayCan_",
    "texture_root": "MyPack\\data\\cans"
  },
  "paints": [
    {
      "id": "FDE",
      "name": "Flat Dark Earth",
      "type": "solid",
      "color": "#5A4F46"
    }
  ]
}
```

This example is documentation only; PackKit deliberately does not ship it as a built-in paint.

The visible PaintZ code remains `PZ-T-ID`, for example `PZ-S-FDE`. Suggested IDs are still supported for compatibility, but explicit IDs should be committed before releasing a pack.

## Can design and fonts

The standard PaintZ label layout is source-controlled as SVG. Paint/pattern content covers the can surface while the template provides the PaintZ identity, product code, finish name, series badge, and footer.

PackKit looks for the canonical local typography first:

- `assets/fonts/BarlowCondensed-Black.ttf`
- `assets/fonts/BarlowCondensed-SemiBold.ttf`

Font binaries are not committed by this project. Authors can place licensed local copies there or set:

- `PAINTZ_PACKKIT_FONT`
- `PAINTZ_PACKKIT_FONT_TEXT`

For compatibility, the original `PAINTZ_FONT*` variables are also recognized. If Barlow is absent, the generator falls back to Arial Bold on Windows or DejaVu Sans Condensed Bold on common Linux installations.

## Outputs retained from paintzgen

For each finish PackKit currently generates:

- `generated/labels/<paint>_co.png` — complete can texture;
- `generated/surfaces/<paint>_co.png` — runtime target surface;
- pattern scale variants such as `_s050`, `_s150`, etc.;
- `generated/previews/<paint>_preview.png`;
- `generated/catalog.json`;
- `generated/dayz/PaintZ_Paints.generated.inc`;
- `generated/dayz/PaintZ_Units.generated.inc`;
- `generated/dayz/PaintZ_PaintCatalog.generated.c`;
- `generated/dayz/types.generated.xml`.

The DayZ output format is intentionally still the existing PaintZ integration model in this first extraction release. Turning PackKit output into the cleaner standalone third-party paint-pack contract discussed for PaintZ is a subsequent step, not silently mixed into this initial port.

## Pattern scaling

The existing scaling behavior is retained. `generator.pattern_scales` controls generated variants for pattern-backed finishes. `1.0` is mandatory. Solid paints produce only their normal 1x surface.

## Architecture boundary

PaintZ owns runtime mechanics. PackKit owns offline generation. Paint packs own content.

PackKit must not become a second implementation of PaintZ persistence, painting actions, target eligibility, synchronization, or target-item compatibility logic.

## Current limitations

- The first release remains intentionally coupled to PaintZ's current v1 generated DayZ catalogue/action format.
- Canonical Barlow font files are local dependencies, not repository content.
- The historical binary wear-overlay library is not bundled. It is optional and supported when supplied by the author.
- PAA conversion, PBO packing, signing, and a fully standalone third-party pack scaffold are not yet performed by PackKit 0.1.

## Development

Run tests with:

```powershell
python -m pip install pytest
pytest -q
```

See `AGENTS.md` for repository and architecture rules.

## License

MIT. See `LICENSE`.
