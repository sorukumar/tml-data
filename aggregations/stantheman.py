#!/usr/bin/env python3
"""
Stan The Man - Breakthrough Analysis
Compares players by matches played before their first Grand Slam title
"""

import pandas as pd
import numpy as np
import os


GRAND_SLAMS = ['Australian Open', 'Roland Garros', 'Wimbledon', 'US Open']


# =============================================================================
# BREAKTHROUGH CALCULATION
# =============================================================================

def calculate_breakthrough_comparison(df):
    """
    Calculate breakthrough comparison for GS champions
    
    Args:
        df: DataFrame with ATP match data
    
    Returns:
        list: Breakthrough data for players
    """
    print("\n" + "="*60)
    print("CALCULATING BREAKTHROUGH COMPARISON")
    print("="*60)
    
    # Get Grand Slam finals
    gs_finals = df[
        (df['tourney_name'].isin(GRAND_SLAMS)) & 
        (df['round'] == 'F')
    ].copy()
    
    if gs_finals.empty:
        print("✗ No Grand Slam finals found")
        return []
    
    print(f"✓ Found {len(gs_finals)} Grand Slam finals")
    
    # Track player statistics
    player_stats = {}
    
    for _, row in df.iterrows():
        winner = row['winner_name']
        loser = row['loser_name']
        
        if pd.isna(winner):
            continue
        
        # Initialize winner stats
        if winner not in player_stats:
            player_stats[winner] = {
                'first_match_date': row['tourney_date'],
                'matches_before_gs': 0,
                'gs_titles': 0,
                'total_matches': 0,
                'wins': 0,
                'losses': 0,
                'first_gs_date': None,
                'first_gs_age': None,
                'gs_matches': 0,
                'gs_wins': 0,
                'peak_ranking': 9999,
                'peak_ranking_before_gs': 9999,
                'wins_before_gs': 0,
                'matches_before_gs_count': 0
            }
        
        # Track overall stats
        player_stats[winner]['total_matches'] += 1
        player_stats[winner]['wins'] += 1
        
        # Track peak ranking (lower is better)
        if pd.notna(row.get('winner_rank')):
            winner_rank = row['winner_rank']
            if winner_rank < player_stats[winner]['peak_ranking']:
                player_stats[winner]['peak_ranking'] = winner_rank
        
        # Track Grand Slam matches
        if row['tourney_name'] in GRAND_SLAMS:
            player_stats[winner]['gs_matches'] += 1
            player_stats[winner]['gs_wins'] += 1
        
        # Initialize loser stats
        if pd.notna(loser):
            if loser not in player_stats:
                player_stats[loser] = {
                    'first_match_date': row['tourney_date'],
                    'matches_before_gs': 0,
                    'gs_titles': 0,
                    'total_matches': 0,
                    'wins': 0,
                    'losses': 0,
                    'first_gs_date': None,
                    'first_gs_age': None,
                    'gs_matches': 0,
                    'gs_wins': 0,
                    'peak_ranking': 9999,
                    'peak_ranking_before_gs': 9999,
                    'wins_before_gs': 0,
                    'matches_before_gs_count': 0
                }
            
            player_stats[loser]['total_matches'] += 1
            player_stats[loser]['losses'] += 1
            
            # Track peak ranking for loser
            if pd.notna(row.get('loser_rank')):
                loser_rank = row['loser_rank']
                if loser_rank < player_stats[loser]['peak_ranking']:
                    player_stats[loser]['peak_ranking'] = loser_rank
            
            # Track Grand Slam matches for loser
            if row['tourney_name'] in GRAND_SLAMS:
                player_stats[loser]['gs_matches'] += 1
        
        # Check if this is a GS final win
        if row['tourney_name'] in GRAND_SLAMS and row['round'] == 'F':
            if player_stats[winner]['first_gs_date'] is None:
                player_stats[winner]['first_gs_date'] = row['tourney_date']
                player_stats[winner]['first_gs_age'] = row.get('winner_age', 25)
            player_stats[winner]['gs_titles'] += 1
    
    print(f"✓ Tracked {len(player_stats)} unique players")
    
    # Calculate stats before first GS for each champion
    for player, stats in player_stats.items():
        if stats['gs_titles'] > 0 and stats['first_gs_date']:
            # Count matches and wins before first GS
            for _, row in df.iterrows():
                if row['tourney_date'] < stats['first_gs_date']:
                    if row['winner_name'] == player:
                        stats['matches_before_gs_count'] += 1
                        stats['wins_before_gs'] += 1
                        
                        # Track peak ranking before first GS
                        if pd.notna(row.get('winner_rank')):
                            winner_rank = row['winner_rank']
                            if winner_rank < stats['peak_ranking_before_gs']:
                                stats['peak_ranking_before_gs'] = winner_rank
                    
                    elif row['loser_name'] == player:
                        stats['matches_before_gs_count'] += 1
                        
                        # Track peak ranking before first GS
                        if pd.notna(row.get('loser_rank')):
                            loser_rank = row['loser_rank']
                            if loser_rank < stats['peak_ranking_before_gs']:
                                stats['peak_ranking_before_gs'] = loser_rank
    
    # Build breakthrough data
    breakthrough_data = []
    
    for player, stats in player_stats.items():
        if stats['gs_titles'] > 0 and stats['first_gs_date']:
            # Calculate actual years on tour from first match to first GS
            first_match_year = int(str(stats['first_match_date'])[:4]) if pd.notna(stats['first_match_date']) else 2000
            first_gs_year = int(str(stats['first_gs_date'])[:4]) if pd.notna(stats['first_gs_date']) else 2000
            years_on_tour = max(0, first_gs_year - first_match_year)
            
            # Calculate win percentages
            overall_win_pct = round(stats['wins'] / stats['total_matches'] * 100, 2) if stats['total_matches'] > 0 else 0
            gs_win_pct = round(stats['gs_wins'] / stats['gs_matches'] * 100, 2) if stats['gs_matches'] > 0 else 0
            win_pct_before_gs = round(stats['wins_before_gs'] / stats['matches_before_gs_count'] * 100, 2) if stats['matches_before_gs_count'] > 0 else 0
            
            # Handle peak rankings (leave empty if no ranking data available)
            peak_rank = float(stats['peak_ranking']) if stats['peak_ranking'] < 9999 else None
            peak_rank_before_gs = float(stats['peak_ranking_before_gs']) if stats['peak_ranking_before_gs'] < 9999 else None
            
            # Calculate career span properly
            last_match_year = 2025  # Current year as upper bound
            career_span = last_match_year - first_match_year
            
            breakthrough_data.append({
                'Player_Name': player,
                'Age_First_GS': round(stats['first_gs_age'], 1) if pd.notna(stats['first_gs_age']) else 25.0,
                'Matches_Before_First_GS': stats['matches_before_gs_count'],
                'Total_GS_Titles': stats['gs_titles'],
                'Year_Turned_Pro': first_match_year,
                'Year_First_GS': first_gs_year,
                'Total_ATP_Matches': stats['total_matches'],
                'Career_Span_Years': career_span,
                'Win_Percentage': overall_win_pct,
                'GS_Win_Ratio': gs_win_pct,
                'Peak_Ranking': peak_rank,
                'Peak_Ranking_Before_GS': peak_rank_before_gs,
                'Win_Percentage_Before_GS': win_pct_before_gs,
                'Years_On_Tour_Before_GS': years_on_tour
            })
    
    # Sort by matches before first GS (descending - "Stan the Man" style)
    breakthrough_data.sort(key=lambda x: x['Matches_Before_First_GS'], reverse=True)
    
    print(f"✓ Calculated breakthrough data for {len(breakthrough_data)} GS champions")
    if breakthrough_data:
        top = breakthrough_data[0]
        print(f"  Most matches before 1st GS: {top['Player_Name']} ({top['Matches_Before_First_GS']} matches)")
    
    return breakthrough_data[:50]


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


def generate_breakthrough_aggregation(base_data_path="data/base/atp_matches_base.pkl",
                                     output_dir="data/stantheman"):
    """Main function to generate breakthrough aggregation"""
    print("Loading base data...")
    df = pd.read_pickle(base_data_path)
    print(f"✓ Loaded {len(df):,} matches")
    
    breakthrough_data = calculate_breakthrough_comparison(df)
    
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
