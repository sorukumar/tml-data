# TML Tennis Data Repository

Automated tennis data repository with aggregated statistics and analytics.

## Overview

This repository automatically fetches and processes tennis match data from the [TML-Database](https://github.com/Tennismylife/TML-Database), generating curated datasets for tennis analytics, visualizations, and research.

**Data Coverage**: 1968 to present (197,911+ matches)  
**Update Schedule**: Weekly (every Monday at 00:00 UTC)  
**Auto-generated Files**: 9 JSON/CSV files

## Quick Start

### Using the Data

All data files are located in the `data/` directory:
- `data/nbi/` - Nailbiter Index (dramatic matches)
- `data/gsdi/` - Grand Slam Dominance Index
- `data/stantheman/` - Breakthrough player analysis
- `data/globaltop100evolution/` - Global tennis evolution metrics

### Running Locally

```bash
# Clone the repository
git clone https://github.com/sorukumar/tml-data.git
cd tml-data

# Install dependencies
pip install -r requirements.txt

# Run the ETL pipeline
python etl_pipeline.py
```

## Features

- **Automated Updates**: GitHub Actions workflow runs weekly
- **Comprehensive Coverage**: Historical data from 1968 onwards
- **Multiple Formats**: JSON and CSV outputs
- **Rich Analytics**: Nailbiter Index, Dominance Rankings, Career Statistics
- **Global Insights**: Country-by-country tennis evolution

## Documentation

For detailed information about data schemas, files, and usage, see [README_DATA.md](README_DATA.md).

## Data Attribution

Raw match data sourced from:
- [TML-Database](https://github.com/Tennismylife/TML-Database)
- [Tennis Mylife Community](https://tennismylife.com)

## License

MIT License - See [LICENSE](LICENSE) file for details.
