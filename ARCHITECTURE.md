"""
MVVM ARCHITECTURE OVERVIEW
==========================

ARCHITECTURE DIAGRAM:
====================

┌─────────────────────────────────────────────────────────────────┐
│                      app_new.py (Main Entry)                    │
│                   - Page setup                                   │
│                   - Orchestration                                │
│                   - Sidebar/Navigation                           │
└──────────┬──────────────────────────────────────────────┬────────┘
           │                                              │
           ▼                                              ▼
    ┌──────────────┐                        ┌──────────────────────┐
    │  SERVICES    │                        │   VIEWS (UI Layer)   │
    │              │                        │                      │
    │ • DataSvc    │◄──────────────────────►│ • CallingView        │
    │ • FilterSvc  │    (depends on)        │ • MarketingView      │
    │ • SheetSvc   │                        │ • PaymentView        │
    └──────┬───────┘                        │ • UIComponents       │
           │                                └──────────┬───────────┘
           │                                           │
           │                   ┌───────────────────────┘
           │                   │
           ▼                   ▼
    ┌──────────────┐    ┌──────────────────┐
    │   MODELS     │    │   VIEWMODELS     │
    │              │    │  (Logic Layer)   │
    │ • MetricsData│◄───│ • BaseVM         │
    │ • ChartData  │    │ • CallingVM      │
    │ • FilterOpts │    │ • MarketingVM    │
    └──────────────┘    │ • PaymentVM      │
                        └──────────────────┘
           │                   ▲
           │                   │
           └───────────────────┘
          (uses data structures)


DATA FLOW:
==========

1. USER INTERACTION
   └─> Click sidebar filter
       └─> app_new.py render_sidebar()

2. DATA LOADING
   └─> Load all data
       └─> DataService.get_calling_reports()
           └─> db.py

3. FILTERING
   └─> app_new.py apply_filters()
       └─> FilterService.apply_filters()

4. BUSINESS LOGIC
   └─> View calls ViewModel
       └─> CallingViewModel.get_calling_metrics()
           └─> Calculates metrics from data

5. RENDERING
   └─> View renders UI
       └─> Uses UIComponents
           └─> Streamlit renders


REQUEST/RESPONSE CYCLE:
======================

User Interaction
    ↓
app_new.py (Main)
    ├─ Renders page
    ├─ Sidebar filters
    ├─ Loads data via Services
    └─ Passes to appropriate View
        ↓
    View (e.g., CallingView)
        ├─ Calls ViewModel methods
        │   ↓
        │ ViewModel (CallingViewModel)
        │   ├─ Calls FilterService
        │   ├─ Performs calculations
        │   ├─ Uses Models (FilterOptions, etc)
        │   └─ Returns metrics dict
        │
        ├─ Calls UIComponents for rendering
        │   └─ Renders charts, tables, metrics
        └─ Renders final UI

Result displayed to user
    ↓
User sees dashboard with data


OLD vs NEW STRUCTURE:
====================

OLD (Single File - 1000+ lines):
────────────────────────────────
app.py
├─ Import statements (line 1-30)
├─ Helper functions (line 30-200)
├─ Metrics functions (line 200-400)
├─ Rendering functions (line 400-800)
├─ Data loading (line 800-900)
├─ Sidebar/filters (line 900-1000)
└─ Main execution (line 1000+)

❌ PROBLEMS:
- Hard to find code (1000+ lines to search through)
- Hard to test individual components
- Hard to add features (where do I add it?)
- Hard to maintain (changes affect multiple parts)
- Hard to debug (too much context)


NEW (Modular - Organized by responsibility):
────────────────────────────────────────────
src/
├─ models/ (Data structures - 50 lines)
│  └─ data_models.py: MetricsData, FilterOptions, ChartData
│
├─ services/ (Data access - 150 lines)
│  ├─ data_service.py: Loading & caching
│  ├─ filter_service.py: Filtering logic
│  └─ google_sheet_service.py: Google Sheets integration
│
├─ viewmodels/ (Business logic - 200 lines)
│  ├─ base_viewmodel.py: Common logic
│  ├─ calling_viewmodel.py: Calling metrics
│  ├─ marketing_viewmodel.py: Marketing metrics
│  └─ payment_viewmodel.py: Payment metrics
│
├─ views/ (UI rendering - 200 lines)
│  ├─ components.py: Reusable UI components
│  ├─ calling_view.py: Calling dashboard UI
│  ├─ marketing_view.py: Marketing dashboard UI
│  └─ payment_view.py: Payment dashboard UI
│
└─ app_new.py (100 lines clean main)

✅ BENEFITS:
- Easy to find code (goes to specific file)
- Easy to test (each module is independent)
- Easy to add features (know where to add it)
- Easy to maintain (changes isolated to module)
- Easy to debug (smaller scope to search)
- Easy to reuse (import and use components)


FINDING THINGS - COMPARISON:
============================

OLD app.py:
───────────
Want to change calling metrics?
└─ Ctrl+F "get_calling_metrics"
└─ Scroll through 1000+ lines to find it
└─ Hope there's no other function with similar name
└─ Make changes, pray nothing breaks

NEW modular:
────────────
Want to change calling metrics?
└─ Go directly to: src/viewmodels/calling_viewmodel.py
└─ Find: get_calling_metrics() method (clearly visible)
└─ Make changes, test isolated component
└─ Push with confidence


MVVM EXPLANATION:
=================

M = Model (data structures)
    └─ What data does my application work with?
       └─ FilterOptions(branch, month, person)
       └─ MetricsData(total_items, key_metrics, etc)

V = View (UI rendering)
    └─ How do I show data to the user?
       └─ Charts, tables, metrics, buttons
       └─ CallingView.render() → displays calling dashboard
       └─ All Streamlit code here

VM = ViewModel (business logic)
    └─ How do I calculate what to display?
        └─ Metrics calculations
        └─ Data transformations
        └─ Aggregations
        └─ No UI code here!

S = Service (data access)
    └─ How do I get data?
       └─ Load from database
       └─ Filter dataframes
       └─ Cache results
       └─ Third-party integrations


BENEFITS OF MVVM:
=================

1. SEPARATION OF CONCERNS
   └─ Views don't know about data loading
   └─ Business logic doesn't know about UI
   └─ Easy to change one without affecting others

2. TESTABILITY
   └─ Can test metrics calculation without Streamlit
   └─ Can test filtering without UI
   └─ Can test data loading independently

3. REUSABILITY
   └─ Use same ViewModel in different Views
   └─ Use same UIComponent in different Dashboards
   └─ Share FilterService across all modules

4. MAINTAINABILITY
   └─ Clear structure - know where to find things
   └─ Single responsibility - each module has one job
   └─ Easy to modify - changes are localized

5. SCALABILITY
   └─ Easy to add new dashboards
   └─ Easy to add new metrics
   └─ Easy to add new data sources
"""
