#!/usr/bin/env python3
"""
Part 2: Merge 2026 CSV into Master Parquet.
Implements a safe 'upsert' logic using tourney_id and match_num as unique keys.
"""
import pandas as pd
import os
import sys

def merge_data(master_path="data/base/atp_matches_raw.parquet", 
               incremental_csv="data/raw/2026.csv"):
    
    print("-" * 60)
    print("DATA MERGE: Master Parquet + 2026 Incremental")
    print("-" * 60)

    # 1. Load Master Data
    if not os.path.exists(master_path):
        print(f"❌ Error: Master file not found at {master_path}")
        return False
    
    df_master = pd.read_parquet(master_path)
    print(f"✓ Loaded Master: {len(df_master):,} matches")
    
    # 2. Load New 2026 Data
    if not os.path.exists(incremental_csv):
        print(f"❌ Error: New CSV not found at {incremental_csv}")
        return False
        
    df_new = pd.read_csv(incremental_csv)
    
    # 3. Validation: Sanity check on new data
    if len(df_new) == 0:
        print("⚠️ Warning: Fetched CSV is empty. Aborting merge to prevent data loss.")
        return False
    
    if 'tourney_id' not in df_new.columns or 'match_num' not in df_new.columns:
        print("❌ Error: CSV schema is missing primary keys (tourney_id, match_num).")
        return False

    print(f"✓ Loaded New Data: {len(df_new):,} matches from 2026")

    # 4. Type Normalization: Ensure new data matches master schema
    # This prevents 'Conversion failed' errors when saving to Parquet
    for col in df_master.columns:
        if col in df_new.columns:
            try:
                # Convert new data to match master data types
                if df_master[col].dtype == 'float64':
                    df_new[col] = pd.to_numeric(df_new[col], errors='coerce')
                elif df_master[col].dtype == 'int64':
                    df_new[col] = pd.to_numeric(df_new[col], errors='coerce').fillna(0).astype('int64')
                else:
                    df_new[col] = df_new[col].astype(df_master[col].dtype)
            except Exception as e:
                print(f"⚠️ Warning: Could not normalize column '{col}': {e}")

    # 5. Upsert Logic:
    # Combine both datasets, then drop duplicates based on the match keys.
    # We keep the 'last' occurrence, which will be the one from the new CSV.
    
    # Ensure column order matches
    df_new = df_new[df_master.columns]
    
    df_combined = pd.concat([df_master, df_new], ignore_index=True)
    
    # Drop duplicates: Keep the latest record for any given match key
    initial_count = len(df_combined)
    df_final = df_combined.drop_duplicates(subset=['tourney_id', 'match_num'], keep='last')
    final_count = len(df_final)
    
    duplicates_updated = initial_count - final_count
    new_matches_added = len(df_final) - len(df_master)
    
    print(f"✓ Statistics:")
    print(f"  - Matches updated/replaced: {duplicates_updated}")
    print(f"  - New matches added: {new_matches_added}")
    print(f"  - Final total: {len(df_final):,} matches")

    # 6. Save back to Parquet
    try:
        df_final.to_parquet(master_path, compression='zstd', index=False)
        print(f"✅ Success: Updated {master_path}")
        return True
    except Exception as e:
        print(f"❌ Error saving parquet: {e}")
        return False

if __name__ == "__main__":
    if merge_data():
        sys.exit(0)
    else:
        sys.exit(1)
