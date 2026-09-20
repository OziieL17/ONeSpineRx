# ONeSpineRx lumbar radiography workflow v0.2

## Design principle
The study, not an individual image, is the unit of work. The required basic projections are AP, neutral lateral, lateral flexion, and lateral extension.

## State machine
1. IMPORT — import/assign the four source projections.
2. HARMONIZE — normalize presentation/orientation without altering source geometry.
3. CALIBRATE — verify DICOM spacing or perform explicit manual calibration per projection.
4. LANDMARK — guided manual anatomical landmark acquisition.
5. REVIEW — navigate, skip, edit, and save landmark changes.
6. MEASURE — deterministic Python calculations from saved landmarks.
7. QC — inspect source landmarks and derived constructions.
8. EXPORT — figures and structured text/data.

Millimetric measurements are blocked until calibration is valid. Angular and dimensionless calculations may remain available.

## Projection isolation
Neutral lateral, flexion, and extension share the same landmark dictionary but never share coordinates. Each projection has its own markup node and viewport. Landmarks are visually differentiated by projection; color is presentation metadata, not measurement identity.

## Landmark interaction
Placement mode starts when landmark registration starts. A separate "place point" button is not part of the target workflow. The panel provides Previous, Next, Skip, Edit, Save changes, and Finish. Each current landmark displays its anatomical name and bilingual placement guidance.

## Outputs
A reproducibility package contains source references, .mrk.json files, calibration metadata, derived measurements, QC/presentation figures, and TXT/JSON/XML/CSV/Markdown results plus manifest.json.
