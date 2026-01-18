#!/usr/bin/env python3
"""
Stan The Man - Breakthrough Analysis
Compares players by matches played before their first Grand Slam title
Now uses pre-aggregated player_metrics table for instant results
"""

import pandas as pd
import numpy as np
import os


# =============================================================================
# BREAKTHROUGH CALCULATION (USING BASE METRICS)
# =============================================================================

def calculate_breakthrough_comparison(player_metrics_df):
    """
    Calculate breakthrough comparison for GS champions using pre-aggregated data
    
    Args:
        player_metrics_df: DataFrame with player career metrics
    
    Returns:
        list: Breakthrough data for players
    """
    print("\n" + "="*60)
    print("CALCULATING BREAKTHROUGH COMPARISON")
    print("="*60)
    
    # Filter to only Grand Slam champions
    champions_df = player_metrics_df[player_metrics_df['has_gs_title'] == True].copy()
    
    if champions_df.empty:
        print("✗ No Grand Slam champions found")
        return []
    
    print(f"✓ Found {len(champions_df)} Grand Slam champions")
    
    # Build breakthrough data from pre-aggregated metrics
    breakthrough_data = []
    
    for _, player in champions_df.iterrows():
        breakthrough_data.append({
            'Player_Name': player['player_name'],
            'Age_First_GS': round(player['first_gs_title_age'], 1) if pd.notna(player['first_gs_title_age']) else 25.0,
            'Matches_Before_First_GS': int(player['matches_before_first_gs']),
            'Total_GS_Titles': int(player['gs_titles']),
            'Year_Turned_Pro': int(player['career_start_year']) if pd.notna(player['career_start_year']) else None,
            'Year_First_GS': int(player['first_gs_title_year']) if pd.notna(player['first_gs_title_year']) else None,
            'Total_ATP_Matches': int(player['total_matches']),
            'Career_Span_Years': int(player['career_span_years']) if pd.notna(player['career_span_years']) else 0,
            'Win_Percentage': player['win_pct'],
            'GS_Win_Ratio': player['gs_win_pct'],
            'Peak_Ranking': int(player['peak_ranking']) if pd.notna(player['peak_ranking']) else None,
            'Peak_Ranking_Before_GS': int(player['peak_ranking_before_first_gs']) if pd.notna(player['peak_ranking_before_first_gs']) else None,
            'Win_Percentage_Before_GS': player['win_pct_before_first_gs'],
            'Years_On_Tour_Before_GS': int(player['years_to_first_gs']) if pd.notna(player['years_to_first_gs']) else 0
        })
    
    # Sort by matches before first GS (descending - "Stan the Man" style)
    breakthrough_data.sort(key=lambda x: x['Matches_Before_First_GS'], reverse=True)
    
    print(f"✓ Calculated breakthrough data for {len(breakthrough_data)} GS champions")
    if breakthrough_data:
        top = breakthrough_data[0]
        print(f"  Most matches before 1st GS: {top['Player_Name']} ({top['Matches_Before_First_GS']} matches)")
    
    return breakthrough_data


# =============================================================================
# SAVE OUTPUTS
# =============================================================================

def save_breakthrough_data(breakthrough_data, output_dir="data/stantheman"):
    """Save breakthrough comparison data"""
    os.makedirs(output_dir, exist_ok=True)
    
    if breakthrough_data:
        df_breakthrough = pd.DataFrame(breakthrough_data)
        csv_path = f"{output_dir}/gs_breakthrough_comparison.csv"
        df_breakthrough.to_csv(csv_path, index=False)
        print(f"✓ Saved CSV: {csv_path} ({len(df_breakthrough)} players)")
    else:
        print("✗ No breakthrough data to save")


def generate_breakthrough_aggregation(player_metrics_path="data/base/player_metrics.parquet",
                                       output_dir="data/stantheman"):
    """
    Generate breakthrough analysis from player metrics
    """
    print("\n" + "="*60)
    print("GENERATING BREAKTHROUGH ANALYSIS (STAN THE MAN)")
    print("="*60)
    
    # Load player metrics (now Parquet format)
    print("\nLoading player metrics...")
    if player_metrics_path.endswith('.parquet'):
        player_metrics_df = pd.read_parquet(player_metrics_path)
    else:
        player_metrics_df = pd.read_pickle(player_metrics_path)

    try:
        print(f"✓ Loaded metrics for {len(player_metrics_df):,} players")
    except FileNotFoundError:
        print(f"❌ ERROR: Player metrics file not found: {player_metrics_path}")
        print("Please run: python build_base_metrics.py")
        return
    
    breakthrough_data = calculate_breakthrough_comparison(player_metrics_df)
    
    if breakthrough_data:
        save_breakthrough_data(breakthrough_data, output_dir)
        print("="*60)
        print("✅ BREAKTHROUGH AGGREGATION COMPLETE")
        print("="*60)
    else:
        print("="*60)
        print("❌ BREAKTHROUGH AGGREGATION FAILED: No data")
        print("="*60)


if __name__ == "__main__":
    generate_breakthrough_aggregation()
