# TML-Data: Tennis Analytics Data Pipeline

**Pre-aggregated tennis statistics (1968-2025) with base metrics architecture**  
*Powers [TennisAnalytics](https://sorukumar.github.io/TennisAnalytics/) visualizations*

[![Update Data](https://github.com/sorukumar/tml-data/actions/workflows/update_data.yml/badge.svg)](https://github.com/sorukumar/tml-data/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 What This Is

Automated tennis data pipeline that fetches, processes, and aggregates ATP match data from the [TML-Database](https://github.com/Tennismylife/TML-Database). Generates analytics-ready datasets for visualizations, research, and applications.

**Key Features**:
- 📊 **197,911 matches** (1968-2025) with 7,534 unique players
- ⚡ **Base metrics layer** - Pre-calculated player/match statistics (7x faster)
- 📦 **Parquet storage** - Compact, fast, portable intermediate files (~80% smaller)
- 🔄 **Monthly updates** - Automated via GitHub Actions (1st of month)
- 📈 **9 analysis modules** - NBI, GSDI, Greatness Race, Network Graphs, and more
- 🌐 **Direct integration** - TennisAnalytics fetches via GitHub raw URLs

---

## 📊 Key Outputs

### **Base Metrics Tables** (Parquet format)
| File | Description | Size |
|------|-------------|------|
| `atp_matches_raw.parquet` | Raw fetched data | ~15 MB |
| `player_metrics.parquet` | 7,534 players × 52 career stats | ~1 MB |
| `matches_enriched.parquet` | 197,911 matches with parsed scores | ~20 MB |
| `head_to_head.parquet` | 112,435 H2H matchup records | ~5 MB |

### **Analysis Datasets** (JSON/CSV for visualizations)
- **NBI** (Nailbiter Index) - 535 dramatic GS Finals/SF ranked by drama
- **GSDI** (Grand Slam Dominance Index) - 227 most dominant GS campaigns
- **gs-breakthrough** - 58 GS champions' breakthrough analysis
- **Network Graphs** - 7 player matchup networks with rich metadata
- **Global Evolution** - Geographic diversity trends over time
- **Career Longevity** - Survival analysis of tennis careers
- **Greatness Race** - Career trajectory comparisons (Djoker/Nadal/Fed/Alcaraz/Sinner)
- **Young Guns** - Breakthrough evolution of next-gen stars
- **Indian Players** - India-specific datasets

---

## ⚡ Quick Start

### **Using the Data**

All visualization data files are publicly accessible via GitHub:

```javascript
// Fetch from GitHub in your application
const baseUrl = 'https://raw.githubusercontent.com/sorukumar/tml-data/main/data';

// Example: Load NBI data
fetch(`${baseUrl}/nbi/gs_nailbiters.json`)
  .then(r => r.json())
  .then(matches => console.log(matches));
```

```python
# In Python - load Parquet for analysis
import pandas as pd

# Load player metrics (Parquet - fast!)
players = pd.read_parquet(
    'https://raw.githubusercontent.com/sorukumar/tml-data/main/data/base/player_metrics.parquet'
)

# Or load enriched matches
matches = pd.read_parquet('data/base/matches_enriched.parquet')
```

### **Running Locally**

```bash
# Clone the repository
git clone https://github.com/sorukumar/tml-data.git
cd tml-data

# Install dependencies
pip install -r requirements.txt

# Run the complete pipeline
python fetch_2026.py             # Step 1a: Fetch latest CSV (audit log)
python merge_2026.py             # Step 1b: Merge into Master Parquet database
python build_base_metrics.py      # Step 2: Build base metrics → Parquet (30s)
python run_aggregations.py        # Step 3: Generate analyses → JSON/CSV (25s)
```

---

## 🏗️ Architecture

**3-Tier Pipeline with Parquet Storage**:

```
┌─────────────────────────────────────────────────────────────┐
│ TIER 1: Raw Data Source (Hybrid)                            │
│ • Historical: Sackmann ATP archive (1968-2025)              │
│ • Fresh: Tennismylife Stats Portal (2026+)                  │
│ • Fetched monthly, saved as Parquet (~15 MB)                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ TIER 2: Base Metrics Layer (Parquet)                        │
│ • player_metrics.parquet - 7,534 players × 52 stats         │
│ • matches_enriched.parquet - 197K matches with parsed scores│
│ • head_to_head.parquet - 112K matchup records               │
│ • Pre-calculated once, consumed by all analyses             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ TIER 3: Analysis Outputs (JSON/CSV for viz)                 │
│ • NBI, GSDI, StanTheMan, Network Graphs, etc.               │
│ • Format chosen per visualization needs                      │
└─────────────────────────────────────────────────────────────┘
```

**Why Parquet for Intermediate Files?**
- ✅ **80% smaller** than CSV+Pickle (~40 MB vs ~270 MB)
- ✅ **Faster loading** than CSV (columnar format)
- ✅ **Portable** across Python versions (unlike Pickle)
- ✅ **Compressed** with zstd for optimal size/speed

See [ARCHITECTURE.md](ARCHITECTURE.md) and [DATA_DICTIONARY.md](DATA_DICTIONARY.md) for complete details.

---

## 📁 Data Files

### **Base Metrics** (`data/base/`)
```
data/base/
├── atp_matches_raw.parquet     # Raw fetched data (~15 MB)
├── player_metrics.parquet      # Player career stats (~1 MB)
├── matches_enriched.parquet    # Enriched matches (~20 MB)
├── head_to_head.parquet        # H2H records (~5 MB)
└── metadata.json               # Fetch metadata
```

### **Analysis Outputs** (JSON/CSV)
- `data/nbi/` - Nailbiter Index (3 files)
- `data/gsdi/` - Grand Slam Dominance Index (1 file)
- `data/gs-breakthrough/` - Breakthrough analysis (1 file)
- `data/network/` - Network graphs (7 files)
- `data/globaltop100evolution/` - Global trends (4 files)
- `data/career_longevity/` - Survival analysis (6 files)
- `data/indian/` - India-specific (9 files)

**Total**: 35+ JSON/CSV files, updated monthly

---

## 🎾 Optional Source: Point-by-Point Tape

Everything above is **match-level**: one row per match with a parsed final score.
An optional, opt-in fetcher can add a second grain — the **point-by-point tape** of
a match (every recorded score state, the server, tiebreak flag, and the provider's
per-point win probability) — from the [Live Tennis API](https://livetennisapi.com),
covering **January 2023 onward**.

This is useful where a final score is currently doing the work of in-match detail:
NBI, for example, infers drama from the end state because the end state is all the
TML layer holds. A tape lets that be measured instead of inferred.

**It is entirely optional.** Without `LIVETENNISAPI_KEY` in the environment the
script prints a notice, writes nothing and exits 0. Nothing in the existing
pipeline reads its output, the monthly workflow is unchanged, and no new
dependency is added (`requests`, `pandas` and `pyarrow` are already required).

```bash
export LIVETENNISAPI_KEY=...     # https://livetennisapi.com

# Completed matches for a month, with each match's tape coverage
python scripts/fetch_livetennisapi.py --from 2026-07-01 --to 2026-07-31

# ...and the actual tapes for the first 200 of them (one request per match)
python scripts/fetch_livetennisapi.py --from 2026-07-01 --to 2026-07-31 --tapes 200

# Offline parsing checks — no key and no network needed
python scripts/fetch_livetennisapi.py --selftest
```

Output lands in `data/livetennisapi/`:

| File | Description |
|------|-------------|
| `history_matches.parquet` | One row per completed match + its tape coverage |
| `tape_points.parquet` | One row per tape row (only written with `--tapes`) |
| `metadata.json` | Provenance: range, counts, coverage histogram |

**Two things to know before using the data:**

1. **It is not joined to TML.** The files keep the provider's own match and player
   ids and are deliberately *not* merged into `data/base/`. Fuzzy-matching player
   names across two tennis providers is wrong often enough that a name-joined
   dataset would quietly corrupt the aggregations that read `data/base/`. A join
   should be an explicit, reviewed crosswalk (like `mcp_player_crosswalk.parquet`),
   not a side effect of a fetch.
2. **Check `tape_coverage` before treating a tape as complete.** It records how the
   rows were obtained — watched live (`from_start`, `partial`) or expanded after the
   fact (`reconstructed`, `reconstructed_partial`). `reconstructed_partial` is known
   *not* to cover the whole match. Rows expanded after the fact carry a null
   `timestamp` and null model fields; nothing is filled in to hide that.

---

## 🔧 Usage Examples

### **Get Grand Slam Champions**

```python
import pandas as pd

# Load player metrics (Parquet)
players = pd.read_parquet("data/base/player_metrics.parquet")

# Filter GS champions
champions = players[players['has_gs_title'] == True]

# Sort by total GS titles
top_players = champions.nlargest(10, 'gs_titles')
print(top_players[['player_name', 'gs_titles', 'career_span_years']])
```

### **Analyze Dramatic Matches**

```python
# Load enriched matches (Parquet)
matches = pd.read_parquet("data/base/matches_enriched.parquet")

# Get GS finals with comebacks from 2 sets down
epic_comebacks = matches[
    (matches['is_grand_slam'] == True) &
    (matches['is_final'] == True) &
    (matches['comeback_score'] >= 2)
]

print(f"Found {len(epic_comebacks)} epic comebacks in GS finals")
```

### **Access H2H Data**

```python
# Load H2H matrix (Parquet)
h2h = pd.read_parquet("data/base/head_to_head.parquet")

# Find Federer-Nadal rivalry
rivalry = h2h[
    ((h2h['player1'] == 'Roger Federer') & (h2h['player2'] == 'Rafael Nadal')) |
    ((h2h['player1'] == 'Rafael Nadal') & (h2h['player2'] == 'Roger Federer'))
]
print(rivalry)
```

---

## 🔄 Automated Updates

GitHub Actions runs on the **1st of every month at 00:00 UTC**:
1. Fetches latest matches from Tennismylife Stats Portal
2. Safely merges them into the master archive
3. Rebuilds base metrics and all analysis products
4. Commits and pushes updates automatically

Manual trigger: **Actions** tab → **Update Tennis Data** → **Run workflow**

---

## 🎯 Integration with TennisAnalytics

All [TennisAnalytics](https://github.com/sorukumar/TennisAnalytics) visualizations fetch data directly from this repository:

```javascript
// Example: gs-breakthrough visualization
d3.csv("https://raw.githubusercontent.com/sorukumar/tml-data/main/data/gs-breakthrough/gs_breakthrough_comparison.csv")
  .then(data => {
    // Render visualization
  });
```

**No local data storage needed** - visualizations always use the latest data from GitHub!

---

## 📊 Analysis Modules

| Module | Output | Description |
|--------|--------|-------------|
| **NBI** | `gs_nailbiters.json` | Drama scores for 535 GS Finals/SF |
| **GSDI** | `gs_dominance_rankings.json` | 227 most dominant GS campaigns |
| **gs-breakthrough** | `gs_breakthrough_comparison.csv` | 58 GS champions' paths to first title |
| **Network** | 7 JSON files | Player matchup networks with metadata |
| **Global Evolution** | 4 JSON files | Geographic diversity trends |
| **Career Longevity** | 6 JSON files | Career length survival analysis |
| **Indian Players** | 9 JSON files | India-specific datasets |

Run individual modules:
```bash
python -m aggregations.nbi
python -m aggregations.gsdi
python -m aggregations.gs_breakthrough
```

---

## 🛠️ Requirements

- Python 3.11+
- pandas >= 2.0.0
- numpy >= 1.24.0
- requests >= 2.31.0
- pyarrow >= 12.0.0

---

## 📈 Statistics

- **Data Range**: 1968-2025
- **Total Matches**: 197,911
- **Unique Players**: 7,534
- **H2H Matchups**: 112,435
- **Analysis Files**: 35+
- **Pipeline Speed**: ~3-4 minutes (complete)
- **Update Frequency**: Monthly (automated)

---

## 🤝 Contributing

Issues and pull requests welcome! Please:
- Maintain backward compatibility for data schemas
- Update documentation for any changes
- Test with `python run_aggregations.py`

---

## 📝 Data Attribution

Raw match data sourced from:
- [TML-Database](https://github.com/Tennismylife/TML-Database) (Jeff Sackmann's archive)
- [Tennismylife Stats Portal](http://stats.tennismylife.org/tennis-match-database) (Live updates)
- [Tennismylife Community](https://tennismylife.com)

Optional, opt-in only (nothing is fetched unless you configure a key):
- [Live Tennis API](https://livetennisapi.com) — point-by-point match tape, 2023+

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

The source data from TML-Database is subject to its own license terms.

---

## 🔗 Links

- **Live Visualizations**: https://sorukumar.github.io/TennisAnalytics/
- **TennisAnalytics Repo**: https://github.com/sorukumar/TennisAnalytics
- **TML-Database**: https://github.com/Tennismylife/TML-Database
- **Data Files**: https://github.com/sorukumar/tml-data/tree/main/data

---

**Last Updated**: February 4, 2026  
**Architecture Version**: 3.0 (Modular Pipeline)  
**Python**: 3.11+
