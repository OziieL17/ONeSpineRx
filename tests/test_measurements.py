import math
from ONeSpineRx.LumbarRadiography.one_spine_rx.measurements import projected_disc_geometry, projected_foraminal_geometry


def test_projected_disc_geometry_rectangle():
    r=projected_disc_geometry((4,2),(0,2),(4,0),(0,0),0.5)
    assert math.isclose(r["DH_central_mm"],1.0)
    assert math.isclose(r["projected_area_mm2"],2.0)
    assert r["measurement_valid"] is True


def test_foraminal_geometry_valid_rectangle():
    r=projected_foraminal_geometry((2,6),(2,0),(4,3),(0,3),0.5,"valid")
    assert math.isclose(r["FH_mm"],3.0)
    assert math.isclose(r["FW_mm"],2.0)
    assert math.isclose(r["projected_area_mm2"],6.0)
    assert r["measurement_valid"] is True
    assert r["measurement_status"]=="valid"


def test_foraminal_geometry_limited_is_provisional():
    r=projected_foraminal_geometry((2,6),(2,0),(4,3),(0,3),1.0,"limited")
    assert r["measurement_valid"] is True
    assert r["measurement_status"]=="provisional"
    assert r["invalid_reason"]=="projection_quality_limited"


def test_foraminal_geometry_invalid_qc_is_not_valid():
    r=projected_foraminal_geometry((2,6),(2,0),(4,3),(0,3),1.0,"invalid")
    assert r["measurement_valid"] is False
    assert r["measurement_status"]=="invalid"


def test_foraminal_geometry_requires_qc():
    r=projected_foraminal_geometry((2,6),(2,0),(4,3),(0,3),1.0,None)
    assert r["measurement_valid"] is False
    assert r["invalid_reason"]=="projection_quality_unset"


def test_foraminal_geometry_requires_calibration_for_mm():
    r=projected_foraminal_geometry((2,6),(2,0),(4,3),(0,3),None,"valid")
    assert r["measurement_valid"] is False
    assert r["FH_mm"] is None
    assert r["FW_mm"] is None
    assert r["projected_area_mm2"] is None
