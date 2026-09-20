# ONeSpineRx Measurement Specification v1.0.0

## Measurement model
Each result stores: measurement ID, definition version, projection, segment/region, value, unit, source landmarks, calibration status, observer, and timestamp.

## Segmental lateral measurements
For each motion segment L1-L2 through L5-S1:
- SEG_ANGLE: angle between the inferior endplate of the cranial vertebra and superior endplate of the caudal vertebra.
- DISC_HEIGHT_ANT: distance between adjacent anterior endplate margins.
- DISC_HEIGHT_POST: distance between adjacent posterior endplate margins.
- DISC_HEIGHT_MID: distance between corresponding midpoints of adjacent endplates.
- DISC_WEDGE: signed angle between adjacent endplates.
- SAG_TRANSLATION_MM: signed sagittal translation using a definition explicitly versioned in measurements.json.
- SAG_TRANSLATION_PCT: translation normalized to the selected vertebral reference dimension.

## Regional lateral measurements
- LL_L1_S1: angle between L1 superior endplate and S1 superior endplate.
- LL_L4_S1: angle between L4 superior endplate and S1 superior endplate.
- SS: sacral slope relative to horizontal.
- PI/PT: calculated only when required femoral-head landmarks are present.

## AP measurements
- CORONAL_COBB_L1_S1.
- Segmental coronal angle.
- Coronal translation where defined.
- Disc wedging.

## Dynamic measurements
Flexion and extension retain their original measurements. Dynamic results are derived, never substituted for source measurements:
- DYN_TRANSLATION = translation_flexion - translation_extension.
- DYN_ANGLE = segmental_angle_flexion - segmental_angle_extension.
Both signed and absolute magnitudes may be exported.

## Calibration
Angles and dimensionless ratios remain valid without millimetric calibration. Any result in mm must be flagged unavailable when calibration is invalid.

## Reproducibility
The raw source image, markups, definition versions, results, QC image, and clean presentation image form the minimum reproducibility package.
