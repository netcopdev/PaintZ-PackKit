# Changelog

## Unreleased

- added `B` / `basic` procedural RGB finishes: Basic cans keep normal generated artwork/classes while painted targets use a generated procedural S100 color descriptor and require no target-surface PNG/PAA;
- kept Basic and Solid as distinct finish semantics and IDs;
- restored the Design 3 PaintZ top logo to its proven can-label position and added a regression test for logo presence/placement;
- synchronized manifest/interoperability documentation with the core-owned `PZ_PaintZOfficial` official-generation model.

## 0.3.0 - namespace contributors and satellite packs

- added source-controlled `dayz.namespace_role` with `owner` as the backward-compatible default and `satellite` for third-party multi-PBO namespace families;
- satellite manifests require the existing namespace `owner_class` and owner/core `owner_patch` linkage;
- third-party satellite config omits `CfgPaintZPacks`, registers finishes against the existing external owner, and depends on both `PaintZ_DynamicPaint` and the owner/core PBO;
- changed official generation to the core-owned `PZ` model: PaintZ runtime owns `PZ` through `PZ_PaintZOfficial`, while `--official` generates independent `PZ-*` content contributors;
- official output emits no namespace owner, references `PZ_PaintZOfficial`, and depends only on `PaintZ_DynamicPaint`;
- official content rejects satellite/owner-patch dependencies and currently accepts only assigned namespace `PZ`; reserved `PZ?` namespaces remain unavailable until explicitly assigned by PaintZ;
- kept complete finish IDs independent from package boundaries so moving an unchanged finish between official content packs or third-party family PBOs need not break persistence;
- added regression tests and documentation for independent official content packs and third-party satellites.

## 0.2.0 - Paint Pack API v1 output

- added one permanent 2-3 character pack namespace prefix and `<PREFIX>-<TYPE>-<SUFFIX>` finish IDs;
- reserved all valid `PZ*` prefixes for official PaintZ content and added explicit `--official` generation for first-party content;
- replaced the embedded-generator DayZ integration output with standalone Paint Pack API v1 `config.cpp` generation;
- generated namespace/finish registration data and thin `paintzFinish` spray-can subclasses depending on `PaintZ_DynamicPaint`;
- removed generated per-finish Enforce paint actions and `PaintZ_PaintCatalog` output;
- added local duplicate/prefix/source-path validation and API-v1 regression tests;
- documented PackKit interoperability obligations and the runtime collision model.

## 0.1.0 - initial extraction

- extracted the existing PaintZ `paintzgen` pipeline into the standalone PackKit project;
- retained v1 manifest, product-code, pattern-scale, preview, catalogue and DayZ output behavior;
- added the standard PaintZ can SVG template as source-controlled generator infrastructure;
- retained canonical Barlow font lookup while allowing system-font fallback and local environment overrides;
- made the historical binary wear-overlay library optional so a clean source checkout can render solid finishes without private artwork;
- added package/CLI entry points and a compatibility `tools/generate_paints.py` launcher;
- added validation and smoke tests;
- intentionally bundled no paints, pattern sources, or finish catalogue.
