# PaintZ PackKit interoperability obligations

The authoritative runtime interoperability specification lives in `netcopdev/PaintZ` at `docs/PAINT_PACK_API.md`; the concrete DayZ representation is in `docs/PAINT_PACK_CONFIG_V1.md`.

PackKit is a reference authoring/build implementation of that contract. It must conform to PaintZ rather than defining a competing runtime API.

## Identity model

API v1 uses one complete short finish ID as the canonical runtime and persistence identity:

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

Package names, repositories, PBO names, Workshop items, and content categories are not part of finish identity.

Changing a released complete finish ID is a persistence-breaking change. Moving an unchanged finish between packages while retaining its complete ID is packaging-only.

Do not generate or require a second canonical ID, UUID, secret, ownership token, or online registry identifier.

## Third-party namespace model

A normal third-party pack chooses one permanent 2-3 character prefix matching:

```text
^[A-Z][A-Z0-9]{1,2}$
```

Normal PackKit generation rejects all valid prefixes beginning with `PZ`.

A third-party standalone owner pack:

- emits exactly one `CfgPaintZPacks` owner;
- registers its finishes against that owner;
- requires `PaintZ_DynamicPaint`.

A third-party family may be split across several PBOs by using `dayz.namespace_role = "satellite"`. A satellite:

- emits no `CfgPaintZPacks` owner;
- references the family's existing `dayz.owner_class`;
- requires both `PaintZ_DynamicPaint` and `dayz.owner_patch`;
- owns its own finish assets, can classes, and finish config children.

This owner/satellite mode is an implementation tool for external multi-PBO namespace families. It is not the user-facing model for official PaintZ collections.

## Official `PZ` namespace

PaintZ runtime itself owns the official `PZ` namespace through the canonical config owner:

```text
PZ_PaintZOfficial
```

Official content packs are independent contributors to that namespace. They do not declare `PZ` and they do not depend on another official content pack merely for namespace access.

The `--official` generation path therefore has strict semantics:

- only `PZ` is currently accepted;
- generated config emits no `CfgPaintZPacks` declaration;
- every generated `PZ-*` finish uses `owner = "PZ_PaintZOfficial"`;
- generated `CfgPatches.requiredAddons[]` contains `PaintZ_DynamicPaint` but no Standard/Military/Pastel/Hunting owner dependency;
- `dayz.namespace_role = "satellite"` is rejected for official content;
- `dayz.owner_patch` is rejected for official content;
- an explicit `dayz.owner_class`, if present, must equal `PZ_PaintZOfficial`;
- unassigned reserved namespaces such as `PZA` or `PZ9` remain rejected until PaintZ explicitly assigns them.

This permits peer official packages such as:

```text
PaintZ Standard Pack -> PaintZ
PaintZ Pastel Pack   -> PaintZ
PaintZ Military Pack -> PaintZ
PaintZ Hunting Pack  -> PaintZ
```

All may contain unique `PZ-*` finishes. None is a parent or mandatory base pack for the others.

## Finish types and Basic semantics

PackKit derives each complete finish ID from the pack prefix, the one-character PaintZ type code, and the finish suffix.

Current type letters include:

```text
B S C P M R W F X T
```

`B` / `basic` means one plain RGB color only. It has no appearance profile, pattern, wear, noise, scratches, grime, rust, or other target-surface treatment. PackKit emits a procedural DayZ color descriptor and does not generate a target-surface PNG/PAA.

`S` / `solid` remains the asset-backed one-color category and may include deterministic surface character. `C` / `camo` and `P` / `pattern` use pattern artwork.

A Basic manifest entry must contain `color` and must not contain `pattern` or `appearance_profile`.

Example:

```json
{
  "id": "BLK",
  "name": "Basic Black",
  "type": "basic",
  "color": "#262827"
}
```

PackKit converts that RGB value to a deterministic procedural runtime surface such as:

```text
#(argb,8,8,3)color(0.149020,0.156863,0.152941,1.0,CO)
```

The descriptor is derived representation only; the complete finish ID remains the persisted identity.

Basic finishes still receive normal generated spray-can artwork and thin can classes. Only the painted target surface avoids a PAA.

Complete finish identity includes the type letter, so IDs such as `NCP-B-FDE` and `NCP-S-FDE` may coexist. DayZ config classnames are a separate namespace and must still be unique. PackKit must detect generated can-class collisions; an explicit `dayz_class` may be used where compatibility or deliberate suffix reuse requires it.

## What PackKit validates

PackKit validates locally:

- prefix syntax and reserved `PZ*` rules;
- third-party owner/satellite requirements;
- official core-owned `PZ` requirements;
- type/suffix syntax;
- Basic/Solid/Pattern field requirements;
- complete finish-ID construction and local uniqueness;
- generated class/config/path consistency;
- generated spray-can classname uniqueness;
- referenced source-file existence and safe paths.

PackKit cannot guarantee that a third-party prefix is globally unused by every independently distributed DayZ mod. It must not pretend a generated UUID or token solves that problem.

## Runtime collision semantics

PaintZ discovers namespace owners before finishes.

- exactly one owner for a prefix -> namespace valid;
- multiple owner declarations for a prefix -> entire namespace disabled;
- duplicate complete finish ID -> that finish ID disabled;
- no registration silently overwrites another because of load order.

For `PZ`, PaintZ core is the one legitimate owner. Noncanonical or unassigned reserved owner declarations are invalid.

## Generated pack contents

A generated pack may contain:

- finish registrations;
- runtime surface representations;
- procedural S100 descriptors for Basic finishes;
- generated surface textures and explicit scale variants for asset-backed finishes;
- standardized can textures for all finishes;
- thin spawnable can subclasses inheriting `PaintZ_SprayCanBase`;
- DayZ dependency metadata;
- optional CE type entries.

A third-party owner also contains one namespace-owner declaration. A third-party satellite and an official `PZ` pack do not.

Generated packs must not contain PaintZ persistence, target policy, synchronization, model inspection, painting actions, per-finish action subclasses, or a private runtime paint catalogue.

## Surface declaration

Generated finish registration explicitly declares every runtime surface representation PaintZ may select.

For Basic finishes:

- exactly one 100% surface is emitted;
- its `texture` value is a procedural color descriptor;
- no target-surface PNG/PAA is generated.

For asset-backed finishes:

- generated config references matching `.paa` names;
- pattern/camouflage finishes declare only scale variants PackKit actually generated;
- every finish includes a 100% surface.

PackKit creates PNG source assets for asset-backed finishes; conversion to PAA/PBO packaging remains a separate pack-build step.

## Standard Pack relationship

`netcopdev/PaintZ-Standard-Pack` is an official reference pack contributing to the core-owned `PZ` namespace.

PackKit must build/validate Standard Pack through the same API-v1 machinery plus the explicit `--official` permission. Do not create a separate incompatible format for official content.

The Standard Pack may contain both `PZ-B-*` Basic colors and existing `PZ-S-*` treated Solid finishes. Adding a Basic counterpart must not repurpose or rename the corresponding Solid finish identity.

## Source of truth

If this file conflicts with `PaintZ/docs/PAINT_PACK_API.md` or `PaintZ/docs/PAINT_PACK_CONFIG_V1.md`, PaintZ wins. Update PackKit code, tests and documentation to conform rather than creating another standard.
