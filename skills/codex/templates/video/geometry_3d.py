"""Pure-numpy 3D math for portable PyReeler scripts.

Use this module when a piece needs perspective depth, rotating geometry, or
perspective-warped face textures (e.g. a rotating cube with textured faces)
without taking on a real-time 3D engine dependency.

Functions:
- get_rotation_matrix(rx, ry, rz): 3x3 rotation matrix from Euler angles (rad)
- project_points(points, w, h, fov, viewer_distance): perspective-project Nx3
  points to Nx2 screen coords + per-point depth
- find_coeffs(target_pb, src_pa): 8 perspective-transform coefficients for
  PIL.Image.PERSPECTIVE. See gotcha below.

PIL.PERSPECTIVE direction gotcha:
PIL.Image.transform(size, Image.PERSPECTIVE, coeffs, ...) interprets coeffs
as an OUTPUT -> INPUT (inverse) mapping: each output pixel looks up its
source coord. Therefore, to paint a source quadrilateral src_pa onto a
target quadrilateral target_pb in the output, call:

    coeffs = find_coeffs(target_pb, src_pa)   # NOT find_coeffs(src_pa, target_pb)
    warped = src_img.transform((W, H), Image.PERSPECTIVE, coeffs, Image.BILINEAR)

Passing arguments in the wrong order produces a tiny/clipped texture in the
corner of the output and is the same bug that lurks in older PyReeler
experiments. Always pass (target_first, source_second).
"""
from __future__ import annotations

import numpy as np


def get_rotation_matrix(rx: float, ry: float, rz: float) -> np.ndarray:
    """Return a 3x3 rotation matrix for Euler angles in radians (X, Y, Z order)."""
    rot_x = np.array([[1, 0, 0],
                      [0, np.cos(rx), -np.sin(rx)],
                      [0, np.sin(rx),  np.cos(rx)]])
    rot_y = np.array([[ np.cos(ry), 0, np.sin(ry)],
                      [0,           1, 0],
                      [-np.sin(ry), 0, np.cos(ry)]])
    rot_z = np.array([[np.cos(rz), -np.sin(rz), 0],
                      [np.sin(rz),  np.cos(rz), 0],
                      [0,           0,          1]])
    return rot_z @ rot_y @ rot_x


def project_points(points: np.ndarray, width: int, height: int,
                   field_of_view: float = 800.0,
                   viewer_distance: float = 6.0) -> tuple[np.ndarray, np.ndarray]:
    """Perspective-project Nx3 points to (Nx2 screen coords, per-point depth).

    The camera looks down +Z. viewer_distance is added to point z so that
    points with z < -viewer_distance disappear behind the camera (clipped to a
    minimum depth of 0.1 to avoid division by zero).
    """
    z_eff = points[:, 2] + viewer_distance
    z_eff = np.where(z_eff < 0.1, 0.1, z_eff)
    factor = field_of_view / z_eff
    x_2d = points[:, 0] * factor + width / 2
    y_2d = points[:, 1] * factor + height / 2
    return np.stack([x_2d, y_2d], axis=1), z_eff


def find_coeffs(target_pb, src_pa) -> np.ndarray:
    """Solve for the 8 perspective coefficients that map target_pb -> src_pa.

    Pass the TARGET (output) quadrilateral first and the SOURCE (input)
    quadrilateral second. The returned coefficients are what
    PIL.Image.transform(size, Image.PERSPECTIVE, coeffs, ...) expects.

    target_pb, src_pa: each a sequence of four (x, y) tuples in matching
    corner order (typically top-left, top-right, bottom-right, bottom-left).
    """
    matrix = []
    for p_target, p_source in zip(target_pb, src_pa):
        x, y = p_target
        u, v = p_source
        matrix.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        matrix.append([0, 0, 0, x, y, 1, -v * x, -v * y])
    A = np.array(matrix, dtype=float)
    B = np.array(src_pa, dtype=float).reshape(8)
    return np.linalg.solve(A, B)
