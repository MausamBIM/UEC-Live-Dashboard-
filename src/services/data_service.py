"""Service for data loading and caching.

Data is loaded from local SQLite database for fast performance.
No Google Sheets dependencies - replaced with database loading.
"""

import logging
import streamlit as st
import pandas as pd
from typing import Optional

logger = logging.getLogger(__name__)


class DataService:
    """Handles data loading with caching from database."""
    
    # Cache TTL in seconds (24 hours)
    CACHE_TTL = 86400
    
    @staticmethod
    @st.cache_data(ttl=CACHE_TTL)
    def get_calling_reports() -> pd.DataFrame:
        """
        Load calling reports from database.
        
        ✅ FAST: Loads from local SQLite database
        ✅ NO GOOGLE SHEETS: Uses database instead
        """
        from db import get_db
        try:
            df = get_db().get_calling_reports()
            logger.info(f"Loaded {len(df)} calling reports from database")
            return df
        except Exception as e:
            logger.error(f"Failed to load calling reports: {e}")
            return pd.DataFrame()
    
    @staticmethod
    @st.cache_data(ttl=CACHE_TTL)
    def get_marketing_reports() -> pd.DataFrame:
        """
        Load marketing reports from database.
        
        ✅ FAST: Loads from local SQLite database
        ✅ NO GOOGLE SHEETS: Uses database instead
        """
        from db import get_db
        try:
            df = get_db().get_marketing_reports()
            logger.info(f"Loaded {len(df)} marketing reports from database")
            return df
        except Exception as e:
            logger.error(f"Failed to load marketing reports: {e}")
            return pd.DataFrame()
    
    @staticmethod
    @st.cache_data(ttl=CACHE_TTL)
    def get_payment_followups() -> pd.DataFrame:
        """
        Load payment followups from database.
        
        ✅ FAST: Loads from local SQLite database
        ✅ NO GOOGLE SHEETS: Uses database instead
        """
        from db import get_db
        try:
            df = get_db().get_payment_followups()
            logger.info(f"Loaded {len(df)} payment followups from database")
            return df
        except Exception as e:
            logger.error(f"Failed to load payment followups: {e}")
            return pd.DataFrame()
    
    @staticmethod
    @st.cache_data(ttl=CACHE_TTL)
    def get_branches() -> list:
        """
        Load branches from database.
        
        ✅ FAST: Loads from local SQLite database
        ✅ NO GOOGLE SHEETS: Uses database instead
        """
        from db import get_db
        try:
            branches = get_db().get_branches()
            logger.info(f"Loaded {len(branches) if branches else 0} branches from database")
            return branches
        except Exception as e:
            logger.error(f"Failed to load branches: {e}")
            return []
    
    @staticmethod
    def clear_cache() -> None:
        """
        Clear all cached data.
        
        Use when:
        - Data is updated in database
        - Need to refresh from database
        - Testing data changes
        """
        if hasattr(DataService.get_calling_reports, "clear"):
            DataService.get_calling_reports.clear()
        if hasattr(DataService.get_marketing_reports, "clear"):
            DataService.get_marketing_reports.clear()
        if hasattr(DataService.get_payment_followups, "clear"):
            DataService.get_payment_followups.clear()
        if hasattr(DataService.get_branches, "clear"):
            DataService.get_branches.clear()
        logger.info("Cache cleared - data will be reloaded from database")
