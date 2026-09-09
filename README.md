# PaintZ PackKit

PaintZ PackKit is the offline authoring/generation toolkit for [PaintZ](https://github.com/netcopdev/PaintZ).

It turns one paint-pack manifest plus source artwork into standardized can textures, runtime surface representations, previews, a machine-readable catalogue, and DayZ config targeting **Paint Pack API v1**.

PackKit is not a PaintZ runtime dependency. A finished paint pack depends on PaintZ; PaintZ does not depend on PackKit or on any specific paint pack.

The authoritative runtime contract lives in PaintZ at `docs/PAINT_PACK_API.md` and `docs/PAINT_PACK_CONFIG_V1.md`. PackKit-specific obligations are summarized in `docs/INTEROPERABILITY.md`.

PackKit contains **no paint catalogue and no finish/pattern artwork**. Paint content belongs to the pack being authored.

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

Use either the installed CLI:

```powershell
paintz-packkit --manifest E:\MyPaintPack\paints.json --check
paintz-packkit --manifest E:\MyPaintPack\paints.json --clean
```

or the compatibility launcher:

```powershell
python tools\generate_paints.py --manifest E:\MyPaintPack\paints.json --check
```

## Paint Pack API v1 identity

Each pack chooses one permanent public namespace prefix:

```text
^[A-Z][A-Z0-9]{1,2}$
```

Examples:

```text
NCP
ABC
TST
```

Every finish ID is derived as:

```text
<PREFIX>-<TYPE>-<SUFFIX>
```

For example:

```text
NCP-B-BLK
NCP-S-FDE
NCP-C-FTN
```

The complete short finish ID is the canonical PaintZ runtime and persisted identity. PackKit does not generate a second reverse-domain identity, UUID, secret, or ownership token.

All valid `PZ*` prefixes are reserved for official PaintZ content. Normal generation rejects them. The PaintZ Standard Pack/official content uses the explicit `--official` option, which permits the reserved namespace and emits `official = 1` in the namespace declaration. This is an interoperability gate, not a security mechanism.

Changing a released pack prefix or complete finish ID is a breaking persistence change.

### Finish types

The current type codes include:

```text
B  Basic       plain RGB only; procedural target surface; no added treatment
S  Solid       one-color asset-backed finish with optional wear/noise/detail
C  Camouflage
P  Pattern
M  Metallic
R  Rusted
W  Weathered
F  Fluorescent
X  Special/Custom
T  Transparent/Tint
```

`B` and `S` are intentionally different even though both may represent one nominal color. Basic means **just the color**. Solid means a one-color finish whose generated texture may add scratches, grain, grime, edge wear, rust hints, or other surface character.

## Manifest

### Minimal Basic finish

A Basic finish is defined by a color and does not generate a target-surface texture asset:

```json
{
  "schema_version": 1,
  "pack": {
    "prefix": "NCP",
    "name": "Netcop Military Paints",
    "author": "netcopdev"
  },
  "paints": [
    {
      "id": "BLK",
      "name": "Basic Black",
      "type": "basic",
      "color": "#262827"
    }
  ]
}
```

This produces the finish ID `NCP-B-BLK`. PackKit emits a DayZ procedural color descriptor for the runtime S100 surface. The spray-can label/texture is still generated normally.

Basic finishes:

- require `color`;
- cannot use `pattern`;
- cannot use `appearance_profile`;
- always use one 100% procedural surface;
- do not generate a target-surface PNG/PAA.

### Solid finish

A Solid finish remains asset-backed and may use an appearance profile:

```json
{
  "id": "FDE",
  "name": "Flat Dark Earth",
  "type": "solid",
  "color": "#5A4F46",
  "appearance_profile": "used"
}
```

This produces `NCP-S-FDE` and a generated 100% target-surface image suitable for conversion to PAA.

`id` is the finish suffix, not the complete finish ID. It must be 2-12 uppercase-alphanumeric characters after normalization; a descriptive 3-character suffix is preferred. PackKit can suggest a suffix when omitted, but release manifests should commit explicit IDs.

### Pattern/camouflage finish

For a pattern/camouflage finish use a safe path relative to the manifest:

```json
{
  "id": "FTN",
  "name": "Flecktarn",
  "type": "camo",
  "pattern": "assets/pattern_sources/flecktarn.png"
}
```

Referenced pattern files must exist. Pattern-backed finishes receive the configured `generator.pattern_scales`; non-pattern asset-backed finishes receive only the required 100% surface.

## Pack workspace

A normal external workspace can be:

```text
MyPaintPack/
  paints.json
  assets/
    pattern_sources/
    overlays/            # optional legacy appearance overlays
  config/
    appearance_profiles.json   # optional override
```

Generation writes only to the workspace's `generated/` directory:

```text
generated/
  labels/
  surfaces/              # asset-backed target surfaces only; Basic has none
  previews/
  dayz/
    config.cpp
    types.generated.xml
  catalog.json
  preview_catalog.png
```

`--clean` removes only that generated directory before rebuilding.

## Generated DayZ contract

PackKit emits a standalone API-v1 `generated/dayz/config.cpp` containing:

- `CfgPatches` with `requiredAddons[] = {"PaintZ_DynamicPaint"}`;
- exactly one `CfgPaintZPacks` namespace-owner declaration;
- one `CfgPaintZFinishes` registration per finish;
- explicit `Surfaces` entries for every runtime surface representation;
- procedural S100 descriptors for Basic finishes;
- texture paths for asset-backed finishes;
- thin spawnable spray-can subclasses of `PaintZ_SprayCanBase` using `paintzFinish`;
- no generated painting mechanics.

A representative Basic registration is conceptually:

```cpp
class NCP_B_BLK
{
    id = "NCP-B-BLK";
    owner = "NCP_NetcopMilitaryPaints";
    displayName = "Basic Black";
    type = "basic";

    class Surfaces
    {
        class S100
        {
            scalePercent = 100;
            texture = "#(argb,8,8,3)color(0.149020,0.156863,0.152941,1.0,CO)";
        };
    };
};
```

Normal API-v1 output does **not** generate:

- `ActionPaintZPaint_<finish>` classes;
- `PaintZ_PaintCatalog` Enforce source;
- per-finish action registration/attachment logic.

PaintZ's generic action/runtime registry resolves the held can's `paintzFinish` instead.

## Spray-can classnames

Each finish gets one unique DayZ spray-can classname. Complete finish IDs remain unique by prefix + type + suffix, so `NCP-B-FDE` and `NCP-S-FDE` are valid distinct finish IDs.

If a pack uses the same suffix in more than one type, make sure the generated can classnames remain distinct. PackKit detects generated classname collisions. An explicit `dayz_class` may be supplied where compatibility or a legacy classname requires it.

## Namespace collision model

PackKit validates syntax and duplicates within the local project, but cannot know whether every independently distributed Workshop pack already uses a chosen prefix.

PaintZ validates the actually loaded set at runtime:

- exactly one owner for a prefix -> namespace active;
- multiple owners for the same prefix -> whole namespace disabled;
- duplicate complete finish ID -> that finish disabled;
- no first-loaded-wins or last-loaded-wins overwrite behavior.

The generated owner config classname is a deterministic linkage key, not another public identity or security credential.

## Can design and fonts

The standard PaintZ label layout is source-controlled as SVG. Paint/pattern content covers the can surface while the template provides the PaintZ identity, product code, finish name, series badge, and footer.

PackKit looks for local typography first:

- `assets/fonts/BarlowCondensed-Black.ttf`
- `assets/fonts/BarlowCondensed-SemiBold.ttf`

Font binaries are not committed. Authors can place licensed local copies there or set:

- `PAINTZ_PACKKIT_FONT`
- `PAINTZ_PACKKIT_FONT_TEXT`

For compatibility, the original `PAINTZ_FONT*` variables are also recognized. If Barlow is absent, the generator falls back to common system fonts.

Reusable grime/scratch/rust/edge-wear overlays are optional for asset-backed finishes. Basic finishes never apply the appearance stack.

## Pattern scaling

`generator.pattern_scales` controls variants generated for pattern-backed finishes. `1.0` is mandatory. Each scale must resolve to a whole percentage between 1 and 1000.

The generated finish registration declares only variants that actually exist. PaintZ does not invent third-party texture paths or assume undeclared scales exist.

Basic finishes are not pattern-scaled and always expose only S100.

## Current limitations

PackKit generates PNG source assets and DayZ config/source, but does not itself:

- convert generated PNG textures to PAA;
- pack a PBO;
- sign a PBO;
- assemble a complete Workshop release directory automatically.

For asset-backed target surfaces, generated `config.cpp` references the matching `.paa` names expected after a normal DayZ asset-conversion/build step. Basic target surfaces instead use procedural descriptors and need no surface PAA.

## Development

Run tests with:

```powershell
python -m pip install pytest
pytest -q
```

High-value tests cover namespaced IDs, reserved `PZ*` rejection, Basic procedural generation, Basic validation rules, explicit official mode, standalone API-v1 config generation, duplicate IDs, and explicit pattern-scale registration.

See `AGENTS.md` and `docs/INTEROPERABILITY.md` before changing runtime-facing output.

## License

MIT. See `LICENSE`.
