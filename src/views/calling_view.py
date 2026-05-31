"""Calling Dashboard View."""

import logging
import streamlit as st
import pandas as pd
from ..models import FilterOptions
from ..viewmodels import CallingViewModel
from .components import UIComponents
from utils import DataProcessor

logger = logging.getLogger(__name__)


class CallingView:
    """UI for calling dashboard."""
    
    def __init__(self):
        self.viewmodel = CallingViewModel()
        self.ui = UIComponents()
    
    def render(self, df: pd.DataFrame, filtered_df: pd.DataFrame) -> None:
        """Render the complete calling dashboard."""
        st.subheader("📞 Calling Dashboard")
        
        # Render metrics
        self._render_metrics(filtered_df)
        
        # Render charts
        st.markdown("---")
        self._render_charts(filtered_df)
        
        # Render data table
        st.markdown("---")
        self._render_data_table(filtered_df)
        
        # Render export buttons
        st.markdown("---")
        self.ui.render_export_buttons(filtered_df, "calling_data")
    
    def _render_metrics(self, df: pd.DataFrame) -> None:
        """Render calling metrics."""
        metrics = self.viewmodel.get_calling_metrics(df)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Calls", metrics["total_calls"])
        with col2:
            st.metric("Not Connected", metrics["total_not_connected"])
        with col3:
            st.metric("Service Confirm", metrics["total_service_confirm"])
        with col4:
            st.metric("Unique Customers", metrics["unique_customers_called"])
    
    def _render_charts(self, df: pd.DataFrame) -> None:
        """Render calling charts."""
        metrics = self.viewmodel.get_calling_metrics(df)
        
        # Calls per person
        st.markdown("### Calls per Person")
        self.ui.render_bar_chart(
            metrics["calls_per_person"],
            x="calling_person",
            y="calls",
            title=""
        )
        
        # Calls over time
        st.markdown("### Calls Over Time")
        chart_df = DataProcessor.prepare_chart_data(df, "date")
        if not chart_df.empty:
            counts = chart_df.groupby(chart_df["date"].dt.to_period("D")).size().reset_index(name="calls")
            counts["date"] = counts["date"].dt.to_timestamp()
            self.ui.render_line_chart(counts, x="date", y="calls", title="")
        else:
            st.info("No data available for time chart.")
        
        # Work status breakdown
        st.markdown("### Work Status Breakdown")
        if not df.empty:
            status_counts = df["work_status"].value_counts().reset_index()
            status_counts.columns = ["work_status", "count"]
            self.ui.render_pie_chart(status_counts, values="count", names="work_status", title="")
        else:
            st.info("No data available for status breakdown.")
    
    def _render_data_table(self, df: pd.DataFrame) -> None:
        """Render calling data table."""
        self.ui.render_dataframe_table(df, "Calling Data")
