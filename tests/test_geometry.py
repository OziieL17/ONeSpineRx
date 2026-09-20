import math
from ONeSpineRx.LumbarRadiography.one_spine_rx.geometry import distance, midpoint, acute_line_angle_deg

def test_distance():
    assert distance((0,0),(3,4)) == 5.0

def test_midpoint():
    assert midpoint((0,0),(4,2)) == (2.0,1.0)

def test_parallel_lines():
    assert math.isclose(acute_line_angle_deg((0,0),(1,0),(0,2),(1,2)),0.0,abs_tol=1e-12)

def test_perpendicular_lines():
    assert math.isclose(acute_line_angle_deg((0,0),(1,0),(0,0),(0,1)),90.0,abs_tol=1e-12)
