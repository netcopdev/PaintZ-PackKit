# PaintZ PackKit interoperability obligations

The authoritative runtime interoperability specification lives in `netcopdev/PaintZ` at `docs/PAINT_PACK_API.md`; the concrete DayZ representation is in `docs/PAINT_PACK_CONFIG_V1.md`.

PackKit is a reference authoring/build implementation of that contract. It must conform to PaintZ rather than defining a competing runtime API.

## Identity model

API v1 uses one complete short finish ID as the canonical runtime and persistence identity:

```text
<PREFIX>-<TYPE>-<SUFFIX>
```

Package names, repositories, PBO names, Workshop items, and content categories are not part of finish identity.

Changing a released complete finish ID is a persistence-breaking change. Moving an unchanged finish between packages while retaining its complete ID is packaging-only.

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

## Runtime collision semantics

PaintZ discovers namespace owners before finishes.

- exactly one owner for a prefix -> namespace valid;
- multiple owner declarations for a prefix -> entire namespace disabled;
- duplicate complete finish ID -> that finish ID disabled;
- no first-loaded-wins or last-loaded-wins overwrite behavior.

For `PZ`, PaintZ core is the one owner. An official content pack that redeclares `PZ` is invalid and will collide with core.

PackKit validates local syntax and local duplicates, but it cannot prove global third-party prefix ownership. Do not introduce UUIDs, secrets, generated ownership tokens, or an online registry as fake security.

## Generated content boundary

A generated pack may contain:

- finish registrations;
- runtime surface representations and pattern-scale variants;
- standardized spray-can textures;
- thin spawnable can subclasses inheriting `PaintZ_SprayCanBase`;
- DayZ dependency metadata;
- optional CE type entries.

A third-party owner also contains one namespace-owner declaration. A third-party satellite and an official `PZ` pack do not.

Generated packs must not contain PaintZ persistence, target policy, synchronization, model inspection, painting actions, per-finish action subclasses, or a private runtime paint catalogue.

## Asset declaration

Every finish explicitly declares the runtime surfaces PaintZ may choose. Pattern/camouflage finishes declare only scale variants that actually exist, and every finish includes a 100% representation. PaintZ must not infer arbitrary third-party texture paths from IDs.

## Source of truth

If this file conflicts with `PaintZ/docs/PAINT_PACK_API.md` or `PaintZ/docs/PAINT_PACK_CONFIG_V1.md`, PaintZ wins. Update PackKit code, tests and documentation to conform rather than creating another standard.
