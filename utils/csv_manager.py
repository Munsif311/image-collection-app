"""
csv_manager.py
==============
All read/write operations for the master employees.csv file.
Thread-safe append using a file-level lock.
"""

import logging
import os
import threading
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from utils.config import CSV_COLUMNS, CSV_PATH

logger = logging.getLogger(__name__)

_csv_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ensure_csv() -> None:
    """Create the CSV with header columns if it does not exist yet."""
    if not os.path.exists(CSV_PATH):
        df = pd.DataFrame(columns=CSV_COLUMNS)
        df.to_csv(CSV_PATH, index=False)
        logger.info("Created new CSV: %s", CSV_PATH)


def _load_df() -> pd.DataFrame:
    """Load the CSV into a DataFrame, creating it if necessary."""
    _ensure_csv()
    try:
        df = pd.read_csv(CSV_PATH, dtype=str)
        # Guarantee all expected columns are present
        for col in CSV_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[CSV_COLUMNS]
    except Exception as exc:
        logger.error("Failed to read CSV (%s): %s", CSV_PATH, exc)
        return pd.DataFrame(columns=CSV_COLUMNS)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def append_record(
    image: str,
    employee_id: str,
    employee_name: str,
    department: str,
    email: str,
    pose_label: str,
) -> None:
    """
    Append a single capture record to the master CSV.

    Parameters
    ----------
    image         : image filename  (e.g. ``img001.jpg``)
    employee_id   : e.g. ``EMP001``
    employee_name : full name
    department    : department string
    email         : optional email (empty string if not provided)
    pose_label    : pose name from the guided capture sequence
    """
    row: Dict[str, str] = {
        "image": image,
        "employee_id": employee_id.strip().upper(),
        "employee_name": employee_name.strip(),
        "department": department.strip(),
        "email": email.strip(),
        "pose_label": pose_label,
        "captured_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    with _csv_lock:
        _ensure_csv()
        try:
            df = _load_df()
            new_row = pd.DataFrame([row], columns=CSV_COLUMNS)
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(CSV_PATH, index=False)
            logger.debug("Appended record for %s (%s).", employee_id, image)
        except Exception as exc:
            logger.error("Failed to append CSV record: %s", exc)
            raise


def get_all_records() -> pd.DataFrame:
    """Return the full master CSV as a DataFrame."""
    return _load_df()


def get_employee_records(employee_id: str) -> pd.DataFrame:
    """Return all rows belonging to *employee_id*."""
    df = _load_df()
    return df[df["employee_id"].str.upper() == employee_id.strip().upper()].copy()


def employee_id_exists(employee_id: str) -> bool:
    """Return True if at least one CSV row exists for *employee_id*."""
    df = _load_df()
    return employee_id.strip().upper() in df["employee_id"].str.upper().values


def delete_employee_records(employee_id: str) -> int:
    """
    Remove all rows for *employee_id* from the CSV.

    Returns the number of rows deleted.
    """
    with _csv_lock:
        df = _load_df()
        mask = df["employee_id"].str.upper() == employee_id.strip().upper()
        count = int(mask.sum())
        df = df[~mask]
        df.to_csv(CSV_PATH, index=False)
        logger.info("Deleted %d CSV records for %s.", count, employee_id)
        return count


def get_summary_stats() -> Dict[str, int]:
    """Return basic statistics about the dataset."""
    df = _load_df()
    return {
        "total_images": len(df),
        "total_employees": df["employee_id"].nunique(),
        "total_departments": df["department"].nunique(),
    }


def search_by_name(query: str) -> pd.DataFrame:
    """Case-insensitive substring search on employee_name."""
    df = _load_df()
    mask = df["employee_name"].str.contains(query.strip(), case=False, na=False)
    return df[mask].drop_duplicates(subset=["employee_id"]).copy()


def search_by_id(query: str) -> pd.DataFrame:
    """Case-insensitive prefix/substring search on employee_id."""
    df = _load_df()
    mask = df["employee_id"].str.contains(query.strip(), case=False, na=False)
    return df[mask].drop_duplicates(subset=["employee_id"]).copy()


def get_csv_bytes() -> bytes:
    """Return the entire CSV as UTF-8 bytes for download widgets."""
    _ensure_csv()
    with open(CSV_PATH, "rb") as f:
        return f.read()


def get_unique_employees() -> pd.DataFrame:
    """
    Return a deduplicated DataFrame with one row per employee
    and an additional ``image_count`` column.
    """
    df = _load_df()
    if df.empty:
        return pd.DataFrame(
            columns=["employee_id", "employee_name", "department", "email", "image_count"]
        )
    counts = df.groupby("employee_id").size().reset_index(name="image_count")
    unique = df.drop_duplicates(subset=["employee_id"])[
        ["employee_id", "employee_name", "department", "email"]
    ].copy()
    merged = unique.merge(counts, on="employee_id", how="left")
    return merged.sort_values("employee_id").reset_index(drop=True)
