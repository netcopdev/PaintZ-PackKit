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

PaintZ owns runtime behaviour, the common spray-can implementation, and the official `PZ` namespace identity. PackKit owns offline generation and validation. Paint packs own finish content.

A generated paint pack must not define painting actions, persistence, synchronization, target policy, or other PaintZ gameplay mechanics.

## Paint Pack API v1 identity

API v1 uses one short complete finish ID as both runtime identity and persisted logical identity:

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

Package/repository/PBO names are not part of finish identity. Moving an unchanged finish between packages is not an identity change when the complete finish ID is retained.

Do **not** introduce a second reverse-domain canonical ID, UUID, secret, generated ownership token, or online registry identifier as a requirement.

## Third-party namespace roles

A normal third-party namespace family has one permanent prefix matching:

```text
^[A-Z][A-Z0-9]{1,2}$
```

All valid prefixes beginning with `PZ` are reserved for official PaintZ use. Normal PackKit validation must reject them.

For third-party content, `dayz.namespace_role` is source-controlled architecture:

- omitted or `owner`: generate a normal namespace-owner pack;
- `satellite`: generate a content PBO that contributes finishes to an existing external namespace owner.

A third-party owner emits exactly one `CfgPaintZPacks` declaration and requires `PaintZ_DynamicPaint`.

A third-party satellite must provide:

- `dayz.owner_class`: exact existing `CfgPaintZPacks` child classname;
- `dayz.owner_patch`: exact owner/core `CfgPatches` classname.

Satellite output must:

- omit `CfgPaintZPacks`;
- set each finish's `owner` to `dayz.owner_class`;
- require both `PaintZ_DynamicPaint` and `dayz.owner_patch`;
- use deterministic local config child names;
- never redeclare the namespace merely to become self-contained.

## Official `PZ` generation

PaintZ runtime itself permanently owns the official `PZ` namespace through:

```text
PZ_PaintZOfficial
```

Official PaintZ content packs are independent contributors, not namespace owners and not satellites of another content pack.

The explicit `--official` path currently means **independent official content in the core-owned `PZ` namespace**. It must:

- accept `PZ` and reject ordinary third-party prefixes;
- reject unassigned reserved namespaces such as `PZA`/`PZ9` until PaintZ explicitly assigns them;
- emit no `CfgPaintZPacks` owner declaration;
- set every finish's `owner` to `PZ_PaintZOfficial`;
- require `PaintZ_DynamicPaint` only;
- reject `dayz.namespace_role = "satellite"`;
- reject `dayz.owner_patch`;
- accept an explicit `dayz.owner_class` only when it equals `PZ_PaintZOfficial`.

Do not create dependencies such as Military -> Standard or Pastel -> Standard merely to access `PZ`. Standard, Pastel, Military, Hunting and other official content packs are peers and each depends directly on PaintZ.

Do not encode content categories by consuming `PZA`, `PZM`, `PZH`, etc. The package/collection name and the canonical finish namespace are separate concerns.

## Runtime collision semantics PackKit must target

PaintZ validates the complete loaded set:

- one namespace owner for a prefix -> namespace valid;
- multiple owners for one prefix -> entire namespace disabled;
- duplicate complete finish ID -> that finish disabled;
- no first-loaded-wins or last-loaded-wins overwrite behavior.

For `PZ`, the legitimate owner is PaintZ core. Any content pack redeclaring `PZ` creates a real collision and is invalid.

PackKit validates local syntax and local duplicates. It cannot guarantee that an arbitrary third-party prefix is globally unused. Do not imply it can prove prefix ownership.

## Generated DayZ config rules

Inspect the current PaintZ runtime config contract before changing runtime-facing output.

Third-party owner output generates:

- `CfgPatches.requiredAddons[]` including `PaintZ_DynamicPaint`;
- one `CfgPaintZPacks` owner declaration;
- one `CfgPaintZFinishes` child per finish;
- exact owner linkage;
- explicit runtime surface declarations;
- mandatory 100% surface representation;
- only actually generated scale variants for patterns;
- one thin spawnable can subclass per finish using `paintzFinish`.

Third-party satellite output generates the same finish/can/surface content except that it emits no owner and additionally depends on the supplied external owner patch.

Official `PZ` output generates the same finish/can/surface content except that it emits no owner, links every finish to `PZ_PaintZOfficial`, and has no content-pack owner dependency.

Normal API-v1 output must **not** generate:

- per-finish `ActionPaintZPaint_*` Enforce classes;
- a generated `PaintZ_PaintCatalog` runtime class;
- per-finish action registration/attachment logic;
- painted subclasses for target items.

Generated owner/config classnames are config linkage/local keys, not another PaintZ identity or security token. Use distinctive deterministic names because DayZ merges config trees before PaintZ enumerates them.

## Finish type and suffix

Keep the type mapping synchronized with the authoritative PaintZ API and runtime. Do not add or remove a type letter in PackKit alone.

Finish suffixes are uppercase alphanumeric, 2-12 characters, with descriptive 3-character suffixes preferred. Changing a released complete finish ID is a breaking persistence change.

IDs and generated classnames must be deterministic from authoritative input. Never derive identity from timestamps, random values or unordered traversal.

## Spray-can design and branding

PaintZ core owns the common can model/UV/runtime behaviour and standard PaintZ label identity. PackKit generates finish-specific can artwork and thin config subclasses.

Standard templates retain PaintZ-controlled layout, logo/identity, geometry, typography rules, badge placement, margins and footer treatment.

Pack-controlled fields may include finish name/ID/type, publisher name, small publisher mark, and restrained collection/series text. Do not expose arbitrary coordinates, unrestricted fonts, free-form geometry or replacement of the common can model as normal manifest fields.

## Generator/source-of-truth discipline

Generated files are derived artifacts. Never hand-edit generated output to fix a generator defect; fix the manifest/template/generator and regenerate.

Generation must be deterministic and offline-capable. Avoid timestamps, random IDs, machine-specific absolute paths and environment-dependent ordering in generated content.

The primary authoring environment is Windows. Avoid Unix-only workflows and handle Windows filesystem paths separately from emitted DayZ/PBO paths.

## Validation-first behavior

Invalid author input should fail early with a useful field/finish-specific error.

Validate as applicable:

- manifest/schema version;
- pack prefix syntax and reserved-prefix rules;
- third-party owner/satellite requirements;
- official core-owned `PZ` requirements;
- finish suffix/type syntax;
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

High-value automated coverage includes:

- namespaced IDs and normalization;
- reserved `PZ*` rejection in normal mode;
- independent official `PZ` generation with `PZ_PaintZOfficial`;
- rejection of official satellite/content-pack dependencies;
- rejection of unassigned `PZ?` namespaces;
- third-party satellite owner-class/owner-patch linkage;
- duplicate finish IDs;
- deterministic class generation;
- owner, satellite and official config structure;
- absence of legacy generated Enforce actions/catalogue;
- representative solid and patterned finishes;
- explicit scale declarations;
- safe/missing source paths;
- Windows/path edge cases.

Do not claim an AddonBuilder/PBO or DayZ runtime compile unless it was actually run with those tools.

## Documentation contract

Keep `README.md`, schema files and `docs/INTEROPERABILITY.md` aligned with author-facing behavior. Long instructions belong in documentation rather than comment-heavy JSON examples.

Examples should be valid PackKit inputs whenever practical.

## Avoid premature complexity

Do not invent a GUI, online prefix registry, cryptographic ownership system, broad plugin framework, unrestricted theming system, or category-specific official namespaces without a concrete requirement.

Prefer the smallest design that supports deterministic identity, explicit ownership, independent official content packs, third-party multi-PBO families, explicit finish registration, validation, and reproducible generation.
