# PaintZ PackKit

PaintZ PackKit is the offline authoring/generation toolkit for [PaintZ](https://github.com/netcopdev/PaintZ).

It turns a paint-pack manifest plus source artwork/data into standardized can textures, runtime surface representations, previews, a machine-readable catalogue, and DayZ config targeting **Paint Pack API v1**.

PackKit is not a runtime dependency. A finished paint pack depends on PaintZ; PaintZ does not depend on PackKit or on any particular content pack.

The authoritative runtime contract lives in PaintZ at `docs/PAINT_PACK_API.md` and `docs/PAINT_PACK_CONFIG_V1.md`. PackKit-specific obligations are summarized in `docs/INTEROPERABILITY.md`; the author-facing manifest contract is `docs/MANIFEST_V1.md`.

## Requirements

- Python 3.10+
- Pillow
- `resvg_py`

Install in a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Typical use:

```powershell
paintz-packkit --manifest E:\MyPaintPack\paints.json --check
paintz-packkit --manifest E:\MyPaintPack\paints.json --clean
```

Official PaintZ content uses:

```powershell
paintz-packkit --manifest E:\PaintZ-Standard-Pack\paints.json --official --clean
```

## Paint Pack API v1 identity

Every finish ID is:

```text
<PREFIX>-<TYPE>-<SUFFIX>
```

Examples:

```text
PZ-B-BLK
PZ-S-FDE
PZ-C-FTN
NCP-B-ODG
NCP-S-FDE
NCP-C-FTN
```

The complete short finish ID is the canonical runtime and persisted identity. Package names and Workshop boundaries are not part of that identity.

Normal third-party namespaces are 2-3 uppercase alphanumeric characters beginning with a letter. All `PZ*` prefixes are reserved for official PaintZ use and are rejected in normal generation.

### Finish types

Current type codes include:

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

`B` and `S` are intentionally distinct. Basic means only the configured RGB color. Solid is asset-backed and may include deterministic scratches, grain, grime, edge wear, rust hints, or other surface character.

### Basic finishes

A minimal Basic finish:

```json
{
  "schema_version": 1,
  "pack": {
    "prefix": "NCP",
    "name": "Netcop Test Paints",
    "author": "netcopdev"
  },
  "paints": [
    {
      "id": "BLK",
      "name": "Black",
      "type": "basic",
      "color": "#262827"
    }
  ]
}
```

This produces `NCP-B-BLK`. PackKit emits a DayZ procedural S100 color descriptor and generates normal spray-can artwork, but no target-surface PNG/PAA.

Basic finishes:

- require `color`;
- cannot use `pattern`;
- cannot use `appearance_profile`;
- always expose one 100% procedural surface;
- do not generate a target-surface image.

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

This produces `NCP-S-FDE` and a generated 100% target-surface image suitable for PAA conversion.

`id` is the suffix, not the complete finish ID. It must be 2-12 uppercase-alphanumeric characters after normalization. A descriptive three-character value is preferred.

## Official `PZ` content

PaintZ runtime itself owns the canonical `PZ` namespace through `PZ_PaintZOfficial`. Official content packs do not declare `PZ` themselves.

`--official` currently means: generate an independent official content pack in the core-owned `PZ` namespace. PackKit therefore:

- accepts `PZ` only;
- does not emit `CfgPaintZPacks`;
- writes `owner = "PZ_PaintZOfficial"` on every finish;
- requires only `PaintZ_DynamicPaint` at runtime;
- rejects `dayz.namespace_role = "satellite"` and `dayz.owner_patch` for official content;
- rejects unassigned reserved namespaces such as `PZA` or `PZ9` until PaintZ explicitly assigns them.

This allows independent peer packages such as PaintZ Standard Pack, PaintZ Field Pack, PaintZ Vanilla Pack, PaintZ Hunter Pack, and PaintZ Pastel Pack to contribute unique `PZ-*` finishes without depending on one another.

Moving an unchanged official finish between those packs is packaging-only if its complete `PZ-*` ID remains unchanged.

## Third-party owner packs

For normal generation, `dayz.namespace_role` defaults to `owner`. PackKit emits one `CfgPaintZPacks` owner declaration and registers the pack's finishes against it.

For a pattern/camouflage finish:

```json
{
  "id": "FTN",
  "name": "Flecktarn",
  "type": "camo",
  "pattern": "assets/pattern_sources/flecktarn.png"
}
```

Referenced pattern files must exist. Pattern-backed finishes receive the configured `generator.pattern_scales`; non-pattern asset-backed finishes receive the required 100% surface.

## Third-party satellite packs

Satellite mode supports a third-party family split across several PBOs. Exactly one owner/core PBO declares the namespace. Additional PBOs reference that owner and depend on its patch:

```json
"dayz": {
  "namespace_role": "satellite",
  "owner_class": "NCP_NetcopPaints",
  "owner_patch": "NCP_Owner_Patch",
  "patch_class": "NCP_Camo_Satellite",
  "addon_root": "NCP_Camo_Satellite"
}
```

A generated third-party satellite:

- omits `CfgPaintZPacks`;
- keeps the same namespace prefix and finish IDs;
- registers finishes against the supplied `owner_class`;
- requires both `PaintZ_DynamicPaint` and `owner_patch`;
- owns its own textures, can classes and finish config children.

Do not use this owner/satellite dependency pattern for official `PZ` collections. PaintZ core is already their stable namespace owner.

## Generated DayZ contract

A third-party owner pack emits:

- `CfgPatches` requiring `PaintZ_DynamicPaint`;
- one `CfgPaintZPacks` owner;
- one `CfgPaintZFinishes` child per finish;
- explicit runtime surface representations;
- procedural S100 descriptors for Basic finishes;
- texture paths and explicit scale variants for asset-backed finishes;
- thin `PaintZ_SprayCanBase` subclasses using `paintzFinish`;
- optional CE type output.

An official `PZ` pack emits the same finish/can/surface content except that it emits no namespace owner and every finish references `PZ_PaintZOfficial`.

Normal API-v1 output does **not** generate per-finish Enforce actions, a runtime `PaintZ_PaintCatalog`, painted target subclasses, persistence logic, or PaintZ gameplay mechanics.

## Spray-can classnames

Each finish gets one unique DayZ spray-can classname. Complete finish IDs include the type letter, so `NCP-B-FDE` and `NCP-S-FDE` are valid distinct finish IDs.

If the same suffix is used in more than one type, generated can classnames must still remain unique. PackKit detects collisions; an explicit `dayz_class` may be supplied where compatibility or a historical classname requires it.

## Collision model

PaintZ validates the complete loaded set at runtime:

- exactly one owner for a namespace -> namespace active;
- multiple owners for one namespace -> namespace disabled;
- duplicate complete finish ID -> duplicated finish disabled;
- no first-loaded-wins or last-loaded-wins overwrite behavior.

For `PZ`, the one legitimate owner is PaintZ core. Official content packs are contributors, not owners.

## Workspace and output

A normal workspace can be:

```text
MyPaintPack/
  paints.json
  assets/
    pattern_sources/
    overlays/
  config/
    appearance_profiles.json
```

Generation writes only below `generated/`:

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

`--clean` removes only PackKit-owned generated output.

## Can design and pattern scaling

The standard PaintZ label layout is source-controlled as `assets/templates/can_design3.svg`. PackKit controls common PaintZ presentation while manifests supply finish identity/content and restrained pack metadata.

The generated can label includes the PaintZ logo at the top with its distinct red `Z`, followed by the finish code/name and series/badge/footer information. Changes to the shared label geometry or renderer must be treated as PackKit behavior changes and covered by tests/documentation.

Basic cans use `BASIC SERIES` by default. Basic finishes never apply the appearance stack and are not pattern-scaled.

`generator.pattern_scales` controls variants for pattern-backed finishes. `1.0` is mandatory and each scale must resolve to a whole percentage between 1 and 1000. PaintZ uses only variants explicitly registered by the finish.

## Current build boundary

PackKit generates PNG source assets and DayZ config/source. PAA conversion, PBO packing/signing, and release assembly remain separate build steps unless a pack repository provides its own wrapper scripts.

For asset-backed target surfaces, generated config references the matching `.paa` names expected after conversion. Basic target surfaces use procedural descriptors and require no surface PAA.

## Development

Run tests with:

```powershell
python -m pip install pytest
pytest -q
```

High-value coverage includes normal namespace ownership, third-party satellites, reserved-prefix rejection, core-owned official `PZ` generation, Basic procedural generation/validation, duplicate IDs, generated classname uniqueness, pattern-scale registration, and shared can-label logo/template integrity.

See `AGENTS.md`, `docs/MANIFEST_V1.md`, and `docs/INTEROPERABILITY.md` before changing author-facing or runtime-facing output.

## License

MIT. See `LICENSE`.
