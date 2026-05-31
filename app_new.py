"""
Main Streamlit application for Unique Engineering Center Dashboard.

Clean MVVM architecture with modular components:
- Models: Data structures
- ViewModels: Business logic
- Views: UI rendering
- Services: Data access & filtering
"""

import logging
import streamlit as st
from config import get_config
from src.services import DataService, FilterService
from src.models import FilterOptions
from src.views import CallingView, MarketingView, PaymentView
from src.views.components import UIComponents
from utils import setup_logging

# ============================================================================
# INITIALIZATION
# ============================================================================

setup_logging(log_level="INFO", log_file="app.log")
logger = logging.getLogger(__name__)
config = get_config()

# Configure Streamlit page
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout=config.LAYOUT,
    initial_sidebar_state="expanded"
)

# Apply custom styling
st.markdown("""
    <style>
    .header-title {
        color: #0f4c81;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 10px;
    }
    .metric-card {
        background: #f7fbff;
        border-radius: 18px;
        padding: 16px;
        border: 1px solid #e5eef8;
    }
    .section-heading {
        margin-top: 24px;
        margin-bottom: 12px;
        color: #0f4c81;
    }
    </style>
""", unsafe_allow_html=True)


# ============================================================================
# DATA LOADING
# ============================================================================

@st.cache_resource
def initialize_services():
    """Initialize all services."""
    return {
        "data_service": DataService(),
        "filter_service": FilterService(),
        "ui_components": UIComponents()
    }


def load_all_data():
    """Load all required data."""
    return {
        "calling": DataService.get_calling_reports(),
        "marketing": DataService.get_marketing_reports(),
        "payment": DataService.get_payment_followups(),
        "branches": DataService.get_branches()
    }


# ============================================================================
# SIDEBAR & FILTERS
# ============================================================================

def render_sidebar(data: dict) -> tuple:
    """Render sidebar with filters and navigation."""
    
    st.sidebar.title("📊 Dashboard Navigation")
    
    # Tab selection
    dashboard_type = st.sidebar.radio(
        "Select Dashboard",
        ["Calling", "Marketing", "Payment"],
        index=0
    )
    
    st.sidebar.markdown("---")
    
    # Get appropriate data based on dashboard type
    if dashboard_type == "Calling":
        current_data = data["calling"]
        person_column = "calling_person"
    elif dashboard_type == "Marketing":
        current_data = data["marketing"]
        person_column = "marketing_person"
    else:  # Payment
        current_data = data["payment"]
        person_column = "calling_person"
    
    # Build filter options
    branches = ["All Branches"] + (["All Branches"] if data["branches"] is None else data["branches"])
    months = FilterService.get_available_months(
        data["calling"], data["marketing"], data["payment"]
    )
    persons = ["All"] + FilterService.get_unique_values(current_data, person_column)
    
    # Render filter controls
    st.sidebar.markdown("### 🔍 Filters")
    selected_branch = st.sidebar.selectbox("Branch", branches, key="branch_filter")
    selected_month = st.sidebar.selectbox("Month", months, key="month_filter")
    selected_person = st.sidebar.selectbox("Person", persons, key="person_filter")
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        DataService.clear_cache()
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**About**: Engineering Center Dashboard")
    
    return (
        dashboard_type,
        FilterOptions(
            branch=selected_branch,
            month=selected_month,
            person=selected_person
        )
    )


# ============================================================================
# MAIN DASHBOARD LOGIC
# ============================================================================

def apply_filters(df, filters, person_column):
    """Apply filters to dataframe."""
    return FilterService.apply_filters(df, filters, person_column)


def render_dashboard(dashboard_type: str, data: dict, filters: FilterOptions) -> None:
    """Render the selected dashboard."""
    
    if dashboard_type == "Calling":
        calling_df = data["calling"]
        filtered_df = apply_filters(calling_df, filters, "calling_person")
        view = CallingView()
        view.render(calling_df, filtered_df)
    
    elif dashboard_type == "Marketing":
        marketing_df = data["marketing"]
        filtered_df = apply_filters(marketing_df, filters, "marketing_person")
        view = MarketingView()
        view.render(marketing_df, filtered_df)
    
    elif dashboard_type == "Payment":
        payment_df = data["payment"]
        filtered_df = apply_filters(payment_df, filters, "calling_person")
        view = PaymentView()
        view.render(payment_df, filtered_df)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main application entry point."""
    
    # Page title
    st.markdown('<h1 class="header-title">📊 Unique Engineering Center Dashboard</h1>', unsafe_allow_html=True)
    
    # Initialize services
    initialize_services()
    
    # Load data
    with st.spinner("Loading data..."):
        data = load_all_data()
    
    # Render sidebar and get selections
    dashboard_type, filters = render_sidebar(data)
    
    # Render selected dashboard
    try:
        render_dashboard(dashboard_type, data, filters)
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}")
        st.error(f"An error occurred: {str(e)}")
        st.info("Please refresh the page or contact support.")


if __name__ == "__main__":
    main()
