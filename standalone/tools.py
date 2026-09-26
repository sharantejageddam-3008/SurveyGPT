"""
Reliable numeric calculators (and one chart generator) for common Surveying
problems. These are plain Python functions, not the language model itself.
Gemini reads each function's name, arguments and docstring, decides which one
(if any) answers the student's question, calls it, and writes up the result.
"""

import base64
import io
import math

import matplotlib.pyplot as plt


def wcb_to_quadrantal(wcb_deg: float) -> dict:
    """Convert a whole circle bearing (0-360 degrees) to a quadrantal (reduced) bearing.

    Args:
        wcb_deg: Whole circle bearing in decimal degrees.
    """
    b = wcb_deg % 360
    if b <= 90:
        qb, ns, ew = b, "N", "E"
    elif b <= 180:
        qb, ns, ew = 180 - b, "S", "E"
    elif b <= 270:
        qb, ns, ew = b - 180, "S", "W"
    else:
        qb, ns, ew = 360 - b, "N", "W"
    return {"wcb_deg": b, "quadrantal_bearing": f"{ns} {qb:.4f} deg {ew}"}


def back_bearing(fore_bearing_deg: float) -> dict:
    """Back bearing (whole circle) of a line from its fore bearing.

    Args:
        fore_bearing_deg: Fore bearing (WCB) in decimal degrees.
    """
    return {"back_bearing_deg": round((fore_bearing_deg + 180) % 360, 4)}


def reduced_levels_hi_method(bm_rl: float, backsight: float, foresights: list) -> dict:
    """Height of instrument method for ONE instrument setup.

    Args:
        bm_rl: Reduced level of the benchmark (m).
        backsight: Staff reading on the benchmark (m).
        foresights: Staff readings (intermediate/foresight) on the other points, in order (m).
    """
    hi = bm_rl + backsight
    return {
        "height_of_instrument": round(hi, 4),
        "reduced_levels": [round(hi - f, 4) for f in foresights],
    }


def rise_and_fall_method(first_rl: float, setups: list) -> dict:
    """Rise and fall method for a level book with one or more instrument setups.

    Args:
        first_rl: Reduced level of the first point (m).
        setups: One list per instrument setup. Each list holds the staff readings in
            order: the first is the backsight, the last is the foresight (any in
            between are intermediate). The foresight point of one setup is the
            backsight point of the next setup.
    """
    rl = first_rl
    rows = [{"reading": setups[0][0], "rise": None, "fall": None, "rl": round(rl, 4)}]
    for readings in setups:
        for prev, cur in zip(readings, readings[1:]):
            diff = prev - cur
            rl += diff
            rows.append(
                {
                    "reading": cur,
                    "rise": round(diff, 4) if diff > 0 else None,
                    "fall": round(-diff, 4) if diff < 0 else None,
                    "rl": round(rl, 4),
                }
            )
    sum_bs = sum(s[0] for s in setups)
    sum_fs = sum(s[-1] for s in setups)
    return {
        "table": rows,
        "arithmetic_check": {
            "sum_BS_minus_sum_FS": round(sum_bs - sum_fs, 4),
            "last_RL_minus_first_RL": round(rl - first_rl, 4),
        },
    }


def curvature_refraction_correction(distance_km: float) -> dict:
    """Curvature, refraction and combined corrections for long sights in levelling.

    Args:
        distance_km: Length of sight in kilometres.
    """
    c = 0.0785 * distance_km**2
    r = c / 7
    return {
        "curvature_m": round(c, 5),
        "refraction_m": round(r, 5),
        "combined_m": round(0.0673 * distance_km**2, 5),
    }


def slope_correction(slope_length_m: float, height_difference_m: float) -> dict:
    """Tape correction for slope (exact formula).

    Args:
        slope_length_m: Measured length along the slope (m).
        height_difference_m: Difference in level between the two ends (m).
    """
    horizontal = math.sqrt(slope_length_m**2 - height_difference_m**2)
    return {
        "horizontal_length_m": round(horizontal, 4),
        "correction_m": round(slope_length_m - horizontal, 4),
    }


def stadia_tacheometry(
    staff_intercept_m: float,
    vertical_angle_deg: float,
    multiplying_constant: float = 100.0,
    additive_constant: float = 0.0,
) -> dict:
    """Stadia tacheometry with an anallactic-less instrument and a VERTICAL staff.

    Horizontal distance D = k*s*cos^2(t) + C*cos(t)
    Vertical component  V = (k*s/2)*sin(2t) + C*sin(t)
    RL of staff station = RL of instrument axis + V - (middle-wire reading)

    Args:
        staff_intercept_m: Staff intercept s = top hair - bottom hair (m).
        vertical_angle_deg: Vertical angle t (positive for elevation, negative for depression).
        multiplying_constant: Stadia multiplying constant k (usually 100).
        additive_constant: Additive constant C (usually 0 for modern instruments).
    """
    t = math.radians(vertical_angle_deg)
    k, s, c = multiplying_constant, staff_intercept_m, additive_constant
    d = k * s * math.cos(t) ** 2 + c * math.cos(t)
    v = 0.5 * k * s * math.sin(2 * t) + c * math.sin(t)
    return {"horizontal_distance_m": round(d, 4), "vertical_component_m": round(v, 4)}


def interior_angle_check(interior_angles_deg: list) -> dict:
    """Angular misclosure of a closed traverse from its measured interior angles.

    Args:
        interior_angles_deg: Measured interior angles in decimal degrees.
    """
    n = len(interior_angles_deg)
    expected = (2 * n - 4) * 90
    total = sum(interior_angles_deg)
    return {
        "n_stations": n,
        "expected_sum_deg": expected,
        "measured_sum_deg": round(total, 6),
        "misclosure_deg": round(total - expected, 6),
    }


def closed_traverse_bowditch(
    legs: list, start_northing: float = 0.0, start_easting: float = 0.0
) -> dict:
    """Latitudes, departures, closing error and Bowditch adjustment for a closed traverse.

    Args:
        legs: One [length_m, whole_circle_bearing_deg] pair per traverse leg, in order
            around the traverse.
        start_northing: Northing (Y) of the starting station.
        start_easting: Easting (X) of the starting station.
    """
    lat = [L * math.cos(math.radians(b)) for L, b in legs]
    dep = [L * math.sin(math.radians(b)) for L, b in legs]
    perimeter = sum(L for L, _ in legs)
    sum_lat, sum_dep = sum(lat), sum(dep)
    e = math.hypot(sum_lat, sum_dep)
    adj_lat = [la - sum_lat * L / perimeter for la, (L, _) in zip(lat, legs)]
    adj_dep = [de - sum_dep * L / perimeter for de, (L, _) in zip(dep, legs)]
    n, east = start_northing, start_easting
    coords = [[round(n, 4), round(east, 4)]]
    for la, de in zip(adj_lat, adj_dep):
        n += la
        east += de
        coords.append([round(n, 4), round(east, 4)])
    return {
        "perimeter_m": round(perimeter, 4),
        "sum_latitudes": round(sum_lat, 4),
        "sum_departures": round(sum_dep, 4),
        "closing_error_m": round(e, 4),
        "relative_precision": f"1 in {round(perimeter / e)}" if e > 1e-9 else "perfect closure",
        "latitudes": [round(x, 4) for x in lat],
        "departures": [round(x, 4) for x in dep],
        "adjusted_latitudes": [round(x, 4) for x in adj_lat],
        "adjusted_departures": [round(x, 4) for x in adj_dep],
        "adjusted_coordinates_[N,E]": coords,
    }


def polygon_area(points: list) -> dict:
    """Area of a polygon from coordinates (shoelace / coordinate method).

    Args:
        points: [[x1, y1], [x2, y2], ...] in order around the boundary (m).
    """
    n = len(points)
    s = 0.0
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    a = abs(s) / 2
    return {"area_m2": round(a, 4), "area_hectare": round(a / 10000, 6)}


def simple_circular_curve(
    radius_m: float, deflection_angle_deg: float, chainage_of_pi_m: float
) -> dict:
    """Elements of a simple circular curve.

    Args:
        radius_m: Radius R of the curve (m).
        deflection_angle_deg: Deflection angle (delta) between the straights (degrees).
        chainage_of_pi_m: Chainage of the point of intersection (m).
    """
    d = math.radians(deflection_angle_deg)
    T = radius_m * math.tan(d / 2)
    L = radius_m * d
    t1 = chainage_of_pi_m - T
    return {
        "tangent_length_m": round(T, 4),
        "curve_length_m": round(L, 4),
        "long_chord_m": round(2 * radius_m * math.sin(d / 2), 4),
        "external_distance_m": round(radius_m * (1 / math.cos(d / 2) - 1), 4),
        "mid_ordinate_m": round(radius_m * (1 - math.cos(d / 2)), 4),
        "chainage_T1_m": round(t1, 4),
        "chainage_T2_m": round(t1 + L, 4),
    }


def generate_matplotlib_plot(
    data_x: list,
    data_y: list,
    plot_type: str = "line",
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
) -> str:
    """Generates a matplotlib plot as a base64-encoded PNG image (returned as an
    HTML <img> tag so it renders directly in the chat window).

    Args:
        data_x: List of x-axis values.
        data_y: List of y-axis values.
        plot_type: Type of plot ('line', 'bar', 'scatter').
        title: Title of the plot.
        xlabel: Label for the x-axis.
        ylabel: Label for the y-axis.
    """
    plt.figure(figsize=(8, 5))
    if plot_type == "line":
        plt.plot(data_x, data_y)
    elif plot_type == "bar":
        plt.bar(data_x, data_y)
    elif plot_type == "scatter":
        plt.scatter(data_x, data_y)
    else:
        plt.close()
        return "Unsupported plot type. Choose 'line', 'bar', or 'scatter'."

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()  # free memory
    image_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f'<img src="data:image/png;base64,{image_base64}" />'


# Every tool the model is allowed to call. Add new functions here to expose them.
ALL_TOOLS = [
    wcb_to_quadrantal,
    back_bearing,
    reduced_levels_hi_method,
    rise_and_fall_method,
    curvature_refraction_correction,
    slope_correction,
    stadia_tacheometry,
    interior_angle_check,
    closed_traverse_bowditch,
    polygon_area,
    simple_circular_curve,
    generate_matplotlib_plot,
]
