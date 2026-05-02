from __future__ import annotations

from pathlib import Path

from .config import VisualConfig
from .event import Event


class VisualBackendError(RuntimeError):
    pass


def _mark_visual_skipped(events: list[Event], reason: str) -> list[Event]:
    for event in events:
        event.reaction_score = 0.0
        event.reaction_type = None
        event.notes = event.notes or []
        event.notes.append(reason)
    return events


def _frame_diffs(frames: list[object]) -> list[float]:
    diffs: list[float] = []
    for previous, current in zip(frames, frames[1:]):
        import cv2
        import numpy as np

        diff = cv2.absdiff(previous, current)
        diffs.append(float(np.mean(diff) / 255.0))
    return diffs


def _read_cv2_frames(
    video_path: Path,
    start: float,
    end: float,
    config: VisualConfig,
    grayscale: bool = True,
) -> list[object]:
    import cv2

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        return []

    source_fps = capture.get(cv2.CAP_PROP_FPS) or 24.0
    stride = max(1, round(source_fps / max(1, config.fps)))
    start_frame = max(0, int(start * source_fps))
    end_frame = max(start_frame + 1, int(end * source_fps))

    frames: list[object] = []
    capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    frame_index = start_frame
    while frame_index <= end_frame:
        ok, frame = capture.read()
        if not ok:
            break
        if (frame_index - start_frame) % stride == 0:
            resized = cv2.resize(frame, (config.width, config.height))
            if grayscale:
                resized = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            frames.append(resized)
        frame_index += 1

    capture.release()
    return frames


def score_opencv_motion(video_path: Path, events: list[Event], config: VisualConfig) -> list[Event]:
    for event in events:
        start = max(0.0, event.t_start - config.context_before)
        end = event.t_end + config.context_after
        frames = _read_cv2_frames(video_path, start, end, config)
        if len(frames) < 2:
            event.reaction_score = 0.0
            event.reaction_type = None
            event.notes = event.notes or []
            event.notes.append("visual_skipped:opencv_frame_decode_failed")
            continue

        diffs = _frame_diffs(frames)
        peak = max(diffs, default=0.0)
        avg_diff = sum(diffs) / len(diffs) if diffs else 0.0
        # Sigmoid normalization to avoid saturation at 1.0 and detect scene cuts
        import math
        raw_score = peak / max(config.reaction_threshold, 0.001)
        # Use sigmoid for smooth scaling instead of hard ceiling
        score = 2.0 / (1.0 + math.exp(-raw_score)) - 1.0
        event.reaction_score = round(score, 3)
        # Detect hard scene cuts (peak >> avg indicates cut, not motion)
        is_scene_cut = peak > avg_diff * 3.0 if avg_diff > 0.01 else False
        if is_scene_cut:
            event.reaction_type = "scene_cut"  # Mark as cut, not reaction
            # Heavily discount scene cuts so they don't trigger false positives
            event.reaction_score = round(score * 0.2, 3)
            event.notes = event.notes or []
            event.notes.append("visual:scene_cut_detected")
        elif score >= config.opencv_motion_type_threshold:
            event.reaction_type = "scene_motion"
        else:
            event.reaction_type = None
    return events


def _landmark_vector(frame: object, pose: object, face_mesh: object) -> list[float] | None:
    import cv2
    import mediapipe as mp
    import numpy as np

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))

    pose_points: list[tuple[float, float]] = []
    face_points: list[tuple[float, float]] = []

    # Extract pose landmarks (head, shoulders)
    pose_result = pose.detect(image)
    if pose_result.pose_landmarks:
        pose_landmarks = pose_result.pose_landmarks[0]
        for index in (0, 11, 12):
            if index < len(pose_landmarks):
                landmark = pose_landmarks[index]
                pose_points.append((landmark.x, landmark.y))

    # Extract face landmarks (eyes, nose, mouth)
    face_result = face_mesh.detect(image)
    if face_result.face_landmarks:
        face = face_result.face_landmarks[0]
        for index in (1, 13, 14, 33, 263):
            if index < len(face):
                landmark = face[index]
                face_points.append((landmark.x, landmark.y))

    # Normalize pose and face independently, then combine
    vectors = []
    
    if len(pose_points) > 0:
        pose_array = np.array(pose_points, dtype=np.float32)
        pose_centroid = pose_array.mean(axis=0)
        pose_spread = np.linalg.norm(pose_array - pose_centroid, axis=1).mean() if len(pose_points) > 1 else 1.0
        pose_spread = max(float(pose_spread), 0.001)
        pose_normalized = (pose_array - pose_centroid) / pose_spread
        vectors.extend(pose_normalized.reshape(-1).tolist())
    
    if len(face_points) > 0:
        face_array = np.array(face_points, dtype=np.float32)
        face_centroid = face_array.mean(axis=0)
        face_spread = np.linalg.norm(face_array - face_centroid, axis=1).mean() if len(face_points) > 1 else 1.0
        face_spread = max(float(face_spread), 0.001)
        face_normalized = (face_array - face_centroid) / face_spread
        vectors.extend(face_normalized.reshape(-1).tolist())
    
    if not vectors:
        return None
    
    return vectors


def _vector_distance(a: list[float], b: list[float]) -> float:
    import math

    length = min(len(a), len(b))
    if length == 0:
        return 0.0
    return math.sqrt(sum((a[index] - b[index]) ** 2 for index in range(length)) / length)


def score_mediapipe_reactions(video_path: Path, events: list[Event], config: VisualConfig) -> list[Event]:
    try:
        import mediapipe as mp
    except ImportError as exc:
        raise VisualBackendError(
            "The MediaPipe backend requires the mediapipe package, which is not "
            "available in this Python environment. Use visual.backend='opencv_motion' "
            "for the runnable demo."
        ) from exc

    pose_model = Path(config.pose_model_path)
    face_model = Path(config.face_model_path)
    if not pose_model.exists() or not face_model.exists():
        raise VisualBackendError(
            "MediaPipe model files are missing. Expected "
            f"{pose_model} and {face_model}. Download them into the models directory."
        )

    vision = mp.tasks.vision
    base_options = mp.tasks.BaseOptions
    pose_options = vision.PoseLandmarkerOptions(
        base_options=base_options(model_asset_path=str(pose_model)),
        running_mode=vision.RunningMode.IMAGE,
        num_poses=1,
    )
    face_options = vision.FaceLandmarkerOptions(
        base_options=base_options(model_asset_path=str(face_model)),
        running_mode=vision.RunningMode.IMAGE,
        num_faces=1,
    )

    with (
        vision.PoseLandmarker.create_from_options(pose_options) as pose,
        vision.FaceLandmarker.create_from_options(face_options) as face_mesh,
    ):
        for event in events:
            start = max(0.0, event.t_start - config.context_before)
            end = event.t_end + config.context_after
            frames = _read_cv2_frames(video_path, start, end, config, grayscale=False)
            vectors = [
                vector
                for vector in (_landmark_vector(frame, pose, face_mesh) for frame in frames)
                if vector is not None
            ]

            if len(vectors) < 2:
                event.reaction_score = 0.0
                event.reaction_type = None
                event.notes = event.notes or []
                event.notes.append("visual_skipped:mediapipe_no_landmarks")
                continue

            baseline = vectors[0]
            peak_delta = max(_vector_distance(baseline, vector) for vector in vectors[1:])
            velocity = max(
                _vector_distance(previous, current)
                for previous, current in zip(vectors, vectors[1:])
            )
            raw_score = 0.65 * peak_delta + 0.35 * velocity
            score = min(1.0, raw_score / config.reaction_threshold)
            event.reaction_score = round(score, 3)
            if score >= 0.65:
                event.reaction_type = "landmark_reaction"
            elif score >= 0.35:
                event.reaction_type = "subtle_landmark_motion"
            else:
                event.reaction_type = None
    return events


def score_visual_reactions(
    video_path: Path | None,
    events: list[Event],
    config: VisualConfig,
) -> list[Event]:
    if video_path is None:
        return _mark_visual_skipped(events, "visual_skipped:no_video_input")

    if config.backend == "none":
        return _mark_visual_skipped(events, "visual_skipped:disabled")
    if config.backend == "opencv_motion":
        return score_opencv_motion(video_path, events, config)
    if config.backend == "mediapipe":
        return score_mediapipe_reactions(video_path, events, config)
    raise VisualBackendError(
        f"Unknown visual backend '{config.backend}'. Supported backends: opencv_motion, mediapipe, none."
    )
