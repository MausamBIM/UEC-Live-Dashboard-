"""Reusable UI components."""

import io
import logging
import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Optional

logger = logging.getLogger(__name__)


class UIComponents:
    """Reusable UI component utilities."""
    
    @staticmethod
    def render_metric_row(metric_label: str, metric_value: int, col_index: int = 0) -> None:
        """Render a single metric in a column."""
        st.metric(metric_label, metric_value)
    
    @staticmethod
    def render_metrics_columns(metrics: dict, labels: list) -> None:
        """Render multiple metrics in columns."""
        cols = st.columns(len(labels))
        for idx, (label, key) in enumerate(labels):
            with cols[idx]:
                UIComponents.render_metric_row(label, metrics.get(key, 0))
    
    @staticmethod
    def render_bar_chart(df: pd.DataFrame, x: str, y: str, title: str = "") -> None:
        """Render a bar chart."""
        if df.empty:
            st.info("No data available for chart.")
            return
        
        try:
            fig = px.bar(df, x=x, y=y, title=title)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            logger.error(f"Error rendering bar chart: {e}")
            st.error("Failed to render chart")
    
    @staticmethod
    def render_line_chart(df: pd.DataFrame, x: str, y: str, title: str = "") -> None:
        """Render a line chart."""
        if df.empty:
            st.info("No data available for chart.")
            return
        
        try:
            fig = px.line(df, x=x, y=y, title=title)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            logger.error(f"Error rendering line chart: {e}")
            st.error("Failed to render chart")
    
    @staticmethod
    def render_pie_chart(df: pd.DataFrame, values: str, names: str, title: str = "") -> None:
        """Render a pie chart."""
        if df.empty:
            st.info("No data available for chart.")
            return
        
        try:
            fig = px.pie(df, values=values, names=names, title=title)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            logger.error(f"Error rendering pie chart: {e}")
            st.error("Failed to render chart")
    
    @staticmethod
    def render_export_buttons(df: pd.DataFrame, prefix: str) -> None:
        """Render CSV and Excel download buttons."""
        if df.empty:
            st.info("No data available for export.")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"{prefix}_export.csv",
                mime="text/csv",
                key=f"csv_{prefix}"
            )
        
        with col2:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Data")
            buffer.seek(0)
            st.download_button(
                label="📥 Download Excel",
                data=buffer,
                file_name=f"{prefix}_export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"excel_{prefix}"
            )
    
    @staticmethod
    def render_filter_sidebar(branches: list, months: list, persons: list) -> tuple:
        """Render filter controls in sidebar."""
        st.sidebar.markdown("### 📊 Filters")
        
        branch = st.sidebar.selectbox("Branch", branches, key="branch_filter")
        month = st.sidebar.selectbox("Month", months, key="month_filter")
        person = st.sidebar.selectbox("Person", persons, key="person_filter")
        
        if st.sidebar.button("🔄 Refresh Data"):
            return branch, month, person, True
        
        return branch, month, person, False
    
    @staticmethod
    def render_dataframe_table(df: pd.DataFrame, title: str = "") -> None:
        """Render a dataframe as a table."""
        if title:
            st.markdown(f"### {title}")
        
        if df.empty:
            st.info("No data available.")
            return
        
        st.dataframe(df, use_container_width=True)
