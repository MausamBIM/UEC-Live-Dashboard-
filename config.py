"""
Configuration module for the dashboard application.
Manages environment variables and application settings.
"""

import os
from typing import Optional


class Config:
    """Application configuration settings."""

    # App settings
    APP_TITLE = "Unique Engineering Center Dashboard"
    APP_ICON = "📊"
    LAYOUT = "wide"
    
    # Database
    DATABASE_PATH = os.getenv("DATABASE_PATH", "dashboard.db")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "app.log")
    
    # Feature flags
    DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"
    ENABLE_CACHING = os.getenv("ENABLE_CACHING", "True").lower() == "true"
    
    # Streamlit specific
    STREAMLIT_LOGGER_LEVEL = "warning"  # Reduce Streamlit's noise
    
    # Report types
    REPORT_TYPES = {
        "All": "all",
        "Calling": "calling",
        "Marketing": "marketing",
        "Payment": "payment"
    }
    
    # Status options
    STATUS_OPTIONS = ["All", "Completed", "Pending", "Failed"]
    
    @classmethod
    def get_database_path(cls) -> str:
        """Get database path."""
        return cls.DATABASE_PATH


def get_config() -> Config:
    """Factory function to get config instance."""
    return Config()
