"""Tests for interior joint-angle feedback."""

import pytest
from mediapipe.tasks.python.vision.pose_landmarker import PoseLandmark

from pose_angles import angle_feedback, joint_angles

ANGLE_JOINTS = {
    "LEFT_ELBOW",
    "RIGHT_ELBOW",
    "LEFT_KNEE",
    "RIGHT_KNEE",
    "LEFT_SHOULDER",
    "RIGHT_SHOULDER",
    "LEFT_HIP",
    "RIGHT_HIP",
}


def make_pose() -> list[dict]:
    """Build a synthetic pose with nondegenerate joint-angle landmarks."""
    pose = [
        {
            "name": PoseLandmark(index).name,
            "x": 10.0 + index,
            "y": 20.0 + index,
            "z": -0.02 * index,
            "visibility": 1.0,
        }
        for index in range(33)
    ]
    coords = {
        "LEFT_SHOULDER": (0.0, 0.0),
        "LEFT_ELBOW": (1.0, 0.0),
        "LEFT_WRIST": (1.0, 1.0),
        "LEFT_HIP": (0.0, 2.0),
        "LEFT_KNEE": (1.0, 2.0),
        "LEFT_ANKLE": (1.0, 3.0),
        "RIGHT_SHOULDER": (4.0, 0.0),
        "RIGHT_ELBOW": (3.0, 0.0),
        "RIGHT_WRIST": (3.0, 1.0),
        "RIGHT_HIP": (4.0, 2.0),
        "RIGHT_KNEE": (3.0, 2.0),
        "RIGHT_ANKLE": (3.0, 3.0),
    }
    for landmark in pose:
        if landmark["name"] in coords:
            landmark["x"], landmark["y"] = coords[landmark["name"]]
    return pose


def test_joint_angles_returns_all_vertex_named_angles() -> None:
    angles = joint_angles(make_pose())

    assert set(angles) == ANGLE_JOINTS
    for angle in angles.values():
        assert isinstance(angle, float)
        assert 0.0 <= angle <= 180.0


def test_right_angle_limb_yields_ninety_degrees() -> None:
    angles = joint_angles(make_pose())

    assert angles["LEFT_ELBOW"] == pytest.approx(90.0)


def test_straight_collinear_limb_yields_one_eighty_degrees() -> None:
    pose = make_pose()
    pose[PoseLandmark.LEFT_WRIST]["x"] = 2.0
    pose[PoseLandmark.LEFT_WRIST]["y"] = 0.0

    angles = joint_angles(pose)

    assert angles["LEFT_ELBOW"] == pytest.approx(180.0)


def test_mirror_invariance() -> None:
    pose = make_pose()
    mirrored_pose = [landmark.copy() for landmark in pose]
    for landmark in mirrored_pose:
        landmark["x"] = -landmark["x"]

    angles = joint_angles(pose)
    mirrored_angles = joint_angles(mirrored_pose)

    assert mirrored_angles == pytest.approx(angles)


def test_angle_feedback_shape_delta_direction_and_sorting() -> None:
    user_pose = make_pose()
    reference_pose = [landmark.copy() for landmark in user_pose]
    reference_pose[PoseLandmark.LEFT_WRIST]["x"] = 2.0
    reference_pose[PoseLandmark.LEFT_WRIST]["y"] = 0.0
    user_pose[PoseLandmark.RIGHT_WRIST]["x"] = 2.0
    user_pose[PoseLandmark.RIGHT_WRIST]["y"] = 0.0

    result = angle_feedback(user_pose, reference_pose)
    by_joint = {entry["joint"]: entry for entry in result}

    assert len(result) == 8
    assert set(by_joint) == ANGLE_JOINTS
    assert by_joint["LEFT_ELBOW"] == {
        "joint": "LEFT_ELBOW",
        "angle": pytest.approx(90.0),
        "reference_angle": pytest.approx(180.0),
        "delta": pytest.approx(90.0),
        "direction": "open",
    }
    assert by_joint["RIGHT_ELBOW"] == {
        "joint": "RIGHT_ELBOW",
        "angle": pytest.approx(180.0),
        "reference_angle": pytest.approx(90.0),
        "delta": pytest.approx(-90.0),
        "direction": "close",
    }
    deltas = [abs(entry["delta"]) for entry in result]
    assert deltas == sorted(deltas, reverse=True)


def test_identical_poses_have_blank_feedback() -> None:
    pose = make_pose()

    result = angle_feedback(pose, pose)

    assert len(result) == 8
    for entry in result:
        assert entry["delta"] == pytest.approx(0.0)
        assert entry["direction"] == ""


def test_missing_required_landmark_raises_value_error() -> None:
    pose = [
        landmark for landmark in make_pose() if landmark["name"] != "LEFT_ELBOW"
    ]

    with pytest.raises(ValueError, match="Missing angle landmark: LEFT_ELBOW"):
        joint_angles(pose)


def test_coincident_landmarks_raise_value_error() -> None:
    pose = make_pose()
    pose[PoseLandmark.LEFT_WRIST]["x"] = pose[PoseLandmark.LEFT_ELBOW]["x"]
    pose[PoseLandmark.LEFT_WRIST]["y"] = pose[PoseLandmark.LEFT_ELBOW]["y"]

    with pytest.raises(ValueError, match="zero-length ray"):
        joint_angles(pose)
