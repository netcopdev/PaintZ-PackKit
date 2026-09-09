# PaintZ PackKit interoperability obligations

The authoritative runtime interoperability specification lives in `netcopdev/PaintZ` at `docs/PAINT_PACK_API.md`.

PackKit is a reference authoring/build implementation of that contract. This document records the rules PackKit must enforce or preserve so its generator cannot drift from PaintZ.

## Identity model

API v1 uses the complete short PaintZ finish ID as the canonical runtime and persistence identity:

```text
<PREFIX>-<TYPE>-<SUFFIX>
```

Examples:

```text
PZ-C-FTN
PZ-S-FDE
NCP-C-FTN
NCP-S-FDE
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

PackKit derives each complete finish ID from:

- the pack prefix;
- the existing one-character PaintZ type code;
- the finish suffix.

Existing type letters remain:

```text
S C P M R W F X T
```

Finish suffixes are uppercase alphanumeric, 2-12 characters, with short descriptive 3-character values preferred.

Changing a released complete finish ID is a breaking persistence change.

## What PackKit can and cannot validate

PackKit validates locally:

- prefix syntax;
- reserved `PZ*` use;
- type/suffix syntax;
- complete finish-ID construction;
- uniqueness of finish IDs inside the project/build set;
- one namespace-owner declaration per generated pack;
- generated class/config/path consistency.

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
- surface textures and explicitly declared pattern-scale variants;
- standardized can textures;
- thin spawnable can subclasses inheriting PaintZ's common base;
- `CfgPatches` dependency on `PaintZ_DynamicPaint`;
- optional `types.xml` entries.

Normal API-v1 output contains no generated per-finish Enforce action subclasses and no generated runtime paint catalogue. PaintZ resolves finishes generically through its runtime registry.

## Asset declaration

Generated finish registration explicitly declares every runtime surface asset PaintZ may select. Pattern/camouflage finishes declare only scale variants that PackKit actually generated, and every finish includes a 100% surface.

The generated `config.cpp` references matching `.paa` names. PackKit currently creates PNG source assets; conversion to PAA/PBO packaging remains a separate build step until PackKit explicitly gains those capabilities.

## Standard Pack relationship

`netcopdev/PaintZ-Standard-Pack` is the official reference pack and initially uses prefix `PZ`.

PackKit must build/validate Standard Pack through the same API-v1 machinery plus the explicit `--official` permission. Do not create a separate incompatible format for official content.

## Source of truth

If this file conflicts with `PaintZ/docs/PAINT_PACK_API.md` or the concrete `PaintZ/docs/PAINT_PACK_CONFIG_V1.md`, PaintZ wins. Update PackKit documentation/code/tests to conform rather than creating a second interoperability standard.
