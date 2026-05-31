"""Payment Dashboard View."""

import logging
import streamlit as st
import pandas as pd
from ..viewmodels import PaymentViewModel
from .components import UIComponents
from utils import format_currency

logger = logging.getLogger(__name__)


class PaymentView:
    """UI for payment dashboard."""
    
    def __init__(self):
        self.viewmodel = PaymentViewModel()
        self.ui = UIComponents()
    
    def render(self, df: pd.DataFrame, filtered_df: pd.DataFrame) -> None:
        """Render the complete payment dashboard."""
        st.subheader("💰 Payment Dashboard")
        
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
        self.ui.render_export_buttons(filtered_df, "payment_data")
    
    def _render_metrics(self, df: pd.DataFrame) -> None:
        """Render payment metrics."""
        metrics = self.viewmodel.get_payment_metrics(df)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Calls", metrics["total_calls"])
        with col2:
            st.metric("Total Collection", format_currency(metrics["total_collection"]))
        with col3:
            st.metric("Total Pending", format_currency(metrics["total_pending"]))
        with col4:
            st.metric("Unique Customers", metrics["unique_customers_contacted"])
    
    def _render_charts(self, df: pd.DataFrame) -> None:
        """Render payment charts."""
        metrics = self.viewmodel.get_payment_metrics(df)
        
        st.markdown("### Collection by Branch")
        self.ui.render_bar_chart(
            metrics["collection_by_branch"],
            x="branch",
            y="payment_received",
            title=""
        )
    
    def _render_data_table(self, df: pd.DataFrame) -> None:
        """Render payment data table."""
        self.ui.render_dataframe_table(df, "Payment Data")
