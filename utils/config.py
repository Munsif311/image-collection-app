"""
config.py
=========
Centralised configuration for the Face Dataset Collection Application.
All tuneable constants live here so the rest of the codebase stays clean.
"""

import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATASET_ROOT = os.path.join(BASE_DIR, "dataset", "employees")
CSV_PATH = os.path.join(BASE_DIR, "dataset", "employees.csv")
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Make sure the critical directories exist at import time
for _d in (DATASET_ROOT, LOG_DIR):
    os.makedirs(_d, exist_ok=True)

# ---------------------------------------------------------------------------
# Image settings
# ---------------------------------------------------------------------------
FACE_SIZE = (224, 224)          # Output face crop dimensions (width, height)
IMAGE_FORMAT = "jpg"            # Output image file extension
IMAGE_QUALITY = 95              # JPEG quality (1-100)

# ---------------------------------------------------------------------------
# Haar Cascade for face detection
# ---------------------------------------------------------------------------
import cv2  # noqa: E402  (import here so config is importable before opencv)
HAAR_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
if not os.path.exists(HAAR_CASCADE_PATH):
    raise RuntimeError(
        f"Haar cascade file not found at {HAAR_CASCADE_PATH}. "
        "This usually means the installed OpenCV package does not ship "
        "the cascade data files. Install a compatible OpenCV release, "
        "for example opencv-python-headless<5.0.0."
    )

# Face detection parameters
SCALE_FACTOR = 1.1
MIN_NEIGHBOURS = 5
MIN_FACE_SIZE = (60, 60)        # Minimum face region to consider valid
FACE_PADDING = 0.20             # Fractional padding around the detected face bbox

# ---------------------------------------------------------------------------
# Guided capture pose sequence (20 poses)
# ---------------------------------------------------------------------------
POSES = [
    {
        "id": 1,
        "label": "Look Straight",
        "instruction": "Look directly at the camera with a neutral expression.",
        "emoji": "😐",
    },
    {
        "id": 2,
        "label": "Slight Left",
        "instruction": "Gently turn your head a little to the LEFT.",
        "emoji": "↙️",
    },
    {
        "id": 3,
        "label": "Left Profile",
        "instruction": "Turn your head fully to the LEFT so only your left cheek shows.",
        "emoji": "⬅️",
    },
    {
        "id": 4,
        "label": "Slight Right",
        "instruction": "Gently turn your head a little to the RIGHT.",
        "emoji": "↘️",
    },
    {
        "id": 5,
        "label": "Right Profile",
        "instruction": "Turn your head fully to the RIGHT so only your right cheek shows.",
        "emoji": "➡️",
    },
    {
        "id": 6,
        "label": "Look Up",
        "instruction": "Tilt your chin UP while keeping eyes on the camera lens.",
        "emoji": "⬆️",
    },
    {
        "id": 7,
        "label": "Look Down",
        "instruction": "Tilt your chin DOWN towards your chest.",
        "emoji": "⬇️",
    },
    {
        "id": 8,
        "label": "Smile",
        "instruction": "Give a natural, relaxed smile.",
        "emoji": "😊",
    },
    {
        "id": 9,
        "label": "Neutral Face",
        "instruction": "Return to a completely neutral expression — no smile.",
        "emoji": "😶",
    },
    {
        "id": 10,
        "label": "Blink",
        "instruction": "Close both eyes for half a second, then open them — capture while open.",
        "emoji": "😌",
    },
    {
        "id": 11,
        "label": "Move Closer",
        "instruction": "Move your face closer to the camera until it fills most of the frame.",
        "emoji": "🔍",
    },
    {
        "id": 12,
        "label": "Move Back",
        "instruction": "Move your face further from the camera so more of your shoulders show.",
        "emoji": "🔭",
    },
    {
        "id": 13,
        "label": "Slight Left + Smile",
        "instruction": "Slightly turn your head LEFT and smile at the same time.",
        "emoji": "😄",
    },
    {
        "id": 14,
        "label": "Slight Right + Smile",
        "instruction": "Slightly turn your head RIGHT and smile at the same time.",
        "emoji": "😁",
    },
    {
        "id": 15,
        "label": "Look Straight Again",
        "instruction": "Return to looking straight at the camera — neutral expression.",
        "emoji": "🎯",
    },
    {
        "id": 16,
        "label": "Turn Left Slowly",
        "instruction": "Slowly rotate your head to the LEFT — capture mid-turn.",
        "emoji": "🔄",
    },
    {
        "id": 17,
        "label": "Turn Right Slowly",
        "instruction": "Slowly rotate your head to the RIGHT — capture mid-turn.",
        "emoji": "🔃",
    },
    {
        "id": 18,
        "label": "Look Up Again",
        "instruction": "Tilt your head UP once more — slightly different angle from pose 6.",
        "emoji": "☝️",
    },
    {
        "id": 19,
        "label": "Look Down Again",
        "instruction": "Tilt your head DOWN once more — slightly different angle from pose 7.",
        "emoji": "👇",
    },
    {
        "id": 20,
        "label": "Final Straight Pose",
        "instruction": "Final image — look straight, relax, and give your best neutral face.",
        "emoji": "✅",
    },
]

TOTAL_POSES = len(POSES)

# ---------------------------------------------------------------------------
# CSV columns
# ---------------------------------------------------------------------------
CSV_COLUMNS = [
    "image",
    "employee_id",
    "employee_name",
    "department",
    "email",
    "pose_label",
    "captured_at",
]

# ---------------------------------------------------------------------------
# UI / App
# ---------------------------------------------------------------------------
APP_TITLE = "FaceID Dataset Studio"
APP_ICON = "📸"
APP_DESCRIPTION = (
    "A professional face dataset collection tool for the "
    "AI Employee Attendance System. Capture 20 guided poses "
    "in under two minutes — securely, from any browser."
)

# Bounding-box overlay colour in BGR
BBOX_COLOR_BGR = (0, 220, 110)      # green
BBOX_THICKNESS = 2
FONT_SCALE = 0.65
FONT_THICKNESS = 2

# ---------------------------------------------------------------------------
# Departments (used in selectbox)
# ---------------------------------------------------------------------------
DEPARTMENTS = [
    "Human Resources",
    "Information Technology",
    "Finance",
    "Operations",
    "Sales & Marketing",
    "Research & Development",
    "Legal",
    "Administration",
    "Customer Support",
    "Other",
]
