"""Tests for normalized pose comparison."""

from pathlib import Path

import pytest
from mediapipe.tasks.python.vision.pose_landmarker import PoseLandmark

from pose_comparison import IDENTITY_TOL, compare_poses
from pose_estimation import estimate_pose


def make_pose() -> list[dict]:
    """Build a synthetic pose with distinct, nondegenerate coordinates."""
    return [
        {
            "name": PoseLandmark(index).name,
            "x": 0.1 * index + 0.25,
            "y": 0.03 * index * index + 0.5,
            "z": -0.02 * index,
            "visibility": 1.0,
        }
        for index in range(33)
    ]


def test_identical_poses_have_zero_score() -> None:
    pose = make_pose()

    assert compare_poses(pose, pose) < IDENTITY_TOL


def test_score_is_translation_invariant() -> None:
    pose = make_pose()
    translated = [
        {**landmark, "x": landmark["x"] + 4.0, "y": landmark["y"] - 3.0}
        for landmark in pose
    ]

    assert compare_poses(pose, translated) < IDENTITY_TOL


def test_score_is_scale_invariant() -> None:
    pose = make_pose()
    scaled = [
        {**landmark, "x": landmark["x"] * 2.0, "y": landmark["y"] * 2.0}
        for landmark in pose
    ]

    assert compare_poses(pose, scaled) < IDENTITY_TOL


def test_visible_landmark_movement_increases_score() -> None:
    pose = make_pose()
    changed = [landmark.copy() for landmark in pose]
    changed[0]["x"] += 1.0

    score = compare_poses(pose, changed)

    assert score > IDENTITY_TOL
    assert score > 1e-3


def test_zero_length_torso_raises_value_error() -> None:
    pose = make_pose()
    anchors = {
        "LEFT_HIP",
        "RIGHT_HIP",
        "LEFT_SHOULDER",
        "RIGHT_SHOULDER",
    }
    for landmark in pose:
        if landmark["name"] in anchors:
            landmark["x"] = 1.0
            landmark["y"] = 1.0

    with pytest.raises(ValueError):
        compare_poses(pose, pose)


def test_estimated_pose_compares_identically_to_itself() -> None:
    image_path = Path(__file__).parent / "fixtures" / "test_image.jpeg"
    pose = estimate_pose(str(image_path))

    assert compare_poses(pose, pose) < IDENTITY_TOL
