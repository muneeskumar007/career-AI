"""
MediaPipe-based landmark extraction from video frames. NOT LIVE-TESTED in
this build: MediaPipe's Tasks API needs a .task model file downloaded from
storage.googleapis.com at runtime, which this environment's network
allowlist doesn't include. An unofficial third-party GitHub mirror of the
file exists and *would* be reachable — deliberately not used here: it's an
unverified binary with no official checksum to validate against, which
isn't something to depend on either for testing or, more importantly, to
recommend baking into a production deployment. Download the official
model files yourself as part of setup — see SETUP.md.

Deliberately isolated from video_analyzer.py: this is the only place that
touches MediaPipe / raw frames. Everything downstream operates on the plain
FaceLandmarks/PoseLandmarks dataclasses it produces, which is why that part
of Module 10 IS tested here despite this part not being.

Official model download (run once, save locally, then set the path below):
  Face:  https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task
  Pose:  https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task
(URLs per MediaPipe's official docs as of this writing — verify current
paths at https://ai.google.dev/edge/mediapipe/solutions/vision, they've
moved before.)
"""

import logging

from app.services.video.video_analyzer import FaceLandmarks, FrameAnalysis, PoseLandmarks, Point
from app.utils.exceptions import AppException

logger = logging.getLogger(__name__)

_face_landmarker = None
_pose_landmarker = None

# MediaPipe's face mesh landmark indices for the points video_analyzer.py
# needs (full 468-point topology at the docs link above)
_LEFT_IRIS_CENTER = 468
_RIGHT_IRIS_CENTER = 473
_LEFT_EYE_CORNERS = (33, 133)
_RIGHT_EYE_CORNERS = (362, 263)
_MOUTH_CORNERS = (61, 291)
_MOUTH_TOP_BOTTOM = (13, 14)
_NOSE_TIP = 1
_FOREHEAD = 10
_CHIN = 152
_FACE_EDGES = (234, 454)


class VideoModelUnavailableError(AppException):
    status_code = 503
    message = (
        "Video analysis models aren't downloaded. See SETUP.md for the official "
        "MediaPipe model download step — this is a one-time setup requirement."
    )


def _get_face_landmarker(model_path: str):
    global _face_landmarker
    if _face_landmarker is None:
        from mediapipe.tasks.python import vision
        from mediapipe.tasks import python as mp_python

        try:
            options = vision.FaceLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=model_path),
                num_faces=1,
            )
            _face_landmarker = vision.FaceLandmarker.create_from_options(options)
        except Exception as exc:
            logger.error("Failed to load face landmarker model from %s: %s", model_path, exc)
            raise VideoModelUnavailableError() from exc
    return _face_landmarker


def _get_pose_landmarker(model_path: str):
    global _pose_landmarker
    if _pose_landmarker is None:
        from mediapipe.tasks.python import vision
        from mediapipe.tasks import python as mp_python

        try:
            options = vision.PoseLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=model_path), num_poses=1
            )
            _pose_landmarker = vision.PoseLandmarker.create_from_options(options)
        except Exception as exc:
            logger.error("Failed to load pose landmarker model from %s: %s", model_path, exc)
            raise VideoModelUnavailableError() from exc
    return _pose_landmarker


def _point(landmark) -> Point:
    return Point(x=landmark.x, y=landmark.y, z=getattr(landmark, "z", 0.0))


def process_frame(frame_bgr, face_model_path: str, pose_model_path: str) -> FrameAnalysis:
    """frame_bgr: a single OpenCV-style BGR numpy array (one video frame)."""
    import mediapipe as mp

    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_bgr[:, :, ::-1])  # BGR -> RGB

    face_result = _get_face_landmarker(face_model_path).detect(mp_image)
    face_landmarks = None
    if face_result.face_landmarks:
        lm = face_result.face_landmarks[0]
        face_landmarks = FaceLandmarks(
            left_iris_center=_point(lm[_LEFT_IRIS_CENTER]),
            right_iris_center=_point(lm[_RIGHT_IRIS_CENTER]),
            left_eye_left_corner=_point(lm[_LEFT_EYE_CORNERS[0]]),
            left_eye_right_corner=_point(lm[_LEFT_EYE_CORNERS[1]]),
            right_eye_left_corner=_point(lm[_RIGHT_EYE_CORNERS[0]]),
            right_eye_right_corner=_point(lm[_RIGHT_EYE_CORNERS[1]]),
            mouth_left_corner=_point(lm[_MOUTH_CORNERS[0]]),
            mouth_right_corner=_point(lm[_MOUTH_CORNERS[1]]),
            mouth_top=_point(lm[_MOUTH_TOP_BOTTOM[0]]),
            mouth_bottom=_point(lm[_MOUTH_TOP_BOTTOM[1]]),
            nose_tip=_point(lm[_NOSE_TIP]),
            forehead=_point(lm[_FOREHEAD]),
            chin=_point(lm[_CHIN]),
            face_left_edge=_point(lm[_FACE_EDGES[0]]),
            face_right_edge=_point(lm[_FACE_EDGES[1]]),
        )

    pose_result = _get_pose_landmarker(pose_model_path).detect(mp_image)
    pose_landmarks = None
    if pose_result.pose_landmarks:
        lm = pose_result.pose_landmarks[0]
        # MediaPipe pose topology: 11=left shoulder, 12=right shoulder, 0=nose
        pose_landmarks = PoseLandmarks(left_shoulder=_point(lm[11]), right_shoulder=_point(lm[12]), nose=_point(lm[0]))

    return FrameAnalysis(face=face_landmarks, pose=pose_landmarks)
