"""Projective floor calibration, independent of Django and browser rendering.

Floor units form a unit square; image coordinates are normalized to the original
background. This does not recover real-world camera dimensions.
"""

import json
import math
from pathlib import Path

from core.lessons import load_exercise_set, load_lesson_visuals, load_room_lesson_visuals


REFERENCE_CORNERS = ((0, 0), (1, 0), (1, 1), (0, 1))
DEFAULT_PATH = Path(__file__).parent / "data" / "png_move_floor.json"
ROOM_PROFILES_DIRECTORY = Path(__file__).parent / "data"
RELATIVE_TOLERANCE = 1e-9


def _point(value):
    """Validate a pair of finite coordinates without changing its coordinate space."""
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError("Each point must contain two coordinates.")

    if any(
        isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
        for v in value
    ):
        raise ValueError("Coordinates must be finite numbers.")

    return tuple(value)


def _validate_corners(values):
    """Return normalized image corners forming a usable convex quadrilateral."""
    if not isinstance(values, (list, tuple)) or len(values) != 4:
        raise ValueError("Provide four corners in perimeter order.")

    corners = tuple(_point(value) for value in values)

    if any(not 0 <= v <= 1 for point in corners for v in point):
        raise ValueError("Corners must be inside the normalized image.")

    span = max(
        max(p[axis] for p in corners) - min(p[axis] for p in corners)
        for axis in (0, 1)
    )
    crosses = []

    for i in range(4):
        a, b, c = (corners[(i + j) % 4] for j in range(3))
        crosses.append(
            (b[0] - a[0]) * (c[1] - b[1])
            - (b[1] - a[1]) * (c[0] - b[0])
        )

    # Absolute tolerance rejects imperceptible image areas; the relative term
    # rejects near-collinear corners at any usable scale.
    tolerance = max(1e-10, span * span * 1e-7)
    if not (
        all(c > tolerance for c in crosses)
        or all(c < -tolerance for c in crosses)
    ):
        raise ValueError("Floor must be a convex, nondegenerate quadrilateral.")

    return corners


def _solve(matrix, target):
    """Solve the small calibration system with scaled partial pivoting."""
    rows = [list(row) + [value] for row, value in zip(matrix, target)]
    scales = [max(abs(v) for v in row) for row in matrix]

    for column in range(len(rows)):
        pivot = max(
            range(column, len(rows)),
            key=lambda i: abs(rows[i][column]) / scales[i],
        )

        if abs(rows[pivot][column]) <= RELATIVE_TOLERANCE * scales[pivot]:
            raise ValueError("Floor calibration is ill-conditioned.")

        rows[column], rows[pivot] = rows[pivot], rows[column]
        scales[column], scales[pivot] = scales[pivot], scales[column]
        divisor = rows[column][column]
        rows[column] = [v / divisor for v in rows[column]]

        for i in range(len(rows)):
            if i != column:
                factor = rows[i][column]
                rows[i] = [a - factor * b for a, b in zip(rows[i], rows[column])]

    return [row[-1] for row in rows]


def _inverse(matrix):
    """Invert a 3x3 matrix, rejecting unsafe conditioning using matrix norms."""
    a, b, c, d, e, f, g, h, i = matrix
    adjugate = [
        e * i - f * h, c * h - b * i, b * f - c * e,
        f * g - d * i, a * i - c * g, c * d - a * f,
        d * h - e * g, b * g - a * h, a * e - b * d,
    ]
    determinant = a * adjugate[0] + b * adjugate[3] + c * adjugate[6]
    norm = max(sum(abs(v) for v in matrix[j:j + 3]) for j in (0, 3, 6))
    adj_norm = max(sum(abs(v) for v in adjugate[j:j + 3]) for j in (0, 3, 6))

    if abs(determinant) <= RELATIVE_TOLERANCE * norm * adj_norm:
        raise ValueError("Floor transformation cannot be safely inverted.")

    return [v / determinant for v in adjugate]


def project_point(matrix, point):
    """Map a point through a flat row-major 3x3 matrix; reject singularities.

    H maps floor units to normalized image coordinates; inverse H reverses it.
    Raises ValueError for nonfinite points or results too near the horizon.
    """
    x, y = _point(point)
    a, b, c, d, e, f, g, h, i = matrix
    denominator = g * x + h * y + i
    scale = abs(g * x) + abs(h * y) + abs(i)

    if abs(denominator) <= RELATIVE_TOLERANCE * scale:
        raise ValueError("Point lies on a projection singularity.")

    result = (
        (a * x + b * y + c) / denominator,
        (d * x + e * y + f) / denominator,
    )

    if not all(math.isfinite(v) for v in result):
        raise ValueError("Projection must be finite.")

    return result


def _solve_floor_matrix(corners):
    """Solve the eight independent coefficients from four point correspondences."""
    rows, target = [], []

    for (x, y), (image_x, image_y) in zip(REFERENCE_CORNERS, corners):
        rows.extend((
            [x, y, 1, 0, 0, 0, -image_x * x, -image_x * y],
            [0, 0, 0, x, y, 1, -image_y * x, -image_y * y],
        ))
        target.extend((image_x, image_y))

    return _solve(rows, target) + [1.0]


def _validate_projection(matrix, inverse, corners):
    """Check the floor domain for singularities and verify corner correspondences."""
    depths = [
        matrix[6] * x + matrix[7] * y + matrix[8]
        for x, y in REFERENCE_CORNERS
    ]

    # w is affine: positive corner depths guarantee no interior horizon crossing.
    # H is normalized with w(0,0)=1.
    if min(depths) <= RELATIVE_TOLERANCE * max(abs(v) for v in depths):
        raise ValueError("Floor crosses or approaches the projection horizon.")

    for floor_point, image_point in zip(REFERENCE_CORNERS, corners):
        correspondences = (
            (project_point(matrix, floor_point), image_point),
            (project_point(inverse, image_point), floor_point),
        )

        for actual, expected in correspondences:
            if max(abs(a - b) for a, b in zip(actual, expected)) > 1e-7:
                raise ValueError("Floor calibration failed its accuracy check.")


def prepare_floor(config):
    """Validate an authored JSON dict; return H, inverse H, and image corners.

    Normalized image corners correspond to unit-square floor points
    (0,0), (1,0), (1,1), (0,1), in that order. Returned matrices are flat row-major
    arrays. All edges may tilt. Invalid schema or unsafe geometry raises ValueError.
    """
    if (
        not isinstance(config, dict)
        or type(config.get("version")) is not int
        or config["version"] != 1
        or config.get("coordinate_space") != "normalized_image"
    ):
        raise ValueError("Unsupported floor configuration schema.")

    corners = _validate_corners(config.get("corners"))
    matrix = _solve_floor_matrix(corners)
    inverse = _inverse(matrix)

    _validate_projection(matrix, inverse, corners)

    return {"matrix": matrix, "inverse_matrix": inverse, "corners": corners}


def load_floor(path=DEFAULT_PATH):
    """Read a trusted plane/path JSON and prepare it with default lesson visuals.

    Raises OSError for unreadable files and ValueError for invalid JSON/geometry.
    """
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    return _prepare_profile(config)


def load_room_floor(mission_id, room_id, background_asset, exercise_set_id=""):
    """Compose a room's plane/path with its placed lesson's sprite settings.

    Non-boss rooms pass their exercise_set_id to select exercises.json content.
    Boss callers omit it to keep their existing data source and browser payload.
    Invalid geometry, paths, or lesson settings raise ValueError.
    """
    floor = load_room_plane(mission_id, room_id, background_asset, exercise_set_id)
    path = floor.pop("path")
    visuals = load_room_lesson_visuals(mission_id, room_id, exercise_set_id)
    floor["motion"] = prepare_motion({**path, **visuals}, floor)
    return floor


def load_room_plane(mission_id, room_id, background_asset, exercise_set_id=""):
    """Return room geometry and image-space path, without lesson/image settings.

    The content reference (or legacy boss IDs) and background select calibration
    so a changed image cannot silently reuse old geometry. Coordinates remain relative
    to the original image. Invalid matching geometry raises ValueError.
    """
    profile = _room_profile(mission_id, room_id, background_asset, exercise_set_id)
    floor = prepare_floor(profile)
    floor["path"] = profile["path"]
    return floor


def _room_profile(mission_id, room_id, background_asset, exercise_set_id=""):
    """Read matching room-owned values, falling back to the default plane/path."""
    if exercise_set_id:
        profile = load_exercise_set(exercise_set_id).get("room_profile")
        if profile is not None and profile["background_asset"] == background_asset:
            return profile
        return json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))

    # Mission IDs select a fixed local filename, never a client-supplied path.
    if type(mission_id) is not int or mission_id <= 0:
        return json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))

    profiles_path = ROOM_PROFILES_DIRECTORY / f"mission_{mission_id}_floor_profiles.json"
    if not profiles_path.is_file():
        return json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))

    profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
    profile = profiles["rooms"].get(str(room_id))

    if (
        mission_id == profiles["mission_id"]
        and profile is not None
        and profile["background_asset"] == background_asset
    ):
        return profile

    return json.loads(DEFAULT_PATH.read_text(encoding="utf-8"))


def _prepare_profile(config):
    """Prepare floor geometry and optional motion from original-image values."""
    floor = prepare_floor(config)

    if "path" in config:
        motion = {**config["path"], **load_lesson_visuals()}
        floor["motion"] = prepare_motion(motion, floor)

    return floor


def _positive_number(value, name):
    """Validate a finite positive scalar, excluding JSON booleans."""
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
    ):
        raise ValueError(f"{name} must be a finite positive number.")

    return value


def _floor_endpoint(image_point, inverse):
    """Convert an image endpoint to floor units, rejecting points outside the floor."""
    floor_point = project_point(inverse, image_point)

    if any(value < -1e-9 or value > 1 + 1e-9 for value in floor_point):
        raise ValueError("Path endpoints must be inside the calibrated floor.")

    return tuple(min(1, max(0, value)) for value in floor_point)


def prepare_motion(config, floor):
    """Prepare a straight approaching path from an authored dict and prepared floor.

    Endpoints use normalized image coordinates; returned endpoints use floor units.
    end_height is a fraction of original background height; duration_ms is milliseconds.
    foot_anchor is a fraction of sprite width/height. Raises ValueError for invalid
    values, outside endpoints, stationary paths, or a direction that shrinks the sprite.
    """
    if not isinstance(config, dict):
        raise ValueError("Motion must be a JSON object.")

    start = _floor_endpoint(config.get("start_image"), floor["inverse_matrix"])
    end = _floor_endpoint(config.get("end_image"), floor["inverse_matrix"])
    anchor = _point(config.get("foot_anchor"))
    height = _positive_number(config.get("end_height"), "Final height")
    duration = _positive_number(config.get("duration_ms"), "Duration")
    asset = config.get("sprite_asset")

    if any(not 0 <= value <= 1 for value in anchor):
        raise ValueError("Foot anchor must lie inside the sprite.")

    if not isinstance(asset, str) or not asset.startswith("core/png_movement/") or ".." in asset:
        raise ValueError("Sprite must reference a local core/png_movement asset.")

    if math.dist(start, end) <= 1e-9:
        raise ValueError("The approach path must have nonzero length.")

    g, h, i = floor["matrix"][6:]
    start_depth = g * start[0] + h * start[1] + i
    end_depth = g * end[0] + h * end[1] + i

    # Depth is affine along this segment. Positive endpoints exclude a horizon
    # crossing; decreasing depth gives nondecreasing inverse-depth billboard size.
    if min(start_depth, end_depth) <= 0 or end_depth > start_depth + 1e-9:
        raise ValueError("Approach must have positive depth and nondecreasing size.")

    return {
        "start_floor": start,
        "end_floor": end,
        "end_depth": end_depth,
        "end_height": height,
        "duration_ms": duration,
        "foot_anchor": anchor,
        "sprite_asset": asset,
    }
