from app.services.video.video_analyzer import (
    FaceLandmarks,
    FrameAnalysis,
    Point,
    PoseLandmarks,
    aggregate_session,
    analyze_frame,
    compute_eye_contact_score,
    compute_head_pose_attention_score,
    compute_posture_score,
    compute_smile_score,
)


def _neutral_face(**overrides) -> FaceLandmarks:
    """A face looking straight at the camera, neutral expression, centered."""
    defaults = dict(
        left_iris_center=Point(0.40, 0.40),
        right_iris_center=Point(0.60, 0.40),
        left_eye_left_corner=Point(0.35, 0.40),
        left_eye_right_corner=Point(0.45, 0.40),
        right_eye_left_corner=Point(0.55, 0.40),
        right_eye_right_corner=Point(0.65, 0.40),
        mouth_left_corner=Point(0.42, 0.65),
        mouth_right_corner=Point(0.58, 0.65),
        mouth_top=Point(0.50, 0.64),
        mouth_bottom=Point(0.50, 0.66),
        nose_tip=Point(0.50, 0.55),
        forehead=Point(0.50, 0.20),
        chin=Point(0.50, 0.85),
        face_left_edge=Point(0.25, 0.50),
        face_right_edge=Point(0.75, 0.50),
    )
    defaults.update(overrides)
    return FaceLandmarks(**defaults)


def test_eye_contact_high_when_iris_centered():
    face = _neutral_face()
    score = compute_eye_contact_score(face)
    assert score > 90


def test_eye_contact_low_when_looking_away():
    # Iris pushed to the outer corner of each eye = looking sharply to a side
    face = _neutral_face(
        left_iris_center=Point(0.35, 0.40),  # at the eye's left corner
        right_iris_center=Point(0.55, 0.40),  # at the eye's left corner too
    )
    score = compute_eye_contact_score(face)
    assert score < 50


def test_smile_score_high_for_raised_mouth_corners():
    smiling = _neutral_face(
        mouth_left_corner=Point(0.42, 0.60),  # corners raised above mid-mouth
        mouth_right_corner=Point(0.58, 0.60),
        mouth_top=Point(0.50, 0.64),
        mouth_bottom=Point(0.50, 0.68),
    )
    score = compute_smile_score(smiling)
    assert score > 50


def test_smile_score_low_for_flat_neutral_mouth():
    neutral = _neutral_face()  # corners level with mid-mouth
    score = compute_smile_score(neutral)
    assert score < 20


def test_head_pose_high_attention_when_facing_forward():
    face = _neutral_face()  # symmetric by construction
    result = compute_head_pose_attention_score(face)
    assert result["attention_score"] > 90
    assert result["yaw_deviation"] < 0.1


def test_head_pose_lower_attention_when_turned_away():
    # Nose pushed toward one face edge = head turned to that side
    turned = _neutral_face(nose_tip=Point(0.65, 0.55), face_left_edge=Point(0.25, 0.50), face_right_edge=Point(0.75, 0.50))
    result = compute_head_pose_attention_score(turned)
    assert result["yaw_deviation"] > 0.2
    assert result["attention_score"] < 80


def test_posture_high_for_level_shoulders():
    pose = PoseLandmarks(left_shoulder=Point(0.3, 0.5), right_shoulder=Point(0.7, 0.5), nose=Point(0.5, 0.2))
    assert compute_posture_score(pose) > 90


def test_posture_lower_for_tilted_shoulders():
    pose = PoseLandmarks(left_shoulder=Point(0.3, 0.35), right_shoulder=Point(0.7, 0.55), nose=Point(0.5, 0.2))
    assert compute_posture_score(pose) < 80


def test_analyze_frame_handles_missing_face_gracefully():
    frame = FrameAnalysis(face=None, pose=PoseLandmarks(left_shoulder=Point(0.3, 0.5), right_shoulder=Point(0.7, 0.5), nose=Point(0.5, 0.2)))
    result = analyze_frame(frame)
    assert result["eye_contact_score"] is None
    assert result["smile_score"] is None
    assert result["posture_score"] is not None


def test_analyze_frame_handles_missing_pose_gracefully():
    frame = FrameAnalysis(face=_neutral_face(), pose=None)
    result = analyze_frame(frame)
    assert result["eye_contact_score"] is not None
    assert result["posture_score"] is None


def test_aggregate_session_averages_across_frames():
    frames = [
        analyze_frame(FrameAnalysis(face=_neutral_face(), pose=PoseLandmarks(Point(0.3, 0.5), Point(0.7, 0.5), Point(0.5, 0.2))))
        for _ in range(5)
    ]
    result = aggregate_session(frames)
    assert result["frames_analyzed"] == 5
    assert result["eye_contact_score"] > 90
    assert result["confidence_score"] is not None


def test_aggregate_session_excludes_frames_without_a_signal_rather_than_treating_as_zero():
    good_frame = analyze_frame(FrameAnalysis(face=_neutral_face(), pose=None))
    no_face_frame = analyze_frame(FrameAnalysis(face=None, pose=PoseLandmarks(Point(0.3, 0.5), Point(0.7, 0.5), Point(0.5, 0.2))))

    result = aggregate_session([good_frame, no_face_frame])
    # eye_contact only came from one frame — should reflect that frame's real
    # score, not be dragged toward zero by averaging in the missing frame as 0
    assert result["eye_contact_score"] > 90


def test_aggregate_session_empty_input_does_not_crash():
    result = aggregate_session([])
    assert result["frames_analyzed"] == 0
    assert result["confidence_score"] is None
