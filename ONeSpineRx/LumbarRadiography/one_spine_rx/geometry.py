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
