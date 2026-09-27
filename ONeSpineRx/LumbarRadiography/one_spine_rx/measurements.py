from __future__ import annotations
from .geometry import distance, midpoint, signed_angle_deg, acute_line_angle_deg, dot2, normalize2, polygon_area_2d

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


def projected_disc_geometry(cranial_ai, cranial_pi, caudal_as, caudal_ps, scale_mm_per_scene=None):
    """
    Projected 2D disc geometry.

    Polygon order:
      cranial posteroinferior -> cranial anteroinferior ->
      caudal anterosuperior -> caudal posterosuperior.

    DH_central is the orthogonal separation of endplate midpoints along the
    normal of the sign-aligned mean endplate direction. It is intentionally
    distinct from the Euclidean midpoint distance and from DH_AP_mean.
    """
    points = [cranial_pi, cranial_ai, caudal_as, caudal_ps]
    m_cranial = midpoint(cranial_ai, cranial_pi)
    m_caudal = midpoint(caudal_as, caudal_ps)

    u_cranial = normalize2((cranial_ai[0]-cranial_pi[0], cranial_ai[1]-cranial_pi[1]))
    u_caudal = normalize2((caudal_as[0]-caudal_ps[0], caudal_as[1]-caudal_ps[1]))
    if dot2(u_cranial, u_caudal) < 0.0:
        u_caudal = (-u_caudal[0], -u_caudal[1])

    u_disc = normalize2((u_cranial[0]+u_caudal[0], u_cranial[1]+u_caudal[1]))
    v_disc = (-u_disc[1], u_disc[0])
    delta_mid = (m_cranial[0]-m_caudal[0], m_cranial[1]-m_caudal[1])
    central_scene = abs(dot2(delta_mid, v_disc))
    area_scene = polygon_area_2d(points)

    anterior_scene = distance(cranial_ai, caudal_as)
    posterior_scene = distance(cranial_pi, caudal_ps)
    ap_mean_scene = 0.5 * (anterior_scene + posterior_scene)

    calibrated = scale_mm_per_scene is not None and float(scale_mm_per_scene) > 0.0
    scale = float(scale_mm_per_scene) if calibrated else None
    return {
        "DH_anterior_mm": anterior_scene*scale if calibrated else None,
        "DH_central_mm": central_scene*scale if calibrated else None,
        "DH_posterior_mm": posterior_scene*scale if calibrated else None,
        "DH_AP_mean_mm": ap_mean_scene*scale if calibrated else None,
        "projected_area_mm2": area_scene*(scale**2) if calibrated else None,
        "measurement_valid": bool(calibrated),
        "measurement_status": "valid" if calibrated else "invalid",
        "invalid_reason": None if calibrated else "calibration_unavailable",
        "debug": {
            "M_cranial": list(m_cranial),
            "M_caudal": list(m_caudal),
            "u_cranial": list(u_cranial),
            "u_caudal": list(u_caudal),
            "u_disc": list(u_disc),
            "v_disc": list(v_disc),
            "polygon_points": [list(p[:2]) for p in points],
            "DH_central_scene": central_scene,
            "area_scene": area_scene,
            "scale_mm_per_scene": scale,
        },
    }
