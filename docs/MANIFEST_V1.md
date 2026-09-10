# PaintZ PackKit manifest v1

This document describes the author-facing `paints.json` consumed by PaintZ PackKit 0.2.x.

The manifest schema version is an authoring/build-time format. It is separate from PaintZ Paint Pack API v1, which is the runtime interoperability contract.

## Minimal structure

```json
{
  "schema_version": 1,
  "pack": {
    "prefix": "NCP",
    "name": "Example Paint Pack",
    "author": "Example Author"
  },
  "generator": {
    "pattern_scales": [0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
  },
  "dayz": {
    "addon_root": "NCP_ExamplePaintPack"
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

## `schema_version`

Must currently be `1`.

Changing the Paint Pack API runtime version does not automatically require changing the PackKit manifest schema version, and vice versa.

## `pack`

Required object.

### `pack.prefix`

Required permanent 2-3 character namespace. PackKit normalizes it to uppercase and requires:

```text
^[A-Z][A-Z0-9]{1,2}$
```

Normal third-party generation rejects every valid prefix beginning with `PZ`.

Official generation is explicit: when PackKit is invoked with `--official`, the currently supported official namespace is exactly `PZ`, owned at runtime by PaintZ core through `PZ_PaintZOfficial`. Unassigned reserved prefixes such as `PZA` or `PZ9` are not available merely because `--official` is supplied.

The prefix becomes part of every persisted finish ID. Changing it after release is a breaking identity change.

### `pack.name`

Required human-readable pack name.

It is also used, together with `pack.author` when supplied, to derive distinctive deterministic DayZ config class names unless explicit DayZ overrides are provided.

### `pack.author`

Optional non-empty publisher/author text. It is metadata and config-classname source material; it is not a security credential or a PaintZ runtime identity.

## `generator`

Object containing rendering/generation settings.

### `generator.label_size`

Optional `[width, height]` for generated can textures. Default is `1024 x 1024`.

### `generator.surface_size`

Optional `[width, height]` for generated asset-backed runtime finish surfaces. Default is `1024 x 1024`.

Basic finishes do not generate a target-surface image, so this setting does not affect their runtime surface representation.

### `generator.pattern_scales`

Optional non-empty array of positive scales. Each value must resolve to a whole percentage from 1 through 1000, and `1.0` is mandatory.

Pattern-backed finishes receive these generated variants. Asset-backed non-pattern finishes generate only their 100% surface. Basic finishes are procedural and always expose only S100 without generating a surface image.

Example:

```json
"pattern_scales": [0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
```

becomes scale percentages:

```text
50 75 100 150 200 300
```

PaintZ receives explicit `Surfaces` entries only for variants that PackKit generated or, for Basic, the single procedural S100 representation.

Other supported rendering settings may be accepted under `generator`; schema validation intentionally permits generator-specific extensions.

## `dayz`

Optional object controlling generated DayZ config names, ownership role, paths and CE defaults.

### `dayz.namespace_role`

For ordinary third-party generation:

- omitted or `owner` — this pack owns its namespace and PackKit emits one `CfgPaintZPacks` declaration;
- `satellite` — this pack contributes content to an existing third-party namespace owner and must provide both `owner_class` and `owner_patch`.

`namespace_role = "satellite"` is invalid with `--official`. Official `PZ` content is not a satellite of Standard or any other content pack; PaintZ core is already the namespace owner.

### `dayz.addon_root`

Optional DayZ/PBO source root used in generated `.paa` references for can artwork and asset-backed target surfaces.

Example:

```json
"addon_root": "NCP_ExamplePaintPack"
```

may produce paths such as:

```text
NCP_ExamplePaintPack\data\cans\ncp_s_fde_co.paa
NCP_ExamplePaintPack\data\surfaces\ncp_s_fde_co.paa
```

Basic target surfaces do not use an addon path; their generated `texture` value is a procedural DayZ color descriptor.

If omitted, PackKit derives a deterministic root.

### `dayz.patch_class`

Optional explicit `CfgPatches` child classname. Normally derived automatically.

### `dayz.owner_class`

Config-tree linkage to the namespace owner.

For a normal third-party owner pack it is optional and normally derived. For a third-party satellite it is required and must name the existing owner's `CfgPaintZPacks` child.

For `--official`, an explicit value is allowed only if it equals:

```text
PZ_PaintZOfficial
```

Official generation does not emit that owner; it references the owner supplied by PaintZ core.

### `dayz.owner_patch`

Required only for a third-party satellite. It is the existing owner/core PBO's `CfgPatches` classname and is added to generated `requiredAddons[]`.

It is invalid for ordinary owner mode and for `--official` generation.

### `dayz.base_class`

Optional can base override. Default:

```text
PaintZ_SprayCanBase
```

Normal packs should not change this without a specific compatibility reason.

### `dayz.class_prefix`

Optional prefix used for generated spawnable can config classnames. Normally derived automatically.

### `dayz.types_nominal`

Optional nominal value for generated `types.generated.xml`. Default `0`.

### `dayz.types_lifetime`

Optional lifetime for generated `types.generated.xml`. Default `14400`.

### `dayz.emit_config_fragment`

Legacy field name retained from the extracted generator. When `false`, DayZ config/type output is skipped. When true/omitted, PackKit emits a complete API-v1 `generated/dayz/config.cpp`, not old per-finish action fragments.

## `paints`

Required non-empty array of finish definitions.

### `id`

Finish suffix, not the complete finish ID.

Allowed after normalization:

```text
[A-Z0-9]{2,12}
```

A descriptive three-character suffix is preferred.

Example with `pack.prefix = NCP` and `type = basic`:

```json
"id": "BLK"
```

produces:

```text
NCP-B-BLK
```

Omitting `id` permits PackKit to suggest one, but release manifests should commit explicit suffixes so identity cannot change because a suggestion algorithm changes.

### `name`

Required human-readable finish name. Type/category words such as `Basic` do not need to be repeated in the display name; the finish type is represented separately by `type` and the ID type letter.

### `type`

Required finish category. Current manifest spellings and PaintZ type letters are:

| Manifest type | ID letter | Meaning |
|---|---|---|
| `basic` | `B` | plain RGB only, procedural target surface, no appearance treatment |
| `solid` | `S` | one-color asset-backed finish; may include wear/noise/detail |
| `camo` | `C` | camouflage artwork |
| `pattern` | `P` | generic non-camouflage pattern |
| `metallic` | `M` | metallic |
| `rusted` | `R` | rusted/oxidized |
| `weathered` | `W` | weathered |
| `fluorescent` | `F` | fluorescent |
| `special` / `custom` | `X` | special/custom |
| `transparent` | `T` | transparent/tint |

Basic and Solid are intentionally distinct even when they share the same nominal/base color.

### `color`

For `basic` and `solid`, specify exactly one `#RRGGBB` color and omit `pattern`.

For `basic`, the color is converted directly to a procedural DayZ surface descriptor. No target-surface PNG/PAA is generated.

For `solid`, the color is the base of the generated target-surface image and may be modified visually by the selected appearance profile.

### `pattern`

For a `camo` or `pattern` finish, specify a safe relative source path and omit `color`.

Absolute paths and parent traversal (`..`) are rejected. The source file must exist when the manifest is validated/generated.

### `appearance_profile`

Optional named appearance profile for asset-backed finishes. It must resolve through the workspace or PackKit appearance-profile configuration during rendering.

`basic` explicitly forbids `appearance_profile`; Basic means color only.

### `dayz_class`

Optional explicit spawnable can classname for this finish. Normally PackKit derives a distinctive deterministic classname.

Use only valid DayZ config classname characters.

Complete finish IDs include the type letter, so the same suffix may legally appear in different types, for example `NCP-B-FDE` and `NCP-S-FDE`. DayZ config classnames still have to be unique. If default classname derivation would collide, use distinct explicit `dayz_class` values where appropriate; PackKit rejects duplicate generated classnames.

### Label text overrides

The renderer accepts optional fields such as:

- `finish`;
- `badge_text`;
- `field_text`;
- `footer_text`.

They affect standard label text only. They do not alter PaintZ runtime identity or mechanics. Basic can labels use `BASIC SERIES` by default.

The standard Design 3 label itself is PackKit-controlled and includes the PaintZ logo at the top with a distinct red `Z`. Pack manifests should not reimplement the shared logo/geometry.

## Generated identity and files

Given:

```text
prefix = NCP
type = basic
id = BLK
```

PackKit generates canonical finish ID:

```text
NCP-B-BLK
```

It generates the can artwork/preview/catalog entries, but no `generated/surfaces/ncp_b_blk_co.png`. Generated config instead includes a procedural S100 value similar to:

```text
#(argb,8,8,3)color(0.149020,0.156863,0.152941,1.0,CO)
```

For asset-backed finishes, generated surface file stems continue to use names such as:

```text
ncp_c_ftn_co.png
ncp_c_ftn_s050_co.png
ncp_c_ftn_s150_co.png
```

and generated `config.cpp` references corresponding `.paa` names after the normal DayZ texture-conversion/build step.

## Official mode

Official PaintZ validation/generation is explicit:

```powershell
paintz-packkit --manifest paints.json --check --official
paintz-packkit --manifest paints.json --clean --official
```

Under the current API-v1 architecture, `--official` means an independent content pack contributing finishes to the **core-owned `PZ` namespace**. It therefore:

- accepts `pack.prefix = "PZ"`;
- rejects ordinary third-party prefixes and unassigned reserved `PZ?` prefixes;
- emits **no** `CfgPaintZPacks` namespace-owner declaration;
- sets every generated finish to `owner = "PZ_PaintZOfficial"`;
- requires `PaintZ_DynamicPaint` directly;
- does not require Standard, Field, Vanilla, Hunter, Pastel, or another official content pack;
- rejects satellite mode and `owner_patch`.

`PZ_PaintZOfficial` is declared by PaintZ runtime, not by the generated content pack. `--official` is an authoring permission/path, not a cryptographic proof of authorship.

## Runtime collision reminder

PackKit can detect duplicates inside the local manifest/build, but cannot guarantee global Workshop prefix uniqueness. PaintZ validates the complete loaded mod set at runtime and disables conflicting namespaces/finish IDs rather than using load-order wins.
