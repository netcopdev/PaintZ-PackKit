# Changelog

## 0.3.0 - satellite content packs

- added source-controlled `dayz.namespace_role` with `owner` as the backward-compatible default and `satellite` for multi-PBO namespace families;
- satellite manifests require the existing namespace `owner_class` and owner/core `owner_patch` linkage;
- satellite config omits `CfgPaintZPacks`, registers finishes against the existing owner, and depends on both `PaintZ_DynamicPaint` and the owner/core PBO;
- official `PZ*` satellites are supported through `--official` without emitting a second `official = 1` namespace owner;
- kept complete finish IDs unchanged across owner/satellite packaging so moving a finish between PBOs need not break persistence;
- added manifest-schema coverage, owner/satellite regression tests, and authoring/interoperability documentation.

## 0.2.0 - Paint Pack API v1 output

- added one permanent 2-3 character pack namespace prefix and `<PREFIX>-<TYPE>-<SUFFIX>` finish IDs;
- reserved all valid `PZ*` prefixes for official PaintZ content and added explicit `--official` generation for Standard Pack/official content;
- replaced the embedded-generator DayZ integration output with standalone Paint Pack API v1 `config.cpp` generation;
- generated one `CfgPaintZPacks` owner declaration and explicit `CfgPaintZFinishes` surface registrations;
- generated thin `paintzFinish` spray-can subclasses depending on `PaintZ_DynamicPaint`;
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
