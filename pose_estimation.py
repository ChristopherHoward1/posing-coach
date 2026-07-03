"""Estimate pose landmarks from a single image."""

import argparse
import json
from pathlib import Path

import mediapipe as mp
from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions
from mediapipe.tasks.python.vision.core.vision_task_running_mode import (
    VisionTaskRunningMode,
)
from mediapipe.tasks.python.vision.pose_landmarker import PoseLandmark

DEFAULT_MODEL = Path(__file__).parent / "models" / "pose_landmarker_lite.task"


def estimate_pose(
    image_path: str, model_path: str | Path = DEFAULT_MODEL
) -> list[dict]:
    """Return the 33 landmarks for the first pose detected in an image."""
    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(model_path)),
        running_mode=VisionTaskRunningMode.IMAGE,
        num_poses=1,
    )
    image = mp.Image.create_from_file(image_path)

    with PoseLandmarker.create_from_options(options) as landmarker:
        result = landmarker.detect(image)

    if not result.pose_landmarks:
        raise ValueError(f"No pose detected in image: {image_path}")

    return [
        {
            "name": PoseLandmark(index).name,
            "x": float(landmark.x),
            "y": float(landmark.y),
            "z": float(landmark.z),
            "visibility": float(landmark.visibility),
        }
        for index, landmark in enumerate(result.pose_landmarks[0])
    ]


def main() -> None:
    """Run the command-line pose estimator."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, help="Path to the input image")
    parser.add_argument("--output", help="Path for JSON output (default: stdout)")
    args = parser.parse_args()

    output = json.dumps(estimate_pose(args.image), indent=2)
    if args.output:
        Path(args.output).write_text(f"{output}\n", encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
