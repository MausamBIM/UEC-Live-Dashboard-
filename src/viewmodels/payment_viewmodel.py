"""ViewModel for Payment Dashboard logic."""

import logging
import pandas as pd
from ..models import MetricsData
from .base_viewmodel import BaseViewModel

logger = logging.getLogger(__name__)


class PaymentViewModel(BaseViewModel):
    """Business logic for payment dashboard."""
    
    def __init__(self):
        super().__init__()
    
    def calculate_metrics(self, df: pd.DataFrame) -> MetricsData:
        """Calculate payment metrics."""
        metrics = MetricsData(
            total_items=int(len(df)),
            key_metric_1=int(df["payment_received"].sum()),
            key_metric_2=int(df["os_amount"].sum()),
            key_metric_3=int(len(df[df["status"] == "followup"])),
            unique_customers=int(df["customer_id"].nunique()),
        )
        return metrics
    
    def get_payment_metrics(self, df: pd.DataFrame) -> dict:
        """Get payment metrics as dictionary."""
        return {
            "total_calls": int(len(df)),
            "total_collection": float(df["payment_received"].sum()),
            "total_pending": float(df["os_amount"].sum()),
            "total_not_connected": int(len(df[df["status"] == "followup"])),
            "unique_customers_contacted": int(df["customer_id"].nunique()),
            "collection_by_branch": df.groupby("branch")["payment_received"].sum().reset_index().sort_values("payment_received", ascending=False) if not df.empty else pd.DataFrame()
        }
