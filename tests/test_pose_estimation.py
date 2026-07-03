"""Tests for pose estimation."""

from pathlib import Path

from pose_estimation import estimate_pose


def test_estimate_pose_returns_33_structured_landmarks() -> None:
    image_path = Path(__file__).parent / "fixtures" / "test_image.jpeg"

    landmarks = estimate_pose(str(image_path))

    assert len(landmarks) == 33
    for landmark in landmarks:
        assert set(landmark) == {"name", "x", "y", "z", "visibility"}
        assert isinstance(landmark["name"], str)
        for field in ("x", "y", "z", "visibility"):
            assert isinstance(landmark[field], (float, int))
