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
- 🔄 **Weekly updates** - Automated via GitHub Actions
- 📈 **7 analysis modules** - NBI, GSDI, Network Graphs, and more
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
- **StanTheMan** - 58 GS champions' breakthrough analysis
- **Network Graphs** - 7 player matchup networks with rich metadata
- **Global Evolution** - Geographic diversity trends over time
- **Career Longevity** - Survival analysis of tennis careers
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
python fetch_base_data.py         # Step 1: Fetch raw data → Parquet (2-3 min)
python build_base_metrics.py      # Step 2: Build base metrics → Parquet (30s)
python run_aggregations.py        # Step 3: Generate analyses → JSON/CSV (25s)
```

---

## 🏗️ Architecture

**3-Tier Pipeline with Parquet Storage**:

```
┌─────────────────────────────────────────────────────────────┐
│ TIER 1: Raw Data Source                                     │
│ • TML-Database (Jeff Sackmann's ATP data, 1968-2025)        │
│ • Fetched weekly, saved as Parquet (~15 MB)                 │
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
- `data/stantheman/` - Breakthrough analysis (1 file)
- `data/network/` - Network graphs (7 files)
- `data/globaltop100evolution/` - Global trends (4 files)
- `data/career_longevity/` - Survival analysis (6 files)
- `data/indian/` - India-specific (9 files)

**Total**: 35+ JSON/CSV files, updated weekly

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

GitHub Actions runs every **Monday at 00:00 UTC**:
1. Fetches latest data from TML-Database
2. Rebuilds base metrics
3. Regenerates all analyses
4. Commits and pushes updates

Manual trigger: **Actions** tab → **Update Tennis Data** → **Run workflow**

---

## 🎯 Integration with TennisAnalytics

All [TennisAnalytics](https://github.com/sorukumar/TennisAnalytics) visualizations fetch data directly from this repository:

```javascript
// Example: StanTheMan visualization
d3.csv("https://raw.githubusercontent.com/sorukumar/tml-data/main/data/stantheman/gs_breakthrough_comparison.csv")
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
| **StanTheMan** | `gs_breakthrough_comparison.csv` | 58 GS champions' paths to first title |
| **Network** | 7 JSON files | Player matchup networks with metadata |
| **Global Evolution** | 4 JSON files | Geographic diversity trends |
| **Career Longevity** | 6 JSON files | Career length survival analysis |
| **Indian Players** | 9 JSON files | India-specific datasets |

Run individual modules:
```bash
python -m aggregations.nbi
python -m aggregations.gsdi
python -m aggregations.stantheman
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
- **Update Frequency**: Weekly (automated)

---

## 🤝 Contributing

Issues and pull requests welcome! Please:
- Maintain backward compatibility for data schemas
- Update documentation for any changes
- Test with `python run_aggregations.py`

---

## 📝 Data Attribution

Raw match data sourced from:
- [TML-Database](https://github.com/Tennismylife/TML-Database) (Jeff Sackmann's ATP data)
- [Tennis Mylife Community](https://tennismylife.com)

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

**Last Updated**: January 17, 2026  
**Architecture Version**: 2.0 (Base Metrics)  
**Python**: 3.11+
