"""
face_detection.py
=================
Face detection utilities using OpenCV Haar Cascades.
Returns cropped, resized 224×224 face images ready for storage.
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import cv2
import numpy as np

from utils.config import (
    BBOX_COLOR_BGR,
    BBOX_THICKNESS,
    FACE_PADDING,
    FACE_SIZE,
    FONT_SCALE,
    FONT_THICKNESS,
    HAAR_CASCADE_PATH,
    MIN_FACE_SIZE,
    MIN_NEIGHBOURS,
    SCALE_FACTOR,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class FaceBox:
    """Axis-aligned bounding box of a detected face."""
    x: int
    y: int
    w: int
    h: int

    @property
    def area(self) -> int:
        return self.w * self.h

    def as_tuple(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.w, self.h)


@dataclass
class DetectionResult:
    """Result of running the face detector on a single frame."""
    faces: List[FaceBox] = field(default_factory=list)
    annotated_frame: Optional[np.ndarray] = None
    status: str = "no_face"          # "ok" | "no_face" | "multiple_faces"
    message: str = "No face detected."

    @property
    def face_count(self) -> int:
        return len(self.faces)

    @property
    def primary_face(self) -> Optional[FaceBox]:
        """Return the largest face box if exactly one face is present."""
        if self.face_count == 1:
            return self.faces[0]
        return None


# ---------------------------------------------------------------------------
# Detector class
# ---------------------------------------------------------------------------

class FaceDetector:
    """
    Wrapper around the OpenCV Haar Cascade frontal-face detector.

    Usage
    -----
    detector = FaceDetector()
    result   = detector.detect(bgr_frame)
    if result.status == "ok":
        cropped = detector.crop_face(bgr_frame, result.primary_face)
    """

    def __init__(self) -> None:
        self._cascade = cv2.CascadeClassifier(HAAR_CASCADE_PATH)
        if self._cascade.empty():
            raise RuntimeError(
                f"Failed to load Haar Cascade from: {HAAR_CASCADE_PATH}"
            )
        logger.info("FaceDetector initialised with cascade: %s", HAAR_CASCADE_PATH)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, frame: np.ndarray) -> DetectionResult:
        """
        Detect faces in *frame* (BGR numpy array).

        Returns a :class:`DetectionResult` with bounding boxes and an
        annotated copy of the frame.
        """
        if frame is None or frame.size == 0:
            return DetectionResult(status="no_face", message="Empty frame received.")

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        raw = self._cascade.detectMultiScale(
            gray,
            scaleFactor=SCALE_FACTOR,
            minNeighbors=MIN_NEIGHBOURS,
            minSize=MIN_FACE_SIZE,
        )

        boxes: List[FaceBox] = []
        if len(raw):
            for (x, y, w, h) in raw:
                boxes.append(FaceBox(int(x), int(y), int(w), int(h)))

        # Sort largest-first so primary_face returns the dominant face
        boxes.sort(key=lambda b: b.area, reverse=True)

        result = DetectionResult(faces=boxes)
        result.annotated_frame = self._annotate(frame.copy(), boxes)

        if len(boxes) == 0:
            result.status = "no_face"
            result.message = "⚠️ No face detected. Please position your face in the frame."
        elif len(boxes) > 1:
            result.status = "multiple_faces"
            result.message = "⚠️ Multiple faces detected. Only one person should be visible."
        else:
            result.status = "ok"
            result.message = "✅ Face detected. Ready to capture."

        return result

    def crop_face(
        self,
        frame: np.ndarray,
        box: FaceBox,
        target_size: Tuple[int, int] = FACE_SIZE,
        padding: float = FACE_PADDING,
    ) -> Optional[np.ndarray]:
        """
        Crop the face region from *frame* with optional padding,
        then resize to *target_size* (width, height).

        Returns the cropped image or None if the crop is degenerate.
        """
        h_frame, w_frame = frame.shape[:2]
        pad_x = int(box.w * padding)
        pad_y = int(box.h * padding)

        x1 = max(0, box.x - pad_x)
        y1 = max(0, box.y - pad_y)
        x2 = min(w_frame, box.x + box.w + pad_x)
        y2 = min(h_frame, box.y + box.h + pad_y)

        crop = frame[y1:y2, x1:x2]
        if crop.size == 0:
            logger.warning("Degenerate face crop — skipping.")
            return None

        resized = cv2.resize(crop, target_size, interpolation=cv2.INTER_AREA)
        return resized

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _annotate(frame: np.ndarray, boxes: List[FaceBox]) -> np.ndarray:
        """Draw bounding boxes and status text onto *frame* (in-place)."""
        for box in boxes:
            cv2.rectangle(
                frame,
                (box.x, box.y),
                (box.x + box.w, box.y + box.h),
                BBOX_COLOR_BGR,
                BBOX_THICKNESS,
            )

        n = len(boxes)
        if n == 0:
            label = "No face detected"
            colour = (0, 60, 220)
        elif n == 1:
            label = "Face detected"
            colour = BBOX_COLOR_BGR
        else:
            label = f"{n} faces — keep only one"
            colour = (0, 140, 255)

        cv2.putText(
            frame,
            label,
            (10, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            FONT_SCALE,
            colour,
            FONT_THICKNESS,
            cv2.LINE_AA,
        )
        return frame


# ---------------------------------------------------------------------------
# Module-level singleton (lazy-initialised)
# ---------------------------------------------------------------------------
_detector_instance: Optional[FaceDetector] = None


def get_detector() -> FaceDetector:
    """Return the module-level singleton :class:`FaceDetector`."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = FaceDetector()
    return _detector_instance
