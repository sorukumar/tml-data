# Quick Start Guide

## For Users (Using the Data)

### 1. Access the Data

All data files are in the `data/` directory and are updated weekly:

```bash
# Clone the repository
git clone https://github.com/sorukumar/tml-data.git
cd tml-data

# Browse the data files
ls -R data/
```

### 2. Use in Your Project

**Python Example:**
```python
import json
import pandas as pd

# Load nailbiter matches
with open('data/nbi/gs_nailbiters.json') as f:
    nailbiters = json.load(f)
    print(f"Top dramatic match: {nailbiters[0]['match']}")

# Load dominance rankings
with open('data/gsdi/gs_dominance_rankings.json') as f:
    dominance = json.load(f)
    print(f"Most dominant performance: {dominance[0]['player']}")

# Load breakthrough data
df = pd.read_csv('data/stantheman/gs_breakthrough_comparison.csv')
print(df.head())
```

**JavaScript Example:**
```javascript
// Fetch nailbiter data
fetch('https://raw.githubusercontent.com/sorukumar/tml-data/main/data/nbi/gs_nailbiters.json')
  .then(response => response.json())
  .then(data => {
    console.log('Top dramatic match:', data[0].match);
  });
```

### 3. Data Files Overview

| File | Description | Format | Records |
|------|-------------|--------|---------|
| `data/nbi/gs_nailbiters.json` | Dramatic Grand Slam matches | JSON | 50 |
| `data/nbi/gs_nailbiters.csv` | Nailbiter matches | CSV | 100 |
| `data/nbi/iconic_gs_matches.json` | Iconic matches | JSON | 20 |
| `data/gsdi/gs_dominance_rankings.json` | Dominance rankings | JSON | 100 |
| `data/stantheman/gs_breakthrough_comparison.csv` | Breakthrough players | CSV | 50 |
| `data/globaltop100evolution/country_code_mapping.json` | Country codes | JSON | 127 |
| `data/globaltop100evolution/tennis_country_profiles.json` | Country profiles | JSON | 108 |
| `data/globaltop100evolution/global_timeline_dataset.json` | Timeline data | JSON | 10 |
| `data/globaltop100evolution/top_tennis_players_timeline.json` | Top players | JSON | 50 |

## For Developers (Running the ETL)

### 1. Setup

```bash
# Clone the repository
git clone https://github.com/sorukumar/tml-data.git
cd tml-data

# Create virtual environment (optional)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the ETL Pipeline

```bash
# Run the complete pipeline
python etl_pipeline.py

# Expected output:
# ============================================================
# Tennis Data ETL Pipeline
# ============================================================
# Fetching data from 1968 to 2025...
# ✓ Loaded 1968 (3723 matches)
# ...
# ✓ ETL Pipeline completed successfully!
```

### 3. Customize the Pipeline

Edit `etl_pipeline.py` to customize:

```python
# Change year range
self.start_year = 2000  # Start from year 2000
self.end_year = 2024    # End at 2024

# Change output directory
self.output_dir = "custom_data"

# Modify aggregations
# See methods: generate_nailbiters(), generate_dominance_rankings(), etc.
```

## For Maintainers (GitHub Actions)

### 1. Manual Trigger

Go to: https://github.com/sorukumar/tml-data/actions
- Click "Update Tennis Data" workflow
- Click "Run workflow"
- Select branch: `main`
- Click "Run workflow" button

### 2. Monitor Automated Runs

- Runs every Monday at 00:00 UTC
- Check status in Actions tab
- View logs for each run
- Check commit history for data updates

### 3. Troubleshooting

**If workflow fails:**
1. Check the Actions logs
2. Verify TML-Database is accessible
3. Check Python dependencies
4. Review error messages in logs

**If no data changes:**
- Workflow will skip commit
- This is normal if TML-Database hasn't updated

### 4. Update Dependencies

```bash
# Update requirements.txt
pip install --upgrade pandas requests numpy
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Update dependencies"
git push
```

## Integration Examples

### With TennisAnalytics

```javascript
// Replace static data imports
// OLD:
// import nailbiters from './nbi/data/gs_nailbiters.json';

// NEW:
import nailbiters from 'tml-data/data/nbi/gs_nailbiters.json';
```

### With Jupyter Notebooks

```python
# Load and analyze data
import pandas as pd
import matplotlib.pyplot as plt

# Load nailbiter data
df = pd.read_csv('data/nbi/gs_nailbiters.csv')

# Analyze by tournament
tournament_counts = df['tourney_name'].value_counts()
tournament_counts.plot(kind='bar')
plt.title('Nailbiter Matches by Tournament')
plt.show()
```

### With Web Applications

```html
<!-- Direct GitHub raw URL -->
<script>
fetch('https://raw.githubusercontent.com/sorukumar/tml-data/main/data/nbi/gs_nailbiters.json')
  .then(response => response.json())
  .then(data => {
    // Use the data in your app
    console.log(data);
  });
</script>
```

## Data Update Schedule

| Day | Time (UTC) | Action |
|-----|------------|--------|
| Monday | 00:00 | Automated update runs |
| Any day | Any time | Manual trigger available |

## Support

- **Issues**: https://github.com/sorukumar/tml-data/issues
- **Documentation**: See [README_DATA.md](README_DATA.md)
- **Source**: [TML-Database](https://github.com/Tennismylife/TML-Database)

## License

MIT License - See [LICENSE](LICENSE) file
