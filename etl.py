"""
ETL module for cleaning messy Google Sheets exports and mapping them into the dashboard schema.
"""

import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from utils import safe_numeric_conversion


COLUMN_RENAME_MAP = {
    "mobile_no_primary": "primary_mobile",
    "mobile_no_primary": "primary_mobile",
    "primary_mobile": "primary_mobile",
    "mobile_no_secondary": "secondary_mobile",
    "secondary_mobile": "secondary_mobile",
    "company_name": "company_name",
    "company": "company_name",
    "customer_name": "contact_name",
    "contact_name": "contact_name",
    "calling_months": "calling_month",
    "calling_month": "calling_month",
    "calling_person": "calling_person",
    "marketing_person": "marketing_person",
    "service_lead": "service_lead",
    "status_remarks": "remarks_status",
    "final_remarks": "final_remarks",
    "next_calling_date": "next_calling_date",
    "payment_received": "payment_received",
    "os_amount": "os_amount",
    "pan_no": "pan_no",
    "vat_no": "vat_no",
    "mobile_no": "primary_mobile",
    "primary_mobile_number": "primary_mobile",
    "secondary_mobile_number": "secondary_mobile",
    "instant_id": "instance_id",
    "instance_id": "instance_id",
    "remark_status": "remarks_status",
    "esn": "esn",
    "report_type": "report_type",
    "date": "date",
    "branch": "branch",
    "branch_name": "branch",
    "remarks": "remarks",
    "amount": "amount",
    "campaign_name": "campaign_name",
    "segment": "segment",
    "outcome": "outcome",
    "address": "address",
    "email": "email",
    "customer_id": "customer_id",
    "work_status": "work_status",
    "payment_method": "payment_method",
    "company_address": "address"
}


def clean_column_name(column: str) -> str:
    """Standardize a raw column name to snake_case."""
    name = str(column).strip().lower()
    name = re.sub(r"[\s\-\/.]+", "_", name)
    name = re.sub(r"[^a-z0-9_]+", "", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")
    return COLUMN_RENAME_MAP.get(name, name)


def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize all column headers in a DataFrame."""
    df = df.copy()
    df.columns = [clean_column_name(col) for col in df.columns]
    return df


def generate_customer_key(row: pd.Series) -> str:
    """Generate a unique customer key using instance_id or contact details."""
    source_id = str(row.get("instance_id", "")).strip()
    source_id = source_id or str(row.get("esn", "")).strip()
    if source_id:
        return source_id

    name = str(row.get("company_name", "")).strip().lower()
    contact_name = str(row.get("contact_name", "")).strip().lower()
    mobile = str(row.get("primary_mobile", "")).strip().lower()
    seed = f"{name}|{contact_name}|{mobile}".encode("utf-8")
    return hashlib.sha1(seed).hexdigest()[:16]


def normalize_phone(value: Optional[str]) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"[^0-9+]", "", str(value)).strip()


def normalize_date(value: Optional[str]) -> Optional[str]:
    if pd.isna(value) or value is None or str(value).strip() == "":
        return None
    try:
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.strftime("%Y-%m-%d")
    except Exception:
        return None


def load_raw_csv(path: Path) -> pd.DataFrame:
    """Load a messy Google Sheets export, normalize headers, and clean types."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df = normalize_headers(df)
    df = df.fillna("")
    for normalized_column in set(COLUMN_RENAME_MAP.values()):
        if normalized_column not in df.columns:
            df[normalized_column] = ""
    return df


def build_customer_dataframe(raw: pd.DataFrame) -> pd.DataFrame:
    """Build a normalized customer table from raw sheet data."""
    if raw.empty:
        return pd.DataFrame(
            columns=[
                "external_customer_id",
                "company_name",
                "address",
                "contact_name",
                "primary_mobile",
                "secondary_mobile",
                "email",
                "pan_no",
                "vat_no"
            ]
        )

    raw = raw.copy()
    for col in [
        "primary_mobile", "secondary_mobile", "company_name", "address",
        "contact_name", "email", "pan_no", "vat_no", "customer_name"
    ]:
        if col not in raw.columns:
            raw[col] = ""

    raw["contact_name"] = raw["contact_name"].fillna(raw.get("customer_name", ""))
    raw["primary_mobile"] = raw["primary_mobile"].apply(normalize_phone)
    raw["secondary_mobile"] = raw["secondary_mobile"].apply(normalize_phone)
    raw["external_customer_id"] = raw.apply(generate_customer_key, axis=1)

    customers = (
        raw[
            [
                "external_customer_id",
                "company_name",
                "address",
                "contact_name",
                "primary_mobile",
                "secondary_mobile",
                "email",
                "pan_no",
                "vat_no"
            ]
        ]
        .drop_duplicates(subset=["external_customer_id"])
        .fillna("")
    )

    return customers


def safe_text(value: Optional[str]) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def determine_work_status(row: pd.Series) -> str:
    status = str(row.get("work_status", "")).strip().lower()
    if status in {"service_confirm", "service confirm", "service-confirm"}:
        return "service_confirm"
    if status in {"connected", "connect", "connected_success"}:
        return "connected"
    if status in {"not_connected", "not connected", "not connected yet"}:
        return "not_connected"
    if status == "pending":
        return "not_connected"

    status_field = str(row.get("status", "")).strip().lower()
    if status_field in {"completed", "done", "ok"}:
        return "connected"
    if status_field in {"pending", "not connected", "not_connected"}:
        return "not_connected"
    if "service" in status_field:
        return "service_confirm"
    return "not_connected"


def determine_outcome(row: pd.Series) -> str:
    outcome = str(row.get("outcome", "")).strip().lower()
    if outcome in {"visit", "service_confirm", "followup"}:
        return outcome

    status = str(row.get("status", "")).strip().lower()
    if status in {"completed", "done"}:
        if "service" in str(row.get("remarks", "")).lower() or "service" in str(row.get("final_remarks", "")).lower():
            return "service_confirm"
        return "visit"
    return "followup"


def determine_payment_status(row: pd.Series) -> str:
    status = str(row.get("status", "")).strip().lower()
    if status in {"paid", "completed", "done"}:
        return "paid"
    if status in {"pending", "due"}:
        return "pending"
    return "followup"


def standardize_calling_data(raw: pd.DataFrame, customer_map: Dict[str, int]) -> pd.DataFrame:
    """Transform raw rows into normalized calling report rows."""
    records = []
    for _, row in raw.iterrows():
        report_type = str(row.get("report_type", "")).strip().lower()
        if "call" not in report_type and "service follow" not in report_type:
            continue

        customer_key = generate_customer_key(row)
        customer_id = customer_map.get(customer_key)
        if customer_id is None:
            continue

        records.append({
            "date": normalize_date(row.get("date")),
            "customer_id": customer_id,
            "branch": safe_text(row.get("branch")),
            "calling_person": safe_text(row.get("calling_person")),
            "work_status": determine_work_status(row),
            "remarks": safe_text(row.get("remarks")),
            "remarks_status": safe_text(row.get("remarks_status")),
            "next_calling_date": normalize_date(row.get("next_calling_date")),
            "service_lead": safe_text(row.get("service_lead"))
        })

    return pd.DataFrame(records)


def standardize_marketing_data(raw: pd.DataFrame, customer_map: Dict[str, int]) -> pd.DataFrame:
    records = []
    for _, row in raw.iterrows():
        report_type = str(row.get("report_type", "")).strip().lower()
        if "marketing" not in report_type:
            continue

        customer_key = generate_customer_key(row)
        customer_id = customer_map.get(customer_key)
        if customer_id is None:
            continue

        records.append({
            "date": normalize_date(row.get("date")),
            "customer_id": customer_id,
            "branch": safe_text(row.get("branch")),
            "marketing_person": safe_text(row.get("marketing_person")),
            "segment": safe_text(row.get("segment")),
            "outcome": determine_outcome(row),
            "remarks": safe_text(row.get("remarks")),
            "final_remarks": safe_text(row.get("final_remarks"))
        })

    return pd.DataFrame(records)


def standardize_payment_data(raw: pd.DataFrame, customer_map: Dict[str, int]) -> pd.DataFrame:
    records = []
    for _, row in raw.iterrows():
        report_type = str(row.get("report_type", "")).strip().lower()
        if "payment" not in report_type and "followup" not in report_type:
            continue

        customer_key = generate_customer_key(row)
        customer_id = customer_map.get(customer_key)
        if customer_id is None:
            continue

        amount = safe_numeric_conversion(row.get("amount", 0.0), default=0.0)
        payment_received = safe_numeric_conversion(row.get("payment_received", amount), default=0.0)
        os_amount = safe_numeric_conversion(row.get("os_amount", 0.0), default=0.0)
        status = determine_payment_status(row)

        if status == "paid" and os_amount == 0:
            os_amount = 0.0
        if status == "pending" and os_amount == 0:
            os_amount = amount

        records.append({
            "date": normalize_date(row.get("date")),
            "customer_id": customer_id,
            "branch": safe_text(row.get("branch")),
            "os_amount": os_amount,
            "payment_received": payment_received,
            "next_calling_date": normalize_date(row.get("next_calling_date")),
            "status": status,
            "remarks": safe_text(row.get("remarks"))
        })

    return pd.DataFrame(records)


def build_normalized_datasets(csv_path: Path) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load raw CSV and emit normalized customer and report tables."""
    raw = load_raw_csv(csv_path)
    customers = build_customer_dataframe(raw)

    # Use a temporary map based on customer external id
    customer_map = {key: idx + 1 for idx, key in enumerate(customers["external_customer_id"].tolist())}
    customers["id"] = customers["external_customer_id"].map(customer_map)
    customers = customers.drop(columns=["external_customer_id"]).rename(columns={"contact_name": "contact_name"})

    calling = standardize_calling_data(raw, customer_map)
    marketing = standardize_marketing_data(raw, customer_map)
    payments = standardize_payment_data(raw, customer_map)

    return customers, calling, marketing, payments
