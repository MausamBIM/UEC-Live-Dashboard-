"""Base ViewModel class with common functionality."""

import logging
from typing import Optional
import pandas as pd
from ..models import MetricsData, FilterOptions
from ..services import FilterService

logger = logging.getLogger(__name__)


class BaseViewModel:
    """Base class for all ViewModels."""
    
    def __init__(self):
        self.filter_service = FilterService()
    
    def apply_filters(self, df: pd.DataFrame, filters: FilterOptions, person_column: str) -> pd.DataFrame:
        """Apply filters to dataframe."""
        return self.filter_service.apply_filters(df, filters, person_column)
    
    def get_months(self, *dfs: pd.DataFrame) -> list:
        """Get available months from dataframes."""
        return self.filter_service.get_available_months(*dfs)
    
    def get_unique_persons(self, df: pd.DataFrame, person_column: str) -> list:
        """Get unique persons from dataframe."""
        if df.empty or person_column not in df.columns:
            return []
        return ["All"] + self.filter_service.get_unique_values(df, person_column)
