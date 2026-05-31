"""Service for filtering and processing data."""

import logging
import pandas as pd
from typing import Optional
from ..models import FilterOptions

logger = logging.getLogger(__name__)


class FilterService:
    """Handles data filtering operations."""
    
    @staticmethod
    def get_available_months(*dfs: pd.DataFrame) -> list:
        """Build list of available months from dataframes."""
        months = set()
        for df in dfs:
            if "date" in df.columns and not df.empty:
                try:
                    months.update(
                        pd.to_datetime(df["date"], errors="coerce")
                        .dt.to_period("M")
                        .astype(str)
                        .dropna()
                        .unique()
                    )
                except Exception as e:
                    logger.warning(f"Error extracting months: {e}")
        return ["All"] + sorted(list(months))
    
    @staticmethod
    def apply_filters(df: pd.DataFrame, filters: FilterOptions, person_column: str) -> pd.DataFrame:
        """Apply filter options to dataframe."""
        if df.empty:
            return df
        
        filtered = df.copy()
        
        # Filter by branch
        if filters.branch != "All Branches":
            filtered = filtered[filtered["branch"] == filters.branch]
        
        # Filter by month
        if filters.month != "All" and "date" in filtered.columns:
            try:
                filtered = filtered[
                    pd.to_datetime(filtered["date"], errors="coerce")
                    .dt.to_period("M")
                    .astype(str) == filters.month
                ]
            except Exception as e:
                logger.warning(f"Error filtering by month: {e}")
        
        # Filter by person
        if filters.person != "All" and person_column in filtered.columns:
            filtered = filtered[filtered[person_column] == filters.person]
        
        return filtered
    
    @staticmethod
    def get_unique_values(df: pd.DataFrame, column: str) -> list:
        """Get unique values from a column."""
        if df.empty or column not in df.columns:
            return []
        
        try:
            values = df[column].dropna().unique()
            return sorted([str(v) for v in values if str(v).strip()])
        except Exception as e:
            logger.error(f"Error getting unique values for {column}: {e}")
            return []
