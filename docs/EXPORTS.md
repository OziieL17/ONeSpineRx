# Export specification v0.2

Required result representations:
- TXT: human-readable clinical/research summary.
- JSON: canonical structured result and provenance representation.
- XML: interoperable structured representation.
- CSV: tidy/tabular measurement export.
- Markdown: readable structured report.
- PNG: reproducible presentation and QC figures.

## Figures
Presentation figures show derived global angles, segmental angles, and relevant distances with collision-aware labels. QC figures additionally show anatomical landmark identifiers.

Dynamic comparison figures keep neutral, flexion, and extension visually distinct and never overlay their source landmark sets.

## Provenance
manifest.json records software version, Slicer version, definition versions, projection/source identifiers, calibration method and factor per projection, observer, timestamps, skipped/missing landmarks, and output filenames.
