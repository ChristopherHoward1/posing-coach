"""Generate directional feedback for the most divergent pose landmarks."""

import argparse
import math

from pose_comparison import IDENTITY_TOL, normalize_pose
from pose_estimation import estimate_pose

DIRECTION_MIN_FRACTION = 0.2


def _direction(dx: float, dy: float, magnitude: float) -> str:
    """Return an image-frame direction cue for a displacement."""
    parts = []
    if abs(dy) >= DIRECTION_MIN_FRACTION * magnitude:
        parts.append("up" if dy < 0 else "down")
    if abs(dx) >= DIRECTION_MIN_FRACTION * magnitude:
        parts.append("left" if dx < 0 else "right")
    return " and ".join(parts)


def pose_feedback(
    user_pose: list[dict], reference_pose: list[dict], top_k: int = 3
) -> list[dict]:
    """Return directional feedback for the top-K divergent landmarks."""
    user_norm = normalize_pose(user_pose)
    ref_norm = normalize_pose(reference_pose)

    feedback = []
    for index, (user_coords, ref_coords) in enumerate(
        zip(user_norm, ref_norm, strict=True)
    ):
        dx = ref_coords[0] - user_coords[0]
        dy = ref_coords[1] - user_coords[1]
        magnitude = math.hypot(dx, dy)
        if magnitude >= IDENTITY_TOL:
            feedback.append(
                {
                    "name": user_pose[index]["name"],
                    "dx": dx,
                    "dy": dy,
                    "magnitude": magnitude,
                    "direction": _direction(dx, dy, magnitude),
                }
            )

    feedback.sort(key=lambda entry: entry["magnitude"], reverse=True)
    return feedback[:top_k]


def main() -> None:
    """Print pose feedback for a user image and reference image."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-a", required=True, help="Path to the user image")
    parser.add_argument("--image-b", required=True, help="Path to the reference image")
    args = parser.parse_args()

    feedback = pose_feedback(
        estimate_pose(args.image_a),
        estimate_pose(args.image_b),
    )
    if not feedback:
        print("Poses match.")
        return

    for entry in feedback:
        print(
            f"{entry['name']}: move {entry['direction']} "
            f"(off by {entry['magnitude']:.2f})"
        )


if __name__ == "__main__":
    main()
