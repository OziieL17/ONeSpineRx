from __future__ import annotations
from .geometry import distance, midpoint, signed_angle_deg, acute_line_angle_deg

def disc_heights(cranial_ai, cranial_pi, caudal_as, caudal_ps):
    anterior = distance(cranial_ai, caudal_as)
    posterior = distance(cranial_pi, caudal_ps)
    c_mid = midpoint(cranial_ai, cranial_pi)
    k_mid = midpoint(caudal_as, caudal_ps)
    middle = distance(c_mid, k_mid)
    return {"anterior": anterior, "posterior": posterior, "middle": middle}

def segmental_angle(cranial_ai, cranial_pi, caudal_as, caudal_ps):
    return signed_angle_deg(cranial_ai, cranial_pi, caudal_as, caudal_ps)

def lumbar_lordosis(l1_as, l1_ps, s1_as, s1_ps):
    return acute_line_angle_deg(l1_as, l1_ps, s1_as, s1_ps)

def lower_lumbar_lordosis(l4_as, l4_ps, s1_as, s1_ps):
    return acute_line_angle_deg(l4_as, l4_ps, s1_as, s1_ps)

def dynamic_delta(flexion_value, extension_value):
    signed = float(flexion_value) - float(extension_value)
    return {"signed": signed, "absolute": abs(signed)}
