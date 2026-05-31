"""
REFACTORED MVVM ARCHITECTURE GUIDE
===================================

This document explains the new modular structure of your dashboard application.

DIRECTORY STRUCTURE:
====================

src/
├── models/              # Data structures
│   ├── data_models.py   # MetricsData, ChartData, FilterOptions
│   └── __init__.py
│
├── viewmodels/          # Business logic layer
│   ├── base_viewmodel.py        # Base class with common logic
│   ├── calling_viewmodel.py     # Calling dashboard logic
│   ├── marketing_viewmodel.py   # Marketing dashboard logic
│   ├── payment_viewmodel.py     # Payment dashboard logic
│   └── __init__.py
│
├── views/               # UI rendering layer
│   ├── components.py            # Reusable UI components
│   ├── calling_view.py          # Calling dashboard UI
│   ├── marketing_view.py        # Marketing dashboard UI
│   ├── payment_view.py          # Payment dashboard UI
│   └── __init__.py
│
├── services/            # Data access & operations
│   ├── data_service.py          # Data loading with caching
│   ├── filter_service.py        # Filtering operations
│   ├── google_sheet_service.py  # Google Sheets integration
│   └── __init__.py
│
├── __init__.py
└── README.md            # This file


WHAT EACH COMPONENT DOES:
=========================

MODELS (Data Structures):
- MetricsData: Holds metrics with fields like total_items, key_metrics, etc.
- ChartData: Container for visualization data
- FilterOptions: Filter criteria (branch, month, person)

SERVICES (Data Access):
- DataService: Loads and caches data from database
- FilterService: Filters dataframes by branch, month, person
- GoogleSheetService: Fetches and normalizes Google Sheets data

VIEWMODELS (Business Logic):
- BaseViewModel: Common methods for all viewmodels
- CallingViewModel: Metrics calculation for calling dashboard
- MarketingViewModel: Metrics calculation for marketing dashboard
- PaymentViewModel: Metrics calculation for payment dashboard

VIEWS (UI Components):
- UIComponents: Reusable UI utilities (charts, tables, buttons, etc.)
- CallingView: Renders calling dashboard layout and charts
- MarketingView: Renders marketing dashboard layout and charts
- PaymentView: Renders payment dashboard layout and charts


HOW TO USE:
===========

1. RUN THE APPLICATION:
   streamlit run app_new.py

2. MODIFY A METRIC CALCULATION:
   - Go to: src/viewmodels/[dashboard]_viewmodel.py
   - Find the method you want to modify (e.g., get_calling_metrics)
   - Modify the logic and save
   - Streamlit will hot-reload automatically

3. ADD A NEW CHART:
   - Go to: src/views/[dashboard]_view.py
   - Add method: _render_new_chart()
   - In render() method, call: self._render_new_chart(filtered_df)
   - Use UIComponents methods for rendering

4. ADD A NEW FILTER:
   - Go to: src/services/filter_service.py
   - Add filtering logic to apply_filters() method
   - Update the render_sidebar() in app_new.py to include new filter widget

5. MODIFY DATA LOADING:
   - Go to: src/services/data_service.py
   - Modify the cache_data method or add new loading methods

6. CHANGE UI STYLING:
   - Go to: app_new.py
   - Modify st.markdown() with CSS styles


WHERE TO FIND THINGS:
=====================

❌ MONOLITHIC (OLD) - All in one file (app.py):
  app.py (1000+ lines) ← You are here, can't find anything!

✅ MODULAR (NEW) - Split by responsibility:

  Find calling metrics? → src/viewmodels/calling_viewmodel.py
  Find calling UI? → src/views/calling_view.py
  Find chart rendering? → src/views/components.py
  Find data filtering? → src/services/filter_service.py
  Find data loading? → src/services/data_service.py
  Need business logic? → src/viewmodels/
  Need to render UI? → src/views/
  Need to load data? → src/services/


QUICK EXAMPLES:
===============

Example 1: Add a new metric to Calling Dashboard
────────────────────────────────────────────────
File: src/viewmodels/calling_viewmodel.py
Location: In get_calling_metrics() method, add:

    "new_metric": int(len(calling_df[calling_df["status"] == "new"]))

Then in src/views/calling_view.py, add in _render_metrics():
    with col5:
        st.metric("New Metric", metrics["new_metric"])


Example 2: Change chart title
──────────────────────────────
File: src/views/calling_view.py
Location: _render_charts() method

Change:
    st.markdown("### Calls per Person")

To:
    st.markdown("### Calls Distribution by Team Member")


Example 3: Add new filter option
────────────────────────────────
File: src/services/filter_service.py
Location: apply_filters() method

Add after branch filter:
    # Filter by status
    if hasattr(filters, 'status') and filters.status != "All":
        filtered = filtered[filtered["status"] == filters.status]

Then update FilterOptions in src/models/data_models.py to include:
    status: str = "All"


DEBUGGING:
==========

1. If data is not showing:
   - Check src/services/data_service.py - is data loading?
   - Check DataService.clear_cache() and reload

2. If chart not rendering:
   - Check src/views/components.py - UIComponents.render_bar_chart()
   - Check if dataframe is empty

3. If filters not working:
   - Check src/services/filter_service.py - apply_filters()
   - Check FilterOptions model in src/models/data_models.py


BEST PRACTICES:
===============

✅ DO:
- Keep viewmodels focused on business logic only
- Keep views focused on UI rendering only
- Use services for all data access
- Document complex calculations
- Use type hints in function signatures

❌ DON'T:
- Put Streamlit code in viewmodels
- Put data access in views
- Mix business logic with UI rendering
- Put heavy calculations in views


MIGRATING FROM OLD app.py:
==========================

The old app.py is now backed up as a reference. The new app_new.py is cleaner.
To use the new version:

1. Test the new version thoroughly
2. Rename app_new.py to app.py (or keep both and use app_new.py)
3. Keep old app.py for reference if needed

The old code is still available in the project root for reference.


ADDING NEW DASHBOARDS:
=====================

To add a new dashboard (e.g., "Support"):

1. Create: src/viewmodels/support_viewmodel.py
   - Inherit from BaseViewModel
   - Implement metrics calculation methods

2. Create: src/views/support_view.py
   - Inherit from a view
   - Implement render() method with charts

3. Update: app_new.py
   - Add "Support" to radio button options
   - Add case in render_dashboard()
   - Handle data loading

4. Add corresponding data load to data_service.py if needed

That's it! The architecture makes it easy to add new dashboards.


QUESTIONS?
==========

Refer to the individual files - they all have detailed docstrings and comments
explaining what each function does and how to use it.
"""
