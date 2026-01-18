#!/usr/bin/env python3
"""
Fetch Base Tennis Data from TML-Database
This script fetches raw data and saves it as a base table for downstream processing.
Run by GitHub Actions weekly to keep data fresh.
"""

import pandas as pd
import requests
from io import StringIO
from datetime import datetime
import os
import sys
import json


def fetch_atp_data(start_year=1968, end_year=None):
    """
    Fetch ATP match data from TML-Database GitHub repository.
    
    Args:
        start_year: First year to fetch (default: 1968)
        end_year: Last year to fetch (default: current year)
    
    Returns:
        pd.DataFrame: Combined ATP match data
    """
    if end_year is None:
        end_year = datetime.now().year
    
    base_url = "https://raw.githubusercontent.com/Tennismylife/TML-Database/master/{}.csv"
    df_list = []
    
    print(f"Fetching ATP data from {start_year} to {end_year}...")
    print("-" * 60)
    
    for year in range(start_year, end_year + 1):
        url = base_url.format(year)
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = StringIO(response.text)
                df = pd.read_csv(data)
                df_list.append(df)
                print(f"✓ {year}: {len(df):,} matches")
            else:
                print(f"✗ {year}: HTTP {response.status_code}")
        except Exception as e:
            print(f"✗ {year}: {str(e)[:50]}")
    
    if not df_list:
        raise Exception("❌ No data fetched! Check network connection and repository URL.")
    
    combined_df = pd.concat(df_list, ignore_index=True)
    print("-" * 60)
    print(f"✓ Total matches loaded: {len(combined_df):,}")
    print(f"✓ Date range: {combined_df['tourney_date'].min()} to {combined_df['tourney_date'].max()}")
    
    return combined_df


def save_base_data(df, output_dir="data/base"):
    """
    Save base data as Parquet (compact, fast, portable).
    
    Args:
        df: DataFrame to save
        output_dir: Directory to save files
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Save as Parquet (compact, fast loading, portable across Python versions)
    parquet_path = f"{output_dir}/atp_matches_raw.parquet"
    df.to_parquet(parquet_path, compression='zstd', index=False)
    print(f"✓ Saved Parquet: {parquet_path} ({os.path.getsize(parquet_path) / 1024 / 1024:.1f} MB)")
    
    # Save metadata
    metadata = {
        'fetch_date': datetime.now().isoformat(),
        'total_matches': len(df),
        'date_range': f"{df['tourney_date'].min()} to {df['tourney_date'].max()}",
        'columns': list(df.columns),
        'shape': list(df.shape),
        'format': 'parquet',
        'compression': 'zstd'
    }
    
    metadata_path = f"{output_dir}/metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)
    print(f"✓ Saved metadata: {metadata_path}")


def main():
    """Main execution function"""
    print("=" * 60)
    print("FETCH BASE DATA - TML Tennis Database")
    print("=" * 60)
    
    try:
        # Fetch data
        df = fetch_atp_data(start_year=1968)
        
        # Save base data
        save_base_data(df)
        
        print("=" * 60)
        print("✅ SUCCESS: Base data fetched and saved")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print("=" * 60)
        print(f"❌ FAILED: {e}")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
