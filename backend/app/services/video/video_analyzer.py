"""
Video/posture analysis logic. Takes structured landmark coordinates (as
MediaPipe's FaceLandmarker/PoseLandmarker would produce) rather than raw
frames — same separation as speech_analyzer.py, and for the same reason:
this is unit-testable with synthetic landmark data even though this build
environment can't download MediaPipe's model file (see frame_processor.py).

Landmark indices below match MediaPipe's 468-point face mesh and 33-point
pose topology (documented at https://ai.google.dev/edge/mediapipe/solutions/
vision/face_landmarker and .../pose_landmarker — verify indices against
current docs if MediaPipe's topology changes).

Coordinates are normalized [0, 1] relative to frame width/height, matching
MediaPipe's output convention.
"""

from dataclasses import dataclass, field


@dataclass
class Point:
    x: float
    y: float
    z: float = 0.0


@dataclass
class FaceLandmarks:
    left_iris_center: Point
    right_iris_center: Point
    left_eye_left_corner: Point
    left_eye_right_corner: Point
    right_eye_left_corner: Point
    right_eye_right_corner: Point
    mouth_left_corner: Point
    mouth_right_corner: Point
    mouth_top: Point
    mouth_bottom: Point
    nose_tip: Point
    forehead: Point
    chin: Point
    face_left_edge: Point
    face_right_edge: Point


@dataclass
class PoseLandmarks:
    left_shoulder: Point
    right_shoulder: Point
    nose: Point


@dataclass
class FrameAnalysis:
    face: FaceLandmarks | None
    pose: PoseLandmarks | None


def _eye_gaze_deviation(iris: Point, corner_a: Point, corner_b: Point) -> float:
    """0 = iris perfectly centered between eye corners (looking straight),
    1 = iris pushed all the way to one corner (looking sharply to a side)."""
    eye_width = abs(corner_b.x - corner_a.x)
    if eye_width == 0:
        return 0.0
    eye_center_x = (corner_a.x + corner_b.x) / 2
    deviation = abs(iris.x - eye_center_x) / (eye_width / 2)
    return min(deviation, 1.0)


def compute_eye_contact_score(face: FaceLandmarks) -> float:
    left_dev = _eye_gaze_deviation(face.left_iris_center, face.left_eye_left_corner, face.left_eye_right_corner)
    right_dev = _eye_gaze_deviation(face.right_iris_center, face.right_eye_right_corner, face.right_eye_left_corner)
    avg_deviation = (left_dev + right_dev) / 2
    return round((1 - avg_deviation) * 100, 1)


def compute_smile_score(face: FaceLandmarks) -> float:
    """Mouth-corner elevation relative to mouth center, normalized by mouth
    width — upturned corners relative to a neutral horizontal mouth line
    indicate a smile. y increases downward in image coordinates, so a
    smile (corners raised) means corner_y < mid_y."""
    mouth_width = abs(face.mouth_right_corner.x - face.mouth_left_corner.x)
    if mouth_width == 0:
        return 0.0
    mid_y = (face.mouth_top.y + face.mouth_bottom.y) / 2
    corner_avg_y = (face.mouth_left_corner.y + face.mouth_right_corner.y) / 2
    lift = (mid_y - corner_avg_y) / mouth_width  # positive = corners raised above mid-mouth
    # Empirically-reasonable scaling: a lift of ~0.15x mouth-width reads as a full smile
    return round(max(0.0, min(lift / 0.15, 1.0)) * 100, 1)


def compute_head_pose_attention_score(face: FaceLandmarks) -> dict:
    """Simplified yaw/pitch estimate from landmark symmetry rather than a
    full solvePnP 3D pose solve (which needs camera intrinsics this pipeline
    doesn't have) — good enough to flag 'facing the camera' vs 'turned away
    or looking down', not precise enough for exact rotation angles."""
    face_width = abs(face.face_right_edge.x - face.face_left_edge.x)
    face_height = abs(face.chin.y - face.forehead.y)

    yaw_deviation = 0.0
    if face_width > 0:
        left_dist = abs(face.nose_tip.x - face.face_left_edge.x)
        right_dist = abs(face.face_right_edge.x - face.nose_tip.x)
        yaw_deviation = abs(left_dist - right_dist) / face_width

    pitch_deviation = 0.0
    if face_height > 0:
        top_dist = abs(face.nose_tip.y - face.forehead.y)
        bottom_dist = abs(face.chin.y - face.nose_tip.y)
        pitch_deviation = abs(top_dist - bottom_dist) / face_height

    facing_forward_score = round(max(0.0, 1 - (yaw_deviation + pitch_deviation)) * 100, 1)
    return {
        "yaw_deviation": round(yaw_deviation, 3),
        "pitch_deviation": round(pitch_deviation, 3),
        "attention_score": facing_forward_score,
    }


def compute_posture_score(pose: PoseLandmarks) -> float:
    """Shoulder levelness as a simple, honest proxy for posture — real
    ergonomic posture assessment (forward-head posture, spinal alignment)
    needs more landmarks and a calibrated reference than a single-frame
    shoulder/nose check can give. This flags obvious slouching/leaning, not
    subtle posture issues."""
    shoulder_width = abs(pose.right_shoulder.x - pose.left_shoulder.x)
    if shoulder_width == 0:
        return 50.0  # can't assess — neutral, not zero
    shoulder_tilt = abs(pose.left_shoulder.y - pose.right_shoulder.y) / shoulder_width
    return round(max(0.0, 1 - shoulder_tilt * 3) * 100, 1)


def analyze_frame(frame: FrameAnalysis) -> dict:
    result: dict = {"eye_contact_score": None, "smile_score": None, "head_pose": None, "posture_score": None}
    if frame.face:
        result["eye_contact_score"] = compute_eye_contact_score(frame.face)
        result["smile_score"] = compute_smile_score(frame.face)
        result["head_pose"] = compute_head_pose_attention_score(frame.face)
    if frame.pose:
        result["posture_score"] = compute_posture_score(frame.pose)
    return result


def aggregate_session(frame_results: list[dict]) -> dict:
    """Averages per-frame scores across a whole interview answer/session into
    one confidence-relevant summary. Frames where a signal wasn't available
    (no face detected that frame, etc.) are excluded from that signal's
    average rather than counted as 0."""
    def avg(key):
        values = [f[key] for f in frame_results if f.get(key) is not None]
        return round(sum(values) / len(values), 1) if values else None

    def avg_nested(outer_key, inner_key):
        values = [f[outer_key][inner_key] for f in frame_results if f.get(outer_key) is not None]
        return round(sum(values) / len(values), 1) if values else None

    eye_contact = avg("eye_contact_score")
    smile = avg("smile_score")
    attention = avg_nested("head_pose", "attention_score")
    posture = avg("posture_score")

    components = [v for v in [eye_contact, attention, posture] if v is not None]
    confidence_score = round(sum(components) / len(components), 1) if components else None

    return {
        "eye_contact_score": eye_contact,
        "smile_score": smile,
        "attention_score": attention,
        "posture_score": posture,
        "confidence_score": confidence_score,
        "frames_analyzed": len(frame_results),
    }
