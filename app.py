"""
app.py
======
FaceID Dataset Studio — Main Application
=========================================
Landing page + Guided capture workflow.

Run with:
    streamlit run app.py
"""

import logging
import os
import zipfile
import io
from typing import Optional

import streamlit as st

# ── Local imports ──────────────────────────────────────────────────────────
from utils.config import (
    APP_DESCRIPTION,
    APP_ICON,
    APP_TITLE,
    DEPARTMENTS,
    POSES,
    TOTAL_POSES,
)
from utils import csv_manager, storage
from utils.capture import get_annotated_preview, process_capture

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ── Page config (must be first Streamlit call) ─────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": f"**{APP_TITLE}** — AI Employee Attendance Dataset Tool",
    },
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Google Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ── Global reset ── */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ── Dark gradient background ── */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #111827 50%, #0f0c29 100%);
        min-height: 100vh;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1035 0%, #12162b 100%);
        border-right: 1px solid rgba(139, 92, 246, 0.2);
    }
    section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }

    /* ── Hero banner ── */
    .hero-banner {
        background: linear-gradient(135deg, #6d28d9 0%, #4f46e5 50%, #0ea5e9 100%);
        border-radius: 20px;
        padding: 2.5rem 3rem;
        margin-bottom: 2rem;
        box-shadow: 0 20px 60px rgba(109, 40, 217, 0.4);
        position: relative;
        overflow: hidden;
    }
    .hero-banner::before {
        content: "";
        position: absolute;
        top: -50%;
        right: -10%;
        width: 400px;
        height: 400px;
        background: rgba(255,255,255,0.05);
        border-radius: 50%;
    }
    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        color: #ffffff;
        margin: 0 0 0.5rem 0;
        letter-spacing: -0.02em;
    }
    .hero-sub {
        font-size: 1.05rem;
        color: rgba(255,255,255,0.85);
        max-width: 600px;
        line-height: 1.7;
    }

    /* ── Metric cards ── */
    div[data-testid="metric-container"] {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1.2rem 1.5rem;
        backdrop-filter: blur(10px);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(109,40,217,0.25);
    }
    div[data-testid="metric-container"] label {
        color: #a78bfa !important;
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #f0f4ff !important;
        font-weight: 700;
        font-size: 1.9rem;
    }

    /* ── Progress bar ── */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #7c3aed, #4f46e5, #0ea5e9);
        border-radius: 99px;
    }
    .stProgress > div > div {
        background: rgba(255,255,255,0.08);
        border-radius: 99px;
    }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #4f46e5);
        color: #ffffff;
        border: none;
        border-radius: 12px;
        padding: 0.65rem 2rem;
        font-size: 0.95rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        transition: transform 0.15s, box-shadow 0.15s, opacity 0.15s;
        box-shadow: 0 4px 15px rgba(124,58,237,0.4);
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(124,58,237,0.55);
        opacity: 0.95;
    }
    .stButton > button:active {
        transform: translateY(0px);
    }

    /* ── Camera input ── */
    div[data-testid="stCameraInput"] {
        border-radius: 16px;
        overflow: hidden;
        border: 2px solid rgba(124,58,237,0.35);
        box-shadow: 0 4px 30px rgba(0,0,0,0.3);
    }

    /* ── Input fields ── */
    .stTextInput > div > div > input,
    .stSelectbox > div > div {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 10px !important;
        color: #f0f4ff !important;
        font-size: 0.95rem;
    }
    .stTextInput > div > div > input:focus {
        border-color: #7c3aed !important;
        box-shadow: 0 0 0 3px rgba(124,58,237,0.25) !important;
    }

    /* ── Info / Success / Warning / Error cards ── */
    .stAlert {
        border-radius: 12px !important;
        border-left-width: 4px !important;
    }

    /* ── Pose instruction card ── */
    .pose-card {
        background: linear-gradient(135deg, rgba(109,40,217,0.2), rgba(79,70,229,0.15));
        border: 1px solid rgba(124,58,237,0.4);
        border-radius: 18px;
        padding: 1.8rem 2rem;
        margin: 1rem 0;
        text-align: center;
        backdrop-filter: blur(8px);
    }
    .pose-emoji { font-size: 3.5rem; line-height: 1; }
    .pose-label {
        font-size: 1.5rem;
        font-weight: 700;
        color: #c4b5fd;
        margin: 0.5rem 0 0.2rem;
    }
    .pose-instruction {
        font-size: 1rem;
        color: #94a3b8;
        line-height: 1.6;
    }

    /* ── Section headers ── */
    .section-header {
        font-size: 1.3rem;
        font-weight: 700;
        color: #c4b5fd;
        margin: 1.5rem 0 0.8rem;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid rgba(124,58,237,0.3);
    }

    /* ── Preview image frame ── */
    .preview-frame {
        border-radius: 14px;
        border: 2px solid rgba(14,165,233,0.4);
        overflow: hidden;
        box-shadow: 0 8px 30px rgba(0,0,0,0.4);
    }

    /* ── Step indicator badge ── */
    .step-badge {
        display: inline-block;
        background: linear-gradient(135deg, #7c3aed, #4f46e5);
        color: white;
        font-size: 0.8rem;
        font-weight: 700;
        padding: 0.3rem 0.9rem;
        border-radius: 99px;
        margin-bottom: 0.5rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }

    /* ── Final summary card ── */
    .summary-card {
        background: linear-gradient(135deg, rgba(16,185,129,0.15), rgba(6,182,212,0.1));
        border: 1px solid rgba(16,185,129,0.35);
        border-radius: 20px;
        padding: 2rem 2.5rem;
        text-align: center;
    }
    .summary-title {
        font-size: 1.8rem;
        font-weight: 800;
        color: #6ee7b7;
        margin-bottom: 0.5rem;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(124,58,237,0.4);
        border-radius: 99px;
    }

    /* ── Hide default Streamlit hamburger & footer ── */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════════════════════════════
# Session-state initialisation
# ═══════════════════════════════════════════════════════════════════════════

def _init_state() -> None:
    """Initialise all required session-state keys if absent."""
    defaults = {
        # Registration
        "reg_submitted": False,
        "employee_id": "",
        "employee_name": "",
        "department": "",
        "email": "",
        # Capture flow
        "capture_started": False,
        "pose_index": 0,
        "captured_images": [],      # list of RGB np arrays (for preview)
        "image_count": 0,
        "employee_folder": "",
        # Duplicate handling
        "dup_action": None,         # "continue" | "replace" | "cancel"
        "dup_checked": False,
        # Retake
        "pending_face_rgb": None,
        "pending_raw_bytes": None,
        "awaiting_retake_decision": False,
        # Completion
        "session_complete": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


_init_state()


# ═══════════════════════════════════════════════════════════════════════════
# Sidebar
# ═══════════════════════════════════════════════════════════════════════════

def _render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            f"""
            <div style="text-align:center; padding: 1.2rem 0 1.5rem;">
                <div style="font-size:3rem;">{APP_ICON}</div>
                <div style="font-size:1.2rem; font-weight:800; color:#c4b5fd;">
                    {APP_TITLE}
                </div>
                <div style="font-size:0.78rem; color:#64748b; margin-top:0.2rem;">
                    AI Attendance Dataset Tool
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # Navigation hint
        st.markdown(
            """
            <div class="section-header" style="font-size:0.9rem;">📌 Navigation</div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            "Use the **Admin** page (sidebar pages list) to view, search, "
            "download, or delete employee datasets."
        )

        st.markdown("---")

        # Live progress
        if st.session_state.capture_started and not st.session_state.session_complete:
            done = st.session_state.image_count
            pct = done / TOTAL_POSES
            st.markdown(
                f"""
                <div class="section-header" style="font-size:0.9rem;">🎯 Session Progress</div>
                """,
                unsafe_allow_html=True,
            )
            st.progress(pct, text=f"Image {done} of {TOTAL_POSES}")
            if st.session_state.employee_name:
                st.info(f"👤 **{st.session_state.employee_name}**")

            if st.button("🔄 Reset Session", key="sidebar_reset"):
                _reset_session()
                st.rerun()
        else:
            st.markdown(
                """
                <div style="color:#64748b; font-size:0.85rem; line-height:1.7;">
                📋 Register an employee<br>
                📸 Capture 20 guided poses<br>
                ✅ Dataset saved automatically
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # Quick stats
        stats = csv_manager.get_summary_stats()
        st.markdown(
            f"""
            <div class="section-header" style="font-size:0.9rem;">📊 Dataset Stats</div>
            <div style="color:#94a3b8; font-size:0.85rem; line-height:2;">
            🗄️ Total images: <strong style="color:#c4b5fd">{stats['total_images']}</strong><br>
            👥 Employees: <strong style="color:#c4b5fd">{stats['total_employees']}</strong><br>
            🏢 Departments: <strong style="color:#c4b5fd">{stats['total_departments']}</strong>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _reset_session() -> None:
    """Reset all capture-related session keys."""
    keys_to_reset = [
        "reg_submitted", "employee_id", "employee_name", "department", "email",
        "capture_started", "pose_index", "captured_images", "image_count",
        "employee_folder", "dup_action", "dup_checked",
        "pending_face_rgb", "pending_raw_bytes", "awaiting_retake_decision",
        "session_complete",
    ]
    for k in keys_to_reset:
        if k in st.session_state:
            del st.session_state[k]
    _init_state()


# ═══════════════════════════════════════════════════════════════════════════
# Section 1: Hero / Landing
# ═══════════════════════════════════════════════════════════════════════════

def _render_hero() -> None:
    st.markdown(
        f"""
        <div class="hero-banner">
            <div class="hero-title">{APP_ICON} {APP_TITLE}</div>
            <div class="hero-sub">{APP_DESCRIPTION}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)
    stats = csv_manager.get_summary_stats()
    col1.metric("📸 Total Images", stats["total_images"])
    col2.metric("👥 Employees", stats["total_employees"])
    col3.metric("🏢 Departments", stats["total_departments"])
    col4.metric("🎯 Poses / Session", TOTAL_POSES)


# ═══════════════════════════════════════════════════════════════════════════
# Section 2: Registration form
# ═══════════════════════════════════════════════════════════════════════════

def _render_registration() -> None:
    st.markdown(
        '<div class="section-header">📝 Employee Registration</div>',
        unsafe_allow_html=True,
    )

    with st.form("registration_form", clear_on_submit=False):
        col_a, col_b = st.columns(2)

        with col_a:
            emp_id = st.text_input(
                "Employee ID *",
                placeholder="e.g. EMP001",
                help="Unique identifier for the employee.",
            )
            emp_name = st.text_input(
                "Full Name *",
                placeholder="e.g. Ali Khan",
            )

        with col_b:
            dept = st.selectbox(
                "Department *",
                options=DEPARTMENTS,
                index=0,
            )
            email = st.text_input(
                "Email (optional)",
                placeholder="ali.khan@company.com",
            )

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.form_submit_button("🚀 Start Camera & Capture", use_container_width=True)

    if submitted:
        emp_id_val = emp_id.strip().upper()
        if not emp_id_val:
            st.error("❌ Employee ID is required.")
            return

        # Look up existing records for auto-resume
        records = csv_manager.get_employee_records(emp_id_val)
        
        if not records.empty:
            first_row = records.iloc[0]
            emp_name_val = emp_name.strip() or first_row["employee_name"]
            dept_val = dept or first_row["department"]
            email_val = email.strip() or str(first_row.get("email", ""))
            
            num_images = len(records)
            if num_images < TOTAL_POSES:
                # AUTO RESUME
                st.session_state.employee_name = emp_name_val
                st.session_state.department = dept_val
                st.session_state.email = email_val
                
                emp_folder = storage.find_employee_folder_by_id(emp_id_val)
                st.session_state.employee_folder = emp_folder
                
                captured = []
                if emp_folder:
                    img_paths = sorted(storage.list_employee_images(emp_folder))
                    for p in img_paths:
                        rgb = storage.load_image_rgb(p)
                        if rgb is not None:
                            captured.append(rgb)
                
                st.session_state.captured_images = captured
                st.session_state.image_count = len(captured)
                st.session_state.pose_index = len(captured)
                
                st.session_state.employee_id = emp_id_val
                st.session_state.reg_submitted = True
                st.session_state.dup_checked = True 
                st.session_state.capture_started = True
                st.rerun()
        else:
            emp_name_val = emp_name.strip()
            dept_val = dept
            email_val = email.strip()

        errors = []
        if not emp_name_val:
            errors.append("Employee Name is required.")
        if not dept_val:
            errors.append("Department is required.")

        if errors:
            for e in errors:
                st.error(f"❌ {e}")
            return

        # Store in session state for a new capture or full dataset
        st.session_state.employee_id = emp_id_val
        st.session_state.employee_name = emp_name_val
        st.session_state.department = dept_val
        st.session_state.email = email_val
        st.session_state.reg_submitted = True
        st.session_state.dup_checked = False
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# Section 3: Duplicate check
# ═══════════════════════════════════════════════════════════════════════════

def _render_duplicate_check() -> bool:
    """
    Show duplicate-handling UI if needed.
    Returns True when it is safe to proceed to capture.
    """
    emp_id = st.session_state.employee_id
    emp_name = st.session_state.employee_name

    if st.session_state.dup_checked:
        return True

    # Check both CSV and folder
    id_in_csv = csv_manager.employee_id_exists(emp_id)
    folder_exists = storage.employee_exists(emp_id, emp_name)

    if not id_in_csv and not folder_exists:
        st.session_state.dup_checked = True
        return True

    # --- Duplicate found ---
    st.markdown(
        f"""
        <div style="
            background: rgba(245,158,11,0.12);
            border: 1px solid rgba(245,158,11,0.4);
            border-radius: 16px;
            padding: 1.5rem 2rem;
            margin-bottom: 1rem;
        ">
            <div style="font-size:1.3rem; font-weight:700; color:#fbbf24;">
                ⚠️ Employee Already Exists
            </div>
            <div style="color:#94a3b8; margin-top:0.4rem;">
                A dataset for <strong style="color:#fbbf24">{emp_id}</strong>
                — {emp_name} was found.
                What would you like to do?
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("➕ Add More Images", key="dup_continue", use_container_width=True):
            st.session_state.dup_action = "continue"
            st.session_state.dup_checked = True
            st.rerun()
    with col2:
        if st.button("🔁 Replace Existing Dataset", key="dup_replace", use_container_width=True):
            st.session_state.dup_action = "replace"
            st.session_state.dup_checked = True
            st.rerun()
    with col3:
        if st.button("❌ Cancel", key="dup_cancel", use_container_width=True):
            _reset_session()
            st.rerun()

    return False


def _apply_duplicate_action() -> None:
    """Execute the chosen duplicate action (delete old data if replacing)."""
    action = st.session_state.dup_action
    if action != "replace":
        return

    emp_id = st.session_state.employee_id
    emp_name = st.session_state.employee_name

    # Delete folder contents
    existing_folder = storage.find_employee_folder_by_id(emp_id)
    if existing_folder:
        storage.clear_employee_folder(existing_folder)

    # Delete CSV rows
    csv_manager.delete_employee_records(emp_id)
    st.session_state.dup_action = None


# ═══════════════════════════════════════════════════════════════════════════
# Section 4: Guided capture flow
# ═══════════════════════════════════════════════════════════════════════════

def _ensure_employee_folder() -> None:
    """Create the employee folder and store it in session state."""
    if not st.session_state.employee_folder:
        folder = storage.get_employee_folder(
            st.session_state.employee_id,
            st.session_state.employee_name,
        )
        st.session_state.employee_folder = folder


def _render_capture_header() -> None:
    """Progress bar and image counter at the top of capture section."""
    done = st.session_state.image_count
    pct = done / TOTAL_POSES

    st.markdown(
        f"""
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.3rem;
        ">
            <span style="color:#a78bfa; font-weight:600;">
                📸 Image {done} of {TOTAL_POSES}
            </span>
            <span style="color:#64748b; font-size:0.9rem;">
                {int(pct * 100)}% complete
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(pct)


def _render_pose_card(pose_index: int) -> None:
    """Render the current pose instruction card."""
    pose = POSES[pose_index]
    st.markdown(
        f"""
        <div class="pose-card">
            <div class="step-badge">Step {pose['id']} of {TOTAL_POSES}</div>
            <div class="pose-emoji">{pose['emoji']}</div>
            <div class="pose-label">{pose['label']}</div>
            <div class="pose-instruction">{pose['instruction']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_capture_ui() -> None:
    """Main guided capture interface."""
    _ensure_employee_folder()
    _apply_duplicate_action()

    pose_index: int = st.session_state.pose_index
    image_count: int = st.session_state.image_count
    employee_folder: str = st.session_state.employee_folder

    _render_capture_header()

    st.markdown("<br>", unsafe_allow_html=True)
    left_col, right_col = st.columns([1.05, 0.95], gap="large")

    with left_col:
        # ── Pose instruction ──
        _render_pose_card(pose_index)

        # ── Camera input ──
        st.markdown(
            '<div class="section-header" style="font-size:0.95rem;">📷 Camera</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "Allow browser camera access when prompted. "
            "Adjust your pose, then click **Capture Photo** below."
        )

        camera_image = st.camera_input(
            label="Live Camera",
            label_visibility="collapsed",
            key=f"camera_{pose_index}_{image_count}",
        )

        # ── Retake decision ──
        if st.session_state.awaiting_retake_decision:
            _render_retake_decision(employee_folder, pose_index, image_count)
            return

        # ── Capture button ──
        if camera_image is not None:
            if st.button(
                f"📸 Capture Pose {pose_index + 1}: {POSES[pose_index]['label']}",
                key=f"btn_capture_{pose_index}",
                use_container_width=True,
            ):
                raw_bytes = camera_image.getvalue()
                success, message, face_rgb = process_capture(
                    raw_bytes=raw_bytes,
                    employee_id=st.session_state.employee_id,
                    employee_name=st.session_state.employee_name,
                    department=st.session_state.department,
                    email=st.session_state.email,
                    pose_index=pose_index,
                    employee_folder=employee_folder,
                    image_index=image_count + 1,
                )

                if success:
                    # Store pending result for retake prompt
                    st.session_state.pending_face_rgb = face_rgb
                    st.session_state.pending_raw_bytes = raw_bytes
                    st.session_state.awaiting_retake_decision = True
                    st.rerun()
                else:
                    st.error(message)
        else:
            st.info("👆 The camera preview will appear above — click the camera icon to take a photo.")

    with right_col:
        # ── Captured gallery ──
        _render_gallery()


def _render_retake_decision(
    employee_folder: str, pose_index: int, image_count: int
) -> None:
    """
    Show the captured face crop and ask the user to Save or Retake.
    This step is shown after a successful process_capture() call.
    Note: process_capture() has already saved to disk and CSV.
    We need to handle the "Retake" case by deleting and re-shooting.
    """
    face_rgb = st.session_state.pending_face_rgb

    st.success(f"✅ **Pose {pose_index + 1}** captured! Review below.")

    if face_rgb is not None:
        st.markdown(
            '<div class="section-header" style="font-size:0.95rem;">🖼️ Captured Face Preview</div>',
            unsafe_allow_html=True,
        )
        st.image(face_rgb, caption="Cropped face (224 × 224)", width=280)

    col_save, col_retake = st.columns(2)
    with col_save:
        if st.button("✅ Save & Continue to Next Pose", key="btn_save", use_container_width=True):
            # Commit: advance counters
            st.session_state.image_count += 1
            st.session_state.pose_index += 1
            if face_rgb is not None:
                st.session_state.captured_images.append(face_rgb)

            st.session_state.pending_face_rgb = None
            st.session_state.pending_raw_bytes = None
            st.session_state.awaiting_retake_decision = False

            if st.session_state.pose_index >= TOTAL_POSES:
                st.session_state.session_complete = True

            st.rerun()

    with col_retake:
        if st.button("🔄 Retake This Photo", key="btn_retake", use_container_width=True):
            # Delete the just-saved image and CSV row
            img_index = image_count + 1
            img_filename = f"img{img_index:03d}.jpg"
            img_path = os.path.join(employee_folder, img_filename)
            if os.path.exists(img_path):
                try:
                    os.remove(img_path)
                except OSError as exc:
                    logger.warning("Retake: could not remove %s: %s", img_path, exc)

            # Remove last CSV row for this employee
            df = csv_manager.get_employee_records(st.session_state.employee_id)
            if not df.empty:
                from utils.config import CSV_PATH, CSV_COLUMNS
                import pandas as pd
                all_df = csv_manager.get_all_records()
                emp_mask = all_df["employee_id"] == st.session_state.employee_id
                img_mask = all_df["image"] == img_filename
                drop_mask = emp_mask & img_mask
                all_df = all_df[~drop_mask]
                all_df.to_csv(CSV_PATH, index=False)

            st.session_state.pending_face_rgb = None
            st.session_state.pending_raw_bytes = None
            st.session_state.awaiting_retake_decision = False
            st.rerun()


def _render_gallery() -> None:
    """Show thumbnails of already-captured images."""
    captured = st.session_state.captured_images
    if not captured:
        st.markdown(
            """
            <div style="
                background: rgba(255,255,255,0.03);
                border: 1px dashed rgba(255,255,255,0.1);
                border-radius: 16px;
                padding: 3rem 2rem;
                text-align: center;
                color: #475569;
                font-size: 0.9rem;
            ">
                📷 Captured images will appear here as you progress.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f'<div class="section-header" style="font-size:0.95rem;">🖼️ Captured Gallery ({len(captured)} / {TOTAL_POSES})</div>',
        unsafe_allow_html=True,
    )

    # Display in rows of 4
    cols = st.columns(4)
    for idx, face_rgb in enumerate(captured):
        pose_name = POSES[idx]["label"] if idx < TOTAL_POSES else f"Image {idx+1}"
        with cols[idx % 4]:
            st.image(face_rgb, caption=f"#{idx+1} {pose_name}", width=90)


# ═══════════════════════════════════════════════════════════════════════════
# Section 5: Final summary
# ═══════════════════════════════════════════════════════════════════════════

def _render_final_summary() -> None:
    st.balloons()

    emp_id = st.session_state.employee_id
    emp_name = st.session_state.employee_name
    dept = st.session_state.department
    count = st.session_state.image_count
    folder = st.session_state.employee_folder

    st.markdown(
        f"""
        <div class="summary-card">
            <div style="font-size:3rem; margin-bottom:0.5rem;">🎉</div>
            <div class="summary-title">Dataset Created Successfully!</div>
            <div style="color:#94a3b8; font-size:0.95rem;">
                All {count} images have been saved and the master CSV has been updated.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👤 Employee", emp_name)
    col2.metric("🆔 ID", emp_id)
    col3.metric("🏢 Department", dept)
    col4.metric("📸 Images", count)

    st.markdown("<br>", unsafe_allow_html=True)

    # Dataset folder info
    st.info(f"📁 **Dataset Folder:** `{folder}`")

    # Pose breakdown table
    captured = st.session_state.captured_images
    if captured:
        import pandas as pd
        rows = []
        for i, _ in enumerate(captured):
            pose = POSES[i] if i < TOTAL_POSES else {"id": i + 1, "label": f"Image {i+1}", "emoji": "📷"}
            rows.append({
                "No.": pose["id"],
                "Pose": f"{pose['emoji']}  {pose['label']}",
                "Filename": f"img{i+1:03d}.jpg",
                "Status": "✅ Saved",
            })
        import pandas as pd
        df = pd.DataFrame(rows)
        st.markdown(
            '<div class="section-header">📋 Captured Image Summary</div>',
            unsafe_allow_html=True,
        )
        st.dataframe(df, use_container_width=True, hide_index=True)

    # Download ZIP of the employee's images
    st.markdown("### ⬇️ Download Dataset")
    col_dl1, col_dl2 = st.columns(2)

    with col_dl1:
        if os.path.isdir(folder):
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for img_path in storage.list_employee_images(folder):
                    zf.write(img_path, arcname=os.path.basename(img_path))
            zip_buf.seek(0)
            safe_folder = os.path.basename(folder)
            st.download_button(
                label=f"📦 Download {emp_id} Images (.zip)",
                data=zip_buf.getvalue(),
                file_name=f"{safe_folder}_dataset.zip",
                mime="application/zip",
                use_container_width=True,
            )

    with col_dl2:
        csv_bytes = csv_manager.get_csv_bytes()
        st.download_button(
            label="📄 Download employees.csv",
            data=csv_bytes,
            file_name="employees.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Start New Session", use_container_width=True, key="btn_new_session"):
        _reset_session()
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# Main render orchestrator
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    _render_sidebar()
    _render_hero()
    st.markdown("---")

    # ── Flow control ────────────────────────────────────────────────────
    if st.session_state.session_complete:
        _render_final_summary()
        return

    if not st.session_state.reg_submitted:
        _render_registration()
        return

    # Duplicate check phase
    if not st.session_state.dup_checked:
        if not _render_duplicate_check():
            return

    # Capture phase
    _render_capture_ui()


if __name__ == "__main__":
    main()
