import math
from ONeSpineRx.LumbarRadiography.one_spine_rx.geometry import distance, midpoint, acute_line_angle_deg, sacral_reference_frame, point_in_frame_2d, spinopelvic_geometry_2d

def test_distance():
    assert distance((0,0),(3,4)) == 5.0

def test_midpoint():
    assert midpoint((0,0),(4,2)) == (2.0,1.0)

def test_parallel_lines():
    assert math.isclose(acute_line_angle_deg((0,0),(1,0),(0,2),(1,2)),0.0,abs_tol=1e-12)

def test_perpendicular_lines():
    assert math.isclose(acute_line_angle_deg((0,0),(1,0),(0,0),(0,1)),90.0,abs_tol=1e-12)


def test_sacral_reference_normalizes_translation_and_rotation():
    sp=(0.0,0.0); sa=(4.0,0.0); p=(3.0,2.0)
    f1=sacral_reference_frame(sp,sa)
    q1=point_in_frame_2d(p,f1)
    theta=math.radians(37.0); ct,st=math.cos(theta),math.sin(theta)
    transform=lambda x:(x[0]*ct-x[1]*st+25.0,x[0]*st+x[1]*ct-11.0)
    sp2,sa2,p2=transform(sp),transform(sa),transform(p)
    f2=sacral_reference_frame(sp2,sa2)
    q2=point_in_frame_2d(p2,f2)
    assert math.isclose(q1[0],q2[0],abs_tol=1e-10)
    assert math.isclose(q1[1],q2[1],abs_tol=1e-10)

def test_sacral_reference_origin_is_s1_midpoint():
    f=sacral_reference_frame((0.0,0.0),(6.0,0.0))
    assert f["origin"]==(3.0,0.0)
    assert point_in_frame_2d((3.0,0.0),f)==(0.0,0.0)


def test_spinopelvic_geometry_resolves_supplementary_pi():
    # S1 slope 60 deg; H->S is 12 deg from vertical => PI = 72 deg.
    ss=math.radians(60.0)
    u=(math.cos(ss),math.sin(ss))
    sp=(-0.5*u[0],-0.5*u[1]); sa=(0.5*u[0],0.5*u[1])
    hs=math.radians(78.0)
    h=(-math.cos(hs),-math.sin(hs))
    g=spinopelvic_geometry_2d(sa,sp,h)
    assert math.isclose(g["SS_deg"],60.0,abs_tol=1e-10)
    assert math.isclose(g["PT_deg"],12.0,abs_tol=1e-10)
    assert math.isclose(g["PI_deg"],72.0,abs_tol=1e-10)
    assert math.isclose(g["PI_identity_error_deg"],0.0,abs_tol=1e-10)

def test_spinopelvic_pi_is_rigid_rotation_invariant():
    sa=(2.0,1.0); sp=(-2.0,-1.0); h=(-3.0,-4.0)
    g1=spinopelvic_geometry_2d(sa,sp,h)
    th=math.radians(31.0); ct,st=math.cos(th),math.sin(th)
    rot=lambda p:(p[0]*ct-p[1]*st,p[0]*st+p[1]*ct)
    g2=spinopelvic_geometry_2d(rot(sa),rot(sp),rot(h))
    assert math.isclose(g1["PI_deg"],g2["PI_deg"],abs_tol=1e-10)
