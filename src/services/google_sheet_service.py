"""Service for handling Google Sheets integration."""

import io
import logging
import warnings
from typing import Optional

import pandas as pd
import requests

from etl import normalize_date, normalize_headers

logger = logging.getLogger(__name__)


class GoogleSheetService:
    """Handles Google Sheets data fetching and normalization."""
    
    GOOGLE_SHEET_CALLING_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vT9HPxS8RKvHXg5Jx79yN6CmcRDtr_GQCyPhsS1xX7gEMTF0CRKGPNglI7urvtto8-AE77LiuDkCIfJ/pub?output=xlsx"
    
    @staticmethod
    def fetch_from_url(url: str) -> pd.DataFrame:
        """Fetch data from Google Sheets URL."""
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
                return _clean_columns(tables[0])
        except Exception as e:
            logger.exception(f"Failed to fetch from URL: {e}")
        
        return pd.DataFrame()
    
    @staticmethod
    def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize Google Sheet headers."""
        df = normalize_headers(df)
        df = df.fillna("")
        
        # Fix common naming inconsistencies
        if "instant_id" in df.columns and "instance_id" not in df.columns:
            df["instance_id"] = df["instant_id"]
        if "remark_status" in df.columns and "remarks_status" not in df.columns:
            df["remarks_status"] = df["remark_status"]
        if "branch" not in df.columns:
            df["branch"] = "Kathmandu"
        
        return df
    
    @staticmethod
    def fetch_calling_data() -> pd.DataFrame:
        """Fetch calling data from Google Sheets."""
        return GoogleSheetService.fetch_from_url(GoogleSheetService.GOOGLE_SHEET_CALLING_URL)
