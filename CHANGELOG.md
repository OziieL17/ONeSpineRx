# Changelog

## Unreleased - v0.2 study workflow

### Changed
- Four-projection lumbar study is the unit of work.
- Workflow: Import -> Harmonize -> Calibrate -> Landmarks -> Review -> Measure -> QC -> Export.
- Calibration is required before millimetric output.
- Neutral lateral, flexion, and extension share a landmark dictionary but use independent Markups.
- Target landmark workflow removes the redundant Place Point button.
- Spanish remains default; English is selectable from the same codebase.

### Added
- Study/calibration data model.
- TXT/JSON/XML/CSV/Markdown export helpers and export specification.
- Reproducible PNG QC/presentation figure requirements.
- Projection-specific visual differentiation requirement.

### Pending implementation
- Four-view 2x2 Slicer layout.
- DICOM import/assignment and harmonization.
- DICOM calibration validation and manual two-point calibration.
- Continuous landmark placement, navigation and editing.
- Measurement results panel and annotated PNG rendering.
- Complete export-package orchestration.
