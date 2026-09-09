# PaintZ PackKit Codex Instructions

## Project purpose

PaintZ PackKit is the offline authoring/build toolkit for PaintZ paint packs. It converts finish metadata, source artwork and limited pack branding into validated PaintZ-compatible generated assets and DayZ config/source output.

This repository is **not** the PaintZ runtime mod. Do not duplicate or reimplement PaintZ gameplay, persistence, networking, eligibility/policy, painting actions or target-item compatibility logic here.

Read `README.md` before architectural work. For pack identity, namespace registration, finish IDs, generated can classes or runtime interoperability, also read `docs/INTEROPERABILITY.md`. The authoritative runtime contract lives in `netcopdev/PaintZ/docs/PAINT_PACK_API.md` and `docs/PAINT_PACK_CONFIG_V1.md`; PackKit conforms to PaintZ rather than defining a competing runtime API.

## Mandatory Git discipline

Before modifying repository work, inspect:

```text
git branch --show-current
git status --short
git log -1 --oneline
git branch -a
```

`main` is the shared integration base. New independent work normally uses a separate branch from current `main`. Base on an unmerged feature branch only when the requested work explicitly depends on it.

Implementation permission is not merge permission. Do not merge, squash, rebase or fast-forward work into `main` unless the user explicitly approves that integration after review/testing or explicitly authorized that exact integration beforehand.

When work is complete, report the branch, relevant commits, tests performed, and anything still requiring real DayZ Tools/runtime verification.

## Architecture boundary

Dependency direction is:

```text
PackKit -> generates paint-pack source/assets
Paint pack -> PaintZ runtime -> CF
PaintZ runtime -X-> PackKit
PaintZ runtime -X-> specific paint packs
```

PaintZ owns runtime behaviour and the common spray-can implementation. PackKit owns offline generation and validation. Paint packs own finish content.

A normal generated API-v1 paint pack may contain:

- exactly one namespace-owner declaration;
- finish registrations;
- runtime surface representations: procedural descriptors for Basic finishes and generated texture assets/explicit scale variants for asset-backed finishes;
- standardized spray-can textures;
- thin spawnable can subclasses inheriting `PaintZ_SprayCanBase`;
- `CfgPatches` dependency metadata;
- optional `types.xml` entries and restrained branding.

A normal paint pack must not define painting actions, persistence, synchronization, target policy, or other PaintZ gameplay mechanics.

## Paint Pack API v1 identity

API v1 uses one short complete finish ID as both runtime identity and persisted logical identity:

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

Do **not** introduce a second reverse-domain canonical ID, UUID, secret, generated ownership token, or online registry identifier as a requirement.

### Prefix

A normal third-party pack has one permanent prefix matching:

```text
^[A-Z][A-Z0-9]{1,2}$
```

All valid prefixes beginning with `PZ` are reserved for official PaintZ content. Normal PackKit validation must reject them.

The PaintZ Standard Pack/official content may use `PZ*` only through the explicit `--official` generation path. That path emits `official = 1` in the namespace declaration. It is an interoperability gate, not cryptographic authentication.

Changing a released prefix is a breaking persistence/identity change.

### Type and suffix

Keep the established type letters:

```text
B S C P M R W F X T
```

`B` / `basic` is a plain RGB-only finish. It has no pattern or appearance profile, PackKit emits a procedural DayZ color descriptor as its S100 runtime surface, and PackKit does not generate a target-surface PNG/PAA for it. It still receives normal can artwork and a thin spray-can class.

`S` / `solid` remains the asset-backed one-color category and may include deterministic surface treatment/detail such as grain, scratches, grime, edge wear or rust hints. Do not collapse Basic and Solid back into one category.

Finish suffixes are uppercase alphanumeric, 2-12 characters, with descriptive 3-character suffixes preferred. Changing a released complete finish ID is a breaking persistence change.

IDs and generated classnames must be deterministic from authoritative input. Never derive identity from timestamps, random values or unordered traversal.

## Runtime collision semantics PackKit must target

PackKit validates local syntax and local duplicates. It cannot know whether every independent Workshop pack already uses a chosen prefix.

PaintZ performs runtime collision detection against the complete loaded set:

- one namespace owner for a prefix -> namespace valid;
- multiple owners for one prefix -> entire namespace disabled;
- duplicate complete finish ID -> that finish disabled;
- no first-loaded-wins or last-loaded-wins overwrite behavior.

Do not imply PackKit can globally reserve or prove ownership of a prefix.

For future multi-PBO pack families, only one owner/core PBO declares the namespace. Satellite PBOs depend on it and do not re-declare ownership.

## Generated DayZ config rules

Inspect the current PaintZ runtime config contract before changing runtime-facing output.

API-v1 output must generate:

- `CfgPatches.requiredAddons[]` including `PaintZ_DynamicPaint`;
- one `CfgPaintZPacks` owner declaration;
- one `CfgPaintZFinishes` child per finish;
- exact `owner` linkage to the generated owner config class;
- explicit `Surfaces` declarations for every runtime surface representation PaintZ may choose;
- a 100% surface for every finish;
- a procedural-color S100 descriptor and no target-surface asset for `B` / `basic`;
- only actually generated scale variants for patterns;
- one thin spawnable can subclass per finish using `paintzFinish`.

Normal API-v1 output must **not** generate:

- per-finish `ActionPaintZPaint_*` Enforce classes;
- a generated `PaintZ_PaintCatalog` runtime class;
- per-finish action registration/attachment logic;
- painted subclasses for weapons, magazines, attachments or other targets.

The generated owner config classname is a deterministic config linkage key, not another PaintZ identity or security token. Generate distinctive owner/finish config class names because DayZ merges config trees before PaintZ enumerates them.

Complete finish identity includes type, so IDs such as `NCP-B-FDE` and `NCP-S-FDE` may coexist. DayZ config classnames are a separate namespace and must still be unique. Detect generated can-class collisions and allow explicit `dayz_class` only where needed for compatibility or deliberate suffix reuse.

## Spray-can design and branding

PaintZ core owns the common can model/UV/runtime behaviour and standard PaintZ label identity. PackKit generates finish-specific can artwork and thin config subclasses.

Standard templates retain PaintZ-controlled layout, logo/identity, geometry, typography rules, badge placement, margins and footer treatment.

Pack-controlled fields may include finish name/ID/type, publisher name, small publisher mark, and restrained collection/series text. Do not expose arbitrary coordinates, unrestricted fonts, free-form geometry or replacement of the common can model as normal manifest fields.

Basic cans should identify themselves as Basic rather than Solid in generated series text.

## Generator/source-of-truth discipline

Generated files are derived artifacts. Never hand-edit generated output to fix a generator defect; fix the manifest/template/generator and regenerate.

Generation must be deterministic and offline-capable. Avoid timestamps, random IDs, machine-specific absolute paths and environment-dependent ordering in generated content.

The existing `PaintZ/tools/paintzgen` implementation is proven source material. Preserve useful rendering/output behaviour where the API-v1 contract does not intentionally replace it.

The primary authoring environment is Windows. Avoid Unix-only workflows and handle Windows filesystem paths separately from emitted DayZ/PBO paths.

## Validation-first behavior

Invalid author input should fail early with a useful field/finish-specific error.

Validate as applicable:

- manifest/schema version;
- pack prefix syntax and reserved-prefix rules;
- finish suffix/type syntax;
- Basic requirements (`color` required, no `pattern`, no `appearance_profile`);
- complete finish-ID uniqueness;
- generated classname uniqueness;
- referenced source-file existence;
- safe relative asset paths and path traversal;
- output path safety;
- duplicate output paths;
- finish-specific requirements;
- supported pattern scales;
- branding constraints when implemented.

Do not silently repair ambiguous identity data. Normalization is acceptable only where the schema explicitly defines it.

## Output safety

Generated output must remain under the selected build/output root. Never delete or overwrite arbitrary user files based solely on manifest-supplied paths.

`--clean` may remove only PackKit-owned generated output, never source artwork or manifests.

## Tests and verification

Add automated tests for generator behavior where practical. High-value coverage includes:

- namespaced IDs and normalization;
- Basic `B` ID generation;
- Basic procedural S100 emission and absence of a target-surface file;
- Basic rejection of pattern/appearance-profile input;
- reserved `PZ*` rejection in normal mode;
- explicit official `PZ` generation;
- duplicate finish IDs;
- deterministic owner/classname generation;
- standalone `config.cpp` structure;
- absence of legacy generated Enforce actions/catalogue;
- representative Solid and patterned finishes;
- explicit scale declarations;
- safe/missing source paths;
- Windows/path edge cases.

Do not claim an AddonBuilder/PBO or DayZ runtime compile unless it was actually run with those tools.

## Documentation contract

Keep `README.md`, schema files and `docs/INTEROPERABILITY.md` aligned with author-facing behavior. Long instructions belong in documentation rather than comment-heavy JSON examples.

Examples should be valid PackKit inputs whenever practical.

## Avoid premature complexity

Do not invent a GUI, online prefix registry, cryptographic ownership system, broad plugin framework, unrestricted theming system or anonymous/runtime-generated color-persistence system without a concrete requirement.

Basic procedural RGB support is infrastructure for predefined pack-owned finishes. Do not reinterpret it as authorization to add arbitrary user-generated colors, paint mixing, cumulative tint state, or RGB persistence without a separate explicit design decision.

Prefer the smallest design that supports:

1. one permanent pack namespace;
2. authoritative finish definitions;
3. standardized asset/procedural-surface generation;
4. thin can-class generation;
5. explicit finish registration;
6. validation;
7. deterministic output.
