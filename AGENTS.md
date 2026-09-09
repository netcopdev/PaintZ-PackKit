# PaintZ PackKit Codex Instructions

## Project purpose

PaintZ PackKit is the offline authoring/build toolkit for PaintZ paint packs. It converts finish metadata, source artwork and limited pack branding into validated PaintZ-compatible generated assets and DayZ config/source output.

This repository is **not** the PaintZ runtime mod. Do not duplicate or reimplement PaintZ gameplay, persistence, networking, eligibility/policy, painting actions or target-item compatibility logic here.

Read `README.md` before making architectural changes. Keep it accurate when the project contract changes materially.

## Mandatory Git preflight

Before modifying, creating, deleting, renaming, generating, rebasing, or moving repository work, inspect:

```text
git branch --show-current
git status --short
git log -1 --oneline
git branch -a
```

`main` is the authoritative shared integration base.

New feature, fix, refactor, experiment, tooling, documentation or schema work should normally be performed on a separate appropriately named branch derived from current `main`, unless the user explicitly directs work on an existing branch or directly on `main`.

Do not base independent work on an unrelated feature branch. Base on another work branch only when the requested change explicitly depends on unmerged work there.

## Merge discipline

Implementation permission is not merge permission.

Do not merge, squash, rebase, fast-forward or otherwise integrate a work branch into `main` unless the user explicitly approves that integration after review/testing, or that exact integration was explicitly authorized beforehand.

When work is complete, report:

- branch name;
- relevant commit(s) or PR;
- tests/validation performed;
- anything requiring real DayZ Tools/runtime verification.

If branch intent is ambiguous, preserve separation and do not merge.

## Core architecture boundary

Keep the dependency direction unambiguous:

```text
Paint pack -> PaintZ runtime
PaintKit/PackKit -> generates paint-pack source/assets
PaintZ runtime -X-> specific paint packs
```

PaintZ core owns runtime behaviour and the common spray-can implementation. PackKit owns offline generation/validation. Paint packs own finish content.

Do not move PaintZ runtime responsibilities into PackKit merely because generation code can inspect or emit DayZ files.

A normal generated paint pack may contain:

- finish metadata/registration;
- surface textures and generated variants;
- generated spray-can textures;
- thin finish-specific spray-can subclasses inheriting the PaintZ base can;
- restrained publisher/collection branding;
- PBO-ready config/source required to expose that content.

A normal paint pack should not define new painting mechanics.

## Spray-can ownership invariant

PaintZ core provides the canonical can model, UV contract, runtime behaviour and non-spawnable base class such as `PaintZ_SprayCan_Base`.

Each paint pack provides its own **spawnable finish-specific can classes**. PackKit should generate these classes from finish metadata rather than require authors to maintain repetitive classes manually.

Generated subclasses should remain thin. They identify/present a finish and inherit behaviour from PaintZ.

Do not duplicate the physical spray-can P3D per finish or per pack unless a future explicit architecture change requires it.

Do not generate painted subclasses for target weapons, magazines, attachments or other paintable items. PaintZ paints existing runtime objects in place.

## Finish identity rules

Design for independent third-party packs from the beginning.

Distinguish:

- a canonical globally collision-resistant machine identity, e.g. `netcop.military.fde`;
- a short human-facing/display paint code, e.g. `PZ-S-FDE`.

Do not use the visible short code as the sole global persistence/registration identity once external packs are supported.

The exact schema is versioned project API. Once a manifest version ships and is used by real packs, do not make silent breaking schema changes. Prefer explicit versioning, migration or clear validation errors.

IDs and generated classnames must be deterministic from authoritative input. Never make identity depend on unordered filesystem traversal, timestamps or random values.

## Standard can design and branding

The PackKit-generated default can must preserve recognizable PaintZ design identity.

PaintZ-controlled/default template elements include:

- PaintZ logo/identity;
- label geometry and proportions;
- typography rules;
- standard margins;
- badge/category placement;
- footer treatment;
- physical can model/UV contract.

Pack-controlled fields may include, subject to the schema:

- finish name;
- visible paint ID;
- finish category/type;
- publisher name;
- small publisher mark/logo;
- collection/series name or restrained secondary text.

Third-party branding is intentionally subordinate to PaintZ branding in the standard template.

Do not expose arbitrary per-pack X/Y coordinates, unrestricted fonts, free-form label geometry or arbitrary replacement of the standard PaintZ layout as ordinary manifest fields. If an advanced theming system is ever added, it must be a deliberate architecture decision rather than accidental schema creep.

## Generator/source-of-truth discipline

Generated files are derived artifacts. Do not hand-edit a generated output to solve a generator bug.

Fix the authoritative source/template/generator and regenerate.

Every generated file type should eventually have an obvious source of truth and, where practical, a generated-file marker/header.

Generation must be deterministic. The same authoritative inputs and tool version should produce byte-equivalent outputs wherever practical. Avoid embedding current timestamps, machine-specific absolute paths, random values or environment-dependent ordering in generated content.

Sort collections explicitly before emission when source order is not semantically meaningful.

Do not rely on network access during normal pack generation unless there is a strong explicit reason. Builds should be reproducible from the repository/pack inputs and documented local dependencies.

## Migration from PaintZ embedded generator

The current PaintZ repository contains an existing generator under `tools/paintzgen`.

Treat it as proven behaviour/source material, not something to rewrite blindly.

When extracting capabilities:

1. inspect the current PaintZ implementation first;
2. identify authoritative inputs and generated outputs;
3. preserve known-good visual/output behaviour unless the task intentionally changes it;
4. move/refactor reusable generation logic into PackKit with regression coverage;
5. coordinate any required PaintZ-side contract change explicitly rather than silently assuming both repositories changed together.

Do not modify the PaintZ repository from a PackKit task unless the user explicitly asks for coordinated cross-repository work.

## Language and tooling direction

The existing PaintZ generator is Python-based. Prefer Python 3 for PackKit unless there is a concrete reason to introduce another implementation language.

Keep the core generation logic usable from tests and library code; do not bury all behaviour directly inside CLI argument handlers.

Prefer a structure where:

- parsing/validation;
- domain models;
- rendering/generation;
- DayZ config emission;
- filesystem/output orchestration;
- CLI presentation

are separable enough to test independently.

Do not add heavy dependencies for trivial functionality. Pin/document nontrivial build dependencies once the project establishes packaging metadata.

The primary DayZ authoring environment is Windows. Avoid Unix-only assumptions in normal user workflows. Handle Windows paths carefully while emitting DayZ/PBO paths in the exact form required by DayZ.

## DayZ config generation rules

Generated `config.cpp`/config fragments must be deterministic and conservative.

Paint packs should depend on PaintZ core through the proper `CfgPatches.requiredAddons[]` relationship and must not require PaintZ core to know their classnames.

Generated can subclasses should contain only the minimum finish-specific data required by the established PaintZ contract.

Do not guess new PaintZ config properties. Inspect the current PaintZ runtime contract before generating or changing runtime-facing properties.

When a PackKit change requires a PaintZ runtime API/config change, call that dependency out explicitly and keep the two repository changes coordinated but conceptually separate.

## Validation-first behaviour

Invalid author input must fail clearly and early.

Validate, as applicable:

- manifest/schema version;
- required fields;
- canonical finish ID syntax/uniqueness;
- visible paint ID syntax/uniqueness where required;
- generated classname uniqueness;
- referenced source-file existence;
- supported image dimensions/formats;
- output path safety;
- forbidden path traversal;
- duplicate output paths;
- branding-field size/format constraints;
- finish-type-specific requirements;
- collisions across a multi-pack build when such a mode exists.

Prefer one useful error that identifies the offending finish/file/field over a later opaque renderer or filesystem exception.

Do not silently repair ambiguous IDs or filenames in a way that changes identity. Normalization is acceptable only when explicitly specified by the schema and deterministic.

## Output safety

Never delete or overwrite arbitrary user files based solely on manifest-supplied paths.

Generated output must be constrained to the selected output/build root. Reject path traversal and absolute output paths where they are not explicitly part of a safe supported workflow.

Before implementing cleaning/pruning, distinguish generated files from author-owned source files. A clean operation must not remove source artwork or manifests.

## Tests and verification

New generator behaviour should include automated tests where practical.

High-value coverage includes:

- deterministic output/golden-file tests;
- manifest validation tests;
- duplicate/collision detection;
- can-label rendering regression checks;
- generated classname/config checks;
- Windows/path edge cases;
- representative solid and patterned finishes;
- optional branding present/absent;
- multiple independent publishers/packs.

Image regression tests should compare intentional render outputs in a stable way rather than relying only on visual inspection.

Generated DayZ config should be checked structurally, but do not claim a real DayZ/Addon Builder compile unless it was actually run with the appropriate tools.

When DayZ Tools are unavailable, report that limitation explicitly.

## Documentation contract

Keep `README.md` focused on project purpose, architecture, supported author workflow and high-level usage.

Once the manifest/schema exists, provide dedicated schema/author documentation rather than turning example JSON into a comment-heavy pseudo-document format.

Examples should be valid files that can be validated/built by PackKit whenever practical.

When generated output or author-facing commands change, update the relevant documentation in the same work.

## Avoid premature commitments

This repository begins before the final pack schema and directory layout are frozen.

Do not invent a large framework, plugin system, GUI, package registry or broad theming API without a concrete requirement.

Prefer the smallest architecture that supports:

1. authoritative finish definitions;
2. standardized asset generation;
3. thin can-class generation;
4. finish registration;
5. validation;
6. deterministic pack output.

Extend from proven requirements rather than speculative abstractions.
