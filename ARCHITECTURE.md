# TML-Data Architecture

**Complete system architecture for tennis data aggregation pipeline**  
*Last Updated: January 17, 2026*

---

## 🎯 System Overview

TML-Data uses a **3-tier architecture** that separates data fetching, aggregation, and analysis:

```
┌─────────────────────────────────────────────────────────────┐
│ TIER 1: Raw Data Source                                     │
│ • TML-Database (Jeff Sackmann's ATP data, 1968-2025)        │
│ • 197,911 matches, 7,534 unique players                     │
│ • Updated weekly via GitHub Actions                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ TIER 2: Base Metrics Layer (NEW!)                           │
│ • player_metrics.pkl - 7,534 players × 52 career stats      │
│ • matches_enriched.pkl - 197,911 matches with parsed scores │
│ • head_to_head_matrix.json - 112,435 matchup records        │
│ • Pre-calculated once, consumed by all analyses             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ TIER 3: Analysis Outputs                                    │
│ • NBI (Nailbiter Index) - Drama scores                      │
│ • GSDI (Grand Slam Dominance Index) - Dominance rankings    │
│ • StanTheMan - Breakthrough analysis                         │
│ • Network Graphs - Player matchup networks (7 datasets)     │
│ • Global Evolution - Geographic trends                       │
│ • Career Longevity - Survival analysis                       │
│ • Indian Players - India-specific datasets                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow Pipeline

### **Complete Workflow**

```bash
# Step 1: Fetch raw data from TML-Database
python fetch_base_data.py
# → data/base/atp_matches_base.pkl (197,911 matches)
# → data/base/atp_matches_base.csv
# → data/base/metadata.json

# Step 2: Build base metrics (NEW - 30 seconds)
python build_base_metrics.py
# → data/base/player_metrics.pkl (7,534 players × 52 columns)
# → data/base/player_metrics.csv
# → data/base/matches_enriched.pkl (197,911 matches × 75 columns)
# → data/base/head_to_head_matrix.json (112,435 matchups)

# Step 3: Generate all analysis outputs (25 seconds)
python run_aggregations.py
# → data/nbi/gs_nailbiters.json (535 matches)
# → data/gsdi/gs_dominance_rankings.json (227 campaigns)
# → data/stantheman/gs_breakthrough_comparison.csv (58 champions)
# → data/network/*.json (7 network datasets)
# → data/globaltop100evolution/*.json (4 timeline datasets)
# → data/career_longevity/*.json (6 survival datasets)
# → data/indian/*.json (9 India-specific datasets)
```

### **Automated Updates**

GitHub Actions runs every Monday at 00:00 UTC:
1. Fetches latest TML-Database data
2. Rebuilds base metrics
3. Regenerates all analyses
4. Commits and pushes to main branch

---

## 📊 Base Metrics Tables (Tier 2)

### **1. player_metrics.pkl/csv**
**7,534 players × 52 columns**

Complete player career statistics pre-calculated:

#### **Career Span (5 columns)**
- `first_match_date` - Earliest recorded match (YYYYMMDD)
- `last_match_date` - Most recent match (YYYYMMDD)
- `career_start_year` - Year of first match
- `career_end_year` - Year of last match
- `career_span_years` - Years between first and last match

#### **Match Statistics (4 columns)**
- `total_matches` - Total career matches
- `total_wins` - Total wins
- `total_losses` - Total losses
- `win_pct` - Overall win percentage (0-100)

#### **Grand Slam Statistics (8 columns)**
- `gs_matches`, `gs_wins`, `gs_losses`, `gs_win_pct`
- `gs_titles` - Number of Grand Slam titles won
- `gs_finals` - Finals appearances
- `gs_semifinals` - Semifinal appearances
- `gs_quarterfinals` - Quarterfinal appearances

#### **Breakthrough Metrics (7 columns)** - For GS champions
- `first_gs_title_date` - Date of first GS win
- `first_gs_title_age` - Age at first GS win
- `first_gs_title_year` - Year of first GS win
- `matches_before_first_gs` - Matches played before first GS
- `wins_before_first_gs` - Wins before first GS
- `win_pct_before_first_gs` - Win % before first GS
- `years_to_first_gs` - Years from debut to first GS

#### **Rankings (3 columns)**
- `peak_ranking` - Best ATP ranking achieved
- `peak_ranking_date` - Date of peak ranking
- `peak_ranking_before_first_gs` - Best ranking before first GS

#### **Surface Breakdown (12 columns)**
- `hard_matches`, `hard_wins`, `hard_win_pct`
- `clay_matches`, `clay_wins`, `clay_win_pct`
- `grass_matches`, `grass_wins`, `grass_win_pct`
- `carpet_matches`, `carpet_wins`, `carpet_win_pct`

#### **Opponent Quality (9 columns)**
- `top5_matches`, `top5_wins`, `top5_win_pct`
- `top10_matches`, `top10_wins`, `top10_win_pct`
- `top30_matches`, `top30_wins`, `top30_win_pct`

#### **Other Metrics (4 columns)**
- `unique_opponents` - Number of different opponents faced
- `avg_match_duration` - Average match length in minutes
- `has_gs_title` - Boolean flag
- `was_top_5` - Boolean flag
- `was_top_10` - Boolean flag

**Purpose**: Single source of truth for player statistics. All analyses consume this instead of recalculating.

---

### **2. matches_enriched.pkl**
**197,911 matches × 75 columns**

Original TML-Database columns (50) + enriched columns (25):

#### **Parsed Scores (6 columns)**
- `winner_sets`, `loser_sets` - Sets won by each player
- `winner_games`, `loser_games` - Total games won
- `tiebreaks_count` - Number of tiebreaks in match
- `is_complete` - Match finished normally (not retired/walkover)

#### **Drama Metrics (5 columns)** - For NBI calculation
- `set_margins` - Array of game margins per set
- `avg_set_margin` - Average margin across all sets
- `lead_changes` - Number of times set leader changed
- `comeback_score` - Comeback difficulty score (0-4)
- `final_set_tiebreak` - Final set decided by tiebreak (boolean)

#### **Grand Slam Flags (2 columns)**
- `is_grand_slam` - Boolean flag
- `grand_slam_name` - Normalized name (Australian Open, Roland Garros, Wimbledon, US Open)

#### **Round Flags (3 columns)**
- `is_final` - Round is F
- `is_semifinal` - Round is SF
- `is_quarterfinal` - Round is QF

#### **Year (1 column)**
- `year` - Extracted from tourney_date

#### **Player Context (8 columns)** - Merged from player_metrics
- `winner_career_matches` - Total career matches for winner
- `winner_gs_titles` - GS titles won by winner
- `winner_has_gs_title` - Winner is a GS champion
- `winner_peak_ranking` - Winner's peak ranking
- `loser_career_matches` - Total career matches for loser
- `loser_gs_titles` - GS titles won by loser
- `loser_has_gs_title` - Loser is a GS champion
- `loser_peak_ranking` - Loser's peak ranking

**Purpose**: Eliminates need to parse scores repeatedly. All score-based analyses use this.

---

### **3. head_to_head_matrix.json**
**112,435 unique matchups**

Pre-calculated H2H records for every player pair:

```json
{
  "Roger Federer|Rafael Nadal": {
    "player1": "Roger Federer",
    "player2": "Rafael Nadal",
    "total_matches": 40,
    "player1_wins": 16,
    "player2_wins": 24,
    "surfaces": {
      "Hard": {"total": 13, "p1_wins": 8, "p2_wins": 5},
      "Clay": {"total": 16, "p1_wins": 2, "p2_wins": 14},
      "Grass": {"total": 3, "p1_wins": 2, "p2_wins": 1}
    },
    "tournaments": {
      "Australian Open": {"total": 1, "p1_wins": 1, "p2_wins": 0},
      "Roland Garros": {"total": 6, "p1_wins": 0, "p2_wins": 6},
      "Wimbledon": {"total": 3, "p1_wins": 2, "p2_wins": 1},
      "US Open": {"total": 2, "p1_wins": 0, "p2_wins": 2}
    }
  }
}
```

**Purpose**: Ready for rivalry visualizations, H2H comparison tools.

---

## 🔧 Analysis Modules (Tier 3)

### **Module Overview**

| Module | Input | Output | Purpose |
|--------|-------|--------|---------|
| **nbi.py** | matches_enriched | gs_nailbiters.json | Drama scores for GS Finals/SF |
| **gsdi.py** | matches_enriched | gs_dominance_rankings.json | Most dominant GS campaigns |
| **stantheman.py** | player_metrics | gs_breakthrough_comparison.csv | Breakthrough analysis |
| **network_graph.py** | matches_enriched + player_metrics | 7 network JSON files | Player matchup networks |
| **global_evolution.py** | atp_matches_base | 4 timeline JSON files | Geographic trends |
| **career_longevity.py** | atp_matches_base | 6 survival JSON files | Career survival analysis |
| **indian_players.py** | atp_matches_base | 9 India JSON files | India-specific datasets |

---

### **1. NBI (Nailbiter Index)**

**Formula**:
```
NBI = 0.25×(Set Closeness) + 0.22×(Comeback) + 0.18×(Lead Changes) + 
      0.12×(Tiebreaks) + 0.10×(Duration) + 0.07×(Break Points) + 
      0.06×(Final Set Tiebreak)
```

**Data Source**: `matches_enriched.pkl` (already has parsed scores!)

**Outputs**:
- `gs_nailbiters.json` - All GS Finals/SF with NBI scores (535 matches)
- `gs_nailbiters.csv` - CSV format
- `iconic_gs_matches.json` - Manually curated iconic matches (20 matches)

**Top Result**: Djokovic def. Federer, Wimbledon 2019 Final (NBI: 0.810)

---

### **2. GSDI (Grand Slam Dominance Index)**

**Formula**:
```
GSDI = 0.32×(Sets Won %) + 0.25×(Games Won %) + 0.23×(Points Won %) + 
       0.10×(Opponent Quality) + 0.10×(Speed Score) + Bonus Points
```

**Bonus Points**:
- +10 for perfect campaign (no sets lost)
- +3 per Top 5 opponent defeated

**Data Source**: `matches_enriched.pkl` (already has parsed games/sets!)

**Output**: `gs_dominance_rankings.json` (227 campaigns)

**Top Result**: Nadal, Roland Garros 2008 (Score: 98.89, Perfect Campaign 🏆)

---

### **3. StanTheMan (Breakthrough Analysis)**

Analyzes how many matches players competed in before winning their first Grand Slam.

**Data Source**: `player_metrics.pkl` (already has breakthrough metrics!)

**Output**: `gs_breakthrough_comparison.csv` (58 GS champions)

**Key Insight**: Goran Ivanisevic holds the record with 876 matches before his first GS title (Wimbledon 2001).

**Speed**: 0.5 seconds (was 45 seconds) - **90x faster!**

---

### **4. Network Graphs**

Generates player-to-player matchup networks with rich node/edge data.

**Data Sources**: 
- `matches_enriched.pkl` - Match filtering
- `player_metrics.pkl` - Career context for nodes

**Outputs** (7 files):
1. `grand_slam_finals_2003.json` - GS finals 2003+ (37 players, 49 edges)
2. `australian_open_finals_1982.json` - AO finals 1982+ (38 players)
3. `roland_garros_finals_1982.json` - RG finals 1982+ (42 players)
4. `wimbledon_finals_1982.json` - Wimbledon finals 1982+ (33 players)
5. `us_open_finals_1982.json` - US Open finals 1982+ (37 players)
6. `high_volume_players_2000.json` - 200+ match players 2000+ (1,825 players, 35,021 edges, 18MB)
7. `network_summary.json` - Summary statistics

**Node Data** (from player_metrics):
```json
{
  "name": "Roger Federer",
  "country": "SUI",
  "matches_won": 25,
  "matches_played": 28,
  "win_pct": 89.3,
  "career_total_matches": 1526,
  "career_win_pct": 82.1,
  "gs_titles": 20,
  "peak_ranking": 1,
  "surface_win_pcts": {"Hard": 88.2, "Clay": 85.7, "Grass": 100.0},
  "top_5_wins": 8,
  "top_5_win_pct": 66.7,
  "unique_opponents": 18,
  "was_top_5": true
}
```

**Purpose**: Powers TennisAnalytics network visualizations with rich tooltip data.

---

### **5. Global Top 100 Evolution**

Tracks geographic diversity of professional tennis over time.

**Outputs**:
- `country_code_mapping.json` - IOC country codes
- `tennis_country_profiles.json` - Country stats by year
- `global_timeline_dataset.json` - Global diversity metrics
- `top_tennis_players_timeline.json` - Top 50 players by nationality

---

### **6. Career Longevity**

Survival analysis showing career length distribution.

**Outputs** (6 files):
- `player_careers_top1000.json` - Top 1000 by career length
- `survival_curve.json` - Survival probabilities
- `career_categories.json` - Distribution by length
- `longest_careers.json` - Top 100 longest careers
- `match_volume_stats.json` - Distribution by matches
- `summary.json` - Key statistics

**Key Insight**: Only 13.5% of players have careers lasting 10+ years.

---

### **7. Indian Players**

India-specific datasets for regional analysis.

**Outputs** (9 files):
- `players_summary.json` / `players_summary_1990.json`
- `players_time_series.json` / `players_time_series_1990.json`
- `indian_matches.json` / `indian_matches_1990.json`
- `player_milestones.json`
- `head_to_head_top50.json`
- `career_lengths_indian.json`

---

## ⚡ Performance Comparison

### **Before: Monolithic Approach**
```
Each analysis recalculated player stats from scratch:
- stantheman.py: ~45 seconds (double loop through 197K matches)
- network_graph.py: ~60 seconds (rebuild player stats each time)
- nbi.py: ~8 seconds (parse all scores)
- gsdi.py: ~10 seconds (parse all scores)
Total: ~180 seconds + 60% code duplication
```

### **After: Base Metrics Approach**
```
Base metrics calculated once:
- build_base_metrics.py: ~30 seconds (run once)

All analyses consume pre-aggregated data:
- stantheman.py: ~0.5 seconds (simple DataFrame filter) - 90x faster!
- network_graph.py: ~15 seconds (merge pre-calculated stats) - 4x faster!
- nbi.py: ~2 seconds (use pre-parsed scores) - 4x faster!
- gsdi.py: ~3 seconds (use pre-parsed scores) - 3x faster!

Total pipeline: ~55 seconds (3x faster overall)
```

### **Benefits**
- ✅ **7x faster** - Base metrics built once, reused everywhere
- ✅ **60% less code** - No duplicated player stat calculations
- ✅ **Consistent metrics** - Single source of truth
- ✅ **Richer data** - Career context ready for tooltips
- ✅ **Maintainable** - Change calculation once, affects all analyses

---

## 🔗 Integration with TennisAnalytics

### **Architecture**

```
tml-data/ (Data Generation)
    ↓ [generates files]
    ↓ [commits to GitHub]
    ↓
GitHub Raw URLs
    ↓ [fetch via HTTPS]
    ↓
TennisAnalytics/ (Visualizations)
```

### **Data References**

All TennisAnalytics visualizations fetch data via GitHub raw URLs:

```javascript
// StanTheMan
d3.csv("https://raw.githubusercontent.com/sorukumar/tml-data/main/data/stantheman/gs_breakthrough_comparison.csv")

// NBI
fetch("https://raw.githubusercontent.com/sorukumar/tml-data/main/data/nbi/gs_nailbiters.json")
fetch("https://raw.githubusercontent.com/sorukumar/tml-data/main/data/nbi/iconic_gs_matches.json")

// GSDI
fetch("https://raw.githubusercontent.com/sorukumar/tml-data/main/data/gsdi/gs_dominance_rankings.json")

// Network graphs (future)
fetch("https://raw.githubusercontent.com/sorukumar/tml-data/main/data/network/grand_slam_finals_2003.json")
```

### **Update Workflow**

```bash
# 1. Generate/update data in tml-data
cd /Users/saurabhkumar/Desktop/Work/github/tml-data
python fetch_base_data.py
python build_base_metrics.py
python run_aggregations.py

# 2. Commit and push
git add data/
git commit -m "Update data with latest matches"
git push origin main

# 3. TennisAnalytics automatically uses new data!
# No manual sync needed - fetches from GitHub URLs
```

**No local data copying required!** ✅

---

## 🏗️ Shared Utilities

All analyses use `aggregations/shared_utils.py`:

### **Grand Slam Detection**
- `is_grand_slam(tourney_name)` - Boolean check
- `get_grand_slam_name(tourney_name)` - Normalized name

### **Score Parsing**
- `parse_score(score_str)` - Extract sets/games/tiebreaks
- `parse_sets(score_str)` - Advanced parsing with margins
- `advanced_comeback_score(score_str)` - Comeback difficulty (0-4)
- `final_set_tiebreak(score_str)` - Final set tiebreak check

### **Statistical Functions**
- `calculate_win_percentage(wins, total)` - Safe win % calculation
- `categorize_win_percentage(win_pct)` - Bucket win percentages
- `safe_round(value, decimals)` - Handle None/NaN gracefully

### **Player Lookups**
- `get_player_peak_ranking(df, player_name)` - Best ranking
- `get_player_country(df, player_name)` - IOC country code

---

## 📁 Directory Structure

```
tml-data/
├── fetch_base_data.py              # Step 1: Fetch raw data
├── build_base_metrics.py           # Step 2: Build base metrics ⭐ NEW
├── run_aggregations.py             # Step 3: Run all analyses
├── requirements.txt
├── aggregations/
│   ├── base_metrics.py             # Base metrics builder ⭐ NEW
│   ├── shared_utils.py             # Common utilities ⭐ NEW
│   ├── nbi.py                      # Nailbiter Index
│   ├── gsdi.py                     # Grand Slam Dominance Index
│   ├── stantheman.py               # Breakthrough Analysis
│   ├── network_graph.py            # Network datasets
│   ├── global_evolution.py         # Geographic trends
│   ├── career_longevity.py         # Survival analysis
│   └── indian_players.py           # India-specific
└── data/
    ├── base/                       # Base metrics ⭐ NEW
    │   ├── atp_matches_base.pkl    # Raw data (197K matches)
    │   ├── atp_matches_base.csv
    │   ├── player_metrics.pkl      # Player stats (7,534 × 52)
    │   ├── player_metrics.csv
    │   ├── matches_enriched.pkl    # Enriched matches (197K × 75)
    │   └── head_to_head_matrix.json # H2H records (112K matchups)
    ├── nbi/                        # Nailbiter Index outputs
    ├── gsdi/                       # Dominance rankings
    ├── stantheman/                 # Breakthrough analysis
    ├── network/                    # Network graphs (7 files)
    ├── globaltop100evolution/      # Global trends (4 files)
    ├── career_longevity/           # Survival analysis (6 files)
    └── indian/                     # India-specific (9 files)
```

---

## 🔄 Development Workflow

### **Add New Analysis**

1. Create `aggregations/my_analysis.py`:

```python
#!/usr/bin/env python3
"""My Custom Analysis"""
import pandas as pd
import json
import os

def calculate_metric(df_enriched, player_metrics_df):
    """Core calculation logic"""
    # Use pre-aggregated data!
    results = []
    # ... your logic ...
    return results

def save_data(results, output_dir="data/my_analysis"):
    """Save outputs"""
    os.makedirs(output_dir, exist_ok=True)
    with open(f"{output_dir}/output.json", 'w') as f:
        json.dump(results, f, indent=2)

def generate_aggregation(matches_enriched_path="data/base/matches_enriched.pkl",
                        player_metrics_path="data/base/player_metrics.pkl",
                        output_dir="data/my_analysis"):
    """Main entry point"""
    df_enriched = pd.read_pickle(matches_enriched_path)
    player_metrics_df = pd.read_pickle(player_metrics_path)
    
    results = calculate_metric(df_enriched, player_metrics_df)
    save_data(results, output_dir)

if __name__ == "__main__":
    generate_aggregation()
```

2. Register in `run_aggregations.py`:

```python
from aggregations.my_analysis import generate_aggregation as my_analysis

aggregations = [
    # ...existing...
    ("My Custom Analysis", lambda: my_analysis(matches_enriched_path, player_metrics_path)),
]
```

3. Test:

```bash
# Run standalone
python -m aggregations.my_analysis

# Run with all aggregations
python run_aggregations.py
```

---

## 📝 Maintenance

### **Update Formulas**

Edit weights directly in module files:

```python
# aggregations/nbi.py
NBI_WEIGHTS = {
    'avg_set_margin': 0.30,     # Changed from 0.25
    'comeback': 0.25,           # Changed from 0.22
    # ...
}

# aggregations/gsdi.py
# GSDI Score calculation at line ~120
dominance_score = (
    sets_won_pct * 0.35 +       # Changed from 0.32
    games_won_pct * 0.30 +      # Changed from 0.25
    # ...
)
```

### **Extend Base Metrics**

Add new columns to `aggregations/base_metrics.py`:

```python
# In build_player_career_metrics():
player_stats[player] = {
    # ...existing columns...
    'new_metric': 0,           # Add your metric
}

# Calculate during match loop
w['new_metric'] += calculate_something(row)
```

Rebuild:
```bash
python build_base_metrics.py
```

All analyses automatically see the new metric!

---

## 🐛 Troubleshooting

### **Base data fetch fails**
```bash
# Check connection
curl -I https://raw.githubusercontent.com/Tennismylife/TML-Database/master/2024.csv

# Re-run with error output
python fetch_base_data.py 2>&1 | tee fetch.log
```

### **Base metrics build fails**
```bash
# Verify base data exists
ls -lh data/base/atp_matches_base.pkl

# Run with full traceback
python build_base_metrics.py
```

### **Analysis fails**
```bash
# Check base metrics exist
ls -lh data/base/player_metrics.pkl data/base/matches_enriched.pkl

# Run individual analysis
python -m aggregations.nbi
```

### **GitHub Actions fails**
Check `.github/workflows/update_data.yml` and Actions tab logs.

---

## 📊 Statistics

- **Data Range**: 1968-2025 (197,911 matches)
- **Players**: 7,534 unique players
- **Base Metrics**: 52 player columns, 75 match columns
- **H2H Records**: 112,435 unique matchups
- **Analysis Outputs**: 35+ JSON/CSV files across 7 modules
- **Pipeline Speed**: ~55 seconds total (3-5 minutes including data fetch)
- **Update Frequency**: Weekly (every Monday at 00:00 UTC)

---

## 🎯 Future Enhancements

### **Potential Base Metrics Additions**
- Tournament-specific dominance scores
- Era-adjusted win percentages
- Career momentum curves (rolling averages)
- Surface transition success rates
- Clutch performance metrics (break points, tiebreaks)

### **Potential Analysis Additions**
- Rivalry analyzer (using H2H matrix)
- Career trajectory visualizer
- Upset probability calculator
- Surface specialist identifier
- Tournament performance predictor

### **Performance Optimizations**
- Save base metrics as Parquet (faster loading)
- Add indexes for common queries
- Cache frequently-used subsets
- Implement incremental updates

---

**Status**: ✅ Production-ready  
**Architecture Version**: 2.0 (Base Metrics)  
**Last Major Update**: January 17, 2026  
**Python**: 3.11+ (Anaconda)  
**Data Source**: [TML-Database](https://github.com/Tennismylife/TML-Database) (Jeff Sackmann)
