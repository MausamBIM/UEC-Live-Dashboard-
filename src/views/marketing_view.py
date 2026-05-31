"""Marketing Dashboard View."""

import logging
import streamlit as st
import pandas as pd
from ..viewmodels import MarketingViewModel
from .components import UIComponents

logger = logging.getLogger(__name__)


class MarketingView:
    """UI for marketing dashboard."""
    
    def __init__(self):
        self.viewmodel = MarketingViewModel()
        self.ui = UIComponents()
    
    def render(self, df: pd.DataFrame, filtered_df: pd.DataFrame) -> None:
        """Render the complete marketing dashboard."""
        st.subheader("📈 Marketing Dashboard")
        
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
        self.ui.render_export_buttons(filtered_df, "marketing_data")
    
    def _render_metrics(self, df: pd.DataFrame) -> None:
        """Render marketing metrics."""
        metrics = self.viewmodel.get_marketing_metrics(df)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Visits", metrics["total_visits"])
        with col2:
            st.metric("Service Confirm", metrics["total_service_confirm"])
        with col3:
            st.metric("Unique Customers", metrics["unique_customers_visited"])
    
    def _render_charts(self, df: pd.DataFrame) -> None:
        """Render marketing charts."""
        metrics = self.viewmodel.get_marketing_metrics(df)
        
        st.markdown("### Visits by Person")
        self.ui.render_bar_chart(
            metrics["visits_by_person"],
            x="marketing_person",
            y="visits",
            title=""
        )
    
    def _render_data_table(self, df: pd.DataFrame) -> None:
        """Render marketing data table."""
        self.ui.render_dataframe_table(df, "Marketing Data")
