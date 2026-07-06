"""Compare two poses after translation and scale normalization."""

import argparse
import math

from pose_estimation import estimate_pose

IDENTITY_TOL = 1e-9


def _normalize_pose(pose: list[dict]) -> list[tuple[float, float]]:
    """Return x/y coordinates centered on the hips and scaled by torso length."""
    landmarks = {landmark["name"]: landmark for landmark in pose}
    anchor_names = (
        "LEFT_HIP",
        "RIGHT_HIP",
        "LEFT_SHOULDER",
        "RIGHT_SHOULDER",
    )
    try:
        left_hip, right_hip, left_shoulder, right_shoulder = (
            landmarks[name] for name in anchor_names
        )
    except KeyError as error:
        raise ValueError(f"Missing normalization landmark: {error.args[0]}") from error

    mid_hip_x = (left_hip["x"] + right_hip["x"]) / 2
    mid_hip_y = (left_hip["y"] + right_hip["y"]) / 2
    mid_shoulder_x = (left_shoulder["x"] + right_shoulder["x"]) / 2
    mid_shoulder_y = (left_shoulder["y"] + right_shoulder["y"]) / 2
    torso_length = math.hypot(
        mid_shoulder_x - mid_hip_x,
        mid_shoulder_y - mid_hip_y,
    )
    if torso_length < IDENTITY_TOL:
        raise ValueError("Cannot normalize a pose with near-zero torso length")

    return [
        (
            (landmark["x"] - mid_hip_x) / torso_length,
            (landmark["y"] - mid_hip_y) / torso_length,
        )
        for landmark in pose
    ]


def compare_poses(pose_a: list[dict], pose_b: list[dict]) -> float:
    """Return the visibility-weighted mean normalized landmark distance."""
    normalized_a = _normalize_pose(pose_a)
    normalized_b = _normalize_pose(pose_b)

    weighted_distance = 0.0
    total_weight = 0.0
    for landmark_a, landmark_b, coords_a, coords_b in zip(
        pose_a,
        pose_b,
        normalized_a,
        normalized_b,
        strict=True,
    ):
        weight = (landmark_a["visibility"] + landmark_b["visibility"]) / 2
        weighted_distance += weight * math.hypot(
            coords_a[0] - coords_b[0],
            coords_a[1] - coords_b[1],
        )
        total_weight += weight

    if total_weight == 0:
        raise ValueError("Cannot compare poses with zero total visibility")

    return weighted_distance / total_weight


def main() -> None:
    """Compare poses estimated from two image paths."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-a", required=True, help="Path to the first image")
    parser.add_argument("--image-b", required=True, help="Path to the second image")
    args = parser.parse_args()

    print(compare_poses(estimate_pose(args.image_a), estimate_pose(args.image_b)))


if __name__ == "__main__":
    main()
