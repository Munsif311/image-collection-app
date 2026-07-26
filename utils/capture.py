"""
capture.py
==========
High-level capture workflow helpers.
Bridges the face detector, storage layer, and CSV manager for the
main Streamlit UI to consume.
"""

import io
import logging
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image

from utils import csv_manager, storage
from utils.config import FACE_SIZE, IMAGE_FORMAT, IMAGE_QUALITY, POSES, TOTAL_POSES
from utils.face_detection import DetectionResult, FaceDetector, get_detector

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Image decoding helpers
# ---------------------------------------------------------------------------

def bytes_to_bgr(data: bytes) -> Optional[np.ndarray]:
    """
    Decode raw image bytes (e.g. from ``st.camera_input``) into a BGR
    numpy array.  Returns ``None`` on failure.
    """
    arr = np.frombuffer(data, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        logger.warning("bytes_to_bgr: cv2.imdecode returned None.")
    return bgr


def bgr_to_rgb(frame: np.ndarray) -> np.ndarray:
    """Convert BGR numpy array to RGB."""
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


def bgr_to_pil(frame: np.ndarray) -> Image.Image:
    """Convert BGR numpy array to a PIL Image (RGB)."""
    return Image.fromarray(bgr_to_rgb(frame))


def pil_to_bytes(img: Image.Image, fmt: str = "JPEG", quality: int = IMAGE_QUALITY) -> bytes:
    """Encode a PIL Image to bytes."""
    buf = io.BytesIO()
    img.save(buf, format=fmt, quality=quality)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Core capture action
# ---------------------------------------------------------------------------

def process_capture(
    raw_bytes: bytes,
    employee_id: str,
    employee_name: str,
    department: str,
    email: str,
    pose_index: int,
    employee_folder: str,
    image_index: int,
) -> Tuple[bool, str, Optional[np.ndarray]]:
    """
    Full pipeline for one capture:
      1. Decode the camera bytes.
      2. Run face detection.
      3. Crop + resize the face.
      4. Save the image to disk.
      5. Append a row to the master CSV.

    Parameters
    ----------
    raw_bytes       : bytes from ``st.camera_input``
    employee_id     : e.g. ``EMP001``
    employee_name   : full name
    department      : department string
    email           : optional email
    pose_index      : 0-based index into POSES list
    employee_folder : absolute path to the employee's folder
    image_index     : 1-based image number (determines filename)

    Returns
    -------
    (success, message, face_rgb_or_None)
    """
    # ---- 1. Decode ----
    bgr = bytes_to_bgr(raw_bytes)
    if bgr is None:
        return False, "Could not decode the camera image. Please try again.", None

    # ---- 2. Detect ----
    detector: FaceDetector = get_detector()
    result: DetectionResult = detector.detect(bgr)

    if result.status == "no_face":
        return False, result.message, None
    if result.status == "multiple_faces":
        return False, result.message, None

    face_box = result.primary_face

    # ---- 3. Crop ----
    face_bgr = detector.crop_face(bgr, face_box)
    if face_bgr is None:
        return False, "Face crop failed. Try repositioning yourself.", None

    # ---- 4. Save image ----
    saved_path = storage.save_face_image(face_bgr, employee_folder, image_index)
    if saved_path is None:
        return False, "Failed to save the image to disk. Check folder permissions.", None

    filename = f"img{image_index:03d}.{IMAGE_FORMAT}"

    # ---- 5. CSV ----
    pose_label = POSES[pose_index]["label"] if pose_index < TOTAL_POSES else "custom"
    try:
        csv_manager.append_record(
            image=filename,
            employee_id=employee_id,
            employee_name=employee_name,
            department=department,
            email=email,
            pose_label=pose_label,
        )
    except Exception as exc:
        logger.error("CSV append failed: %s", exc)
        # Not fatal — image is saved; log and continue

    face_rgb = bgr_to_rgb(face_bgr)
    msg = f"✅ Image {image_index} of {TOTAL_POSES} captured — **{pose_label}**"
    return True, msg, face_rgb


# ---------------------------------------------------------------------------
# Annotated preview helper
# ---------------------------------------------------------------------------

def get_annotated_preview(raw_bytes: bytes) -> Tuple[Optional[np.ndarray], str]:
    """
    Decode camera bytes, run detection, and return the *annotated* frame
    (RGB) together with a status message.  Used for the live preview panel.
    """
    bgr = bytes_to_bgr(raw_bytes)
    if bgr is None:
        return None, "Could not decode image."

    detector: FaceDetector = get_detector()
    result: DetectionResult = detector.detect(bgr)
    annotated_rgb = bgr_to_rgb(result.annotated_frame)
    return annotated_rgb, result.message
