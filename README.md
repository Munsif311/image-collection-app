# FaceID Dataset Studio

A **production-ready Streamlit web application** for collecting face image datasets to power an AI Employee Attendance System.

Users open the app link in any browser, fill in their information, allow camera access, and capture **20 guided face poses** in under two minutes. All images are automatically cropped to **224 × 224 px**, organised into labelled folders, and logged in a master CSV.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🎯 Guided capture | 20 distinct head poses with on-screen instructions |
| 🤖 Face detection | OpenCV Haar Cascade — detects single faces, rejects multiples |
| 🖼️ Face crop | Padded crop → 224 × 224 JPEG |
| 📋 CSV logging | Appended master `employees.csv` with pose labels & timestamps |
| 🔁 Retake | Review each cropped face before committing |
| 🧹 Duplicate check | Continue, replace, or cancel if employee already exists |
| 🛡️ Admin dashboard | View, search, download ZIP/CSV, delete employees |
| 📦 One-click download | Per-employee or full-dataset ZIP |
| 🌙 Dark UI | Inter font, violet gradient theme, glassmorphism cards |
| ☁️ Cloud-ready | Works on Streamlit Community Cloud out of the box |

---

## 🗂️ Project Structure

```
attendance_dataset_app/
├── app.py                  ← Main application (landing + capture)
├── pages/
│   └── Admin.py            ← Admin dashboard
├── utils/
│   ├── __init__.py
│   ├── config.py           ← All configuration constants
│   ├── face_detection.py   ← OpenCV Haar Cascade face detector
│   ├── capture.py          ← Capture pipeline (decode → detect → crop → save → CSV)
│   ├── storage.py          ← File-system helpers
│   └── csv_manager.py      ← Thread-safe CSV read/write
├── dataset/
│   ├── employees/          ← Auto-created: one sub-folder per employee
│   └── employees.csv       ← Auto-created master CSV
├── .streamlit/
│   └── config.toml         ← Streamlit theme
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start (Local)

```bash
# 1. Clone / enter the project folder
cd attendance_dataset_app

# 2. Create a virtual environment (recommended)
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## ☁️ Deploy on Streamlit Community Cloud

1. Push this folder to a **public GitHub repository**.
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Set:
   - **Repository**: your repo
   - **Branch**: `main`
   - **Main file path**: `attendance_dataset_app/app.py`  
     *(or `app.py` if the repo root is the project folder)*
4. Click **Deploy** — done!

> **Note**: Streamlit Community Cloud has an **ephemeral file system** — uploaded images are lost when the app restarts. For production persistence use **Google Drive**, **AWS S3**, or a database. See the [Streamlit file storage guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app).

---

## 📁 Dataset Output

```
dataset/
└── employees/
    ├── EMP001_Ali_Khan/
    │   ├── img001.jpg   ← Look Straight
    │   ├── img002.jpg   ← Slight Left
    │   │   ...
    │   └── img020.jpg   ← Final Straight Pose
    └── EMP002_Sara_Ahmed/
        └── ...
employees.csv
```

**employees.csv columns:**

| Column | Example |
|---|---|
| image | img001.jpg |
| employee_id | EMP001 |
| employee_name | Ali Khan |
| department | Information Technology |
| email | ali@company.com |
| pose_label | Look Straight |
| captured_at | 2024-01-15T09:30:00Z |

---

## 🔒 Duplicate Handling

If an Employee ID already exists the app presents three choices:

- **Add More Images** — appends to the existing folder
- **Replace Existing Dataset** — wipes old images + CSV rows and starts fresh
- **Cancel** — returns to the registration form

---

## 🛡️ Admin Page

Access via the **sidebar → Admin** page:

- 📊 KPI cards (total images, employees, departments, complete datasets)
- 👥 Employee table with image counts
- 🖼️ Per-employee image gallery
- 📦 Download individual or full dataset ZIPs
- 📄 Download per-employee or master CSV
- 🗑️ Safe deletion with typed confirmation

---

## ⚙️ Configuration

All tuneable settings are in [`utils/config.py`](utils/config.py):

| Setting | Default | Description |
|---|---|---|
| `FACE_SIZE` | `(224, 224)` | Output image resolution |
| `IMAGE_QUALITY` | `95` | JPEG quality |
| `FACE_PADDING` | `0.20` | Padding around face crop |
| `SCALE_FACTOR` | `1.1` | Haar Cascade scale factor |
| `MIN_NEIGHBOURS` | `5` | Haar Cascade min neighbours |
| `TOTAL_POSES` | `20` | Number of guided poses |

---

## 🐛 Troubleshooting

| Problem | Solution |
|---|---|
| Camera not opening | Allow camera permission in browser; use HTTPS |
| "No face detected" | Ensure good lighting; move closer to the camera |
| Import errors | Make sure you're in the project root and venv is active |
| `cv2` not found | `pip install opencv-python-headless` |

---

## 📄 License

MIT — free to use and modify.
