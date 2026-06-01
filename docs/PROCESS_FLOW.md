# Process Flow

This document describes every script and module in the pipeline — what it does, what data it reads, what data it writes, and how everything connects. Reading this alongside `DATA_DICTIONARY.md` gives a complete picture of how the database is built and maintained.

---

## Architecture Overview

The pipeline has three tiers:

```
┌─────────────────────────────────────────────────────────────────────┐
│  TIER 1 — RAW DATA                                                  │
│  data/raw/   (unmodified external downloads)                        │
│    ├── 2026.csv              ← fetch_2026.py                        │
│    └── mcp/                 ← fetch_mcp.py                          │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│  TIER 2 — BASE TABLES                                               │
│  data/base/  (Parquet, zstd compression)                            │
│    ├── atp_matches_raw.parquet     ← merge_2026.py                  │
│    ├── player_metrics.parquet      ← build_base_metrics.py          │
│    ├── matches_enriched.parquet    ← build_base_metrics.py          │
│    ├── head_to_head.parquet        ← build_base_metrics.py          │
│    ├── mcp_player_metrics.parquet  ← build_mcp_base_metrics.py      │
│    ├── mcp_matches_enriched.parquet← build_mcp_base_metrics.py      │
│    └── mcp_player_crosswalk.parquet← build_mcp_base_metrics.py      │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│  TIER 3 — AGGREGATION OUTPUTS                                       │
│  data/{nbi,gsdi,gs-breakthrough,greatness,...}/  (JSON, CSV)        │
│    ← run_aggregations.py                                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Entry-Point Scripts (`scripts/`)

### `process_pipeline.py` — Full Rebuild

**Purpose:** Orchestrates the entire TML pipeline in one command. Runs base metrics first, then all aggregations.

```
python scripts/process_pipeline.py
```

**Steps executed:**
1. `build_base_metrics.py` — rebuild Tier 2 TML tables
2. `run_aggregations.py` — rebuild all Tier 3 JSON outputs

**Inputs:** `data/base/atp_matches_raw.parquet` (must already exist)
**Outputs:** All Tier 2 and Tier 3 files

---

### `fetch_2026.py` — Fetch Current Year Data

**Purpose:** Downloads the current-year ATP match CSV from the TML stats portal and saves it to `data/raw/2026.csv`. Run this when new match results need to be incorporated.

```
python scripts/fetch_2026.py
```

**Source URL:** `https://stats.tennismylife.org/data/2026.csv`
**Input:** None
**Output:** `data/raw/2026.csv`
**Notes:** Each run overwrites the previous file (cumulative source — always contains all matches for the year).

---

### `merge_2026.py` — Merge Current Year Into Master

**Purpose:** Safely upserts the downloaded `2026.csv` into the master Parquet file. Uses `(tourney_id, match_num)` as the unique match key — existing records are updated, new records are appended.

```
python scripts/merge_2026.py
```

**Inputs:**
- `data/base/atp_matches_raw.parquet` (master — must exist)
- `data/raw/2026.csv` (incremental — from `fetch_2026.py`)

**Output:** `data/base/atp_matches_raw.parquet` (updated in place)

**Safety checks:**
- Aborts if the CSV is empty
- Aborts if `tourney_id` or `match_num` columns are missing
- Normalises column dtypes to match master schema before merging

---

### `build_base_metrics.py` — Build TML Base Tables

**Purpose:** Reads `atp_matches_raw.parquet` and calls `aggregations/base_metrics.py` to produce three Tier 2 Parquet tables.

```
python scripts/build_base_metrics.py
```

**Inputs:** `data/base/atp_matches_raw.parquet`
**Outputs:**
- `data/base/player_metrics.parquet`
- `data/base/matches_enriched.parquet`
- `data/base/head_to_head.parquet`

**Run before:** `run_aggregations.py`

---

### `fetch_mcp.py` — Fetch MCP Raw Files

**Purpose:** Downloads all six Match Charting Project CSV files from Jeff Sackmann's GitHub repository and saves them to `data/raw/mcp/`. Each run does a full overwrite because MCP files are cumulatively appended with no versioning.

```
python scripts/fetch_mcp.py
```

**Source:** `https://raw.githubusercontent.com/JeffSackmann/tennis_MatchChartingProject/master/`
**Input:** None
**Output:** Six files in `data/raw/mcp/`:
- `charting-m-matches.csv`
- `charting-m-points-to-2009.csv`
- `charting-m-points-2010s.csv`
- `charting-m-points-2020s.csv`
- `charting-m-stats-Overview.csv`
- `charting-m-stats-Rally.csv`

**License:** MCP data is CC BY-NC-SA 4.0 (non-commercial use only).

---

### `build_mcp_base_metrics.py` — Build MCP Base Tables

**Purpose:** Reads MCP raw CSVs and calls `aggregations/mcp_base_metrics.py` to produce three Tier 2 Parquet tables for shot-tracking analytics.

```
python scripts/build_mcp_base_metrics.py
```

**Inputs:**
- `data/raw/mcp/charting-m-matches.csv`
- `data/raw/mcp/charting-m-stats-Overview.csv`
- `data/raw/mcp/charting-m-stats-Rally.csv`
- `data/base/atp_matches_raw.parquet` (for the TML join)

**Outputs:**
- `data/base/mcp_player_metrics.parquet`
- `data/base/mcp_matches_enriched.parquet`
- `data/base/mcp_player_crosswalk.parquet`

**Prerequisite:** Run `fetch_mcp.py` first.

---

### `run_aggregations.py` — Build All Tier 3 Outputs

**Purpose:** Sequentially runs every aggregation module and writes all JSON/CSV outputs consumed by the front-end.

```
python scripts/run_aggregations.py
```

**Inputs:**
- `data/base/matches_enriched.parquet`
- `data/base/player_metrics.parquet`
- `data/base/atp_matches_raw.parquet`

**Outputs:** All JSON and CSV files in `data/nbi/`, `data/gsdi/`, `data/gs-breakthrough/`, `data/greatness/`, `data/globaltop100evolution/`, `data/career_longevity/`, `data/indian/`, `data/network/`

**Aggregations run:**
1. NBI (Nailbiter Index)
2. GSDI (Grand Slam Dominance Index)
3. GS Breakthrough
4. Network Graph
5. Global Top 100 Evolution
6. Career Longevity
7. Indian Players
8. Greatness Race
9. Young Guns Race

---

## Aggregation Modules (`aggregations/`)

### `shared_utils.py` — Shared Utilities

**Purpose:** Common helper functions imported by every other aggregation module.

**Key functions:**

| Function | Description |
|----------|-------------|
| `is_grand_slam(name)` | Returns `True` if the tournament name is one of the four Grand Slams |
| `get_grand_slam_name(name)` | Normalises GS names (e.g. handles historical variants like "Australian Championships") |
| `parse_score(score_str)` | Parses a score string like `"6-3 7-5 6-4"` into structured set data |
| `parse_sets(score_str)` | Returns list of `(winner_games, loser_games)` per set |
| `advanced_comeback_score(sets)` | Scores how dramatic a comeback was (0–3) |
| `final_set_tiebreak(sets)` | Returns 1 if the final set ended in a tiebreak |
| `calculate_win_percentage(wins, total)` | Safe division returning 0.0 on zero denominator |
| `get_player_peak_ranking(df, name)` | Looks up the career best ranking for a player |
| `get_player_country(df, name)` | Looks up the IOC country code for a player |

**Used by:** All aggregation modules.

---

### `base_metrics.py` — TML Base Table Builder

**Purpose:** Reads `atp_matches_raw.parquet` and produces three Parquet tables: player career stats, enriched matches, and head-to-head records.

**Inputs:** `atp_matches_raw.parquet`
**Outputs:** `player_metrics.parquet`, `matches_enriched.parquet`, `head_to_head.parquet`

**Key functions:**

| Function | Description |
|----------|-------------|
| `build_player_career_metrics(df)` | Loops over every player, computes all career stats including GS history, surface records, and opponent quality |
| `enrich_matches(df, player_metrics)` | Adds parsed score fields, drama indicators, and player context columns to each match row |
| `build_head_to_head(df)` | Groups all matches by sorted player pair to compute H2H records by surface |
| `generate_base_metrics(base_data_path, output_dir)` | Top-level entry point called by `build_base_metrics.py` |

**Processing steps (inside `generate_base_metrics`):**
1. Load `atp_matches_raw.parquet`
2. Build player career metrics → save `player_metrics.parquet`
3. Enrich matches using parsed scores and player lookup → save `matches_enriched.parquet`
4. Aggregate H2H records → save `head_to_head.parquet`
5. Write `metadata.json`

---

### `mcp_base_metrics.py` — MCP Base Table Builder

**Purpose:** Transforms the three MCP stats CSVs into three Parquet tables. This module handles all the complexity of the MCP data format, player name resolution, and joining back to the TML archive.

**Inputs:** MCP raw CSVs + `atp_matches_raw.parquet`
**Outputs:** `mcp_player_metrics.parquet`, `mcp_matches_enriched.parquet`, `mcp_player_crosswalk.parquet`

**Key functions:**

| Function | Description |
|----------|-------------|
| `load_matches(raw_dir)` | Loads `charting-m-matches.csv`, renames columns (`Player 1` → `player1`, `Best of` → `best_of`, etc.), converts `Date` to numeric |
| `load_overview_stats(raw_dir)` | Loads `charting-m-stats-Overview.csv`, filters to `set='Total'` rows only |
| `load_rally_stats(raw_dir)` | Loads `charting-m-stats-Rally.csv` (all rows) |
| `build_rally_zone_player_view(rally)` | Expands rally data to player-perspective: for each `{zone}-{1 or 2}` row, creates separate server-role and returner-role records with `player_won` correctly assigned |
| `build_match_zone_totals(rally)` | Extracts match-level zone totals from `row ∈ {Total, 1-3, 4-6, 7-9, 10}` rows |
| `build_player_metrics(overview, rally_player, matches)` | Aggregates serve, return, rally, and clutch metrics across all charted matches per player. Only includes players with ≥3 charted matches |
| `build_match_metrics(overview, rally, matches)` | Pivots per-player stats to P1/P2 columns per match. Adds match-level rally distribution and computed rates |
| `build_player_crosswalk(matches, tml_matches)` | Resolves MCP player names to TML names. Step 1: exact join on `(actual_date, sorted_player_pair)`. Step 2: fuzzy difflib matching at threshold 0.85 for unresolved names |
| `join_to_tml(match_stats, tml_matches)` | Joins match stats to `atp_matches_raw`. Uses two-step strategy due to date mismatch between TML (tournament week start) and MCP (actual match date). See join strategy below |
| `generate_mcp_base_metrics(raw_dir, base_data_path, output_dir)` | Top-level entry point |

**TML Join Strategy:**

TML stores `tourney_date` as the **tournament week start** (e.g. `20240701` for all Wimbledon 2024 matches). MCP stores the **actual match date** (e.g. `20240712` for the SF). A direct date-based join fails for ~89% of matches.

Instead, the join uses:

```
Step 1 (Primary — ~82% of matches):
  join key = year + normalised_tournament_name + round + sorted_player_pair

Step 2 (Fallback — ~10% of matches):
  join key = year + sorted_player_pair
  (used when tournament name doesn't align; picks first matching row)

Step 3: Remaining unmatched rows (~8%)
  tml_winner_name / tml_loser_name left as NaN
  tml_join_confidence = 'unmatched'
```

The `tml_join_confidence` column flags the method used: `primary`, `fallback`, or `unmatched`.

---

### `nbi.py` — Nailbiter Index

**Purpose:** Scores every Grand Slam Final and Semi-Final on a "drama scale" using a weighted formula.

**Input:** `matches_enriched.parquet`
**Outputs:** `data/nbi/gs_nailbiters.json`, `data/nbi/gs_nailbiters.csv`, `data/nbi/iconic_gs_matches.json`

**Formula inputs (from enriched matches):** `avg_set_margin`, `tiebreaks_count`, `lead_changes`, `comeback_score`, `bp_saved_ratio` (from raw stats), `final_set_tiebreak`, `minutes`

**Filters:** Grand Slam + Finals/SF + `is_complete = True` + year ≥ 1968

---

### `gsdi.py` — Grand Slam Dominance Index

**Purpose:** Ranks every Grand Slam-winning campaign by how dominant the champion was across all their matches in that tournament.

**Input:** `matches_enriched.parquet`
**Output:** `data/gsdi/gs_dominance_rankings.json`

**Metrics per campaign:** opponent quality (average ATP ranking of each opponent beaten), dominance (sets dropped), speed (minutes per set), and consistency.

---

### `gs_breakthrough.py` — Grand Slam Breakthrough Analysis

**Purpose:** For every Grand Slam champion, calculates how many ATP matches they played before winning their first Slam title. The "Stan The Man" analysis.

**Input:** `player_metrics.parquet`
**Output:** `data/gs-breakthrough/gs_breakthrough_comparison.csv`

**How it works:** Filters `player_metrics` to players where `has_gs_title = True`. Reads `matches_before_first_gs` and related fields pre-computed in `base_metrics.py`. Applies manual overrides from `data/gs-breakthrough/legacy_overrides.json` for pre-digital-era players.

---

### `global_evolution.py` — Global Top 100 Evolution

**Purpose:** Tracks how the geographic makeup of professional tennis has changed over decades.

**Input:** `atp_matches_raw.parquet` (full raw archive, needs full ranking data)
**Outputs:** Five JSON files in `data/globaltop100evolution/`

**How it works:** Every 5 years from 1975, identifies all players who reached the Top 100 in that year using ranking data. Groups by country. Builds year-by-year timelines and country profiles.

---

### `network_graph.py` — Network Graph

**Purpose:** Builds player network graphs for each Grand Slam. Nodes are players, edges are match results, edge weights encode win rates and rivalry strength.

**Inputs:** `matches_enriched.parquet`, `player_metrics.parquet`
**Outputs:** Seven JSON files in `data/network/`

**How it works:** For each GS (or all GS combined), filters to finals round, computes pairwise connections. Node attributes: career stats. Edge attributes: total matches, win/loss record, surface breakdown.

---

### `career_longevity.py` — Career Longevity & Survival

**Purpose:** Analyses how long professional tennis careers last — survival rates, longest careers, career length distributions.

**Input:** `atp_matches_raw.parquet` (needs full player career coverage)
**Outputs:** Six JSON files in `data/career_longevity/`

**How it works:** Groups all player appearances (as winner and loser), computes career start/end dates, builds a survival-curve by counting how many players were still active after N years.

---

### `indian_players.py` — Indian Players

**Purpose:** Builds all datasets for the Indian tennis visualization — career summaries, match records, surface performance, H2H against top opponents, year-by-year rankings.

**Input:** `atp_matches_raw.parquet`
**Outputs:** 14 JSON files in `data/indian/`

**How it works:** Filters matches to players with `winner_ioc = 'IND'` or `loser_ioc = 'IND'`. Builds time series, surface breakdowns, milestone events (first Top 50 entry, best GS result, etc.). Produces two parallel sets: all-time and 1990–present.

---

### `greatness_race.py` — Greatness Race

**Purpose:** Generates cumulative career trajectories for 10 selected players (Big 3 + historical greats + Alcaraz/Sinner) to enable age-adjusted "Who was better at age 25?" comparisons.

**Input:** `matches_enriched.parquet`
**Output:** `data/greatness/race_to_greatness.json`

**How it works:** For each target player, filters to their matches and aggregates quarterly. Converts match dates to decimal age. Output is a list of `{player, dob, trajectory: [{age, cumulative_wins, cumulative_titles, ...}]}` objects.

**Target players:** Federer, Nadal, Djokovic, Borg, Sampras, McEnroe, Lendl, Agassi, Alcaraz, Sinner.

---

### `young_guns_race.py` — Young Guns Race

**Purpose:** Same as Greatness Race but focused on the current generation of breakthrough players.

**Input:** `matches_enriched.parquet`
**Output:** `data/greatness/young_guns_race.json`

**Target players:** Alcaraz, Sinner, Fonseca, Mensik, Tien, Jodar.

---

## Full Pipeline: Step-by-Step Reference

### Initial Setup (first time only)

The historical master Parquet was built once from the TML complete archive via `legacy_scripts/fetch_base_data.py`. This step does not need to be repeated.

### Automated Updates (GitHub Actions)

A GitHub Actions workflow runs on the **1st of every month at 00:00 UTC** and executes the standard update sequence automatically:

1. `fetch_2026.py` — download latest results
2. `merge_2026.py` — upsert into master Parquet
3. `build_base_metrics.py` — rebuild Tier 2 tables
4. `run_aggregations.py` — regenerate all JSON outputs
5. Commits and pushes all `data/` changes to the main branch

For live-season tracking (Grand Slams, etc.) the workflow can be triggered manually from the Actions tab.

---

### Standard Update (start of each year, or weekly during active season)

```
# 1. Get latest match results
python scripts/fetch_2026.py

# 2. Merge into master
python scripts/merge_2026.py

# 3. Rebuild TML base tables
python scripts/build_base_metrics.py

# 4. Regenerate all visualisation data
python scripts/run_aggregations.py
```

### MCP Update (when new matches have been charted)

MCP is updated by the community — run this when you want the latest charting data:

```
# 1. Download latest MCP files
python scripts/fetch_mcp.py

# 2. Rebuild MCP base tables (also re-runs the TML join)
python scripts/build_mcp_base_metrics.py
```

### Full Rebuild From Scratch (nuclear option)

```
python scripts/fetch_2026.py
python scripts/merge_2026.py
python scripts/fetch_mcp.py
python scripts/build_base_metrics.py
python scripts/build_mcp_base_metrics.py
python scripts/run_aggregations.py
```

---

## Data Flow Diagram

```
External Sources
    │
    ├─ stats.tennismylife.org/data/2026.csv
    │     └─ fetch_2026.py ──────────────────► data/raw/2026.csv
    │                                                   │
    │                                            merge_2026.py
    │                                                   │
    ├─ github.com/JeffSackmann/                         │
    │  tennis_MatchChartingProject/                     │
    │     └─ fetch_mcp.py ──────────────────► data/raw/mcp/*.csv
    │                                                   │
    │                                     build_mcp_base_metrics.py
    │                                                   │
    └─ (historical archive — built once)                │
          └──────────────────────────────► data/base/atp_matches_raw.parquet
                                                        │
                                         build_base_metrics.py
                                                        │
                        ┌───────────────────────────────┼──────────────────────────────┐
                        ▼                               ▼                              ▼
             player_metrics.parquet    matches_enriched.parquet    head_to_head.parquet
                        │                               │
             (from mcp pipeline)                        │
                        │                               │
    ┌───────────────────┤               ┌───────────────┤
    │                   │               │               │
    ▼                   ▼               ▼               ▼
mcp_player_    mcp_matches_     nbi.py          gsdi.py
metrics        enriched         gs_breakthrough global_evolution
.parquet       .parquet         network_graph   career_longevity
                                indian_players  greatness_race
mcp_player_                     young_guns_race
crosswalk                               │
.parquet                                ▼
                               data/{nbi,gsdi,gs-breakthrough,
                                greatness,globaltop100evolution,
                                career_longevity,indian,network}/
                               *.json / *.csv
                                        │
                                        ▼
                               tennis-analytics/ (front-end)
                               reads JSON files directly
```

---

## File Ownership Matrix

| File | Created by | Read by |
|------|-----------|---------|
| `data/raw/2026.csv` | `fetch_2026.py` | `merge_2026.py` |
| `data/raw/mcp/*.csv` | `fetch_mcp.py` | `build_mcp_base_metrics.py` |
| `data/base/atp_matches_raw.parquet` | `merge_2026.py` (updates) | `build_base_metrics.py`, `build_mcp_base_metrics.py`, `global_evolution.py`, `career_longevity.py`, `indian_players.py` |
| `data/base/player_metrics.parquet` | `build_base_metrics.py` | `run_aggregations.py` → `gs_breakthrough.py`, `network_graph.py` |
| `data/base/matches_enriched.parquet` | `build_base_metrics.py` | `run_aggregations.py` → `nbi.py`, `gsdi.py`, `network_graph.py`, `greatness_race.py`, `young_guns_race.py` |
| `data/base/head_to_head.parquet` | `build_base_metrics.py` | *(available for future aggregations)* |
| `data/base/mcp_player_metrics.parquet` | `build_mcp_base_metrics.py` | *(available for future MCP aggregations)* |
| `data/base/mcp_matches_enriched.parquet` | `build_mcp_base_metrics.py` | *(available for future MCP aggregations)* |
| `data/base/mcp_player_crosswalk.parquet` | `build_mcp_base_metrics.py` | *(available for future MCP aggregations)* |
| `data/nbi/*.json/csv` | `nbi.py` | Front-end: `nbi/` visualization |
| `data/gsdi/*.json` | `gsdi.py` | Front-end: `gsdi/` visualization |
| `data/gs-breakthrough/*.csv` | `gs_breakthrough.py` | Front-end: `gs-breakthrough/` visualization |
| `data/greatness/race_to_greatness.json` | `greatness_race.py` | Front-end: `greatness/` visualization |
| `data/greatness/young_guns_race.json` | `young_guns_race.py` | Front-end: `greatness/` visualization |
| `data/globaltop100evolution/*.json` | `global_evolution.py` | Front-end: `globaltop100evolution/` visualization |
| `data/career_longevity/*.json` | `career_longevity.py` | Front-end: `network/` and `bigthree/` visualizations |
| `data/indian/*.json` | `indian_players.py` | Front-end: `indianplayers/` visualization |
| `data/network/*.json` | `network_graph.py` | Front-end: `network/` visualization |

---

## Key Design Decisions

### Why Parquet for Tier 2?

Parquet with zstd compression gives ~10× smaller files than CSV, column-pruning (load only the columns you need), and faster read times than CSV. All aggregation modules use `pd.read_parquet(path, columns=[...])` to load only what they need.

### Why is `atp_matches_raw` separate from `matches_enriched`?

`atp_matches_raw` is the ground truth — it mirrors the TML source exactly and is only modified by `merge_2026.py`. `matches_enriched` adds derived columns (parsed scores, flags, player context) that are computed from the raw data. This separation means re-enrichment is free and the raw data is never at risk of being corrupted by computed fields.

### Why does the MCP join use tournament + round instead of date?

TML stores `tourney_date` as the **Monday of the tournament week**, not the actual match date. So all 128 first-round Wimbledon matches have `tourney_date = 20240701` even though they were played on different days. MCP records the actual match date. Joining on date alone gives only ~11% match rate. Joining on `(year + tournament + round + sorted player pair)` gives ~92%.

### Why MIN_CHARTED_MATCHES = 3 for MCP player metrics?

A single charted match is not statistically meaningful for per-player averages. Three matches gives at least a minimal sample while keeping the dataset inclusive enough to cover a wide range of players.
