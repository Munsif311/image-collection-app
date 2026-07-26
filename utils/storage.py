"""
storage.py
==========
File-system helpers: folder creation, image saving, employee lookup,
duplicate detection, and dataset deletion.
"""

import logging
import os
import re
import shutil
from typing import List, Optional

import cv2
import numpy as np

from utils.config import DATASET_ROOT, FACE_SIZE, IMAGE_FORMAT, IMAGE_QUALITY

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Naming helpers
# ---------------------------------------------------------------------------

def _sanitize(value: str) -> str:
    """Replace characters unsafe for folder/file names with underscores."""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return cleaned.strip("_") or "unknown"


def build_employee_folder_name(employee_id: str, employee_name: str) -> str:
    """
    Return a deterministic folder name for an employee.

    Example: ``EMP001_Ali_Khan``
    """
    safe_id = _sanitize(employee_id.upper())
    safe_name = _sanitize(employee_name)
    return f"{safe_id}_{safe_name}"


def get_employee_folder(employee_id: str, employee_name: str) -> str:
    """
    Return the *absolute* path of the employee's dataset folder.
    The folder is created if it does not already exist.
    """
    folder_name = build_employee_folder_name(employee_id, employee_name)
    path = os.path.join(DATASET_ROOT, folder_name)
    os.makedirs(path, exist_ok=True)
    return path


# ---------------------------------------------------------------------------
# Image I/O
# ---------------------------------------------------------------------------

def save_face_image(
    face_bgr: np.ndarray,
    employee_folder: str,
    image_index: int,
) -> Optional[str]:
    """
    Save a 224×224 BGR face crop as ``img{index:03d}.jpg``.

    Returns the *absolute* file path on success, or ``None`` on failure.
    """
    filename = f"img{image_index:03d}.{IMAGE_FORMAT}"
    filepath = os.path.join(employee_folder, filename)

    # Ensure the face is the correct size before writing
    if face_bgr.shape[:2] != (FACE_SIZE[1], FACE_SIZE[0]):
        face_bgr = cv2.resize(face_bgr, FACE_SIZE, interpolation=cv2.INTER_AREA)

    encode_params = [cv2.IMWRITE_JPEG_QUALITY, IMAGE_QUALITY]
    success, encoded = cv2.imencode(".jpg", face_bgr, encode_params)
    if not success:
        logger.error("cv2.imencode failed for %s", filepath)
        return None

    try:
        with open(filepath, "wb") as f:
            f.write(encoded.tobytes())
        logger.debug("Saved face image: %s", filepath)
        return filepath
    except OSError as exc:
        logger.error("Could not write %s: %s", filepath, exc)
        return None


def load_image_rgb(path: str) -> Optional[np.ndarray]:
    """Load an image from *path* and return it as an RGB numpy array."""
    bgr = cv2.imread(path)
    if bgr is None:
        return None
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


# ---------------------------------------------------------------------------
# Employee existence checks
# ---------------------------------------------------------------------------

def employee_exists(employee_id: str, employee_name: str) -> bool:
    """Return True if the employee folder already exists and contains images."""
    folder = os.path.join(
        DATASET_ROOT, build_employee_folder_name(employee_id, employee_name)
    )
    if not os.path.isdir(folder):
        return False
    images = list_employee_images(folder)
    return len(images) > 0


def find_employee_folder_by_id(employee_id: str) -> Optional[str]:
    """
    Search DATASET_ROOT for any folder whose name starts with the given
    employee ID (case-insensitive).  Returns the folder path or None.
    """
    safe_id = _sanitize(employee_id.upper())
    if not os.path.isdir(DATASET_ROOT):
        return None
    for entry in os.scandir(DATASET_ROOT):
        if entry.is_dir() and entry.name.upper().startswith(safe_id):
            return entry.path
    return None


# ---------------------------------------------------------------------------
# Listing helpers
# ---------------------------------------------------------------------------

def list_employee_images(folder: str) -> List[str]:
    """Return a sorted list of absolute image paths inside *folder*."""
    if not os.path.isdir(folder):
        return []
    exts = {".jpg", ".jpeg", ".png"}
    paths = [
        os.path.join(folder, f)
        for f in sorted(os.listdir(folder))
        if os.path.splitext(f)[1].lower() in exts
    ]
    return paths


def list_all_employees() -> List[dict]:
    """
    Return metadata dicts for every employee found in DATASET_ROOT.

    Each dict contains: folder_name, folder_path, image_count.
    """
    results = []
    if not os.path.isdir(DATASET_ROOT):
        return results

    for entry in sorted(os.scandir(DATASET_ROOT), key=lambda e: e.name):
        if not entry.is_dir():
            continue
        images = list_employee_images(entry.path)
        results.append(
            {
                "folder_name": entry.name,
                "folder_path": entry.path,
                "image_count": len(images),
            }
        )
    return results


# ---------------------------------------------------------------------------
# Destructive operations
# ---------------------------------------------------------------------------

def delete_employee_folder(folder_path: str) -> bool:
    """
    Permanently delete the employee's dataset folder.

    Returns True on success, False if the folder did not exist.
    """
    if not os.path.isdir(folder_path):
        logger.warning("delete_employee_folder: folder not found: %s", folder_path)
        return False
    try:
        shutil.rmtree(folder_path)
        logger.info("Deleted employee folder: %s", folder_path)
        return True
    except OSError as exc:
        logger.error("Could not delete %s: %s", folder_path, exc)
        return False


def clear_employee_folder(folder_path: str) -> int:
    """
    Remove all images from an employee folder without deleting the folder.

    Returns the number of files deleted.
    """
    count = 0
    for img_path in list_employee_images(folder_path):
        try:
            os.remove(img_path)
            count += 1
        except OSError as exc:
            logger.warning("Could not remove %s: %s", img_path, exc)
    logger.info("Cleared %d images from %s", count, folder_path)
    return count
