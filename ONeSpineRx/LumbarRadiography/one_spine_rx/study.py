from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

class Projection(str, Enum):
    AP = "ap"
    LATERAL = "lat"
    FLEXION = "flex"
    EXTENSION = "ext"

class StudyStage(str, Enum):
    IMPORT = "import"
    HARMONIZE = "harmonize"
    CALIBRATE = "calibrate"
    LANDMARK = "landmark"
    REVIEW = "review"
    MEASURE = "measure"
    QC = "qc"
    EXPORT = "export"

@dataclass
class Calibration:
    valid: bool = False
    method: str = "none"  # none | dicom | manual
    mm_per_unit: Optional[float] = None
    reference_length_mm: Optional[float] = None

@dataclass
class ProjectionRecord:
    projection: Projection
    volume_node_id: Optional[str] = None
    markup_node_id: Optional[str] = None
    calibration: Calibration = field(default_factory=Calibration)
    skipped_landmarks: List[str] = field(default_factory=list)

@dataclass
class LumbarStudy:
    records: Dict[Projection, ProjectionRecord] = field(default_factory=lambda: {
        p: ProjectionRecord(p) for p in Projection
    })

    def all_sources_assigned(self) -> bool:
        return all(r.volume_node_id for r in self.records.values())

    def all_calibrated(self) -> bool:
        return all(r.calibration.valid for r in self.records.values())

    def millimetric_measurements_allowed(self, projection: Projection) -> bool:
        return self.records[projection].calibration.valid
