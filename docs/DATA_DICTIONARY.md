# Data Dictionary

This document covers every data file in the pipeline — from raw source downloads through intermediate base tables to final visualization-ready outputs. The pipeline is organised into three tiers:

- **Tier 1 — Raw** (`data/raw/`) — unmodified files downloaded from external sources
- **Tier 2 — Base** (`data/base/`) — cleaned, merged, enriched Parquet tables used by all aggregations
- **Tier 3 — Aggregations** (`data/*/`) — domain-specific JSON/CSV files consumed by the front-end visualizations

---

## Tier 1 — Raw Source Files

### TML (Tennis My Life) — `data/raw/`

| File | Source | Description |
|------|--------|-------------|
| `2026.csv` | `https://stats.tennismylife.org/data/2026.csv` | Incremental ATP match data for the current year. Used to update the master Parquet. Same column schema as `atp_matches_raw.parquet`. |

> **Note:** The historical master (`atp_matches_raw.parquet`, covering 1968 – 2025) was built once via `legacy_scripts/fetch_base_data.py`. Only the current year needs to be fetched + merged via `fetch_2026.py` + `merge_2026.py`.

---

### MCP (Match Charting Project) — `data/raw/mcp/`

All files are downloaded from `https://github.com/JeffSackmann/tennis_MatchChartingProject` (CC BY-NC-SA 4.0 — non-commercial use only).

| File | Rows (approx.) | Description |
|------|----------------|-------------|
| `charting-m-matches.csv` | ~7,600 | Match metadata: match ID, player names, date, tournament, round, surface, best-of |
| `charting-m-stats-Overview.csv` | ~15,000 | Pre-aggregated per-player-per-match serve and return totals |
| `charting-m-stats-Rally.csv` | ~97,000 | Pre-aggregated rally-length distribution per match |
| `charting-m-points-to-2009.csv` | large | Raw point-by-point notation for matches before 2010 *(not currently used — see schema below for future extension)* |
| `charting-m-points-2010s.csv` | large | Raw point-by-point notation 2010–2019 *(not currently used)* |
| `charting-m-points-2020s.csv` | large | Raw point-by-point notation 2020–present *(not currently used)* |

#### `charting-m-matches.csv` — Column Reference

| Column | Type | Description |
|--------|------|-------------|
| `match_id` | string | Primary key, format `{date}-{surface}-{tournament}-{round}-{p1}-{p2}` |
| `Player 1` | string | First player name (as listed by the chartist) |
| `Player 2` | string | Second player name |
| `Date` | integer | Actual match date `YYYYMMDD` (not tournament week start) |
| `Tournament` | string | Tournament name, e.g. `Wimbledon`, `Roland Garros` |
| `Round` | string | Round code: `F`, `SF`, `QF`, `R16`, `R32`, `R64`, `R128`, `RR`, `Q1`–`Q3` |
| `Surface` | string | `Hard`, `Clay`, `Grass`, `Carpet` |
| `Best of` | integer | `3` or `5` |
| `Pl 1 hand` | string | Handedness of Player 1 |
| `Pl 2 hand` | string | Handedness of Player 2 |
| `Final TB?` | string | Whether match had a final-set tiebreak |
| `Charted by` | string | Username of the person who charted the match |

#### `charting-m-stats-Overview.csv` — Column Reference

Filtered to `set = 'Total'` rows to get match-level totals.

| Column | Type | Description |
|--------|------|-------------|
| `match_id` | string | Foreign key to matches file |
| `player` | string | Player name |
| `set` | string | `Total` (match total) or `1`, `2`, `3`, `4`, `5` (per-set) |
| `serve_pts` | integer | Total serve points played |
| `aces` | integer | Aces |
| `dfs` | integer | Double faults |
| `first_in` | integer | First serves in |
| `first_won` | integer | Points won on first serve |
| `second_in` | integer | Second serves in |
| `second_won` | integer | Points won on second serve |
| `bk_pts` | integer | Break points faced (as server) |
| `bp_saved` | integer | Break points saved |
| `return_pts` | integer | Total return points played |
| `return_pts_won` | integer | Return points won |
| `winners` | integer | Total winners |
| `winners_fh` | integer | Forehand winners |
| `winners_bh` | integer | Backhand winners |
| `unforced` | integer | Unforced errors |
| `unforced_fh` | integer | Forehand unforced errors |
| `unforced_bh` | integer | Backhand unforced errors |

#### `charting-m-stats-Rally.csv` — Column Reference

Contains one row per (match, server, returner, rally-length band). The `row` column determines what the row represents:

| `row` value | Meaning |
|-------------|---------|
| `Total` | All points in the match |
| `1-3` | Points ending in 1–3 shot rallies |
| `4-6` | Points ending in 4–6 shot rallies |
| `7-9` | Points ending in 7–9 shot rallies |
| `10` | Points ending in 10+ shot rallies |
| `1-3-1` | Player 1 serving, rally 1–3 shots |
| `1-3-2` | Player 2 serving, rally 1–3 shots |
| `4-6-1`, `4-6-2`, `7-9-1`, `7-9-2`, `10-1`, `10-2` | Same pattern for other zones |

| Column | Type | Description |
|--------|------|-------------|
| `match_id` | string | Foreign key to matches file |
| `server` | string | Name of the serving player |
| `returner` | string | Name of the returning player |
| `row` | string | Rally band / role code (see table above) |
| `pts` | integer | Total points in this band/role |
| `pl1_won` | integer | Points won by Player 1 |
| `pl1_winners` | integer | Winners by Player 1 |
| `pl1_forced` | integer | Forced errors by Player 1 |
| `pl1_unforced` | integer | Unforced errors by Player 1 |
| `pl2_won` | integer | Points won by Player 2 |
| `pl2_winners` | integer | Winners by Player 2 |
| `pl2_forced` | integer | Forced errors by Player 2 |
| `pl2_unforced` | integer | Unforced errors by Player 2 |

> **Role encoding:** For rows `{zone}-1` (P1 serving): `pl1_won` = server's wins, `pl2_won` = returner's wins.
> For rows `{zone}-2` (P2 serving): `pl2_won` = server's wins, `pl1_won` = returner's wins.

#### `charting-m-points-*.csv` — Point-by-Point Data (Reference)

These files are **not used by the current pipeline** but contain the raw shot-by-shot data that would enable more granular metrics (exact Serve+1 win rates, clutch point analysis, shot-type breakdowns). Listed here as a reference for future extension.

**Identity & Score State**

| Column | Type | Description |
|--------|------|-------------|
| `match_id` | string | Foreign key to `charting-m-matches.csv` |
| `Pt` | integer | Point number within the match (1-based) |
| `Set1` | integer | Sets won by Player 1 so far |
| `Set2` | integer | Sets won by Player 2 so far |
| `Gm1` | integer | Games won by Player 1 in the current set |
| `Gm2` | integer | Games won by Player 2 in the current set |
| `Pts` | string | Game score from server's perspective: `"0-0"`, `"15-30"`, `"40-A"`, etc. |
| `Gm#` | integer | Game number within the set |
| `TbSet` | integer | Set number if in a tiebreak |
| `Svr` | integer | `1` = Player 1 serving, `2` = Player 2 serving |
| `1st` | string | Shot sequence notation for first serve (e.g. `4b37y1r3n#`) — raw chartist encoding |
| `2nd` | string | Shot sequence notation for second serve |
| `Notes` | string | Freeform annotations by the chartist |
| `PtWinner` | integer | `1` = Player 1 won the point, `2` = Player 2 won |

**Derived columns available in the MCP repo's decoded version** (not in the raw files as-downloaded):

| Column | Type | Description |
|--------|------|-------------|
| `isSvrWinner` | integer | `1` = server won the point, `0` = returner won |
| `rallyCount` | integer | Shots in rally including serve. Ace = 1. Serve+1 situation = 2. |
| `isAce` | boolean | Point ended by ace |
| `isUnret` | boolean | Returner did not put serve back in play (not an ace) |
| `isForced` | boolean | Point ended by forced error |
| `isUnforced` | boolean | Point ended by unforced error |
| `isDouble` | boolean | Double fault |

---

## Tier 2 — Base Tables (`data/base/`)

All files in this tier are stored as **Parquet with zstd compression**. They are the single source of truth for all downstream aggregations.

---

### `atp_matches_raw.parquet`

**Description:** Master match-by-match record of all ATP tour matches from 1968 to present. Produced by merging TML historical data with the annual incremental fetch.

**Rows:** ~198,500 | **Key:** `(tourney_id, match_num)`

> **Important:** `tourney_date` stores the **tournament week start date** (Monday), not the actual match date. For example, all Wimbledon 2024 matches have `tourney_date = 20240701` regardless of when each match was played.

| Column | Type | Example | Description |
|--------|------|---------|-------------|
| `tourney_id` | string | `2024-540` | Unique tournament identifier |
| `tourney_name` | string | `Wimbledon` | Tournament name |
| `surface` | string | `Grass` | `Hard`, `Clay`, `Grass`, `Carpet` |
| `draw_size` | float | `128.0` | Draw size (number of players) |
| `tourney_level` | string | `G` | `G`=Grand Slam, `M`=Masters, `A`=ATP 250/500, `F`=Finals, `D`=Davis Cup |
| `indoor` | string | `O` | `I`=indoor, `O`=outdoor |
| `tourney_date` | integer | `20240701` | Tournament week start date (`YYYYMMDD`) |
| `match_num` | float | `1.0` | Match number within tournament |
| `winner_id` | string | `D643` | Player ID of winner |
| `winner_seed` | float | `1.0` | Seeding of winner, `NaN` if unseeded |
| `winner_entry` | string | `Q` | `Q`=qualifier, `WC`=wildcard, `LL`=lucky loser, `NaN`=direct acceptance |
| `winner_name` | string | `Carlos Alcaraz` | Full name of winner |
| `winner_hand` | string | `R` | `R`=right, `L`=left, `U`=unknown |
| `winner_ht` | float | `185.0` | Height in cm |
| `winner_ioc` | string | `ESP` | 3-letter IOC country code |
| `winner_age` | float | `21.25` | Age at match date (decimal years) |
| `winner_rank` | float | `3.0` | ATP ranking at match time |
| `winner_rank_points` | float | `6215.0` | ATP ranking points |
| `loser_id` | string | `N409` | Player ID of loser |
| `loser_seed` | float | `2.0` | Seeding of loser |
| `loser_entry` | string | | Same as winner_entry |
| `loser_name` | string | `Novak Djokovic` | Full name of loser |
| `loser_hand` | string | `R` | Handedness |
| `loser_ht` | float | `188.0` | Height in cm |
| `loser_ioc` | string | `SRB` | Country code |
| `loser_age` | float | `37.1` | Age at match |
| `loser_rank` | float | `2.0` | Ranking |
| `loser_rank_points` | float | `8710.0` | Ranking points |
| `score` | string | `6-3 6-3 6-4` | Match score string |
| `best_of` | integer | `5` | `3` or `5` sets |
| `round` | string | `F` | `F`, `SF`, `QF`, `R16`, `R32`, `R64`, `R128`, `RR`, `BR`, `3rd/4th` |
| `minutes` | float | `137.0` | Match duration in minutes |
| `w_ace` | float | `11.0` | Aces by winner |
| `w_df` | float | `2.0` | Double faults by winner |
| `w_svpt` | float | `89.0` | Serve points by winner |
| `w_1stIn` | float | `57.0` | First serves in by winner |
| `w_1stWon` | float | `48.0` | 1st serve points won by winner |
| `w_2ndWon` | float | `22.0` | 2nd serve points won by winner |
| `w_SvGms` | float | `13.0` | Service games by winner |
| `w_bpSaved` | float | `2.0` | Break points saved by winner |
| `w_bpFaced` | float | `3.0` | Break points faced by winner |
| `l_ace` … `l_bpFaced` | float | | Same stats for loser (prefix `l_`) |

---

### `player_metrics.parquet`

**Description:** Career-level aggregate statistics for every player who appears in `atp_matches_raw`. One row per player. Built by `aggregations/base_metrics.py`.

**Rows:** ~7,600 | **Key:** `player_name`

| Column | Type | Description |
|--------|------|-------------|
| `player_name` | string | Full player name (matches `winner_name` / `loser_name` in raw) |
| `country` | string | IOC 3-letter country code |
| `first_match_date` | integer | Date of first career match (`YYYYMMDD`) |
| `last_match_date` | integer | Date of last career match (`YYYYMMDD`) |
| `career_start_year` | float | Year of first career match |
| `career_end_year` | float | Year of last career match |
| `career_span_years` | integer | `career_end_year - career_start_year` |
| `total_matches` | integer | Total career matches played |
| `total_wins` | integer | Total wins |
| `total_losses` | integer | Total losses |
| `win_pct` | float | Win percentage (0–100) |
| `gs_matches` | integer | Grand Slam matches played |
| `gs_wins` | integer | Grand Slam wins |
| `gs_losses` | integer | Grand Slam losses |
| `gs_win_pct` | float | Grand Slam win percentage |
| `gs_titles` | integer | Number of Grand Slam titles |
| `gs_finals` | integer | Grand Slam final appearances |
| `gs_semifinals` | integer | Grand Slam semi-final appearances |
| `gs_quarterfinals` | integer | Grand Slam quarter-final appearances |
| `first_gs_title_date` | float | Date of first GS title win (`YYYYMMDD`), `NaN` if none |
| `first_gs_title_age` | float | Age at first GS title (decimal years) |
| `first_gs_title_year` | float | Year of first GS title |
| `matches_before_first_gs` | integer | Total ATP matches played before first GS title |
| `wins_before_first_gs` | integer | Wins before first GS title |
| `win_pct_before_first_gs` | float | Win % before first GS title |
| `years_to_first_gs` | integer | Years on tour before first GS title |
| `peak_ranking` | float | Career best ATP ranking |
| `peak_ranking_date` | string | Date of peak ranking |
| `peak_ranking_before_first_gs` | float | Best ranking achieved before first GS title |
| `hard_matches` / `hard_wins` / `hard_win_pct` | int/float | Surface-specific records — Hard |
| `clay_matches` / `clay_wins` / `clay_win_pct` | int/float | Surface-specific records — Clay |
| `grass_matches` / `grass_wins` / `grass_win_pct` | int/float | Surface-specific records — Grass |
| `carpet_matches` / `carpet_wins` / `carpet_win_pct` | int/float | Surface-specific records — Carpet |
| `top5_matches` / `top5_wins` / `top5_win_pct` | int/float | Record vs. Top 5 ranked opponents |
| `top10_matches` / `top10_wins` / `top10_win_pct` | int/float | Record vs. Top 10 |
| `top30_matches` / `top30_wins` / `top30_win_pct` | int/float | Record vs. Top 30 |
| `avg_opponent_rank` | float | Average ranking of opponents faced |
| `unique_opponents` | integer | Number of distinct opponents |
| `avg_match_duration` | float | Average match duration (minutes) |
| `total_match_minutes` | float | Sum of all match durations |
| `matches_with_duration` | integer | Matches where duration was recorded |
| `has_gs_title` | boolean | True if player has won at least one Grand Slam |
| `was_top_5` | boolean | True if player ever reached Top 5 |
| `was_top_10` | boolean | True if player ever reached Top 10 |

---

### `matches_enriched.parquet`

**Description:** Extends `atp_matches_raw` with parsed score fields, drama metrics, match context flags, and player career stats at time of match. One row per match. Built by `aggregations/base_metrics.py`.

**Rows:** ~198,500 | **Key:** `(tourney_id, match_num)`

Contains all columns from `atp_matches_raw` plus:

| Column | Type | Description |
|--------|------|-------------|
| `winner_sets` | integer | Sets won by the winner |
| `loser_sets` | integer | Sets won by the loser |
| `winner_games` | integer | Total games won by winner |
| `loser_games` | integer | Total games won by loser |
| `tiebreaks_count` | integer | Number of tiebreaks in the match |
| `is_complete` | boolean | True if match had a valid, fully-parsed score |
| `set_margins` | list | Game-margin per set, e.g. `[5, 2, 3]` |
| `avg_set_margin` | float | Average game margin across all sets |
| `lead_changes` | integer | Number of times the set lead changed hands |
| `comeback_score` | integer | 0–3 indicator of how dramatic a comeback was |
| `final_set_tiebreak` | integer | `1` if the final set was decided by tiebreak |
| `is_grand_slam` | boolean | True if the tournament is one of the four Grand Slams |
| `grand_slam_name` | string | Normalised GS name, or original tournament name if not a GS |
| `year` | integer | Year extracted from `tourney_date` |
| `is_final` | boolean | True if `round == 'F'` |
| `is_semifinal` | boolean | True if `round == 'SF'` |
| `is_quarterfinal` | boolean | True if `round == 'QF'` |
| `winner_career_matches` | integer | Career match count for winner at time of match |
| `winner_gs_titles` | integer | GS titles held by winner at time of match |
| `winner_has_gs_title` | boolean | Whether winner had won a GS by this point |
| `winner_peak_ranking` | float | Winner's career peak ranking |
| `loser_career_matches` | integer | Same for loser |
| `loser_gs_titles` | integer | Same for loser |
| `loser_has_gs_title` | boolean | Same for loser |
| `loser_peak_ranking` | float | Loser's career peak ranking |

---

### `head_to_head.parquet`

**Description:** All pairwise head-to-head records between every pair of players who have met at least once. Built by `aggregations/base_metrics.py`.

**Rows:** ~112,800 | **Key:** `(player1, player2)` — sorted alphabetically so each pair appears once

| Column | Type | Description |
|--------|------|-------------|
| `player1` | string | Alphabetically first player |
| `player2` | string | Alphabetically second player |
| `total_matches` | integer | Total matches between the pair |
| `player1_wins` | integer | Wins for player1 |
| `player2_wins` | integer | Wins for player2 |
| `hard_total` / `hard_p1_wins` / `hard_p2_wins` | integer | Hard court H2H |
| `clay_total` / `clay_p1_wins` / `clay_p2_wins` | integer | Clay H2H |
| `grass_total` / `grass_p1_wins` / `grass_p2_wins` | integer | Grass H2H |
| `carpet_total` / `carpet_p1_wins` / `carpet_p2_wins` | integer | Carpet H2H |

---

### `mcp_player_metrics.parquet`

**Description:** Telemetry-level career aggregates derived from MCP shot-tracking data. Covers 475 players with at least 3 charted matches. Built by `aggregations/mcp_base_metrics.py`.

**Rows:** ~475 | **Key:** `player_name`

> Serves as the MCP equivalent of `player_metrics.parquet`, providing stroke-play statistics that the TML archive does not contain.

| Column | Type | Description |
|--------|------|-------------|
| `player_name` | string | Player name (MCP naming convention) |
| `mcp_match_count` | integer | Number of charted matches (≥3 to be included) |
| `mcp_year_min` | integer | First year with a charted match |
| `mcp_year_max` | integer | Most recent year with a charted match |
| `serve_pts` | integer | Career total serve points charted |
| `aces` | integer | Career total aces |
| `double_faults` | integer | Career total double faults |
| `first_in_pct` | float | First-serve percentage (0–100) |
| `first_won_pct` | float | % of first-serve points won |
| `second_won_pct` | float | % of second-serve points won |
| `serve_win_pct` | float | Overall serve points won % |
| `return_pts` | integer | Career total return points charted |
| `return_win_pct` | float | Return points won % |
| `winners` | integer | Career total winners |
| `unforced_errors` | integer | Career total unforced errors |
| `uf_rate` | float | Unforced error rate (errors per 100 total points) |
| `avg_rally_length` | float | Weighted average rally length (shots) using zone midpoints |
| `rally_1_3_pct` | float | % of charted points ending in 1–3 shot rallies |
| `rally_4_6_pct` | float | % of charted points ending in 4–6 shot rallies |
| `rally_7_9_pct` | float | % of charted points ending in 7–9 shot rallies |
| `rally_10p_pct` | float | % of charted points ending in 10+ shot rallies |
| `rally_1_3_win_pct` | float | Win % in 1–3 shot rallies (all points the player participated in) |
| `rally_7p_win_pct` | float | Win % in 7+ shot rallies (extended points) |
| `serve_trans_pts` | integer | Points played while serving in the 1–3 rally zone (Serve+1 approximation) |
| `serve_trans_won` | integer | Points won in the serve-transition zone |
| `serve_trans_win_pct` | float | Win % in serve-transition zone |
| `bp_faced` | integer | Career total break points faced |
| `bp_saved` | integer | Career total break points saved |
| `bp_save_pct` | float | Break point save percentage (0–100) |
| `bp_save_vs_serve_win_delta` | float | `bp_save_pct - serve_win_pct`; positive = player raises level under pressure |

---

### `mcp_matches_enriched.parquet`

**Description:** Per-match stats derived from MCP charting, with each row joined back to the TML archive where possible. One row per charted match. Built by `aggregations/mcp_base_metrics.py`.

**Rows:** ~7,700 | **Key:** `match_id`

| Column | Type | Description |
|--------|------|-------------|
| `match_id` | string | MCP match identifier |
| `player1_name` | string | Name of Player 1 (MCP convention) |
| `player2_name` | string | Name of Player 2 |
| `tourney_date` | float | Actual match date (`YYYYMMDD`) — differs from TML's week-start date |
| `tournament` | string | Tournament name |
| `round` | string | Round code |
| `surface` | string | Surface |
| `best_of` | string | `3` or `5` |
| `player1_serve_pts` | float | P1 serve points |
| `player1_aces` | float | P1 aces |
| `player1_dfs` | float | P1 double faults |
| `player1_first_in` | float | P1 first serves in |
| `player1_first_won` | float | P1 first-serve points won |
| `player1_second_won` | float | P1 second-serve points won |
| `player1_bp_faced` | float | P1 break points faced |
| `player1_bp_saved` | float | P1 break points saved |
| `player1_return_pts` | float | P1 return points |
| `player1_return_won` | float | P1 return points won |
| `player1_winners` | float | P1 winners |
| `player1_unforced` | float | P1 unforced errors |
| `player2_*` (same columns) | float | Same stats for Player 2 |
| `match_avg_rally` | float | Weighted average rally length for the match |
| `rally_1_3_pct` | float | % of match points in 1–3 shot rallies |
| `rally_4_6_pct` | float | % of match points in 4–6 shot rallies |
| `rally_7_9_pct` | float | % of match points in 7–9 shot rallies |
| `rally_10_pct` | float | % of match points in 10+ shot rallies |
| `total_pts` | float | Total points charted in the match |
| `p1_long_rally_win_pct` | float | P1's win % in 7+ shot rallies |
| `p2_long_rally_win_pct` | float | P2's win % in 7+ shot rallies |
| `p1_serve_win_pct` | float | P1 overall serve win % |
| `p1_return_win_pct` | float | P1 return win % |
| `p1_bp_save_pct` | float | P1 break point save % |
| `p2_serve_win_pct` | float | P2 serve win % |
| `p2_return_win_pct` | float | P2 return win % |
| `p2_bp_save_pct` | float | P2 break point save % |
| `tml_tourney_date` | float | TML tournament week start date (from join) |
| `tml_winner_name` | string | Winner name from TML archive (populated after join) |
| `tml_loser_name` | string | Loser name from TML archive (populated after join) |
| `tml_join_confidence` | string | `primary` (tournament+round+year+players match), `fallback` (year+players only), or `unmatched` |

---

### `mcp_player_crosswalk.parquet`

**Description:** Name mapping table between MCP player names and TML player names. Required because the two sources use slightly different name formats. Built by `aggregations/mcp_base_metrics.py`.

**Rows:** ~1,000 | **Key:** `mcp_player_name`

| Column | Type | Description |
|--------|------|-------------|
| `mcp_player_name` | string | Player name as it appears in MCP files |
| `tml_player_name` | string | Corresponding player name in TML archive (`NaN` if unresolved) |
| `join_method` | string | `exact` (date+players matched), `fuzzy` (difflib ≥0.85 threshold), or `unmatched` |
| `match_count` | integer | Number of charted matches for this MCP player |

---

### `metadata.json`

Lightweight JSON tracking last pipeline run time and row counts for each base table.

---

## Quick-Start Code Examples

```python
import pandas as pd

# Load player metrics — one row per player
players = pd.read_parquet("data/base/player_metrics.parquet")

# All Grand Slam champions
champions = players[players["has_gs_title"] == True]

# Big 3 career stats
big3 = players[players["player_name"].isin(["Roger Federer", "Rafael Nadal", "Novak Djokovic"])]

# Load enriched matches — filter to Grand Slam finals
matches = pd.read_parquet("data/base/matches_enriched.parquet")
gs_finals = matches[(matches["is_grand_slam"]) & (matches["round"] == "F")]

# Dramatic comebacks (winner came back from 2 sets down)
comebacks = matches[matches["comeback_score"] >= 2]

# Load MCP player metrics — serve/rally telemetry
mcp = pd.read_parquet("data/base/mcp_player_metrics.parquet")

# Players with strong clutch performance (bp_save_pct above serve_win_pct)
clutch = mcp[mcp["bp_save_vs_serve_win_delta"] > 5].sort_values(
    "bp_save_vs_serve_win_delta", ascending=False
)

# Head-to-head for a specific pair
h2h = pd.read_parquet("data/base/head_to_head.parquet")
pair = h2h[
    (h2h["player1"].isin(["Roger Federer", "Rafael Nadal"])) &
    (h2h["player2"].isin(["Roger Federer", "Rafael Nadal"]))
]
```

---

## Tier 3 — Aggregation Outputs

All JSON/CSV files are produced by the aggregation modules and consumed directly by the front-end JavaScript visualizations.

---

### `data/nbi/` — Nailbiter Index

Produced by `aggregations/nbi.py`.

| File | Description |
|------|-------------|
| `gs_nailbiters.json` | All Grand Slam Finals and Semi-Finals ranked by NBI score. Each record includes the drama formula components: `avg_set_margin`, `tiebreaks_count`, `lead_changes`, `comeback_score`, `bp_saved_ratio`, `final_set_tiebreak`, `duration_score`, plus computed `nbi_score` and `drama_tags`. |
| `gs_nailbiters.csv` | Same data in CSV format for analysis. |
| `iconic_gs_matches.json` | Curated subset: top-scoring matches per era (pre-1980, 1980s, 1990s, 2000s, 2010s, 2020s). |

**NBI Formula Weights:**

| Component | Weight | Meaning |
|-----------|--------|---------|
| `avg_set_margin` | 0.25 | Closer set scores = more drama |
| `lead_changes` | 0.20 | Set lead flipping between players |
| `comeback` | 0.20 | Winner came back from sets/games down |
| `tiebreak_count` | 0.12 | Each tiebreak adds excitement |
| `duration_score` | 0.10 | Longer matches score higher |
| `bp_saved_ratio` | 0.07 | High proportion of break points saved |
| `final_set_tiebreak` | 0.06 | Final set decided by tiebreak |

---

### `data/gsdi/` — Grand Slam Dominance Index

Produced by `aggregations/gsdi.py`.

| File | Description |
|------|-------------|
| `gs_dominance_rankings.json` | All Grand Slam winning campaigns ranked by GSDI score. Each record covers one player/tournament/year combination with metrics: opponent quality (average rank of opponents beaten), dominance (sets lost), speed (minutes per set), consistency (across all rounds). |

---

### `data/gs-breakthrough/` — Breakthrough Analysis

Produced by `aggregations/gs_breakthrough.py`.

| File | Description |
|------|-------------|
| `gs_breakthrough_comparison.csv` | One row per Grand Slam champion. Columns: `Player_Name`, `Age_First_GS`, `Matches_Before_First_GS`, `Total_GS_Titles`, `Year_First_GS`, `Total_ATP_Matches`, `Win_Percentage`, `Peak_Ranking`, `Years_On_Tour_Before_GS`, etc. |
| `legacy_overrides.json` | Manual corrections for pre-digital-era players where match counts are incomplete in the archive. |

---

### `data/greatness/` — Greatness Race

Produced by `aggregations/greatness_race.py` and `aggregations/young_guns_race.py`.

| File | Description |
|------|-------------|
| `race_to_greatness.json` | Quarterly career trajectories for the Big 3 (Federer, Nadal, Djokovic) and historical greats. X-axis = age, Y-axis = cumulative wins/titles. Enables age-adjusted comparisons across eras. |
| `young_guns_race.json` | Same structure for next-generation players: Alcaraz, Sinner, Fonseca, Mensik, Tien, Jodar. |

---

### `data/globaltop100evolution/` — Global Top 100 Evolution

Produced by `aggregations/global_evolution.py`.

| File | Description |
|------|-------------|
| `country_code_mapping.json` | IOC country code → full country name mapping |
| `tennis_country_profiles.json` | Per-country statistics: total Top 100 players, peak years, top players list |
| `global_timeline_dataset.json` | Every 5 years from 1975, count of Top 100 players by country |
| `top_tennis_players_timeline.json` | Year-by-year ranking data for top players with country breakdowns |
| `top_players_list.json` | Summary list of all players who have ever been in the Top 100 |

---

### `data/career_longevity/` — Career Longevity

Produced by `aggregations/career_longevity.py`.

| File | Description |
|------|-------------|
| `summary.json` | High-level career length statistics (median, mean, percentiles) |
| `survival_curve.json` | Kaplan-Meier style survival curve: probability of still playing after N years |
| `longest_careers.json` | Top 100 longest careers by active years on tour |
| `player_careers_top1000.json` | Career records for top 1000 players by match volume |
| `career_categories.json` | Players bucketed into career length categories (1–3 yrs, 4–7 yrs, 8–12 yrs, 13+ yrs) |
| `match_volume_stats.json` | Distribution of total matches played per career |

---

### `data/indian/` — Indian Players

Produced by `aggregations/indian_players.py`.

| File | Description |
|------|-------------|
| `players_summary.json` | Career summary for all Indian players (all eras) |
| `players_summary_1990.json` | Same, filtered to 1990–present |
| `notable_players.json` / `notable_players_1990.json` | Spotlight records for prominent Indian players |
| `indian_matches.json` | Match-by-match records for Indian players |
| `indian_matches_1990.json` | Same, filtered to 1990–present |
| `players_time_series.json` | Year-by-year win/loss and ranking for each Indian player |
| `players_time_series_1990.json` | Same, 1990–present |
| `surface_performance_by_player.json` | Win % by surface for each Indian player |
| `win_loss_by_year.json` | Aggregate win/loss totals for Indian players by year |
| `player_yearly_rank.json` | Year-end ranking for each Indian player |
| `player_milestones.json` | Career milestones: first Top 50 entry, best ranking, GS results |
| `career_lengths_indian.json` | Career longevity breakdown for Indian players |
| `head_to_head_top50.json` | H2H records of Indian players against Top 50 opponents |
| `tournament_participation_country.json` | Tournaments entered by Indian players |
| `tournament_participation_global.json` | Global tournament participation context |

---

### `data/network/` — Network Graph

Produced by `aggregations/network_graph.py`.

| File | Description |
|------|-------------|
| `grand_slam_finals_1968.json` | All-time Grand Slam finals network (nodes = players, edges = matches) |
| `wimbledon_finals_1968.json` | Wimbledon finals network |
| `roland_garros_finals_1968.json` | Roland Garros finals network |
| `australian_open_finals_1968.json` | Australian Open finals network |
| `us_open_finals_1968.json` | US Open finals network |
| `tennis_legends_rivalries_1968.json` | Top rivalries network across all Grand Slams |
| `network_summary.json` | Summary statistics: most connected players, rivalry strength rankings |

---

### `data/shared/`

| File | Description |
|------|-------------|
| `player_metadata.json` | Consolidated player metadata: country, handedness, height, birth year. Used across multiple visualizations. |
