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
      "id": "FDE",
      "name": "Flat Dark Earth",
      "type": "solid",
      "color": "#5A4F46"
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

The official PaintZ Standard Pack/official content may use a reserved `PZ*` namespace only when PackKit is invoked with `--official`.

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

Optional `[width, height]` for runtime finish surfaces. Default is `1024 x 1024`.

### `generator.pattern_scales`

Optional non-empty array of positive scales. Each value must resolve to a whole percentage from 1 through 1000, and `1.0` is mandatory.

Pattern-backed finishes receive these generated variants. Solid finishes always generate only their 100% surface.

Example:

```json
"pattern_scales": [0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
```

becomes scale percentages:

```text
50 75 100 150 200 300
```

PaintZ receives explicit `Surfaces` entries only for variants that PackKit generated.

Other existing rendering settings retained from the extracted generator remain accepted under `generator`.

## `dayz`

Optional object controlling generated DayZ config names/paths. In normal use only `addon_root` usually needs explicit consideration.

### `dayz.addon_root`

Optional DayZ/PBO source root used in generated `.paa` references.

Example:

```json
"addon_root": "NCP_ExamplePaintPack"
```

produces paths such as:

```text
NCP_ExamplePaintPack\data\cans\ncp_s_fde_co.paa
NCP_ExamplePaintPack\data\surfaces\ncp_s_fde_co.paa
```

If omitted, PackKit derives a deterministic root from the generated owner config class.

### `dayz.patch_class`

Optional explicit `CfgPatches` child classname. Normally derived automatically.

### `dayz.owner_class`

Optional explicit `CfgPaintZPacks` owner child classname. Normally derived automatically from the pack prefix/name/author.

This is only a config-tree linkage key. It is not persisted, user-facing, or proof of namespace ownership.

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

Legacy field name retained from the extracted generator. When `false`, DayZ config/type output is skipped. When true/omitted, PackKit 0.2 emits a complete API-v1 `generated/dayz/config.cpp`, not the old per-finish action fragments.

## `paints`

Required non-empty array of finish definitions.

### `id`

Finish suffix, not the complete finish ID.

Allowed after normalization:

```text
[A-Z0-9]{2,12}
```

A descriptive three-character suffix is preferred.

Example with `pack.prefix = NCP` and `type = solid`:

```json
"id": "FDE"
```

produces:

```text
NCP-S-FDE
```

Omitting `id` permits PackKit to suggest one, but release manifests should commit explicit suffixes so identity cannot change because a suggestion algorithm changes.

### `name`

Required human-readable finish name.

### `type`

Required finish category. Current manifest spellings and PaintZ type letters are:

| Manifest type | ID letter |
|---|---|
| `solid` | `S` |
| `camo` | `C` |
| `pattern` | `P` |
| `metallic` | `M` |
| `rusted` | `R` |
| `weathered` | `W` |
| `fluorescent` | `F` |
| `special` / `custom` | `X` |
| `transparent` | `T` |

### `color`

For a solid/color-backed finish, specify exactly one `#RRGGBB` color and omit `pattern`.

### `pattern`

For a pattern-backed finish, specify a safe relative source path and omit `color`.

Absolute paths and parent traversal (`..`) are rejected. The source file must exist when the manifest is validated/generated.

### `appearance_profile`

Optional named appearance profile. It must resolve through the workspace or PackKit appearance-profile configuration during rendering.

### `dayz_class`

Optional explicit spawnable can classname for this finish. Normally PackKit derives a distinctive deterministic classname.

Use only valid DayZ config classname characters.

### Label text overrides

The extracted renderer currently retains optional fields such as:

- `finish`;
- `badge_text`;
- `field_text`;
- `footer_text`.

They affect standard label text only. They do not alter PaintZ runtime identity or mechanics.

## Generated identity and files

Given:

```text
prefix = NCP
type = camo
id = FTN
```

PackKit generates canonical finish ID:

```text
NCP-C-FTN
```

and file stems such as:

```text
ncp_c_ftn_co.png
ncp_c_ftn_s050_co.png
ncp_c_ftn_s150_co.png
```

The generated `config.cpp` references corresponding `.paa` names after the normal DayZ texture-conversion/build step.

## Official mode

Normal third-party validation:

```powershell
paintz-packkit --manifest paints.json --check
```

Official PaintZ/Standard Pack validation:

```powershell
paintz-packkit --manifest paints.json --check --official
```

`--official` is valid only for a reserved `PZ*` prefix. It causes the namespace owner declaration to include:

```cpp
official = 1;
```

This does not prove authorship; it is the explicit PackKit path for producing official reserved-namespace content.

## Runtime collision reminder

PackKit can detect duplicates inside the local manifest/build, but cannot guarantee global Workshop prefix uniqueness. PaintZ validates the complete loaded mod set at runtime and disables conflicting namespaces/finish IDs rather than using load-order wins.
