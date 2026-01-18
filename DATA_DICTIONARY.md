# Data Dictionary

**Complete schema reference for all TML-Data outputs**  
*Last Updated: January 17, 2026*

---

## 📊 Base Metrics Tables

### **1. player_metrics.pkl / player_metrics.csv**

**Dimensions**: 7,534 players × 52 columns  
**Format**: Pickle (binary) and CSV  
**Update Frequency**: Weekly  
**Source**: Aggregated from atp_matches_base.pkl

#### Column Reference

| Column | Type | Range/Values | Description |
|--------|------|--------------|-------------|
| **Career Span** |
| `player_name` | str | - | Player full name |
| `player_id` | str | - | TML-Database player ID |
| `country` | str | IOC code | Player nationality |
| `first_match_date` | int | YYYYMMDD | Date of first recorded match |
| `last_match_date` | int | YYYYMMDD | Date of most recent match |
| `career_start_year` | int | 1968-2025 | Year of professional debut |
| `career_end_year` | int | 1968-2025 | Year of last recorded match |
| `career_span_years` | int | 0-30 | Years between first and last match |
| **Match Statistics** |
| `total_matches` | int | ≥1 | Total career matches played |
| `total_wins` | int | ≥0 | Total wins |
| `total_losses` | int | ≥0 | Total losses |
| `win_pct` | float | 0-100 | Overall win percentage |
| **Grand Slam Statistics** |
| `gs_matches` | int | ≥0 | Grand Slam matches played |
| `gs_wins` | int | ≥0 | Grand Slam wins |
| `gs_losses` | int | ≥0 | Grand Slam losses |
| `gs_win_pct` | float | 0-100 | Grand Slam win percentage |
| `gs_titles` | int | ≥0 | Grand Slam titles won (0-24) |
| `gs_finals` | int | ≥0 | Grand Slam finals reached |
| `gs_semifinals` | int | ≥0 | Grand Slam semifinals reached |
| `gs_quarterfinals` | int | ≥0 | Grand Slam quarterfinals reached |
| **Breakthrough Metrics** (only for GS champions) |
| `first_gs_title_date` | int | YYYYMMDD | Date of first GS title (null if none) |
| `first_gs_title_age` | float | 17-35 | Age at first GS win |
| `first_gs_title_year` | int | 1968-2025 | Year of first GS win |
| `matches_before_first_gs` | int | ≥0 | Matches played before first GS |
| `wins_before_first_gs` | int | ≥0 | Wins before first GS |
| `win_pct_before_first_gs` | float | 0-100 | Win % before first GS |
| `years_to_first_gs` | int | 0-15 | Years from debut to first GS |
| **Rankings** |
| `peak_ranking` | int | 1-1500 | Best ATP ranking achieved |
| `peak_ranking_date` | int | YYYYMMDD | Date of peak ranking |
| `peak_ranking_before_first_gs` | int | 1-1500 | Best ranking before first GS |
| **Surface Breakdown - Hard** |
| `hard_matches` | int | ≥0 | Matches on hard courts |
| `hard_wins` | int | ≥0 | Wins on hard courts |
| `hard_win_pct` | float | 0-100 | Hard court win percentage |
| **Surface Breakdown - Clay** |
| `clay_matches` | int | ≥0 | Matches on clay courts |
| `clay_wins` | int | ≥0 | Wins on clay courts |
| `clay_win_pct` | float | 0-100 | Clay court win percentage |
| **Surface Breakdown - Grass** |
| `grass_matches` | int | ≥0 | Matches on grass courts |
| `grass_wins` | int | ≥0 | Wins on grass courts |
| `grass_win_pct` | float | 0-100 | Grass court win percentage |
| **Surface Breakdown - Carpet** |
| `carpet_matches` | int | ≥0 | Matches on carpet courts |
| `carpet_wins` | int | ≥0 | Wins on carpet courts |
| `carpet_win_pct` | float | 0-100 | Carpet court win percentage |
| **Opponent Quality - Top 5** |
| `top5_matches` | int | ≥0 | Matches vs Top 5 opponents |
| `top5_wins` | int | ≥0 | Wins vs Top 5 opponents |
| `top5_win_pct` | float | 0-100 | Win % vs Top 5 opponents |
| **Opponent Quality - Top 10** |
| `top10_matches` | int | ≥0 | Matches vs Top 10 opponents |
| `top10_wins` | int | ≥0 | Wins vs Top 10 opponents |
| `top10_win_pct` | float | 0-100 | Win % vs Top 10 opponents |
| **Opponent Quality - Top 30** |
| `top30_matches` | int | ≥0 | Matches vs Top 30 opponents |
| `top30_wins` | int | ≥0 | Wins vs Top 30 opponents |
| `top30_win_pct` | float | 0-100 | Win % vs Top 30 opponents |
| **Other Metrics** |
| `unique_opponents` | int | ≥1 | Number of different opponents faced |
| `avg_match_duration` | float | 60-300 | Average match length (minutes) |
| `has_gs_title` | bool | True/False | Player has won ≥1 Grand Slam |
| `was_top_5` | bool | True/False | Player reached Top 5 ranking |
| `was_top_10` | bool | True/False | Player reached Top 10 ranking |

#### Usage Example (Python)

```python
import pandas as pd

# Load player metrics
players = pd.read_pickle("data/base/player_metrics.pkl")
# or
players = pd.read_csv("data/base/player_metrics.csv")

# Get all Grand Slam champions
champions = players[players['has_gs_title'] == True]

# Get players with 200+ matches
high_volume = players[players['total_matches'] >= 200]

# Get Big 3 stats
big3 = players[players['player_name'].isin(['Roger Federer', 'Rafael Nadal', 'Novak Djokovic'])]
```

---

### **2. matches_enriched.pkl**

**Dimensions**: 197,911 matches × 75 columns  
**Format**: Pickle (binary)  
**Update Frequency**: Weekly  
**Source**: atp_matches_base.pkl + enrichments

#### Original TML-Database Columns (50)

Standard Jeff Sackmann ATP match data schema - see [TML-Database documentation](https://github.com/Tennismylife/TML-Database)

#### Enriched Columns (25)

| Column | Type | Description |
|--------|------|-------------|
| **Parsed Scores** |
| `winner_sets` | int | Sets won by winner (0-5) |
| `loser_sets` | int | Sets won by loser (0-4) |
| `winner_games` | int | Total games won by winner |
| `loser_games` | int | Total games won by loser |
| `tiebreaks_count` | int | Number of tiebreaks in match (0-5) |
| `is_complete` | bool | Match finished normally (not retired/walkover) |
| **Drama Metrics** |
| `set_margins` | list | Game margin for each set [6-4, 7-6, ...] |
| `avg_set_margin` | float | Average game margin across all sets |
| `lead_changes` | int | Times the set leader changed (0-10) |
| `comeback_score` | int | Comeback difficulty: 0=none, 1=1-set-down, 2=2-sets-down, 3=0-2-down-won, 4=match-points-saved |
| `final_set_tiebreak` | bool | Final set decided by tiebreak |
| **Grand Slam Flags** |
| `is_grand_slam` | bool | Match at Australian Open, Roland Garros, Wimbledon, or US Open |
| `grand_slam_name` | str | Normalized GS name or null |
| **Round Flags** |
| `is_final` | bool | Round code is 'F' |
| `is_semifinal` | bool | Round code is 'SF' |
| `is_quarterfinal` | bool | Round code is 'QF' |
| **Date** |
| `year` | int | Year extracted from tourney_date |
| **Player Context** (from player_metrics) |
| `winner_career_matches` | int | Winner's total career matches |
| `winner_gs_titles` | int | Winner's GS titles count |
| `winner_has_gs_title` | bool | Winner is a GS champion |
| `winner_peak_ranking` | int | Winner's peak ranking |
| `loser_career_matches` | int | Loser's total career matches |
| `loser_gs_titles` | int | Loser's GS titles count |
| `loser_has_gs_title` | bool | Loser is a GS champion |
| `loser_peak_ranking` | int | Loser's peak ranking |

#### Usage Example (Python)

```python
import pandas as pd

# Load enriched matches
matches = pd.read_pickle("data/base/matches_enriched.pkl")

# Get Grand Slam finals
gs_finals = matches[(matches['is_grand_slam'] == True) & (matches['round'] == 'F')]

# Get dramatic matches (comebacks from 2 sets down)
comebacks = matches[matches['comeback_score'] >= 2]

# Get matches with pre-parsed scores
print(matches[['winner_name', 'loser_name', 'winner_sets', 'loser_sets', 'winner_games', 'loser_games']].head())
```

---

### **3. head_to_head_matrix.json**

**Dimensions**: 112,435 unique matchups  
**Format**: JSON  
**Update Frequency**: Weekly  
**Key Format**: "Player1|Player2" (alphabetically sorted)

#### Schema

```json
{
  "Player A|Player B": {
    "player1": "Player A",
    "player2": "Player B",
    "total_matches": 40,
    "player1_wins": 16,
    "player2_wins": 24,
    "surfaces": {
      "Hard": {
        "total": 13,
        "p1_wins": 8,
        "p2_wins": 5
      },
      "Clay": {
        "total": 16,
        "p1_wins": 2,
        "p2_wins": 14
      },
      "Grass": {
        "total": 3,
        "p1_wins": 2,
        "p2_wins": 1
      }
    },
    "tournaments": {
      "Australian Open": {
        "total": 1,
        "p1_wins": 1,
        "p2_wins": 0
      },
      "Roland Garros": {
        "total": 6,
        "p1_wins": 0,
        "p2_wins": 6
      }
    }
  }
}
```

#### Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `player1` | str | First player (alphabetically) |
| `player2` | str | Second player (alphabetically) |
| `total_matches` | int | Total H2H matches |
| `player1_wins` | int | Wins by player1 |
| `player2_wins` | int | Wins by player2 |
| `surfaces` | object | Breakdown by surface |
| `surfaces.{Surface}.total` | int | Matches on this surface |
| `surfaces.{Surface}.p1_wins` | int | Player1 wins on surface |
| `surfaces.{Surface}.p2_wins` | int | Player2 wins on surface |
| `tournaments` | object | Breakdown by tournament |
| `tournaments.{Tourney}.total` | int | Matches at tournament |
| `tournaments.{Tourney}.p1_wins` | int | Player1 wins at tournament |
| `tournaments.{Tourney}.p2_wins` | int | Player2 wins at tournament |

#### Usage Example (JavaScript)

```javascript
fetch('https://raw.githubusercontent.com/sorukumar/tml-data/main/data/base/head_to_head_matrix.json')
  .then(r => r.json())
  .then(h2h => {
    // Get Federer-Nadal rivalry
    const key = "Rafael Nadal|Roger Federer"; // alphabetical order!
    const rivalry = h2h[key];
    
    console.log(`Total matches: ${rivalry.total_matches}`);
    console.log(`Clay matches: ${rivalry.surfaces.Clay.total}`);
    console.log(`At Roland Garros: ${rivalry.tournaments['Roland Garros'].total}`);
  });
```

---

## 🎯 Analysis Outputs

### **NBI (Nailbiter Index)**

#### gs_nailbiters.json

**Records**: 535 Grand Slam Finals/SF matches  
**Sorted By**: NBI score (descending)

```json
[
  {
    "match": "Novak Djokovic def. Roger Federer",
    "tourney": "Wimbledon",
    "round": "F",
    "date": "20190714",
    "score": "7-6(5) 1-6 7-6(4) 4-6 13-12(3)",
    "duration": 296,
    "NBI": 0.810,
    "NBI_100": 81.0,
    "drama_tags": "comeback, tiebreaks, momentum, final set tiebreak",
    "raw_stats": {
      "avg_set_margin": 1.2,
      "tiebreak_count": 4,
      "lead_changes": 3,
      "comeback": 2,
      "bp_saved_ratio": 0.734,
      "bp_total": 79
    }
  }
]
```

#### Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `match` | str | "Winner def. Loser" |
| `tourney` | str | Tournament name |
| `round` | str | Round code (F, SF) |
| `date` | str | Match date YYYYMMDD |
| `score` | str | Set-by-set score |
| `duration` | int | Match duration (minutes) |
| `NBI` | float | Nailbiter Index (0-1 scale) |
| `NBI_100` | float | NBI scaled to 0-100 |
| `drama_tags` | str | Comma-separated drama tags |
| `raw_stats.avg_set_margin` | float | Average game margin per set |
| `raw_stats.tiebreak_count` | int | Number of tiebreaks |
| `raw_stats.lead_changes` | int | Set leader changes |
| `raw_stats.comeback` | int | Comeback score (0-4) |
| `raw_stats.bp_saved_ratio` | float | Break points saved / total |
| `raw_stats.bp_total` | int | Total break points |

#### iconic_gs_matches.json

**Records**: 20 manually curated iconic matches  
**Purpose**: Editorial context for famous matches

```json
[
  {
    "match": "Novak Djokovic def. Roger Federer",
    "tourney": "Wimbledon",
    "date": "20190714",
    "historical_significance": "Longest Wimbledon Final",
    "short_commentary": "First-ever final set tiebreak at Wimbledon...",
    "career_impact": "Djokovic's 16th Grand Slam...",
    "cultural_resonance": "Generated massive social media buzz..."
  }
]
```

---

### **GSDI (Grand Slam Dominance Index)**

#### gs_dominance_rankings.json

**Records**: 227 Grand Slam championship campaigns  
**Sorted By**: Dominance score (descending)

```json
[
  {
    "rank": 1,
    "player": "Rafael Nadal",
    "tournament": "Roland Garros",
    "year": 2008,
    "dominance_score": 98.89,
    "sets_won": 21,
    "sets_won_pct": 100.0,
    "games_won_pct": 87.3,
    "points_won_pct": 72.4,
    "pct_top30_opponents": 42.9,
    "speed_score": 78.5,
    "avg_match_minutes": 128.6,
    "top5_wins": 2,
    "perfect_campaign": true,
    "sets_lost": 0,
    "matches_won": 7,
    "score_breakdown": {
      "sets": 32.0,
      "games": 21.8,
      "points": 16.6,
      "opponent": 4.3,
      "speed": 7.9,
      "bonus": 16.0
    }
  }
]
```

#### Field Reference

| Field | Type | Description |
|-------|------|-------------|
| `rank` | int | Dominance ranking |
| `player` | str | Player name |
| `tournament` | str | Grand Slam name |
| `year` | int | Tournament year |
| `dominance_score` | float | Overall GSDI score |
| `sets_won` | int | Total sets won in tournament |
| `sets_won_pct` | float | Percentage of sets won |
| `games_won_pct` | float | Percentage of games won |
| `points_won_pct` | float | Estimated points won % |
| `pct_top30_opponents` | float | % opponents in Top 30 |
| `speed_score` | float | Match efficiency score |
| `avg_match_minutes` | float | Average match duration |
| `top5_wins` | int | Wins vs Top 5 opponents |
| `perfect_campaign` | bool | No sets lost |
| `sets_lost` | int | Sets lost in tournament |
| `matches_won` | int | Matches won (usually 7) |
| `score_breakdown` | object | Contribution by component |

---

### **StanTheMan (Breakthrough Analysis)**

#### gs_breakthrough_comparison.csv

**Records**: 58 Grand Slam champions  
**Sorted By**: Matches before first GS (descending)

| Column | Type | Description |
|--------|------|-------------|
| `Player_Name` | str | Player name |
| `Age_First_GS` | float | Age at first GS win |
| `Matches_Before_First_GS` | int | Matches before first GS |
| `Total_GS_Titles` | int | Total GS titles won |
| `Year_Turned_Pro` | int | Debut year |
| `Year_First_GS` | int | Year of first GS |
| `Total_ATP_Matches` | int | Career total matches |
| `Career_Span_Years` | int | Career length |
| `Win_Percentage` | float | Career win % |
| `GS_Win_Ratio` | float | GS match win % |
| `Peak_Ranking` | int | Best ranking achieved |
| `Peak_Ranking_Before_GS` | int | Best ranking before first GS |
| `Win_Percentage_Before_GS` | float | Win % before first GS |
| `Years_On_Tour_Before_GS` | int | Years to first GS |

---

### **Network Graphs**

#### Node Schema

All network JSON files use this node structure:

```json
{
  "nodes": [
    {
      "name": "Roger Federer",
      "country": "SUI",
      "matches_won": 25,
      "matches_played": 28,
      "win_pct": 89.3,
      "win_pct_category": "Above 70%",
      "career_total_matches": 1526,
      "career_win_pct": 82.1,
      "gs_titles": 20,
      "peak_ranking": 1,
      "top_5_wins": 8,
      "top_5_matches": 12,
      "top_5_win_pct": 66.7,
      "was_top_5": true,
      "unique_opponents": 18,
      "surface_wins": {"Hard": 15, "Clay": 6, "Grass": 4},
      "surface_matches": {"Hard": 17, "Clay": 7, "Grass": 4},
      "surface_win_pcts": {"Hard": 88.2, "Clay": 85.7, "Grass": 100.0},
      "tourney_wins": {"Australian Open": 6, "Wimbledon": 8},
      "tourney_matches": {"Australian Open": 7, "Wimbledon": 8},
      "tourney_win_pcts": {"Australian Open": 85.7, "Wimbledon": 100.0}
    }
  ]
}
```

#### Edge Schema

```json
{
  "edges": [
    {
      "player1": "Roger Federer",
      "player2": "Rafael Nadal",
      "total_matches": 15,
      "player1_wins": 6,
      "player2_wins": 9,
      "surface_breakdown": {"Hard": 8, "Clay": 5, "Grass": 2},
      "tourney_breakdown": {"Australian Open": 1, "Roland Garros": 4, "Wimbledon": 2},
      "surface_wins": {
        "Roger Federer": {"Hard": 5, "Clay": 0, "Grass": 1},
        "Rafael Nadal": {"Hard": 3, "Clay": 5, "Grass": 1}
      }
    }
  ]
}
```

#### Metadata Schema

```json
{
  "metadata": {
    "total_matches": 91,
    "total_players": 37,
    "total_matchups": 49,
    "year_range": {
      "min": 2003,
      "max": 2024
    }
  }
}
```

---

## 🔄 Data Types & Conventions

### Date Formats
- **Dates**: `YYYYMMDD` (int) - e.g., 20190714
- **Years**: `YYYY` (int) - e.g., 2019

### Percentages
- **Scale**: 0-100 (float)
- **Precision**: 1-2 decimal places
- **Example**: 82.35 (not 0.8235)

### Missing Data
- **Numeric**: `null` or `NaN`
- **String**: `null` or empty string
- **Boolean**: `null` or explicit False

### Country Codes
- **Format**: IOC 3-letter codes
- **Examples**: USA, SUI, ESP, SRB

### Player Names
- **Format**: "FirstName LastName"
- **Encoding**: UTF-8 (handles accents)
- **Examples**: "Rafael Nadal", "Björn Borg"

---

## 📖 Usage Examples

### Python

```python
import pandas as pd
import json

# Load base metrics
players = pd.read_pickle("data/base/player_metrics.pkl")
matches = pd.read_pickle("data/base/matches_enriched.pkl")

with open("data/base/head_to_head_matrix.json") as f:
    h2h = json.load(f)

# Get Big 3 breakthrough data
big3 = players[players['player_name'].isin(['Roger Federer', 'Rafael Nadal', 'Novak Djokovic'])]
print(big3[['player_name', 'matches_before_first_gs', 'first_gs_title_age']])

# Get dramatic GS finals
dramatic = matches[(matches['is_grand_slam']) & (matches['round'] == 'F') & (matches['comeback_score'] >= 2)]

# Get Federer-Nadal H2H
fed_nadal = h2h.get("Rafael Nadal|Roger Federer", {})
print(f"Total: {fed_nadal['total_matches']}, Clay: {fed_nadal['surfaces']['Clay']['total']}")
```

### JavaScript

```javascript
// Fetch from GitHub
const baseUrl = 'https://raw.githubusercontent.com/sorukumar/tml-data/main/data';

// Load NBI data
fetch(`${baseUrl}/nbi/gs_nailbiters.json`)
  .then(r => r.json())
  .then(matches => {
    const top10 = matches.slice(0, 10);
    console.log('Top 10 dramatic matches:', top10);
  });

// Load network graph
fetch(`${baseUrl}/network/grand_slam_finals_2003.json`)
  .then(r => r.json())
  .then(network => {
    console.log(`${network.metadata.total_players} players, ${network.metadata.total_matchups} edges`);
    // Use network.nodes and network.edges for visualization
  });
```

---

**Last Updated**: January 17, 2026  
**Data Version**: 2.0 (Base Metrics Architecture)  
**For API/Schemas**: All files available at `https://raw.githubusercontent.com/sorukumar/tml-data/main/data/`
