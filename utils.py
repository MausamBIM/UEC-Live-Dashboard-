"""
Utility functions for the dashboard application.
Includes helpers for formatting, caching, and common operations.
"""

import logging
import streamlit as st
from functools import wraps
from datetime import datetime
from typing import Callable, Any
import pandas as pd

logger = logging.getLogger(__name__)


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Configure logging for the application."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[logging.StreamHandler()]
    )
    
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)
    
    logger.info(f"Logging configured with level: {log_level}")


def format_currency(value: float) -> str:
    """Format value as currency."""
    return f"${value:,.2f}"


def format_date(date_obj) -> str:
    """Format date object as readable string."""
    if isinstance(date_obj, str):
        date_obj = pd.to_datetime(date_obj)
    return date_obj.strftime("%Y-%m-%d")


def format_datetime(datetime_obj) -> str:
    """Format datetime object as readable string."""
    if isinstance(datetime_obj, str):
        datetime_obj = pd.to_datetime(datetime_obj)
    return datetime_obj.strftime("%Y-%m-%d %H:%M:%S")


def cache_with_ttl(ttl_seconds: int = 3600):
    """Decorator for caching with TTL (Time To Live)."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            cache_key = f"{func.__name__}_{args}_{kwargs}"
            
            now = datetime.now()
            
            if cache_key in st.session_state:
                cached_value, cached_time = st.session_state[cache_key]
                time_diff = (now - cached_time).total_seconds()
                
                if time_diff < ttl_seconds:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_value
            
            logger.debug(f"Cache miss for {func.__name__}, executing function")
            result = func(*args, **kwargs)
            st.session_state[cache_key] = (result, now)
            return result
        
        return wrapper
    return decorator


def safe_numeric_conversion(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float."""
    try:
        if pd.isna(value) or (isinstance(value, str) and value.strip() == ""):
            return default
        return float(value)
    except (ValueError, TypeError):
        logger.warning(f"Could not convert {value} to float, using default: {default}")
        return default


def validate_dataframe(df: pd.DataFrame, required_columns: list) -> bool:
    """Validate that DataFrame has required columns."""
    missing = set(required_columns) - set(df.columns)
    if missing:
        logger.error(f"DataFrame missing columns: {missing}")
        return False
    return True


def filter_dataframe_by_status(df: pd.DataFrame, status: str) -> pd.DataFrame:
    """Filter DataFrame by status."""
    if status == "All":
        return df
    return df[df["status"] == status]


def get_status_color(status: str) -> str:
    """Get color for status badge."""
    status_colors = {
        "Completed": "🟢",
        "Pending": "🟡",
        "Failed": "🔴"
    }
    return status_colors.get(status, "⚪")


class DataProcessor:
    """Helper class for data processing operations."""
    
    @staticmethod
    def prepare_chart_data(df: pd.DataFrame, date_column: str, value_column: str = None) -> pd.DataFrame:
        """Prepare data for charting."""
        if df.empty:
            return df
        
        df_copy = df.copy()
        df_copy[date_column] = pd.to_datetime(df_copy[date_column])
        
        if value_column and value_column in df_copy.columns:
            df_copy[value_column] = pd.to_numeric(df_copy[value_column], errors='coerce')
        
        return df_copy.sort_values(date_column)
    
    @staticmethod
    def get_status_summary(df: pd.DataFrame) -> dict:
        """Get summary of statuses in DataFrame."""
        if df.empty:
            return {"Completed": 0, "Pending": 0, "Failed": 0}
        
        return {
            "Completed": len(df[df["status"] == "Completed"]),
            "Pending": len(df[df["status"] == "Pending"]),
            "Failed": len(df[df["status"] == "Failed"])
        }


def handle_error(error: Exception, context: str = "") -> None:
    """Handle and display errors in Streamlit."""
    error_msg = f"Error {context}: {str(error)}"
    logger.error(error_msg)
    st.error(f"❌ {error_msg}")


def success_message(message: str) -> None:
    """Display success message."""
    st.success(f"✅ {message}")


def info_message(message: str) -> None:
    """Display info message."""
    st.info(f"ℹ️ {message}")
