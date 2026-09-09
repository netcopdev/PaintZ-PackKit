# Changelog

## 0.1.0 - initial extraction

- extracted the existing PaintZ `paintzgen` pipeline into the standalone PackKit project;
- retained v1 manifest, product-code, pattern-scale, preview, catalogue and DayZ output behavior;
- added the standard PaintZ can SVG template as source-controlled generator infrastructure;
- retained canonical Barlow font lookup while allowing system-font fallback and local environment overrides;
- made the historical binary wear-overlay library optional so a clean source checkout can render solid finishes without private artwork;
- added package/CLI entry points and a compatibility `tools/generate_paints.py` launcher;
- added validation and smoke tests;
- intentionally bundled no paints, pattern sources, or finish catalogue.
