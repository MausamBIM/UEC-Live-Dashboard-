"""
QUICK START GUIDE - COMMON TASKS
================================

This guide shows you exactly how to do common tasks with copy-paste examples.


TASK 1: RUN THE NEW DASHBOARD
=============================

Command:
    streamlit run app_new.py

The new clean dashboard will launch. All the same functionality, but organized!


TASK 2: CHANGE A METRIC CALCULATION
===================================

Example: Add "Total Service Calls" metric to Calling Dashboard

Step 1: Open file
    src/viewmodels/calling_viewmodel.py

Step 2: Find method
    def get_calling_metrics(self, df: pd.DataFrame) -> dict:

Step 3: Add new metric to returned dictionary
    Original return statement has these metrics:
        "total_calls": ...,
        "total_not_connected": ...,
        "total_service_confirm": ...,
        
    Add your new metric:
        "total_service_calls": int(len(calling_df[calling_df["work_status"] == "service_confirm"])),

Step 4: Display in UI
    File: src/views/calling_view.py
    Find: def _render_metrics(self, df: pd.DataFrame) -> None:
    
    Add new metric column:
        Original:
            col1, col2, col3, col4 = st.columns(4)
        
        New:
            col1, col2, col3, col4, col5 = st.columns(5)
            with col5:
                st.metric("Service Calls", metrics["total_service_calls"])

Done! Streamlit will reload automatically.


TASK 3: ADD A NEW CHART
=======================

Example: Add bar chart showing "Calls by Remarks Status"

Step 1: Open file
    src/views/calling_view.py

Step 2: Add new method in CallingView class
    def _render_remarks_chart(self, df: pd.DataFrame) -> None:
        \"\"\"Render calls by remarks status.\"\"\"
        metrics = self.viewmodel.get_calling_metrics(df)
        self.ui.render_bar_chart(
            metrics["remarks_status_counts"],
            x="remarks_status",
            y="count",
            title="Calls by Status"
        )

Step 3: Call it from render() method
    Add in render() method after other charts:
        st.markdown("---")
        self._render_remarks_chart(filtered_df)

Done! Chart appears in dashboard.


TASK 4: MODIFY A FILTER
=======================

Example: Change "All Branches" to show only "Kathmandu" by default

File: src/services/filter_service.py
Find: def apply_filters()

Or update default in src/models/data_models.py:
    @dataclass
    class FilterOptions:
        branch: str = "Kathmandu"  # Changed from "All Branches"
        month: str = "All"
        person: str = "All"


TASK 5: ADD A NEW FILTER OPTION
===============================

Example: Add "Status" filter to Calling Dashboard

Step 1: Update FilterOptions model
    File: src/models/data_models.py
    
    Add to FilterOptions class:
        status: str = "All"

Step 2: Update filtering logic
    File: src/services/filter_service.py
    
    In apply_filters() method, add:
        # Filter by status
        if filters.status != "All" and "work_status" in filtered.columns:
            filtered = filtered[filtered["work_status"] == filters.status]

Step 3: Add filter widget to sidebar
    File: app_new.py
    
    In render_sidebar() function, add:
        selected_status = st.sidebar.selectbox(
            "Status",
            ["All", "connected", "not_connected", "service_confirm"],
            key="status_filter"
        )
    
    Update FilterOptions:
        filters = FilterOptions(
            branch=selected_branch,
            month=selected_month,
            person=selected_person,
            status=selected_status  # Add this line
        )

Done! New filter appears in sidebar.


TASK 6: CHANGE CHART TYPE
=========================

Example: Change "Calls per Person" from bar chart to line chart

File: src/views/calling_view.py
Find: _render_charts() method

Change:
    self.ui.render_bar_chart(
        metrics["calls_per_person"],
        x="calling_person",
        y="calls",
        title=""
    )

To:
    self.ui.render_line_chart(
        metrics["calls_per_person"],
        x="calling_person",
        y="calls",
        title=""
    )

Available chart types:
    - render_bar_chart()
    - render_line_chart()
    - render_pie_chart()


TASK 7: RENAME METRIC LABEL
============================

Example: Change "Total Calls" to "Calls Made"

File: src/views/calling_view.py
Find: _render_metrics() method

Change:
    st.metric("Total Calls", metrics["total_calls"])

To:
    st.metric("Calls Made", metrics["total_calls"])


TASK 8: ADD NEW DASHBOARD TYPE
==============================

Example: Add "Customer" dashboard

Step 1: Create ViewModel
    File: src/viewmodels/customer_viewmodel.py
    
    from .base_viewmodel import BaseViewModel
    import pandas as pd
    
    class CustomerViewModel(BaseViewModel):
        def __init__(self):
            super().__init__()
        
        def get_customer_metrics(self, df: pd.DataFrame) -> dict:
            return {
                "total_customers": int(df["customer_id"].nunique()),
                "customers_by_branch": df.groupby("branch")["customer_id"].nunique()
            }

Step 2: Create View
    File: src/views/customer_view.py
    
    from ..viewmodels import CustomerViewModel
    from .components import UIComponents
    
    class CustomerView:
        def __init__(self):
            self.viewmodel = CustomerViewModel()
            self.ui = UIComponents()
        
        def render(self, df: pd.DataFrame, filtered_df: pd.DataFrame) -> None:
            st.subheader("👥 Customer Dashboard")
            metrics = self.viewmodel.get_customer_metrics(filtered_df)
            
            col1 = st.columns(1)[0]
            with col1:
                st.metric("Total Customers", metrics["total_customers"])

Step 3: Update main app
    File: app_new.py
    
    Import the view:
        from src.views import CallingView, MarketingView, PaymentView, CustomerView
    
    Update radio button:
        dashboard_type = st.sidebar.radio(
            "Select Dashboard",
            ["Calling", "Marketing", "Payment", "Customer"],
            index=0
        )
    
    Add case in render_dashboard():
        elif dashboard_type == "Customer":
            view = CustomerView()
            view.render(data["calling"], apply_filters(data["calling"], filters, "calling_person"))

Done! New dashboard appears in navigation.


TASK 9: CHANGE EXPORT FORMAT
=============================

Example: Add JSON export option

File: src/views/components.py
Find: render_export_buttons() method

Add after Excel download:
    with st.columns(3)[2]:
        json_data = df.to_json(orient="records")
        st.download_button(
            label="📥 Download JSON",
            data=json_data,
            file_name=f"{prefix}_export.json",
            mime="application/json",
            key=f"json_{prefix}"
        )


TASK 10: DEBUG EMPTY DATA
==========================

If no data shows up:

Step 1: Check data loading
    File: src/services/data_service.py
    
    Add logging:
        import logging
        logger = logging.getLogger(__name__)
        
        In get_calling_reports():
            df = get_db().get_calling_reports()
            logger.info(f"Loaded {len(df)} calling records")
            return df

Step 2: Check filters
    File: src/services/filter_service.py
    
    Add logging in apply_filters():
        logger.info(f"Before filter: {len(filtered)} rows")
        # ... filtering code ...
        logger.info(f"After filter: {len(filtered)} rows")
        return filtered

Step 3: Check cache
    In app_new.py:
        Click "🔄 Refresh Data" button to clear cache


COMMON PATTERNS:
================

Pattern 1: Add metric to ViewModel
    def get_calling_metrics(self, df: pd.DataFrame) -> dict:
        return {
            "new_metric": int(len(df[df["column"] == "value"])),
            "existing_metric": ...
        }

Pattern 2: Display metric in View
    col1.metric("Label", metrics["new_metric"])

Pattern 3: Create chart
    self.ui.render_bar_chart(dataframe, x="col1", y="col2")

Pattern 4: Filter dataframe
    filtered = self.apply_filters(df, filters, "person_column")

Pattern 5: Get unique values
    unique = FilterService.get_unique_values(df, "column")


FREQUENTLY USED IMPORTS:
======================

In ViewModels:
    from .base_viewmodel import BaseViewModel
    import pandas as pd

In Views:
    import streamlit as st
    import pandas as pd
    from ..viewmodels import SomeViewModel
    from .components import UIComponents

In Services:
    import pandas as pd
    import logging
    logger = logging.getLogger(__name__)

In Models:
    from dataclasses import dataclass, field
    import pandas as pd


CODE TEMPLATES:
===============

ViewModel Template:
────────────────
from .base_viewmodel import BaseViewModel
import pandas as pd

class MyViewModel(BaseViewModel):
    def __init__(self):
        super().__init__()
    
    def calculate_metrics(self, df: pd.DataFrame) -> dict:
        return {
            "metric_1": 0,
            "metric_2": 0
        }


View Template:
───────────
import streamlit as st
import pandas as pd
from ..viewmodels import MyViewModel
from .components import UIComponents

class MyView:
    def __init__(self):
        self.viewmodel = MyViewModel()
        self.ui = UIComponents()
    
    def render(self, df: pd.DataFrame, filtered_df: pd.DataFrame) -> None:
        st.subheader("📊 My Dashboard")
        
        # Metrics
        metrics = self.viewmodel.calculate_metrics(filtered_df)
        col1 = st.columns(1)[0]
        with col1:
            st.metric("Metric 1", metrics["metric_1"])
        
        # Charts
        st.markdown("---")
        # Add charts here
        
        # Data table
        self.ui.render_dataframe_table(filtered_df, "Data")
        
        # Export
        self.ui.render_export_buttons(filtered_df, "my_data")


TIPS & TRICKS:
==============

✅ Tip 1: Use copy-paste from components.py for UI elements
✅ Tip 2: Keep viewmodels pure (no Streamlit code)
✅ Tip 3: Use logging.getLogger(__name__) for debugging
✅ Tip 4: Test filters on sample data first
✅ Tip 5: Restart Streamlit after modifying models or services
✅ Tip 6: Use st.write(df) to debug dataframes in sidebar
✅ Tip 7: Add type hints for better code clarity
✅ Tip 8: Cache expensive operations with @st.cache_data

❌ Never: Import Streamlit (st) in ViewModels or Services
❌ Never: Put complex UI logic in ViewModels
❌ Never: Skip documentation for new functions
❌ Never: Hardcode values - use config or models
"""
