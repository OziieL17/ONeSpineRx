from __future__ import annotations
import math
from typing import Sequence, Tuple

Point = Sequence[float]

def vector(a: Point, b: Point) -> Tuple[float, float]:
    return float(b[0]-a[0]), float(b[1]-a[1])

def distance(a: Point, b: Point) -> float:
    return math.hypot(b[0]-a[0], b[1]-a[1])

def midpoint(a: Point, b: Point) -> Tuple[float, float]:
    return ((a[0]+b[0])/2.0, (a[1]+b[1])/2.0)

def signed_angle_deg(a1: Point, a2: Point, b1: Point, b2: Point) -> float:
    ax, ay = vector(a1, a2)
    bx, by = vector(b1, b2)
    cross = ax*by - ay*bx
    dot = ax*bx + ay*by
    return math.degrees(math.atan2(cross, dot))

def acute_line_angle_deg(a1: Point, a2: Point, b1: Point, b2: Point) -> float:
    angle = abs(signed_angle_deg(a1,a2,b1,b2)) % 180.0
    return min(angle, 180.0-angle)


def dot2(a: Point, b: Point) -> float:
    return float(a[0]*b[0] + a[1]*b[1])

def norm2(v: Point) -> float:
    return math.hypot(v[0], v[1])

def normalize2(v: Point) -> Tuple[float, float]:
    n = norm2(v)
    if n <= 1e-12:
        raise ValueError("zero_length_vector")
    return float(v[0]/n), float(v[1]/n)

def polygon_area_2d(points) -> float:
    """Unsigned projected area of an ordered 2D polygon in scene units squared."""
    if points is None or len(points) < 3:
        raise ValueError("polygon_requires_at_least_three_points")
    area2 = 0.0
    for i, p in enumerate(points):
        q = points[(i+1) % len(points)]
        area2 += float(p[0])*float(q[1]) - float(q[0])*float(p[1])
    return abs(area2) * 0.5


def orthonormal_frame_2d(origin: Point, posterior: Point, anterior: Point):
    """Return a right-handed 2D frame with +u directed posterior -> anterior."""
    u = normalize2((anterior[0]-posterior[0], anterior[1]-posterior[1]))
    v = (-u[1], u[0])
    return {
        "origin": (float(origin[0]), float(origin[1])),
        "u": u,
        "v": v,
    }

def sacral_reference_frame(s1_posterior: Point, s1_anterior: Point):
    """Pelvic-sacral reference frame centered at the midpoint of the S1 superior endplate."""
    origin = midpoint(s1_posterior, s1_anterior)
    return orthonormal_frame_2d(origin, s1_posterior, s1_anterior)

def point_in_frame_2d(point: Point, frame):
    """Coordinates of point in an orthonormal 2D frame."""
    r = (float(point[0])-frame["origin"][0], float(point[1])-frame["origin"][1])
    return dot2(r, frame["u"]), dot2(r, frame["v"])

def vector_in_frame_2d(vector_: Point, frame):
    """Components of a free vector in an orthonormal 2D frame."""
    return dot2(vector_, frame["u"]), dot2(vector_, frame["v"])


def spinopelvic_geometry_2d(s1_anterior: Point, s1_posterior: Point, femoral_center: Point):
    """Projected spinopelvic geometry in a common 2D image frame.

    PI is treated as an unoriented line angle to remove the supplementary-angle
    ambiguity of the S1 normal. SS and PT remain image-frame dependent and
    therefore require a trustworthy radiographic horizontal/vertical reference
    for clinical interpretation.
    """
    s = midpoint(s1_anterior, s1_posterior)
    u_s1 = normalize2((s1_anterior[0]-s1_posterior[0], s1_anterior[1]-s1_posterior[1]))
    n_s1 = (-u_s1[1], u_s1[0])
    s_to_h = normalize2((femoral_center[0]-s[0], femoral_center[1]-s[1]))
    h_to_s = (-s_to_h[0], -s_to_h[1])

    # PI is the smaller angle between the S1 normal line and S-H line.
    pi = math.degrees(math.acos(max(-1.0, min(1.0, abs(dot2(n_s1, s_to_h))))))

    # Image-frame horizontal/vertical. These are valid only when that frame has
    # been established as the true radiographic frame.
    horizontal = (1.0, 0.0)
    vertical = (0.0, 1.0)
    ss = math.degrees(math.acos(max(-1.0, min(1.0, abs(dot2(u_s1, horizontal))))))
    pt = math.degrees(math.acos(max(-1.0, min(1.0, abs(dot2(h_to_s, vertical))))))

    identity_error = abs(pi - (pt + ss))
    return {
        "PI_deg": pi,
        "PT_deg": pt,
        "SS_deg": ss,
        "PI_identity_error_deg": identity_error,
        "identity_consistent": identity_error <= 1e-6,
        "reference_frame": "image_xy",
        "reference_frame_validated": False,
        "debug": {
            "S1_midpoint": list(s),
            "femoral_center": [float(femoral_center[0]), float(femoral_center[1])],
            "u_S1": list(u_s1),
            "n_S1": list(n_s1),
            "S_to_H": list(s_to_h),
            "H_to_S": list(h_to_s),
            "horizontal_reference": list(horizontal),
            "vertical_reference": list(vertical),
        },
    }
