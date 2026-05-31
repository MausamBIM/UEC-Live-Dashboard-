"""ViewModel for Marketing Dashboard logic."""

import logging
import pandas as pd
from ..models import MetricsData
from .base_viewmodel import BaseViewModel

logger = logging.getLogger(__name__)


class MarketingViewModel(BaseViewModel):
    """Business logic for marketing dashboard."""
    
    def __init__(self):
        super().__init__()
    
    def calculate_metrics(self, df: pd.DataFrame) -> MetricsData:
        """Calculate marketing metrics."""
        metrics = MetricsData(
            total_items=int(len(df[df["outcome"] == "visit"])),
            key_metric_1=int(len(df[df["outcome"] == "service_confirm"])),
            key_metric_2=0,
            key_metric_3=0,
            unique_customers=int(df[df["outcome"].isin(["visit", "service_confirm"])]["customer_id"].nunique()),
        )
        return metrics
    
    def get_marketing_metrics(self, df: pd.DataFrame) -> dict:
        """Get marketing metrics as dictionary."""
        return {
            "total_visits": int(len(df[df["outcome"] == "visit"])),
            "total_service_confirm": int(len(df[df["outcome"] == "service_confirm"])),
            "unique_customers_visited": int(df[df["outcome"].isin(["visit", "service_confirm"])]["customer_id"].nunique()),
            "visits_by_person": df.groupby("marketing_person").size().reset_index(name="visits").sort_values("visits", ascending=False) if not df.empty else pd.DataFrame()
        }
