# ONeSpineRx Landmark Dictionary v1.0.0

## Principle
The observer performs only anatomical landmark placement. Measurements are derived deterministically in Python. Derived lines, angles, distances, and classifications are never primary observations.

## Projection independence
AP, lateral neutral, flexion, and extension are independent observations. Coordinates are never transferred between projections.

## Lateral lumbar landmarks
For L1-L5, four vertebral-body corners are recorded:
- AS: anterosuperior
- PS: posterosuperior
- AI: anteroinferior
- PI: posteroinferior

S1 records the anterior and posterior margins of the superior endplate:
- S1_AS
- S1_PS

Optional pelvic landmarks:
- FH_R: center of right femoral head
- FH_L: center of left femoral head

The bicoxofemoral center is derived from FH_R and FH_L.

## AP landmarks
For L1-L5, four projected vertebral-body corners are recorded:
- SL: superior-left
- SR: superior-right
- IL: inferior-left
- IR: inferior-right

S1 superior endplate:
- S1_L
- S1_R

## Rules
1. Landmark identifiers are immutable once released.
2. Missing or non-visible anatomy is stored as missing; it is never estimated.
3. Raw coordinates are retained with the source image and measurement-definition version.
4. Markups are saved so measurements can be recalculated without repeating landmark placement.
5. Distance measurements require valid spatial calibration; angular and normalized measurements do not.
