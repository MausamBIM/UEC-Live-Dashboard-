"""Data models and structures for metrics and analytics."""

from dataclasses import dataclass, field
from typing import Dict, Any
import pandas as pd


@dataclass
class MetricsData:
    """Container for dashboard metrics."""
    
    total_items: int = 0
    key_metric_1: int = 0
    key_metric_2: int = 0
    key_metric_3: int = 0
    unique_customers: int = 0
    breakdown_data: pd.DataFrame = field(default_factory=pd.DataFrame)
    detailed_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "total": self.total_items,
            "metric_1": self.key_metric_1,
            "metric_2": self.key_metric_2,
            "metric_3": self.key_metric_3,
            "customers": self.unique_customers,
            "details": self.detailed_metrics
        }


@dataclass
class ChartData:
    """Container for chart visualization data."""
    
    title: str
    data: pd.DataFrame
    chart_type: str  # 'bar', 'line', 'pie', etc.
    x_axis: str = ""
    y_axis: str = ""
    group_by: str = ""
    
    def is_valid(self) -> bool:
        """Check if chart data is valid."""
        return not self.data.empty


@dataclass
class FilterOptions:
    """Filter criteria for data queries."""
    
    branch: str = "All Branches"
    month: str = "All"
    person: str = "All"
    
    def is_all(self) -> bool:
        """Check if all filters are set to 'All'."""
        return (self.branch == "All Branches" and 
                self.month == "All" and 
                self.person == "All")
