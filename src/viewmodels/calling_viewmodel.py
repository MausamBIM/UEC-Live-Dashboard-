"""ViewModel for Calling Dashboard logic."""

import logging
import pandas as pd
from typing import Optional
from ..models import MetricsData, FilterOptions
from .base_viewmodel import BaseViewModel

logger = logging.getLogger(__name__)


class CallingViewModel(BaseViewModel):
    """Business logic for calling dashboard."""
    
    def __init__(self):
        super().__init__()
    
    def normalize_service_lead(self, value) -> str:
        """Normalize service lead value."""
        if pd.isna(value):
            return ""
        text = str(value).strip()
        if text.lower() in {"", "nan", "none"}:
            return ""
        return text
    
    def get_calling_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Get rows without service leads (pending calling)."""
        if df.empty:
            return df.copy()
        result = df.copy()
        if "service_lead" not in result.columns:
            return result
        result["service_lead"] = result["service_lead"].apply(self.normalize_service_lead)
        return result[result["service_lead"] == ""].copy()
    
    def get_lead_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Get rows with service leads (assigned leads)."""
        if df.empty:
            return df.copy()
        result = df.copy()
        if "service_lead" not in result.columns:
            return result.iloc[0:0].copy()
        result["service_lead"] = result["service_lead"].apply(self.normalize_service_lead)
        return result[result["service_lead"] != ""].copy()
    
    def calculate_metrics(self, df: pd.DataFrame) -> MetricsData:
        """Calculate calling metrics."""
        calling_df = self.get_calling_rows(df)
        
        status_by_person = pd.DataFrame()
        remarks_status_counts = pd.DataFrame()
        
        if not calling_df.empty and "remarks_status" in calling_df.columns:
            status_by_person = (
                calling_df.groupby(["calling_person", "remarks_status"]).size()
                .reset_index(name="count")
                .sort_values(["calling_person", "count"], ascending=[True, False])
            )
            remarks_status_counts = (
                calling_df["remarks_status"].fillna("Unknown")
                .value_counts()
                .reset_index(name="count")
                .rename(columns={"index": "remarks_status"})
            )
        
        calls_per_person = calling_df.groupby("calling_person").size().reset_index(name="calls").sort_values("calls", ascending=False) if not calling_df.empty else pd.DataFrame()
        
        metrics = MetricsData(
            total_items=int(len(calling_df)),
            key_metric_1=int(len(calling_df[calling_df["work_status"] == "not_connected"])),
            key_metric_2=int(len(calling_df[calling_df["work_status"] == "service_confirm"])),
            key_metric_3=int(len(calling_df[calling_df["remarks_status"].astype(str).str.contains("quotation", case=False, na=False)])) if "remarks_status" in calling_df.columns else 0,
            unique_customers=int(calling_df["customer_id"].nunique()) if "customer_id" in calling_df.columns else 0,
            detailed_metrics={
                "quotation_sent": metrics.key_metric_3,
                "followup_needed": int(len(calling_df[calling_df["remarks_status"].astype(str).str.contains("followup", case=False, na=False)])) if "remarks_status" in calling_df.columns else 0,
                "calls_per_person": calls_per_person,
                "status_by_person": status_by_person,
                "remarks_status": remarks_status_counts
            }
        )
        return metrics
    
    def get_calling_metrics(self, df: pd.DataFrame) -> dict:
        """Get calling metrics as dictionary."""
        calling_df = self.get_calling_rows(df)
        status_by_person = pd.DataFrame()
        remarks_status_counts = pd.DataFrame()
        
        if not calling_df.empty and "remarks_status" in calling_df.columns:
            status_by_person = (
                calling_df.groupby(["calling_person", "remarks_status"]).size()
                .reset_index(name="count")
                .sort_values(["calling_person", "count"], ascending=[True, False])
            )
            remarks_status_counts = (
                calling_df["remarks_status"].fillna("Unknown")
                .value_counts()
                .reset_index(name="count")
                .rename(columns={"index": "remarks_status"})
            )
        
        return {
            "total_calls": int(len(calling_df)),
            "total_not_connected": int(len(calling_df[calling_df["work_status"] == "not_connected"])),
            "total_service_confirm": int(len(calling_df[calling_df["work_status"] == "service_confirm"])),
            "total_quotation_sent": int(len(calling_df[calling_df["remarks_status"].astype(str).str.contains("quotation", case=False, na=False)])) if "remarks_status" in calling_df.columns else 0,
            "total_followup": int(len(calling_df[calling_df["remarks_status"].astype(str).str.contains("followup", case=False, na=False)])) if "remarks_status" in calling_df.columns else 0,
            "unique_customers_called": int(calling_df["customer_id"].nunique()) if "customer_id" in calling_df.columns else 0,
            "calls_per_person": calling_df.groupby("calling_person").size().reset_index(name="calls").sort_values("calls", ascending=False) if not calling_df.empty else pd.DataFrame(),
            "status_by_person": status_by_person,
            "remarks_status_counts": remarks_status_counts
        }
    
    def get_lead_metrics(self, df: pd.DataFrame) -> dict:
        """Get lead metrics as dictionary."""
        lead_df = self.get_lead_rows(df)
        lead_counts = pd.DataFrame()
        
        if not lead_df.empty:
            lead_counts = (
                lead_df.groupby(["service_lead", "calling_person"]).size()
                .reset_index(name="leads")
                .sort_values(["service_lead", "leads"], ascending=[True, False])
            )
        
        return {
            "total_leads": int(len(lead_df)),
            "unique_customers": int(lead_df["customer_id"].nunique()) if "customer_id" in lead_df.columns else 0,
            "leads_by_service": lead_df.groupby("service_lead").size().reset_index(name="leads").sort_values("leads", ascending=False) if not lead_df.empty else pd.DataFrame(),
            "leads_by_person": lead_df.groupby("calling_person").size().reset_index(name="leads").sort_values("leads", ascending=False) if not lead_df.empty else pd.DataFrame(),
            "lead_breakdown": lead_counts
        }
