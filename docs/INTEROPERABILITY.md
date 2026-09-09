# PaintZ PackKit interoperability obligations

The authoritative runtime interoperability specification lives in `netcopdev/PaintZ` at `docs/PAINT_PACK_API.md` and `docs/PAINT_PACK_CONFIG_V1.md`.

PackKit is a reference authoring/build implementation of that contract. This document records the rules PackKit must enforce or preserve so its generator cannot drift from PaintZ.

## Identity model

API v1 uses the complete short PaintZ finish ID as the canonical runtime and persistence identity:

```text
<PREFIX>-<TYPE>-<SUFFIX>
```

Examples:

```text
PZ-B-BLK
PZ-S-FDE
PZ-C-FTN
NCP-B-ODG
NCP-C-FTN
```

Do not generate or require a separate reverse-domain canonical finish ID, UUID, secret, ownership token, or online registry identifier.

## Pack prefix

A normal third-party pack chooses exactly one permanent 2-3 character prefix.

Valid syntax after normalization:

```text
^[A-Z][A-Z0-9]{1,2}$
```

All valid prefixes beginning with `PZ` are reserved for official PaintZ content. Ordinary third-party generation must reject `PZ`, `PZA`-`PZZ`, `PZ0`-`PZ9`, and any other valid prefix beginning with `PZ`.

The official PaintZ Standard Pack is allowed to use `PZ` through the explicit `--official` generation path. This is an interoperability gate, not cryptographic authentication.

Changing a released pack prefix is a breaking identity change.

## Finish suffix and type

PackKit derives each complete finish ID from the pack prefix, the one-character PaintZ type code, and the finish suffix.

Current type letters are:

```text
B S C P M R W F X T
```

The relevant category semantics are:

- `B` / `basic`: one plain RGB color only. No appearance profile, pattern, wear, noise, scratches, grime, rust or other target-surface treatment. PackKit emits a procedural DayZ color descriptor and does not generate a target-surface PAA.
- `S` / `solid`: fundamentally one color, but asset-backed and therefore allowed to include deterministic surface character such as grain, scratches, grime, edge wear or rust hints.
- `C` / `camo`: camouflage artwork.
- `P` / `pattern`: generic non-camouflage pattern artwork.

Finish suffixes are uppercase alphanumeric, 2-12 characters, with short descriptive 3-character values preferred.

Changing a released complete finish ID is a breaking persistence change.

## Basic finish requirements

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

PackKit converts the RGB value to a deterministic procedural runtime surface such as:

```text
#(argb,8,8,3)color(0.149020,0.156863,0.152941,1.0,CO)
```

The generated config still declares that value as the finish's S100 `texture`, preserving the existing API-v1 `Surfaces` shape. The descriptor is derived representation only; the complete finish ID remains the persisted identity.

Basic finishes still receive normal generated spray-can artwork and thin can classes. Only the painted target surface avoids a PAA.

## What PackKit can and cannot validate

PackKit validates locally:

- prefix syntax;
- reserved `PZ*` use;
- type/suffix syntax;
- Basic/Solid/Pattern field requirements;
- complete finish-ID construction;
- uniqueness of finish IDs inside the project/build set;
- one namespace-owner declaration per generated pack;
- generated class/config/path consistency;
- generated spray-can classname uniqueness.

PackKit cannot guarantee that a third-party prefix is globally unused by every independently distributed DayZ mod. It must not pretend a generated UUID or token solves that problem.

Runtime collision detection belongs to PaintZ because only the runtime knows the complete installed mod set.

## Generated ownership structure

A generated single-pack output has exactly one namespace-owner declaration under `CfgPaintZPacks`.

The owner config class is a deterministic config linkage key. It is not persisted and is not another public PaintZ identity. Finish registrations reference that owner key through their `owner` property.

For future multi-PBO pack families, only the owner/core PBO should declare the namespace. Satellite PBOs must depend on that owner and must not re-declare ownership.

## Runtime collision semantics PackKit targets

PaintZ discovers namespace owners before finishes.

- exactly one owner for a prefix -> valid namespace;
- multiple owner declarations for a prefix -> entire namespace conflicted/disabled;
- duplicate complete finish ID -> that finish ID is ambiguous/disabled;
- no registration silently overwrites another because of load order.

## Generated pack contents

A normal generated pack contains content/registration rather than PaintZ gameplay logic:

- one namespace-owner declaration;
- finish metadata;
- procedural S100 surface descriptors for Basic finishes;
- generated surface textures and explicitly declared pattern-scale variants for asset-backed finishes;
- standardized can textures for all finishes;
- thin spawnable can subclasses inheriting PaintZ's common base;
- `CfgPatches` dependency on `PaintZ_DynamicPaint`;
- optional `types.xml` entries.

Normal API-v1 output contains no generated per-finish Enforce action subclasses and no generated runtime paint catalogue. PaintZ resolves finishes generically through its runtime registry.

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

PackKit currently creates PNG source assets for asset-backed finishes; conversion to PAA/PBO packaging remains a separate build step until PackKit explicitly gains those capabilities.

## Spray-can classname uniqueness

Complete finish identity includes the type letter, so IDs such as `NCP-B-FDE` and `NCP-S-FDE` may coexist.

DayZ config classnames are a separate namespace and must still be unique. PackKit must detect duplicate generated can classnames. An explicit `dayz_class` may be used when a pack needs two finishes with the same suffix or needs to preserve historical classnames.

## Standard Pack relationship

`netcopdev/PaintZ-Standard-Pack` is the official reference pack and initially uses prefix `PZ`.

PackKit must build/validate Standard Pack through the same API-v1 machinery plus the explicit `--official` permission. Do not create a separate incompatible format for official content.

The Standard Pack may contain both `PZ-B-*` Basic colors and existing `PZ-S-*` treated Solid finishes. Adding a Basic counterpart must not repurpose or rename the corresponding Solid finish identity.

## Source of truth

If this file conflicts with `PaintZ/docs/PAINT_PACK_API.md` or `PaintZ/docs/PAINT_PACK_CONFIG_V1.md`, PaintZ wins. Update PackKit documentation/code/tests to conform rather than creating a second interoperability standard.
