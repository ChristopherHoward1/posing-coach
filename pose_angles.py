"""Compute and compare interior joint angles for pose landmarks."""

import argparse
import math

from pose_estimation import estimate_pose

ANGLE_TOL = 1e-9

_ANGLE_TRIPLES = (
    ("LEFT_ELBOW", "LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_WRIST"),
    ("RIGHT_ELBOW", "RIGHT_SHOULDER", "RIGHT_ELBOW", "RIGHT_WRIST"),
    ("LEFT_KNEE", "LEFT_HIP", "LEFT_KNEE", "LEFT_ANKLE"),
    ("RIGHT_KNEE", "RIGHT_HIP", "RIGHT_KNEE", "RIGHT_ANKLE"),
    ("LEFT_SHOULDER", "LEFT_ELBOW", "LEFT_SHOULDER", "LEFT_HIP"),
    ("RIGHT_SHOULDER", "RIGHT_ELBOW", "RIGHT_SHOULDER", "RIGHT_HIP"),
    ("LEFT_HIP", "LEFT_SHOULDER", "LEFT_HIP", "LEFT_KNEE"),
    ("RIGHT_HIP", "RIGHT_SHOULDER", "RIGHT_HIP", "RIGHT_KNEE"),
)


def _angle_degrees(a: dict, b: dict, c: dict) -> float:
    """Return the 2-D interior angle at landmark b."""
    ux = a["x"] - b["x"]
    uy = a["y"] - b["y"]
    vx = c["x"] - b["x"]
    vy = c["y"] - b["y"]
    if math.hypot(ux, uy) < ANGLE_TOL or math.hypot(vx, vy) < ANGLE_TOL:
        raise ValueError("Cannot compute an angle with a zero-length ray")

    cross = ux * vy - uy * vx
    dot = ux * vx + uy * vy
    return float(math.degrees(math.atan2(abs(cross), dot)))


def joint_angles(pose: list[dict]) -> dict[str, float]:
    """Return the eight named interior joint angles for a pose."""
    landmarks = {landmark["name"]: landmark for landmark in pose}
    angles = {}
    for vertex_name, a_name, b_name, c_name in _ANGLE_TRIPLES:
        try:
            a, b, c = (landmarks[name] for name in (a_name, b_name, c_name))
        except KeyError as error:
            raise ValueError(f"Missing angle landmark: {error.args[0]}") from error
        angles[vertex_name] = _angle_degrees(a, b, c)
    return angles


def angle_feedback(user_pose: list[dict], reference_pose: list[dict]) -> list[dict]:
    """Return reference-relative open/close feedback for interior joint angles."""
    user_angles = joint_angles(user_pose)
    reference_angles = joint_angles(reference_pose)

    feedback = []
    for joint, angle in user_angles.items():
        reference_angle = reference_angles[joint]
        delta = reference_angle - angle
        if delta > ANGLE_TOL:
            direction = "open"
        elif delta < -ANGLE_TOL:
            direction = "close"
        else:
            direction = ""
        feedback.append(
            {
                "joint": joint,
                "angle": angle,
                "reference_angle": reference_angle,
                "delta": delta,
                "direction": direction,
            }
        )

    feedback.sort(key=lambda entry: abs(entry["delta"]), reverse=True)
    return feedback


def main() -> None:
    """Print interior angle feedback for a user image and reference image."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image-a", required=True, help="Path to the user image")
    parser.add_argument("--image-b", required=True, help="Path to the reference image")
    args = parser.parse_args()

    feedback = angle_feedback(
        estimate_pose(args.image_a),
        estimate_pose(args.image_b),
    )
    if all(not entry["direction"] for entry in feedback):
        print("Angles match.")
        return

    for entry in feedback:
        if entry["direction"]:
            adjustment = (
                f"{entry['direction']} by {abs(entry['delta']):.1f}"
            )
        else:
            adjustment = "matched"
        print(
            f"{entry['joint']}: {entry['angle']:.1f} deg "
            f"(reference {entry['reference_angle']:.1f} deg, {adjustment})"
        )


if __name__ == "__main__":
    main()
