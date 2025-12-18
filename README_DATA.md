# TML Tennis Data

Automated tennis data repository sourced from the [TML-Database](https://github.com/Tennismylife/TML-Database).

## Overview

This repository contains aggregated tennis statistics and analysis data, automatically updated weekly from the TML-Database. The data is processed and structured to support various tennis analytics visualizations and research projects.

## Data Files

### Nailbiter Index (NBI)
Located in `data/nbi/`:
- **gs_nailbiters.json** - Top 50 most dramatic Grand Slam matches with detailed statistics
- **gs_nailbiters.csv** - CSV version with 100 nailbiter matches
- **iconic_gs_matches.json** - Top 20 iconic Grand Slam matches

The Nailbiter Index measures match drama based on:
- Set margins
- Tiebreak occurrences
- Match duration
- Comebacks and momentum shifts

### Grand Slam Dominance Index (GSDI)
Located in `data/gsdi/`:
- **gs_dominance_rankings.json** - Top 100 most dominant Grand Slam tournament performances

Rankings are calculated based on:
- Set/game/point win percentages
- Match efficiency (speed score)
- Quality of opposition
- Perfect campaigns (no sets lost)

### Breakthrough Comparison
Located in `data/stantheman/`:
- **gs_breakthrough_comparison.csv** - Career statistics for players before and after their first Grand Slam title

Includes metrics like:
- Age at first Grand Slam win
- Matches played before first title
- Career win percentages
- Peak rankings

### Global Top 100 Evolution
Located in `data/globaltop100evolution/`:
- **country_code_mapping.json** - IOC country code mappings
- **tennis_country_profiles.json** - Country-by-country tennis statistics over time
- **global_timeline_dataset.json** - Global tennis diversity metrics by era
- **top_tennis_players_timeline.json** - Top 50 players' career timelines

Tracks:
- Countries represented in top 100
- Geographic diversity of professional tennis
- Top players by nationality
- Historical trends in global tennis participation

## Data Updates

The data is automatically updated:
- **Schedule**: Every Monday at 00:00 UTC
- **Source**: [TML-Database](https://github.com/Tennismylife/TML-Database)
- **Method**: GitHub Actions workflow
- **Coverage**: 1968 to present

### Manual Update

To manually trigger a data update:
1. Go to the "Actions" tab in this repository
2. Select "Update Tennis Data" workflow
3. Click "Run workflow"

## ETL Pipeline

The `etl_pipeline.py` script:
1. Fetches CSV files from TML-Database (all years)
2. Processes and aggregates the data
3. Generates JSON and CSV output files
4. Maintains consistent schemas for downstream applications

## Requirements

- Python 3.11+
- pandas >= 2.0.0
- requests >= 2.31.0
- numpy >= 1.24.0

## Usage

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the ETL pipeline
python etl_pipeline.py
```

### Integration

The generated data files can be used directly in web applications, analytics dashboards, or research projects. All files use standard JSON/CSV formats.

## Data Schema

### Nailbiter Matches (JSON)
```json
{
  "match": "Player A def. Player B",
  "tourney": "Tournament Name",
  "round": "Round",
  "date": "YYYYMMDD",
  "score": "Set scores",
  "duration": 180,
  "NBI": 0.95,
  "NBI_100": 95.0,
  "drama_tags": "tags",
  "raw_stats": { ... }
}
```

### Dominance Rankings (JSON)
```json
{
  "rank": 1,
  "player": "Player Name",
  "tournament": "Grand Slam",
  "year": 2020,
  "dominance_score": 95.5,
  "sets_won": 21,
  "sets_won_pct": 100.0,
  ...
}
```

## Source Data Attribution

All raw tennis match data is sourced from:
- **TML-Database**: https://github.com/Tennismylife/TML-Database
- **Tennis Mylife Community**: https://tennismylife.com

## License

This project is licensed under the MIT License - see the LICENSE file for details.

The source data from TML-Database is subject to its own license terms.

## Contributing

Issues and pull requests are welcome! Please ensure:
- ETL pipeline changes maintain backward compatibility
- Generated data files match existing schemas
- Documentation is updated accordingly

## Contact

For questions or issues, please open a GitHub issue in this repository.
