"""Tests for per-landmark directional pose feedback."""

import pytest
from mediapipe.tasks.python.vision.pose_landmarker import PoseLandmark

from pose_feedback import pose_feedback


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


def test_identical_poses_have_no_feedback() -> None:
    pose = make_pose()

    assert pose_feedback(pose, pose) == []


def test_perturbed_landmark_is_top_ranked() -> None:
    user_pose = make_pose()
    reference_pose = [landmark.copy() for landmark in user_pose]
    reference_pose[PoseLandmark.NOSE]["x"] += 2.0

    result = pose_feedback(user_pose, reference_pose)

    assert result[0]["name"] == PoseLandmark.NOSE.name


def test_up_direction() -> None:
    user_pose = make_pose()
    reference_pose = [landmark.copy() for landmark in user_pose]
    reference_pose[PoseLandmark.NOSE]["y"] -= 1.0

    result = pose_feedback(user_pose, reference_pose)

    assert result[0]["direction"] == "up"


def test_right_direction() -> None:
    user_pose = make_pose()
    reference_pose = [landmark.copy() for landmark in user_pose]
    reference_pose[PoseLandmark.NOSE]["x"] += 1.0

    result = pose_feedback(user_pose, reference_pose)

    assert result[0]["direction"] == "right"


def test_diagonal_direction() -> None:
    user_pose = make_pose()
    reference_pose = [landmark.copy() for landmark in user_pose]
    reference_pose[PoseLandmark.NOSE]["x"] += 1.0
    reference_pose[PoseLandmark.NOSE]["y"] -= 1.0

    result = pose_feedback(user_pose, reference_pose)

    assert result[0]["direction"] == "up and right"


def test_top_k_returns_largest_movements() -> None:
    user_pose = make_pose()
    reference_pose = [landmark.copy() for landmark in user_pose]
    movements = {
        PoseLandmark.NOSE: 0.5,
        PoseLandmark.LEFT_EYE_INNER: 2.0,
        PoseLandmark.LEFT_EYE: 1.0,
        PoseLandmark.LEFT_EYE_OUTER: 3.0,
    }
    for index, movement in movements.items():
        reference_pose[index]["x"] += movement

    result = pose_feedback(user_pose, reference_pose, top_k=3)

    assert len(result) == 3
    assert [entry["name"] for entry in result] == [
        PoseLandmark.LEFT_EYE_OUTER.name,
        PoseLandmark.LEFT_EYE_INNER.name,
        PoseLandmark.LEFT_EYE.name,
    ]


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
        pose_feedback(pose, pose)
