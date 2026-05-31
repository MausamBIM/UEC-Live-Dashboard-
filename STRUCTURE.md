"""
COMPLETE PROJECT STRUCTURE
==========================

Alied Itesm/New Dashboard app/
│
├─ 📄 README.md                          ← YOU ARE HERE (Project overview)
├─ 📄 QUICK_START.md                     ← Copy-paste examples for common tasks
├─ 📄 ARCHITECTURE.md                    ← Visual diagrams and MVVM explanation
│
├─ 🐍 app_new.py                         ← ⭐ NEW CLEAN MAIN APP (Use this!)
├─ 🐍 app.py                             ← Old app (reference only)
│
├─ 🐍 config.py                          ← Configuration settings
├─ 🐍 db.py                              ← Database management
├─ 🐍 etl.py                             ← ETL transformations
├─ 🐍 utils.py                           ← Utility functions
│
├─ 📄 requirements.txt                   ← Python dependencies
├─ 📁 .venv/                             ← Virtual environment
├─ 📁 .git/                              ← Git repository
│
└─ 📁 src/                               ← ⭐ NEW MODULAR CODE (organized by responsibility)
   │
   ├─ 📄 __init__.py                     ← Package initialization
   ├─ 📄 README.md                       ← Detailed guide to src structure
   │
   ├─ 📁 models/                         ← 🟦 DATA STRUCTURES (what data looks like)
   │  ├─ 📄 __init__.py
   │  └─ 🐍 data_models.py               ← MetricsData, ChartData, FilterOptions classes
   │
   ├─ 📁 services/                       ← 🟩 DATA ACCESS LAYER (get & filter data)
   │  ├─ 📄 __init__.py
   │  ├─ 🐍 data_service.py              ← Load reports from database with caching
   │  ├─ 🐍 filter_service.py            ← Filter by branch, month, person
   │  └─ 🐍 google_sheet_service.py      ← Fetch data from Google Sheets
   │
   ├─ 📁 viewmodels/                     ← 🟨 BUSINESS LOGIC LAYER (how to calculate)
   │  ├─ 📄 __init__.py
   │  ├─ 🐍 base_viewmodel.py            ← Base class with common methods
   │  ├─ 🐍 calling_viewmodel.py         ← Calling dashboard metrics calculations
   │  ├─ 🐍 marketing_viewmodel.py       ← Marketing dashboard metrics calculations
   │  └─ 🐍 payment_viewmodel.py         ← Payment dashboard metrics calculations
   │
   └─ 📁 views/                          ← 🟪 UI RENDERING LAYER (show to user)
      ├─ 📄 __init__.py
      ├─ 🐍 components.py                ← Reusable UI components (charts, tables, buttons)
      ├─ 🐍 calling_view.py              ← Calling dashboard layout & rendering
      ├─ 🐍 marketing_view.py            ← Marketing dashboard layout & rendering
      └─ 🐍 payment_view.py              ← Payment dashboard layout & rendering


FILE COUNT & LINES OF CODE:
===========================

BEFORE (Old monolithic structure):
──────────────────────────────────
app.py                                  1000+ lines ❌ TOO LONG

AFTER (New modular structure):
──────────────────────────────
app_new.py                              ~100 lines ✅ Clean
src/models/data_models.py               ~50 lines
src/services/data_service.py            ~50 lines
src/services/filter_service.py          ~60 lines
src/services/google_sheet_service.py    ~50 lines
src/viewmodels/base_viewmodel.py        ~30 lines
src/viewmodels/calling_viewmodel.py     ~100 lines
src/viewmodels/marketing_viewmodel.py   ~30 lines
src/viewmodels/payment_viewmodel.py     ~30 lines
src/views/components.py                 ~100 lines
src/views/calling_view.py               ~70 lines
src/views/marketing_view.py             ~50 lines
src/views/payment_view.py               ~50 lines
─────────────────────────────────────────────────
TOTAL NEW CODE                          ~700 lines
Average file size                       50-70 lines ✅ Easy to manage!


ORGANIZATION BY RESPONSIBILITY:
===============================

Need to modify...                    Find it in...
─────────────────────────────────────────────────────────────────────
Calling dashboard metrics           src/viewmodels/calling_viewmodel.py
Calling dashboard UI                src/views/calling_view.py
Chart rendering logic               src/views/components.py
Data filtering                      src/services/filter_service.py
Data loading from database          src/services/data_service.py
Google Sheets integration           src/services/google_sheet_service.py
Filter/sort options                 src/models/data_models.py
Dashboard navigation                app_new.py (main entry)
Page configuration                  app_new.py (main entry)


DEPENDENCY GRAPH:
=================

app_new.py (Main Entry)
    │
    ├──> Views/
    │     ├──> CallingView
    │     ├──> MarketingView
    │     └──> PaymentView
    │          │
    │          └──> ViewModels/
    │               ├──> CallingViewModel
    │               ├──> MarketingViewModel
    │               └──> PaymentViewModel
    │                    │
    │                    └──> Services/
    │                         ├──> FilterService
    │                         └──> DataService
    │                              │
    │                              └──> Models/
    │                                   ├──> FilterOptions
    │                                   ├──> MetricsData
    │                                   └──> ChartData
    │
    └──> Services/
         ├──> DataService
         ├──> FilterService
         └──> GoogleSheetService


WHAT EACH DIRECTORY IS RESPONSIBLE FOR:
========================================

src/models/
───────────
Responsibility: Define data structures
Files: data_models.py
Contains:
  - MetricsData (metrics with values and breakdowns)
  - ChartData (chart configuration and data)
  - FilterOptions (filter criteria)
Dependencies: None (independent)
Used by: Views, ViewModels, Services
Imports: pandas, dataclasses


src/services/
─────────────
Responsibility: Access data and provide operations
Files: data_service.py, filter_service.py, google_sheet_service.py
Contains:
  - DataService: Load and cache data from database
  - FilterService: Filter dataframes by criteria
  - GoogleSheetService: Fetch from Google Sheets
Dependencies: db.py, etl.py
Used by: Views, ViewModels
Imports: pandas, logging, requests


src/viewmodels/
───────────────
Responsibility: Business logic and calculations
Files: base_viewmodel.py, calling/marketing/payment_viewmodel.py
Contains:
  - BaseViewModel: Common logic (filtering, getting months, etc.)
  - CallingViewModel: Calculate calling metrics
  - MarketingViewModel: Calculate marketing metrics
  - PaymentViewModel: Calculate payment metrics
Dependencies: Services, Models
Used by: Views
Imports: pandas, logging (NO STREAMLIT!)


src/views/
──────────
Responsibility: UI rendering and layout
Files: components.py, calling/marketing/payment_view.py
Contains:
  - UIComponents: Reusable UI utilities (charts, tables, buttons)
  - CallingView: Render calling dashboard
  - MarketingView: Render marketing dashboard
  - PaymentView: Render payment dashboard
Dependencies: ViewModels, Models
Used by: app_new.py
Imports: streamlit (ONLY HERE!)


LAYERED ARCHITECTURE VISUALIZATION:
===================================

┌─────────────────────────────────────────────┐
│           PRESENTATION (UI)                 │
│        app_new.py (Entry Point)             │
├─────────────────────────────────────────────┤
│           VIEWS (Rendering)                 │
│  CallingView, MarketingView, PaymentView    │
├─────────────────────────────────────────────┤
│       VIEWMODELS (Business Logic)           │
│ CallingVM, MarketingVM, PaymentVM, BaseVM  │
├─────────────────────────────────────────────┤
│        SERVICES (Data Operations)           │
│ DataService, FilterService, SheetService    │
├─────────────────────────────────────────────┤
│          MODELS (Data Structures)           │
│      MetricsData, FilterOptions, etc        │
├─────────────────────────────────────────────┤
│        DATA LAYER (Persistence)             │
│       db.py, config.py, etl.py              │
└─────────────────────────────────────────────┘


IMPORT RULES:
=============

✅ ALLOWED (Best practices):
  Views ──import──> ViewModels
  Views ──import──> Components
  ViewModels ─> Services
  ViewModels ─> Models
  Services ──> Models
  Services ──> db, etl, config

❌ NOT ALLOWED (Creates circular dependencies):
  ViewModels ──import──> Views (NO!)
  Services ──import──> Views (NO!)
  Models ──import──> Services (NO!)
  Anything ──import──> Streamlit except Views (NO!)


═════════════════════════════════════════════════════════════════════════════

HOW TO START:
═════════════

1. Read: README.md (this directory)
2. Run: streamlit run app_new.py
3. Learn: Read src/README.md for detailed explanations
4. Reference: Check QUICK_START.md for copy-paste examples
5. Modify: Edit files as per ARCHITECTURE.md patterns

═════════════════════════════════════════════════════════════════════════════
"""
