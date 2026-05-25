"""
Main Streamlit application for Unique Engineering Center.
Structured dashboard with normalized customer/report model and derived BI insights.
"""

import io
import logging
import warnings
from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from streamlit.runtime.scriptrunner import RerunException
from streamlit.runtime.scriptrunner_utils.script_requests import RerunData

from config import get_config
from db import DatabaseManager, get_db
from etl import normalize_date, normalize_headers
from utils import setup_logging, format_currency, handle_error, DataProcessor

# Configure logging early so helper functions can log if needed.
logger = logging.getLogger(__name__)

# Public Google Sheet URL (calling data) - used to fetch Kathmandu calling data
GOOGLE_SHEET_CALLING_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT9HPxS8RKvHXg5Jx79yN6CmcRDtr_GQCyPhsS1xX7gEMTF0CRKGPNglI7urvtto8-AE77LiuDkCIfJ/pub?output=xlsx"


def fetch_calling_from_sheet(url: str) -> pd.DataFrame:
    """Fetch the first table from a published Google Sheets URL and return as DataFrame.

    Supports both `pubhtml` and `output=xlsx` URLs.
    Returns an empty DataFrame on failure.
    """
    def _clean_columns(frame: pd.DataFrame) -> pd.DataFrame:
        frame.columns = [str(c).strip() for c in frame.columns]
        return frame

    try:
        if "output=xlsx" in url.lower() or url.lower().endswith(".xlsx"):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                df = pd.read_excel(io.BytesIO(response.content), dtype=str)
            return _clean_columns(df)

        tables = pd.read_html(url)
        if tables:
            df = tables[0]
            return _clean_columns(df)
    except Exception:
        logger.exception("Failed to fetch Google Sheet calling data")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            df = pd.read_excel(io.BytesIO(response.content), dtype=str)
        return _clean_columns(df)
    except Exception:
        logger.exception("Failed to fetch Google Sheet as XLSX fallback")

    return pd.DataFrame()


def normalize_google_sheet_headers(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_headers(df)
    df = df.fillna("")
    if "instant_id" in df.columns and "instance_id" not in df.columns:
        df["instance_id"] = df["instant_id"]
    if "remark_status" in df.columns and "remarks_status" not in df.columns:
        df["remarks_status"] = df["remark_status"]
    if "branch" not in df.columns:
        df["branch"] = "Kathmandu"
    return df


def normalize_person_name(value: str) -> str:
    if pd.isna(value) or str(value).strip() == "":
        return ""
    normalized = " ".join(str(value).strip().split())
    return normalized.title()


def derive_sheet_work_status(row: pd.Series) -> str:
    status = str(row.get("work_status", "")).strip().lower()
    if status:
        if "service" in status:
            return "service_confirm"
        if "connected" in status and "not" not in status:
            return "connected"
        if "not" in status or "no" in status:
            return "not_connected"

    remarks_status = str(row.get("remarks_status", "")).strip().lower()
    if remarks_status:
        if "service" in remarks_status:
            return "service_confirm"
        if "quotation" in remarks_status:
            return "not_connected"
        if "followup" in remarks_status or "need to followup" in remarks_status:
            return "not_connected"
        if "not receive" in remarks_status or "not connected" in remarks_status or "not connect" in remarks_status:
            return "not_connected"
        if "called" in remarks_status and "not" not in remarks_status:
            return "connected"

    remarks = str(row.get("remarks", "")).strip().lower()
    if remarks:
        if "service" in remarks:
            return "service_confirm"
        if "quotation" in remarks:
            return "not_connected"
        if "followup" in remarks or "need to followup" in remarks:
            return "not_connected"
        if "not receive" in remarks or "not connected" in remarks or "not connect" in remarks:
            return "not_connected"
        if "called" in remarks and "not" not in remarks:
            return "connected"

    return "not_connected"


def prepare_google_sheet_calling_data(raw_df: pd.DataFrame) -> pd.DataFrame:
    if raw_df.empty:
        return pd.DataFrame(columns=["date", "branch", "instance_id", "customer_id", "customer_name", "contact_name", "address", "contact_number", "calling_person", "work_status", "remarks_status", "remarks"])

    df = normalize_google_sheet_headers(raw_df.copy())
    if "branch" in df.columns:
        kathmandu_mask = df["branch"].astype(str).str.contains("Kathmandu", case=False, na=False)
        if kathmandu_mask.any():
            df = df[kathmandu_mask].copy()
        else:
            df["branch"] = "Kathmandu"
    else:
        df["branch"] = "Kathmandu"

    def clean_sheet_text(value):
        if pd.isna(value):
            return ""
        text = str(value).strip()
        if text.lower() in {"nan", "none"}:
            return ""
        return text

    df["instance_id"] = df.get(
        "instance_id",
        pd.Series([""] * len(df), index=df.index)
    ).astype(str).fillna("")
    df["customer_id"] = df["instance_id"]
    df["customer_name"] = df.get("company_name", pd.Series([""] * len(df), index=df.index)).apply(clean_sheet_text)

    if "contact_name" in df.columns:
        df["contact_name"] = df["contact_name"].apply(clean_sheet_text)
    elif "contact" in df.columns:
        df["contact_name"] = df["contact"].apply(clean_sheet_text)
    else:
        df["contact_name"] = ""

    if "address" in df.columns:
        df["address"] = df["address"].apply(clean_sheet_text)

    primary_mobile = df.get("primary_mobile", pd.Series([""] * len(df), index=df.index)).apply(clean_sheet_text)
    if primary_mobile.ne("").any():
        df["contact_number"] = primary_mobile
    else:
        df["contact_number"] = ""

    df["calling_person"] = df.get("calling_person", pd.Series([""] * len(df), index=df.index)).apply(clean_sheet_text).apply(normalize_person_name)
    df["remarks_status"] = df.get("remarks_status", pd.Series([""] * len(df), index=df.index)).astype(str).fillna("")
    df["remarks"] = df.get("remarks", pd.Series([""] * len(df), index=df.index)).astype(str).fillna("")
    df["work_status"] = df.apply(derive_sheet_work_status, axis=1)
    if "date" in df.columns:
        df["date"] = df["date"].apply(normalize_date).fillna("")
    else:
        df["date"] = ""

    columns = ["date", "branch", "instance_id", "customer_id", "customer_name", "address", "contact_number", "calling_person", "work_status", "remarks_status", "remarks"]
    if "contact_name" in df.columns:
        columns.insert(5, "contact_name")
    return df[columns]

def clear_report_caches() -> None:
    if hasattr(load_calling_data, "clear"):
        load_calling_data.clear()
    if hasattr(load_marketing_data, "clear"):
        load_marketing_data.clear()
    if hasattr(load_payment_data, "clear"):
        load_payment_data.clear()
    if hasattr(load_branches, "clear"):
        load_branches.clear()


def maybe_rerun() -> None:
    rerun_fn = getattr(st, "experimental_rerun", None)
    if callable(rerun_fn):
        rerun_fn()
    else:
        raise RerunException(RerunData())

# Configure logging
setup_logging(log_level="INFO", log_file="app.log")

config = get_config()

st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout=config.LAYOUT,
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .header-title {
        color: #0f4c81;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 10px;
    }
    .metric-card {
        background: #f7fbff;
        border-radius: 18px;
        padding: 16px;
        border: 1px solid #e5eef8;
    }
    .section-heading {
        margin-top: 24px;
        margin-bottom: 12px;
        color: #0f4c81;
    }
    </style>
""", unsafe_allow_html=True)


def load_database() -> DatabaseManager:
    return get_db()


@st.cache_data(ttl=86400)
def load_calling_data() -> pd.DataFrame:
    return load_database().get_calling_reports()


@st.cache_data(ttl=86400)
def load_marketing_data() -> pd.DataFrame:
    return load_database().get_marketing_reports()


@st.cache_data(ttl=86400)
def load_payment_data() -> pd.DataFrame:
    return load_database().get_payment_followups()


@st.cache_data(ttl=86400)
def load_branches() -> list:
    return load_database().get_branches()


def build_month_options(*dfs: pd.DataFrame) -> list:
    months = set()
    for df in dfs:
        if "date" in df.columns and not df.empty:
            months.update(
                pd.to_datetime(df["date"], errors="coerce")
                  .dt.to_period("M")
                  .astype(str)
                  .dropna()
                  .unique()
            )
    return ["All"] + sorted(months)


def filter_dataframe(df: pd.DataFrame, branch: str, month: str, person: str, person_column: str) -> pd.DataFrame:
    if df.empty:
        return df
    filtered = df.copy()
    if branch != "All Branches":
        filtered = filtered[filtered["branch"] == branch]
    if month != "All" and "date" in filtered.columns:
        filtered = filtered[pd.to_datetime(filtered["date"], errors="coerce").dt.to_period("M").astype(str) == month]
    if person != "All" and person_column in filtered.columns:
        filtered = filtered[filtered[person_column] == person]
    return filtered


def render_export_buttons(df: pd.DataFrame, prefix: str) -> None:
    if df.empty:
        st.info("No data available for export.")
        return
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download CSV",
        data=csv_data,
        file_name=f"{prefix}_export.csv",
        mime="text/csv",
        key=f"csv_{prefix}"
    )
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
    buffer.seek(0)
    st.download_button(
        label="Download Excel",
        data=buffer,
        file_name=f"{prefix}_export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"excel_{prefix}"
    )


def get_calling_metrics(df: pd.DataFrame) -> dict:
    status_by_person = pd.DataFrame()
    remarks_status_counts = pd.DataFrame()
    if not df.empty and "remarks_status" in df.columns:
        status_by_person = (
            df.groupby(["calling_person", "remarks_status"]).size()
              .reset_index(name="count")
              .sort_values(["calling_person", "count"], ascending=[True, False])
        )
        remarks_status_counts = (
            df["remarks_status"].fillna("Unknown")
              .value_counts()
              .reset_index(name="count")
              .rename(columns={"index": "remarks_status"})
        )

    return {
        "total_calls": int(len(df)),
        "total_not_connected": int(len(df[df["work_status"] == "not_connected"])),
        "total_service_confirm": int(len(df[df["work_status"] == "service_confirm"])),
        "total_quotation_sent": int(len(df[df["remarks_status"].astype(str).str.contains("quotation", case=False, na=False)])) if "remarks_status" in df.columns else 0,
        "total_followup": int(len(df[df["remarks_status"].astype(str).str.contains("followup", case=False, na=False)])) if "remarks_status" in df.columns else 0,
        "unique_customers_called": int(df["customer_id"].nunique()) if "customer_id" in df.columns else 0,
        "calls_per_person": df.groupby("calling_person").size().reset_index(name="calls").sort_values("calls", ascending=False),
        "status_by_person": status_by_person,
        "remarks_status_counts": remarks_status_counts
    }


def get_marketing_metrics(df: pd.DataFrame) -> dict:
    return {
        "total_visits": int(len(df[df["outcome"] == "visit"])),
        "total_service_confirm": int(len(df[df["outcome"] == "service_confirm"])),
        "unique_customers_visited": int(df[df["outcome"].isin(["visit", "service_confirm"])]["customer_id"].nunique()),
        "visits_by_person": df.groupby("marketing_person").size().reset_index(name="visits").sort_values("visits", ascending=False)
    }


def get_payment_metrics(df: pd.DataFrame) -> dict:
    return {
        "total_calls": int(len(df)),
        "total_collection": float(df["payment_received"].sum()),
        "total_pending": float(df["os_amount"].sum()),
        "total_not_connected": int(len(df[df["status"] == "followup"])),
        "unique_customers_contacted": int(df["customer_id"].nunique()),
        "collection_by_branch": df.groupby("branch")["payment_received"].sum().reset_index().sort_values("payment_received", ascending=False)
    }


def render_calling_dashboard(df: pd.DataFrame) -> None:
    st.subheader("Calling Dashboard")
    metrics = get_calling_metrics(df)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Calls", metrics["total_calls"])
    col2.metric("Not Connected", metrics["total_not_connected"])
    col3.metric("Service Confirm", metrics["total_service_confirm"])
    col4.metric("Unique Customers", metrics["unique_customers_called"])

    st.markdown("### Calls per Person")
    fig = px.bar(metrics["calls_per_person"], x="calling_person", y="calls", labels={"calling_person": "Calling Person", "calls": "Calls"})
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Calls Over Time")
    chart_df = DataProcessor.prepare_chart_data(df, "date")
    if not chart_df.empty:
        counts = chart_df.groupby(chart_df["date"].dt.to_period("D")).size().reset_index(name="calls")
        counts["date"] = counts["date"].dt.to_timestamp()
        fig = px.line(counts, x="date", y="calls", labels={"date": "Date", "calls": "Calls"}, title="Calls Over Time")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Work Status Breakdown")
    status_counts = df["work_status"].value_counts().reset_index()
    status_counts.columns = ["work_status", "count"]
    fig = px.pie(status_counts, values="count", names="work_status", title="Connected vs Not Connected vs Service Confirm")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Remark Status Breakdown (Primary analysis column)")
    if "remarks_status" in df.columns:
        remark_counts = df["remarks_status"].fillna("Unknown").value_counts().reset_index()
        remark_counts.columns = ["remarks_status", "count"]
        fig = px.bar(remark_counts, x="remarks_status", y="count", labels={"remarks_status": "Remark Status", "count": "Count"}, title="Call Counts by Remark Status")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Calls by Person and Remark Status")
    if "status_by_person" in metrics and not metrics["status_by_person"].empty:
        fig = px.bar(metrics["status_by_person"], x="calling_person", y="count", color="remarks_status", barmode="group", labels={"calling_person": "Calling Person", "count": "Calls", "remarks_status": "Remark Status"})
        st.plotly_chart(fig, use_container_width=True)


def render_marketing_dashboard(df: pd.DataFrame) -> None:
    st.subheader("Marketing Dashboard")
    metrics = get_marketing_metrics(df)
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Visits", metrics["total_visits"])
    col2.metric("Service Confirm", metrics["total_service_confirm"])
    col3.metric("Unique Customers", metrics["unique_customers_visited"])

    st.markdown("### Visits by Marketing Person")
    fig = px.bar(metrics["visits_by_person"], x="marketing_person", y="visits", labels={"marketing_person": "Marketing Person", "visits": "Visits"})
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Visits Trend")
    chart_df = DataProcessor.prepare_chart_data(df, "date")
    if not chart_df.empty:
        counts = chart_df.groupby(chart_df["date"].dt.to_period("D")).size().reset_index(name="visits")
        counts["date"] = counts["date"].dt.to_timestamp()
        fig = px.line(counts, x="date", y="visits", labels={"date": "Date", "visits": "Visits"}, title="Visits Trend")
        st.plotly_chart(fig, use_container_width=True)


def render_payment_dashboard(df: pd.DataFrame) -> None:
    st.subheader("Payment Dashboard")
    metrics = get_payment_metrics(df)
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Contacts", metrics["total_calls"])
    col2.metric("Total Collection", format_currency(metrics["total_collection"]))
    col3.metric("Total Pending", format_currency(metrics["total_pending"]))

    st.markdown("### Collection by Branch")
    fig = px.bar(metrics["collection_by_branch"], x="branch", y="payment_received", labels={"branch": "Branch", "payment_received": "Collection"})
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Collection Trend")
    chart_df = DataProcessor.prepare_chart_data(df, "date", "payment_received")
    if not chart_df.empty:
        totals = chart_df.groupby(chart_df["date"].dt.to_period("D"))["payment_received"].sum().reset_index()
        totals["date"] = totals["date"].dt.to_timestamp()
        fig = px.line(totals, x="date", y="payment_received", labels={"date": "Date", "payment_received": "Collected"}, title="Collection Trend")
        st.plotly_chart(fig, use_container_width=True)


def render_team_review_dashboard() -> None:
    st.header("Team Review: Monthly Calling Performance")
    agents = [
        {"agent": "Jyoti", "total_calls": 836, "connected_calls": 676, "calls_per_day": 32},
        {"agent": "Sneha", "total_calls": 539, "connected_calls": 497, "calls_per_day": 33},
        {"agent": "Urmila", "total_calls": 237, "connected_calls": 197, "calls_per_day": 8},
        {"agent": "Shanja", "total_calls": 145, "connected_calls": 128, "calls_per_day": 9},
    ]
    df = pd.DataFrame(agents)
    grand_total_calls = int(df["total_calls"].sum())
    grand_actual_calls = int(df["connected_calls"].sum())

    col1, col2, col3, col4 = st.columns(4)
    for idx, agent in enumerate(agents):
        if idx < 4:
            col = [col1, col2, col3, col4][idx]
            col.metric(agent["agent"], f"{agent['total_calls']} calls", f"{agent['connected_calls']} connected")

    st.markdown("---")
    st.markdown("### Team totals")
    st.write(f"**Total Calls:** {grand_total_calls}  \
              **Connected Calls:** {grand_actual_calls}  \
              **Average Calls/Day:** {df['calls_per_day'].mean():.1f}")

    st.markdown("### Total Calls vs Actual Connected Calls")
    fig = px.bar(
        df.melt(id_vars=["agent"], value_vars=["total_calls", "connected_calls"], var_name="call_type", value_name="count"),
        x="agent",
        y="count",
        color="call_type",
        barmode="group",
        labels={"agent": "Agent", "count": "Call Count", "call_type": "Type"},
        color_discrete_map={"total_calls": "#0f4c81", "connected_calls": "#7c9ccf"}
    )
    fig.update_layout(title_text="Total Calls vs Actual Connected Calls", legend_title_text="")
    fig.update_traces(texttemplate="%{y}", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Calls Per Day")
    df_calls_per_day = df.sort_values("calls_per_day", ascending=True)
    fig2 = px.bar(
        df_calls_per_day,
        x="calls_per_day",
        y="agent",
        orientation="h",
        labels={"agent": "Agent", "calls_per_day": "Calls Per Day"},
        color="calls_per_day",
        color_continuous_scale=["#2f4f6d", "#8ab6d6"]
    )
    fig2.update_layout(title_text="Calls Per Day Efficiency", showlegend=False)
    fig2.update_traces(texttemplate="%{x}", textposition="outside")
    st.plotly_chart(fig2, use_container_width=True)


def render_comparison_dashboard(calling_df: pd.DataFrame, marketing_df: pd.DataFrame, payment_df: pd.DataFrame, branch: str, month: str) -> None:
    st.subheader(f"Comparison across branches{f' for {month}' if month != 'All' else ''}")
    calling_filtered = filter_dataframe(calling_df, branch, month, "All", "calling_person")
    marketing_filtered = filter_dataframe(marketing_df, branch, month, "All", "marketing_person")
    payment_filtered = filter_dataframe(payment_df, branch, month, "All", "customer_name")

    branches = sorted(set(calling_filtered["branch"].unique()).union(marketing_filtered["branch"].unique(), payment_filtered["branch"].unique()))
    summary = pd.DataFrame({"branch": branches})
    summary["calling_count"] = summary["branch"].map(calling_filtered["branch"].value_counts()).fillna(0).astype(int)
    summary["marketing_count"] = summary["branch"].map(marketing_filtered["branch"].value_counts()).fillna(0).astype(int)
    summary["payment_collection"] = summary["branch"].map(payment_filtered.groupby("branch")["payment_received"].sum()).fillna(0.0)
    summary["payment_pending"] = summary["branch"].map(payment_filtered.groupby("branch")["os_amount"].sum()).fillna(0.0)

    if not summary.empty:
        st.markdown("### Branch summary")
        fig = px.bar(summary, x="branch", y=["calling_count", "marketing_count", "payment_collection"], title="Branch-wise Performance", barmode="group")
        st.plotly_chart(fig, use_container_width=True)
        render_export_buttons(summary, "branch_summary")

    daily_frames = []
    for label, df in [("Calling", calling_filtered), ("Marketing", marketing_filtered), ("Payment", payment_filtered)]:
        if not df.empty and "date" in df.columns:
            tmp = df.copy()
            tmp["date"] = pd.to_datetime(tmp["date"], errors="coerce").dt.date
            if not tmp["date"].isna().all():
                counts = tmp.groupby("date").size().reset_index(name=f"{label.lower()}_count")
                daily_frames.append(counts)

    if daily_frames:
        daily_summary = daily_frames[0]
        for frame in daily_frames[1:]:
            daily_summary = daily_summary.merge(frame, on="date", how="outer")
        daily_summary = daily_summary.fillna(0).sort_values("date")
        month_label = month if month != "All" else "All dates"
        st.markdown(f"### Daily count for {month_label} ({'All branches' if branch == 'All Branches' else branch})")
        fig = px.line(daily_summary, x="date", y=[c for c in daily_summary.columns if c != "date"],
                      title=f"Daily activity for {month_label}", markers=True)
        st.plotly_chart(fig, use_container_width=True)
        render_export_buttons(daily_summary, "daily_activity")


def render_table(df: pd.DataFrame, columns: list | None, prefix: str) -> None:
    if df.empty:
        st.info("No data available for the selected filters.")
        return
    display = df.copy()
    display.columns = ["COMPANY NAME" if col in {"customer_name", "company_name"} else col for col in display.columns]
    if "date" in display.columns:
        display["date"] = pd.to_datetime(display["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    if "payment_received" in display.columns:
        display["payment_received"] = display["payment_received"].apply(format_currency)
    if "os_amount" in display.columns:
        display["os_amount"] = display["os_amount"].apply(format_currency)
    if columns is None:
        columns = list(display.columns)
    else:
        columns = ["COMPANY NAME" if col in {"customer_name", "company_name"} else col for col in columns]
    st.dataframe(display[columns], use_container_width=True, hide_index=True)
    render_export_buttons(display[columns], prefix)


def main():
    try:
        calling_df = load_calling_data()
        marketing_df = load_marketing_data()
        payment_df = load_payment_data()

        # Attempt to auto-load Kathmandu calling data from the public Google Sheet.
        sheet_df = pd.DataFrame()
        try:
            raw_sheet = fetch_calling_from_sheet(GOOGLE_SHEET_CALLING_URL)
            if not raw_sheet.empty:
                prepared = prepare_google_sheet_calling_data(raw_sheet)
                if not prepared.empty:
                    calling_df = prepared
                    sheet_df = prepared
                    logger.info("Using Google Sheet calling data as primary source (%d rows)", len(prepared))
        except Exception:
            logger.exception("Auto-load of Google Sheet failed; falling back to system DB data.")

        branches = ["All Branches"] + (sorted(set(load_branches() + (["Kathmandu"] if not sheet_df.empty else []))))

        st.markdown(f"<div class='header-title'>{config.APP_TITLE}</div>", unsafe_allow_html=True)

        with st.sidebar:
            st.header("Filters")
            branch = st.selectbox("Branch", options=branches)
            report_type = st.selectbox("Report Type", options=["All", "Calling", "Marketing", "Payment", "Team Review"])
            month = st.selectbox("Month", options=build_month_options(calling_df, marketing_df, payment_df))
            person = "All"
            if report_type == "Calling":
                person = st.selectbox("Calling Person", options=["All"] + sorted(calling_df["calling_person"].dropna().unique()))
            elif report_type == "Marketing":
                person = st.selectbox("Marketing Person", options=["All"] + sorted(marketing_df["marketing_person"].dropna().unique()))

            st.markdown("---")
            if st.button("Refresh data"):
                load_database().insert_sample_data(replace=True)
                clear_report_caches()
                maybe_rerun()

        if report_type == "Calling":
            st.header("Calling Dashboard")
            df = filter_dataframe(calling_df, branch, month, person, "calling_person")
            render_calling_dashboard(df)
            common_columns = ["date", "branch", "calling_person", "work_status", "remarks_status", "remarks"]
            if "customer_name" in df.columns:
                common_columns.insert(2, "customer_name")
                if "contact_name" in df.columns:
                    common_columns.insert(3, "contact_name")
                if "address" in df.columns:
                    common_columns.insert(4, "address")
                if "contact_number" in df.columns:
                    common_columns.insert(5, "contact_number")
            if "next_calling_date" in df.columns:
                common_columns.append("next_calling_date")
            render_table(df, common_columns, "calling")

        elif report_type == "Marketing":
            st.header("Marketing Dashboard")
            df = filter_dataframe(marketing_df, branch, month, person, "marketing_person")
            render_marketing_dashboard(df)
            marketing_columns = ["date", "branch", "customer_name", "marketing_person", "segment", "outcome", "remarks", "final_remarks"]
            if "contact_name" in df.columns:
                marketing_columns.insert(3, "contact_name")
            if "address" in df.columns:
                marketing_columns.insert(4, "address")
            if "contact_number" in df.columns:
                marketing_columns.insert(5, "contact_number")
            render_table(df, marketing_columns, "marketing")

        elif report_type == "Payment":
            st.header("Payment Dashboard")
            df = filter_dataframe(payment_df, branch, month, "All", "customer_name")
            render_payment_dashboard(df)
            payment_columns = ["date", "branch", "customer_name", "status", "payment_received", "os_amount", "next_calling_date", "remarks"]
            if "contact_name" in df.columns:
                payment_columns.insert(3, "contact_name")
            if "address" in df.columns:
                payment_columns.insert(4, "address")
            if "contact_number" in df.columns:
                payment_columns.insert(5, "contact_number")
            render_table(df, payment_columns, "payment")

        elif report_type == "Team Review":
            render_team_review_dashboard()

        else:
            st.header("Executive Summary")
            overall = load_database().get_summary_stats()
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Calls", overall.get("total_calls", 0))
            col2.metric("Total Visits", overall.get("total_marketing", 0))
            col3.metric("Total Collection", format_currency(overall.get("total_collection", 0.0)))
            col4.metric("Total Pending", format_currency(overall.get("total_pending", 0.0)))
            render_comparison_dashboard(calling_df, marketing_df, payment_df, branch, month)

        st.markdown("---")
        st.markdown(f"<p style='text-align: center; color: gray; font-size: 0.8rem;'>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>", unsafe_allow_html=True)

    except Exception as e:
        handle_error(e, "rendering dashboard")


if __name__ == "__main__":
    main()
