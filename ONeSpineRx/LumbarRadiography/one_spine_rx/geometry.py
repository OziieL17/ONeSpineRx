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
