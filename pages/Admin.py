"""
pages/Admin.py
==============
Admin Dashboard — view, search, download, and delete employee datasets.
Accessible via the Streamlit sidebar multi-page navigation.
"""

import io
import logging
import os
import zipfile

import pandas as pd
import streamlit as st

from utils import csv_manager, storage
from utils.config import APP_ICON, APP_TITLE, DATASET_ROOT, TOTAL_POSES

logger = logging.getLogger(__name__)

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title=f"Admin — {APP_TITLE}",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS (mirrors app.py) ────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #111827 50%, #0f0c29 100%);
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1035 0%, #12162b 100%);
        border-right: 1px solid rgba(139, 92, 246, 0.2);
    }
    section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }

    .admin-hero {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        border: 1px solid rgba(139,92,246,0.3);
        border-radius: 20px;
        padding: 2rem 2.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.4);
    }
    .admin-title {
        font-size: 2rem; font-weight: 800; color: #a78bfa;
    }
    .admin-sub { color: #64748b; font-size: 0.95rem; margin-top: 0.3rem; }

    div[data-testid="metric-container"] {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1.2rem 1.5rem;
        backdrop-filter: blur(10px);
    }
    div[data-testid="metric-container"] label {
        color: #a78bfa !important;
        font-size: 0.82rem; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.05em;
    }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #f0f4ff !important; font-weight: 700; font-size: 1.9rem;
    }

    .section-header {
        font-size: 1.15rem; font-weight: 700; color: #c4b5fd;
        margin: 1.5rem 0 0.8rem;
        padding-bottom: 0.4rem;
        border-bottom: 1px solid rgba(124,58,237,0.3);
    }

    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #4f46e5);
        color: #fff; border: none; border-radius: 12px;
        padding: 0.55rem 1.5rem; font-size: 0.9rem;
        font-weight: 600; width: 100%;
        box-shadow: 0 4px 15px rgba(124,58,237,0.35);
        transition: transform 0.15s, box-shadow 0.15s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(124,58,237,0.5);
    }

    .danger-btn > button {
        background: linear-gradient(135deg, #dc2626, #b91c1c) !important;
        box-shadow: 0 4px 15px rgba(220,38,38,0.35) !important;
    }
    .danger-btn > button:hover {
        box-shadow: 0 8px 25px rgba(220,38,38,0.5) !important;
    }

    .employee-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 0.8rem;
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    .employee-card:hover {
        border-color: rgba(124,58,237,0.35);
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    }
    .emp-name { font-size: 1.1rem; font-weight: 700; color: #e2e8f0; }
    .emp-meta { font-size: 0.82rem; color: #64748b; }

    .stTextInput > div > div > input {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 10px !important;
        color: #f0f4ff !important;
    }

    .stDataFrame { border-radius: 12px; overflow: hidden; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ═══════════════════════════════════════════════════════════════════════════
# Sidebar
# ═══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        f"""
        <div style="text-align:center; padding: 1.2rem 0 1.5rem;">
            <div style="font-size:2.5rem;">🛡️</div>
            <div style="font-size:1.1rem; font-weight:800; color:#c4b5fd;">Admin Panel</div>
            <div style="font-size:0.75rem; color:#64748b;">{APP_TITLE}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    stats = csv_manager.get_summary_stats()
    st.markdown(
        f"""
        <div style="color:#94a3b8; font-size:0.85rem; line-height:2.2;">
        🗄️ Total Images: <strong style="color:#c4b5fd">{stats['total_images']}</strong><br>
        👥 Employees: <strong style="color:#c4b5fd">{stats['total_employees']}</strong><br>
        🏢 Departments: <strong style="color:#c4b5fd">{stats['total_departments']}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    if st.button("🔃 Refresh Data", key="sidebar_refresh"):
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# Hero
# ═══════════════════════════════════════════════════════════════════════════
st.markdown(
    """
    <div class="admin-hero">
        <div class="admin-title">🛡️ Admin Dashboard</div>
        <div class="admin-sub">
            Manage the employee face dataset — view, search, download, and delete records.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════════════
# KPI metrics row
# ═══════════════════════════════════════════════════════════════════════════
stats = csv_manager.get_summary_stats()
col1, col2, col3, col4 = st.columns(4)
col1.metric("📸 Total Images", stats["total_images"])
col2.metric("👥 Total Employees", stats["total_employees"])
col3.metric("🏢 Departments", stats["total_departments"])
all_emp = storage.list_all_employees()
complete = sum(1 for e in all_emp if e["image_count"] >= TOTAL_POSES)
col4.metric("✅ Complete Datasets", complete)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════
# Tabs
# ═══════════════════════════════════════════════════════════════════════════
tab_all, tab_search, tab_detail = st.tabs(
    ["👥 All Employees", "🔍 Search", "📋 Master CSV"]
)


# ─────────────────────────────────────────────────────────────────────────
# Tab 1 — All Employees
# ─────────────────────────────────────────────────────────────────────────
with tab_all:
    st.markdown('<div class="section-header">👥 Registered Employees</div>', unsafe_allow_html=True)

    unique_emp_df = csv_manager.get_unique_employees()

    if unique_emp_df.empty:
        st.info("No employees found in the dataset yet. Capture some faces to get started.")
    else:
        # Summary table
        display_df = unique_emp_df.copy()
        display_df.index = range(1, len(display_df) + 1)
        st.dataframe(display_df, use_container_width=True)

        st.markdown(
            '<div class="section-header">🧑 Employee Actions</div>',
            unsafe_allow_html=True,
        )
        st.caption("Select an employee to view their images, download their dataset, or delete them.")

        emp_options = [
            f"{row['employee_id']} — {row['employee_name']}"
            for _, row in unique_emp_df.iterrows()
        ]
        selected_label = st.selectbox(
            "Select Employee", options=emp_options, key="admin_select_emp"
        )

        if selected_label:
            selected_id = selected_label.split(" — ")[0].strip()
            selected_row = unique_emp_df[unique_emp_df["employee_id"] == selected_id].iloc[0]
            emp_folder_path = storage.find_employee_folder_by_id(selected_id)

            # Employee detail card
            st.markdown(
                f"""
                <div class="employee-card">
                    <div class="emp-name">
                        👤 {selected_row['employee_name']}
                        &nbsp;<span style="color:#7c3aed; font-size:0.9rem;">
                            [{selected_row['employee_id']}]
                        </span>
                    </div>
                    <div class="emp-meta">
                        🏢 {selected_row['department']} &nbsp;|&nbsp;
                        ✉️ {selected_row.get('email', '—') or '—'} &nbsp;|&nbsp;
                        📸 {int(selected_row['image_count'])} images captured
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Image gallery for selected employee
            if emp_folder_path and os.path.isdir(emp_folder_path):
                img_paths = storage.list_employee_images(emp_folder_path)
                if img_paths:
                    st.markdown(
                        f'<div class="section-header" style="font-size:0.9rem;">🖼️ Image Gallery ({len(img_paths)} images)</div>',
                        unsafe_allow_html=True,
                    )
                    gallery_cols = st.columns(min(len(img_paths), 5))
                    for i, img_path in enumerate(img_paths):
                        rgb = storage.load_image_rgb(img_path)
                        if rgb is not None:
                            with gallery_cols[i % 5]:
                                st.image(rgb, caption=os.path.basename(img_path), use_container_width=True)
                else:
                    st.warning("No images found in this employee's folder.")
            else:
                st.warning("Employee folder not found on disk (CSV record may be an orphan).")

            # Action buttons
            st.markdown("<br>", unsafe_allow_html=True)
            btn_col1, btn_col2, btn_col3 = st.columns(3)

            with btn_col1:
                # Download ZIP
                if emp_folder_path and os.path.isdir(emp_folder_path):
                    img_paths = storage.list_employee_images(emp_folder_path)
                    if img_paths:
                        zip_buf = io.BytesIO()
                        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                            for ip in img_paths:
                                zf.write(ip, arcname=os.path.basename(ip))
                        zip_buf.seek(0)
                        st.download_button(
                            label=f"📦 Download {selected_id} ZIP",
                            data=zip_buf.getvalue(),
                            file_name=f"{os.path.basename(emp_folder_path)}_dataset.zip",
                            mime="application/zip",
                            use_container_width=True,
                            key=f"dl_zip_{selected_id}",
                        )

            with btn_col2:
                # Download employee CSV rows
                emp_records = csv_manager.get_employee_records(selected_id)
                if not emp_records.empty:
                    csv_bytes = emp_records.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label=f"📄 Download {selected_id} CSV",
                        data=csv_bytes,
                        file_name=f"{selected_id}_records.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key=f"dl_csv_{selected_id}",
                    )

            with btn_col3:
                # Delete employee
                with st.expander("⚠️ Delete Employee", expanded=False):
                    st.warning(
                        f"This will permanently delete all images and CSV records for "
                        f"**{selected_row['employee_name']}** ({selected_id})."
                    )
                    confirm_text = st.text_input(
                        f'Type "{selected_id}" to confirm deletion',
                        key=f"confirm_del_{selected_id}",
                    )
                    st.markdown('<div class="danger-btn">', unsafe_allow_html=True)
                    if st.button(
                        "🗑️ Permanently Delete", key=f"del_btn_{selected_id}", use_container_width=True
                    ):
                        if confirm_text.strip().upper() == selected_id.upper():
                            # Delete folder
                            if emp_folder_path:
                                storage.delete_employee_folder(emp_folder_path)
                            # Delete CSV rows
                            deleted = csv_manager.delete_employee_records(selected_id)
                            st.success(f"✅ Deleted {deleted} records and all images for {selected_id}.")
                            st.rerun()
                        else:
                            st.error("Confirmation text does not match. Deletion cancelled.")
                    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────
# Tab 2 — Search
# ─────────────────────────────────────────────────────────────────────────
with tab_search:
    st.markdown('<div class="section-header">🔍 Search Employees</div>', unsafe_allow_html=True)

    search_col1, search_col2 = st.columns(2)

    with search_col1:
        id_query = st.text_input(
            "Search by Employee ID",
            placeholder="e.g. EMP001",
            key="search_by_id",
        )
        if id_query.strip():
            results = csv_manager.search_by_id(id_query)
            if results.empty:
                st.warning(f'No employees found matching ID: "{id_query}"')
            else:
                st.success(f"Found {len(results)} result(s):")
                st.dataframe(results, use_container_width=True, hide_index=True)

    with search_col2:
        name_query = st.text_input(
            "Search by Employee Name",
            placeholder="e.g. Ali Khan",
            key="search_by_name",
        )
        if name_query.strip():
            results = csv_manager.search_by_name(name_query)
            if results.empty:
                st.warning(f'No employees found matching name: "{name_query}"')
            else:
                st.success(f"Found {len(results)} result(s):")
                st.dataframe(results, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Image count distribution
    unique_emp_df = csv_manager.get_unique_employees()
    if not unique_emp_df.empty and "image_count" in unique_emp_df.columns:
        st.markdown(
            '<div class="section-header">📊 Image Count Distribution</div>',
            unsafe_allow_html=True,
        )
        chart_df = unique_emp_df[["employee_name", "image_count"]].copy()
        chart_df = chart_df.rename(columns={"employee_name": "Employee", "image_count": "Images"})
        chart_df = chart_df.set_index("Employee")
        st.bar_chart(chart_df, color="#7c3aed")


# ─────────────────────────────────────────────────────────────────────────
# Tab 3 — Master CSV
# ─────────────────────────────────────────────────────────────────────────
with tab_detail:
    st.markdown('<div class="section-header">📋 Master CSV — employees.csv</div>', unsafe_allow_html=True)

    master_df = csv_manager.get_all_records()

    if master_df.empty:
        st.info("The master CSV is empty. No captures have been made yet.")
    else:
        # Filter widget
        dept_options = ["All Departments"] + sorted(master_df["department"].dropna().unique().tolist())
        dept_filter = st.selectbox("Filter by Department", dept_options, key="dept_filter")
        if dept_filter != "All Departments":
            master_df = master_df[master_df["department"] == dept_filter]

        st.dataframe(master_df, use_container_width=True, hide_index=True)
        st.caption(f"Showing {len(master_df)} records.")

    st.markdown("---")
    st.markdown('<div class="section-header">⬇️ Downloads</div>', unsafe_allow_html=True)

    dl_col1, dl_col2 = st.columns(2)

    with dl_col1:
        csv_bytes = csv_manager.get_csv_bytes()
        st.download_button(
            label="📄 Download employees.csv",
            data=csv_bytes,
            file_name="employees.csv",
            mime="text/csv",
            use_container_width=True,
            key="admin_dl_csv",
        )

    with dl_col2:
        # Full dataset ZIP (all employees)
        if os.path.isdir(DATASET_ROOT):
            all_images = []
            for emp_info in storage.list_all_employees():
                all_images.extend(storage.list_employee_images(emp_info["folder_path"]))

            if all_images:
                zip_buf = io.BytesIO()
                with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                    # Add CSV
                    from utils.config import CSV_PATH
                    if os.path.exists(CSV_PATH):
                        zf.write(CSV_PATH, arcname="employees.csv")
                    # Add images maintaining folder structure relative to DATASET_ROOT
                    for ip in all_images:
                        rel = os.path.relpath(ip, os.path.dirname(DATASET_ROOT))
                        zf.write(ip, arcname=rel)
                zip_buf.seek(0)
                st.download_button(
                    label="📦 Download Full Dataset (.zip)",
                    data=zip_buf.getvalue(),
                    file_name="face_dataset_full.zip",
                    mime="application/zip",
                    use_container_width=True,
                    key="admin_dl_full_zip",
                )
            else:
                st.info("No images in dataset yet.")
