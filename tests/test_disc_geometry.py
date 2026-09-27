import math
from ONeSpineRx.LumbarRadiography.one_spine_rx.measurements import projected_disc_geometry

def close(a,b,tol=1e-9):
    assert math.isclose(a,b,rel_tol=tol,abs_tol=tol)

def test_rectangle_disc():
    g=projected_disc_geometry((4,2),(0,2),(4,0),(0,0),1.0)
    close(g["DH_central_mm"],2.0); close(g["projected_area_mm2"],8.0)
    close(g["DH_anterior_mm"],2.0); close(g["DH_posterior_mm"],2.0)

def test_trapezoid_disc():
    g=projected_disc_geometry((5,3),(0,2),(4,0),(0,0),1.0)
    close(g["projected_area_mm2"],10.5)

def test_rigid_translation_invariance():
    a=((4,2),(0,2),(4,0),(0,0))
    b=tuple((x+100,y-37) for x,y in a)
    g1=projected_disc_geometry(*a,1.0); g2=projected_disc_geometry(*b,1.0)
    close(g1["DH_central_mm"],g2["DH_central_mm"])
    close(g1["projected_area_mm2"],g2["projected_area_mm2"])

def test_rigid_rotation_area_invariance():
    pts=((4,2),(0,2),(4,0),(0,0)); th=math.radians(31)
    rot=lambda p:(p[0]*math.cos(th)-p[1]*math.sin(th),p[0]*math.sin(th)+p[1]*math.cos(th))
    g1=projected_disc_geometry(*pts,1.0); g2=projected_disc_geometry(*(rot(p) for p in pts),1.0)
    close(g1["projected_area_mm2"],g2["projected_area_mm2"])
    close(g1["DH_central_mm"],g2["DH_central_mm"])

def test_scale_distance_and_area():
    pts=((4,2),(0,2),(4,0),(0,0))
    g1=projected_disc_geometry(*pts,1.0); g2=projected_disc_geometry(*pts,2.0)
    close(g2["DH_central_mm"],2*g1["DH_central_mm"])
    close(g2["projected_area_mm2"],4*g1["projected_area_mm2"])

def test_no_calibration():
    g=projected_disc_geometry((4,2),(0,2),(4,0),(0,0),None)
    assert g["DH_central_mm"] is None
    assert g["projected_area_mm2"] is None
    assert g["measurement_valid"] is False
    assert g["invalid_reason"]=="calibration_unavailable"

def test_antiparallel_endplates_are_aligned():
    # cranial posterior->anterior points right; caudal posterior->anterior is supplied left.
    g=projected_disc_geometry((4,2),(0,2),(0,0),(4,0),1.0)
    close(g["DH_central_mm"],2.0)
    close(abs(g["debug"]["u_disc"][0]),1.0)
