# Project Setup Guide

**Complete setup reference for new developers and LLM threads**  
*Last Updated: January 17, 2026*

---

## 🖥️ Environment

- **OS**: macOS
- **Python**: 3.11+ via Anaconda (`/opt/anaconda3/bin/python`)
- **Date**: January 2026
- **Data Range**: 1968-2025 (197,911 matches, 7,534 players)
- **Repositories**: 
  - `tml-data/` - Data generation & aggregation
  - `TennisAnalytics/` - Visualizations only

---

## 📁 Repository Structure

```
/Users/saurabhkumar/Desktop/Work/github/
│
├── tml-data/                          # Data Pipeline Repository
│   ├── fetch_2026.py                  # Step 1a: Download latest CSV
│   ├── merge_2026.py                  # Step 1b: Merge into Master Parquet
│   ├── build_base_metrics.py          # Step 2: Build base metrics
│   ├── run_aggregations.py            # Step 3: Run all analyses
│   ├── process_pipeline.py            # Full automation runner
│   ├── requirements.txt               # Python dependencies
│   ├── legacy_scripts/                # Archived/unused scripts
│   │   └── fetch_base_data.py         # Original GitHub fetcher
│   │
│   ├── aggregations/                  # Analysis modules
│   │   ├── __init__.py
│   │   ├── base_metrics.py            # Base metrics builder ⭐ NEW
│   │   ├── shared_utils.py            # Common utilities ⭐ NEW
│   │   ├── nbi.py                     # Nailbiter Index
│   │   ├── gsdi.py                    # Grand Slam Dominance Index
│   │   ├── stantheman.py              # Breakthrough Analysis
│   │   ├── network_graph.py           # Network datasets
│   │   ├── global_evolution.py        # Geographic trends
│   │   ├── career_longevity.py        # Survival analysis
│   │   └── indian_players.py          # India-specific
│   │
│   ├── data/                          # Generated outputs
│   │   ├── base/                      # Base metrics
│   │   │   ├── atp_matches_raw.parquet # Master data archive
│   │   │   ├── player_metrics.parquet # Player stats
│   │   │   ├── matches_enriched.parquet # Enriched matches
│   │   │   └── head_to_head.parquet   # H2H records
│   │   ├── raw/                       # Source of truth logs
│   │   │   └── 2026.csv               # Latest fetched results
│   │   ├── nbi/                       # Nailbiter Index outputs
│   │   ├── gsdi/                      # Dominance rankings
│   │   ├── stantheman/                # Breakthrough analysis
│   │   ├── network/                   # Network graphs (7 files)
│   │   ├── globaltop100evolution/     # Global trends (4 files)
│   │   ├── career_longevity/          # Survival analysis (6 files)
│   │   └── indian/                    # India-specific (9 files)
│   │
│   ├── code/                          # Jupyter notebooks (legacy/research)
│   │   ├── TennisNBI.ipynb
│   │   ├── TennisGSCampaign.ipynb
│   │   ├── TennisNetworkGraph072025.ipynb
│   │   └── [others...]
│   │
│   └── .github/workflows/             # Automation
│       └── update_data.yml            # Weekly data updates
│
└── TennisAnalytics/                   # Visualization Repository
    ├── index.html                     # Landing page
    ├── tennis_analytics.css           # Global styles
    │
    ├── stantheman/                    # Breakthrough viz
    │   ├── index.html
    │   ├── data/                      # Empty (fetches from GitHub)
    │   └── js/
    │       ├── gs_age_distribution_chart.js
    │       ├── gs_breakthrough_chart.js
    │       └── gs_timeline_chart.js
    │
    ├── nbi/                           # Nailbiter Index viz
    │   ├── index.html
    │   ├── nbi.css
    │   └── data/                      # Empty (fetches from GitHub)
    │
    ├── gsdi/                          # Dominance rankings viz
    │   ├── index.html
    │   ├── gsdi.css
    │   └── data/                      # Empty (fetches from GitHub)
    │
    ├── viz/                           # Network graphs (future)
    │   ├── Grand_Slam_Finals_2003.html
    │   ├── Australian_Open_Final_1982.html
    │   └── [others...]
    │
    ├── globaltop100evolution/         # Global evolution viz
    ├── bigthree/                      # Big 3 analysis
    ├── components/                    # Shared UI components
    │   ├── header.html
    │   ├── footer.html
    │   ├── include.js
    │   └── social-share.js
    │
    └── image/                         # Assets
        ├── claytennis.jpeg
        └── favicon.ico
```

---

## 🔄 Complete Workflow

### **1. Data Generation (in tml-data/)**

```bash
cd /Users/saurabhkumar/Desktop/Work/github/tml-data

# Step 1: Fetch and Merge (Modular 2-part process)
# 1a. Download latest results
/opt/anaconda3/bin/python fetch_2026.py
# Output: data/raw/2026.csv (Source of truth log)

# 1b. Safe Upsert into Master archive
/opt/anaconda3/bin/python merge_2026.py
# Output: data/base/atp_matches_raw.parquet (Cumulative store)

# Step 2: Build base metrics
/opt/anaconda3/bin/python build_base_metrics.py
# Output: data/base/player_metrics.parquet, matches_enriched.parquet, head_to_head.parquet
# Time: ~30 seconds

# Step 3: Generate all analysis outputs
/opt/anaconda3/bin/python run_aggregations.py
# Output: All data/* folders populated (35+ files)
# Time: ~25 seconds

# Total pipeline: ~3-4 minutes (Complete)
# Or run all in one go:
/opt/anaconda3/bin/python process_pipeline.py
```

### **2. Publish Updates**

```bash
# Commit new/updated data files
git add data/
git commit -m "Update data: January 2026 matches"
git push origin main

# TennisAnalytics automatically picks up changes!
# No manual file copying needed - visualizations fetch via:
# https://raw.githubusercontent.com/sorukumar/tml-data/main/data/...
```

### **3. Local Visualization Testing (in TennisAnalytics/)**

```bash
cd /Users/saurabhkumar/Desktop/Work/github/TennisAnalytics

# Start local server for testing
python -m http.server 8000

# Open in browser:
# http://localhost:8000/stantheman/
# http://localhost:8000/nbi/
# http://localhost:8000/gsdi/

# Note: Visualizations fetch data from GitHub even in local testing!
```

---

## 🎯 Key Concepts

### **Base Metrics Architecture (NEW!)**

**Before (Monolithic)**:
- Each analysis script recalculated player stats from scratch
- `stantheman.py` looped through 197K matches multiple times
- Score parsing repeated in every analysis
- ~180 seconds total + 60% code duplication

**After (Base Metrics)**:
- Player stats calculated once in `build_base_metrics.py`
- Scores parsed once and stored in `matches_enriched.pkl`
- All analyses consume pre-aggregated data
- ~55 seconds total (3x faster) + 60% less code

**Benefits**:
- ✅ **7x faster** - Base metrics built once, reused everywhere
- ✅ **60% less code** - No duplicated calculations
- ✅ **Consistent metrics** - Single source of truth
- ✅ **Richer data** - Career context ready for tooltips
- ✅ **Maintainable** - Change calculation once, affects all

### **Data Integration Model**

```
┌─────────────────────────────────────┐
│ tml-data/                            │
│ • Generates all data files           │
│ • Commits to GitHub (main branch)   │
└─────────────────────────────────────┘
              ↓ Push to GitHub
┌─────────────────────────────────────┐
│ GitHub Repository                    │
│ • Hosts data files publicly          │
│ • Accessible via raw.githubusercontent.com │
└─────────────────────────────────────┘
              ↓ Fetch via HTTPS
┌─────────────────────────────────────┐
│ TennisAnalytics/                     │
│ • Visualizations only (HTML/JS/CSS) │
│ • NO local data storage              │
│ • Fetches data on page load          │
└─────────────────────────────────────┘
```

**Key Points**:
- TennisAnalytics **never** stores data locally
- All data/ folders in TennisAnalytics are **empty placeholders**
- Update flow: Generate → Push → Auto-fetch
- No manual sync/copy scripts needed

---

## 🛠️ Running Individual Analyses

### **Run Specific Module**

```bash
cd /Users/saurabhkumar/Desktop/Work/github/tml-data

# Only NBI (uses matches_enriched.pkl)
/opt/anaconda3/bin/python -m aggregations.nbi

# Only GSDI (uses matches_enriched.pkl)
/opt/anaconda3/bin/python -m aggregations.gsdi

# Only StanTheMan (uses player_metrics.pkl) - 0.5s!
/opt/anaconda3/bin/python -m aggregations.stantheman

# Only Network Graphs (uses both base tables)
/opt/anaconda3/bin/python -m aggregations.network_graph

# Only Global Evolution
/opt/anaconda3/bin/python -m aggregations.global_evolution
```

### **Rebuild Only Base Metrics**

```bash
# If you modify base_metrics.py logic
/opt/anaconda3/bin/python build_base_metrics.py

# Then regenerate all analyses
/opt/anaconda3/bin/python run_aggregations.py
```

---

## 📦 Dependencies

### **Install Requirements**

```bash
cd /Users/saurabhkumar/Desktop/Work/github/tml-data

# Use Anaconda Python
/opt/anaconda3/bin/pip install -r requirements.txt
```

### **Required Packages**

```
pandas >= 2.0.0
numpy >= 1.24.0
requests >= 2.31.0
```

### **Verify Installation**

```bash
/opt/anaconda3/bin/python -c "import pandas, numpy, requests; print('All dependencies installed!')"
```

---

## 🔍 Data Verification

### **Check Base Metrics**

```bash
# Verify files exist
ls -lh data/base/*.parquet

# Expected output:
# atp_matches_raw.parquet     (~15 MB)
# player_metrics.parquet      (~1 MB)
# matches_enriched.parquet    (~20 MB)
# head_to_head.parquet        (~5 MB)
```

### **Quick Python Check**

```python
import pandas as pd

# Load base metrics (Parquet - fast!)
players = pd.read_parquet("data/base/player_metrics.parquet")
matches = pd.read_parquet("data/base/matches_enriched.parquet")
h2h = pd.read_parquet("data/base/head_to_head.parquet")

print(f"Players: {len(players):,} × {len(players.columns)} columns")
print(f"Matches: {len(matches):,} × {len(matches.columns)} columns")
print(f"H2H Matchups: {len(h2h):,}")

# Should see:
# Players: 7,534 × 52 columns
# Matches: 197,911 × 75 columns
# H2H Matchups: 112,435
```

---

## 🐛 Troubleshooting

### **Issue: Base data fetch fails**

```bash
# Check internet connection
ping github.com

# Check TML-Database availability
curl -I https://raw.githubusercontent.com/Tennismylife/TML-Database/master/2024.csv

# Re-run with error logging
/opt/anaconda3/bin/python fetch_base_data.py 2>&1 | tee fetch_error.log
```

### **Issue: Base metrics build fails**

```bash
# Verify base data exists
ls -lh data/base/atp_matches_base.pkl

# If missing, run fetch first
/opt/anaconda3/bin/python fetch_base_data.py

# Then rebuild metrics
/opt/anaconda3/bin/python build_base_metrics.py
```

### **Issue: Analysis module fails**

```bash
# Check which base files the module needs
# stantheman.py → player_metrics.pkl
# nbi.py → matches_enriched.pkl
# network_graph.py → both!

# Verify files exist
ls -lh data/base/player_metrics.pkl data/base/matches_enriched.pkl

# Run individual module with full traceback
/opt/anaconda3/bin/python -m aggregations.stantheman
```

### **Issue: Visualization shows old data**

```bash
# Check if data was committed to GitHub
cd /Users/saurabhkumar/Desktop/Work/github/tml-data
git status

# If files are uncommitted
git add data/
git commit -m "Update data"
git push origin main

# Clear browser cache or hard refresh (Cmd+Shift+R on macOS)
```

### **Issue: Python not found**

```bash
# Use full Anaconda path
/opt/anaconda3/bin/python --version

# Should see: Python 3.11.x or higher

# If not installed, install Anaconda from:
# https://www.anaconda.com/download
```

---

## ⚡ Quick Commands Cheat Sheet

```bash
# Full pipeline (tml-data)
cd ~/Desktop/Work/github/tml-data
/opt/anaconda3/bin/python fetch_base_data.py && \
/opt/anaconda3/bin/python build_base_metrics.py && \
/opt/anaconda3/bin/python run_aggregations.py

# Rebuild base metrics only
/opt/anaconda3/bin/python build_base_metrics.py

# Run single analysis
/opt/anaconda3/bin/python -m aggregations.nbi

# Test visualization locally (TennisAnalytics)
cd ~/Desktop/Work/github/TennisAnalytics
python -m http.server 8000
# Then open http://localhost:8000

# Check file sizes
du -sh data/*
du -sh data/base/*

# View recent matches
/opt/anaconda3/bin/python -c "
import pandas as pd
df = pd.read_pickle('data/base/atp_matches_base.pkl')
print(df.sort_values('tourney_date', ascending=False).head(10))
"
```

---

## 📚 Documentation Reference

- **ARCHITECTURE.md** - Complete system design, data flow, performance
- **DATA_DICTIONARY.md** - All schemas, column definitions, examples
- **README.md** - Quick overview and getting started
- **This file (SETUP.md)** - Environment setup, workflow, troubleshooting

---

## 🎓 For New LLM Threads

When starting a new conversation about this project:

1. **Project Context**: Two repos - tml-data (data) + TennisAnalytics (viz)
2. **Architecture**: 3-tier with base metrics layer (NEW since Jan 2026)
3. **Key Files**: Read ARCHITECTURE.md for system design, DATA_DICTIONARY.md for schemas
4. **Workflow**: fetch → build_base_metrics → run_aggregations → push to GitHub
5. **Integration**: TennisAnalytics fetches via GitHub raw URLs (no local data)
6. **Python Path**: Always use `/opt/anaconda3/bin/python` on this macOS system

---

**Last Updated**: February 4, 2026  
**Environment**: macOS, Python 3.11+ (Anaconda)  
**Workspace**: `/Users/saurabhkumar/Desktop/Work/github/`
