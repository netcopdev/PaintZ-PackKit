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

Official PaintZ content is allowed to use `PZ*` through the explicit `--official` generation path. This applies to both namespace-owner packs and official satellite packs. The flag is an interoperability gate, not cryptographic authentication.

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

Changing a released complete finish ID is a breaking persistence change. Moving an unchanged finish between PBOs in the same namespace family is not a persistence change when its complete finish ID remains unchanged.

## What PackKit can and cannot validate

PackKit validates locally:

- prefix syntax;
- reserved `PZ*` use;
- type/suffix syntax;
- complete finish-ID construction;
- uniqueness of finish IDs inside the project/build set;
- owner-versus-satellite manifest requirements;
- generated class/config/path consistency.

PackKit cannot guarantee that a third-party prefix is globally unused by every independently distributed DayZ mod. It must not pretend a generated UUID or token solves that problem.

Runtime collision detection belongs to PaintZ because only the runtime knows the complete installed mod set.

## Namespace roles

PackKit supports two DayZ namespace roles through `dayz.namespace_role`.

### Owner role

`owner` is the default and preserves the normal standalone-pack behavior. The generated PBO:

- declares exactly one `CfgPaintZPacks` namespace owner;
- registers its finishes against that owner;
- depends on `PaintZ_DynamicPaint`.

For an official `PZ*` owner generated with `--official`, the owner declaration includes `official = 1`.

### Satellite role

`satellite` is for an additional PBO in an already-owned namespace family. Its manifest must provide:

```json
"dayz": {
  "namespace_role": "satellite",
  "owner_class": "NCP_MyOwnerPack",
  "owner_patch": "NCP_MyOwnerPack_Patch"
}
```

`owner_class` is the exact existing `CfgPaintZPacks` child classname. `owner_patch` is the exact existing owner/core PBO `CfgPatches` classname.

A generated satellite:

- does **not** emit `CfgPaintZPacks`;
- registers each finish with `owner = "<owner_class>"`;
- adds `owner_patch` to `CfgPatches.requiredAddons[]` after `PaintZ_DynamicPaint`;
- uses its own deterministic config-registration root so independently generated satellite content does not unnecessarily reuse the owner PBO's config child classnames;
- still owns its own textures and thin spray-can classes.

A satellite must never redeclare the namespace owner. Doing so would create the exact duplicate-owner collision the API is designed to reject.

For an official `PZ*` satellite, use `--official` so the reserved prefix passes PackKit validation. Because a satellite emits no owner declaration, it also emits no second `official = 1` owner.

## Runtime collision semantics PackKit targets

PaintZ discovers namespace owners before finishes.

- exactly one owner for a prefix -> valid namespace;
- multiple owner declarations for a prefix -> entire namespace conflicted/disabled;
- duplicate complete finish ID -> that finish ID is ambiguous/disabled;
- no registration silently overwrites another because of load order.

## Generated pack contents

A generated owner pack contains content/registration rather than PaintZ gameplay logic:

- one namespace-owner declaration;
- finish metadata;
- surface textures and explicitly declared pattern-scale variants;
- standardized can textures;
- thin spawnable can subclasses inheriting PaintZ's common base;
- `CfgPatches` dependency on `PaintZ_DynamicPaint`;
- optional `types.xml` entries.

A generated satellite contains the same finish/content assets but references the existing namespace owner rather than declaring another one, and adds a dependency on the owner/core PBO.

Normal API-v1 output contains no generated per-finish Enforce action subclasses and no generated runtime paint catalogue. PaintZ resolves finishes generically through its runtime registry.

## Asset declaration

Generated finish registration explicitly declares every runtime surface asset PaintZ may select. Pattern/camouflage finishes declare only scale variants that PackKit actually generated, and every finish includes a 100% surface.

The generated `config.cpp` references matching `.paa` names. PackKit currently creates PNG source assets; conversion to PAA/PBO packaging remains a separate build step until PackKit explicitly gains those capabilities.

## Standard Pack relationship

`netcopdev/PaintZ-Standard-Pack` is the official reference owner pack and initially uses prefix `PZ`.

Additional official content PBOs may remain inside that same `PZ` namespace by using satellite mode with the Standard Pack's owner linkage. This allows a finish such as `PZ-C-FTN` to move to another official content PBO without changing its canonical/persisted finish ID.

A separate official namespace such as `PZA` remains a different canonical namespace. Moving `PZ-C-FTN` to `PZA-C-FTN` would therefore be an identity-breaking change rather than a packaging-only move.

PackKit must build/validate official owner and satellite content through the same API-v1 machinery plus the explicit `--official` permission. Do not create a separate incompatible format for official content.

## Source of truth

If this file conflicts with `PaintZ/docs/PAINT_PACK_API.md` or the concrete `PaintZ/docs/PAINT_PACK_CONFIG_V1.md`, PaintZ wins. Update PackKit documentation/code/tests to conform rather than creating a second interoperability standard.
