#!/usr/bin/env python3
"""
Career Longevity & Survival Analysis Aggregator
Analyzes player career lengths and survival probabilities in professional tennis
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime


# =============================================================================
# CAREER LONGEVITY ANALYSIS
# =============================================================================

def calculate_career_stats(df):
    """
    Calculate career statistics for all players
    
    Returns:
        DataFrame with player career information
    """
    print("\n" + "="*60)
    print("CALCULATING CAREER LONGEVITY STATISTICS")
    print("="*60)
    
    # Convert tourney_date to datetime
    df['tourney_date'] = pd.to_datetime(df['tourney_date'].astype(str), format='%Y%m%d', errors='coerce')
    
    # Get all player appearances (both as winner and loser)
    winner_data = df[['winner_id', 'winner_name', 'tourney_date', 'winner_rank']].rename(
        columns={'winner_id': 'player_id', 'winner_name': 'player_name', 'winner_rank': 'rank'}
    )
    loser_data = df[['loser_id', 'loser_name', 'tourney_date', 'loser_rank']].rename(
        columns={'loser_id': 'player_id', 'loser_name': 'player_name', 'loser_rank': 'rank'}
    )
    
    all_player_data = pd.concat([winner_data, loser_data], ignore_index=True)
    all_player_data = all_player_data.dropna(subset=['player_id', 'tourney_date'])
    
    print(f"✓ Processing {len(all_player_data):,} player match records...")
    
    # Calculate career statistics for each player
    career_stats = []
    
    for player_id, player_matches in all_player_data.groupby('player_id'):
        player_name = player_matches['player_name'].mode()[0] if not player_matches['player_name'].empty else 'Unknown'
        
        career_start = player_matches['tourney_date'].min()
        career_end = player_matches['tourney_date'].max()
        career_length_days = (career_end - career_start).days
        career_length_years = career_length_days / 365.25
        
        total_matches = len(player_matches)
        
        # Get best ranking
        best_rank = player_matches['rank'].min() if player_matches['rank'].notna().any() else 999
        
        # Calculate wins and losses
        wins = len(df[df['winner_id'] == player_id])
        losses = len(df[df['loser_id'] == player_id])
        win_pct = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
        
        career_stats.append({
            'player_id': str(player_id),
            'player_name': player_name,
            'career_start': career_start.strftime('%Y-%m-%d'),
            'career_end': career_end.strftime('%Y-%m-%d'),
            'career_length_days': int(career_length_days),
            'career_length_years': round(career_length_years, 2),
            'total_matches': int(total_matches),
            'wins': int(wins),
            'losses': int(losses),
            'win_pct': round(win_pct, 2),
            'best_rank': int(best_rank) if best_rank < 999 else None
        })
    
    career_df = pd.DataFrame(career_stats)
    
    print(f"✓ Calculated career stats for {len(career_df):,} players")
    print(f"  Avg career length: {career_df['career_length_years'].mean():.2f} years")
    print(f"  Median career length: {career_df['career_length_years'].median():.2f} years")
    
    return career_df


def calculate_survival_data(career_df):
    """
    Calculate survival probabilities (what % of players remain active after X years)
    
    Returns:
        dict with survival curve data
    """
    print("\n--- Calculating Survival Curve ---")
    
    # Define year thresholds
    year_thresholds = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 18, 20, 25, 30]
    
    total_players = len(career_df)
    survival_data = []
    
    for year in year_thresholds:
        players_surviving = len(career_df[career_df['career_length_years'] >= year])
        survival_pct = (players_surviving / total_players * 100) if total_players > 0 else 0
        
        survival_data.append({
            'years': year,
            'players_remaining': players_surviving,
            'survival_probability': round(survival_pct, 2)
        })
        
        if year <= 10:
            print(f"  After {year:2d} years: {survival_pct:5.1f}% ({players_surviving:,} players)")
    
    return {
        'timeline': survival_data,
        'total_players': total_players
    }


def calculate_career_categories(career_df):
    """
    Categorize players by career length
    """
    print("\n--- Career Length Distribution ---")
    
    categories = {
        'less_than_1_year': {
            'label': 'Less than 1 year',
            'count': len(career_df[career_df['career_length_years'] < 1]),
            'min_years': 0,
            'max_years': 1
        },
        '1_to_2_years': {
            'label': '1-2 years',
            'count': len(career_df[(career_df['career_length_years'] >= 1) & (career_df['career_length_years'] < 2)]),
            'min_years': 1,
            'max_years': 2
        },
        '2_to_5_years': {
            'label': '2-5 years',
            'count': len(career_df[(career_df['career_length_years'] >= 2) & (career_df['career_length_years'] < 5)]),
            'min_years': 2,
            'max_years': 5
        },
        '5_to_10_years': {
            'label': '5-10 years',
            'count': len(career_df[(career_df['career_length_years'] >= 5) & (career_df['career_length_years'] < 10)]),
            'min_years': 5,
            'max_years': 10
        },
        '10_to_15_years': {
            'label': '10-15 years',
            'count': len(career_df[(career_df['career_length_years'] >= 10) & (career_df['career_length_years'] < 15)]),
            'min_years': 10,
            'max_years': 15
        },
        '15_plus_years': {
            'label': '15+ years',
            'count': len(career_df[career_df['career_length_years'] >= 15]),
            'min_years': 15,
            'max_years': None
        }
    }
    
    total = len(career_df)
    
    for key, cat in categories.items():
        pct = (cat['count'] / total * 100) if total > 0 else 0
        cat['percentage'] = round(pct, 2)
        print(f"  {cat['label']:20s}: {cat['count']:6,} players ({pct:5.1f}%)")
    
    return categories


def get_longest_careers(career_df, top_n=50):
    """Get players with longest careers"""
    print(f"\n--- Top {top_n} Longest Careers ---")
    
    longest = career_df.nlargest(top_n, 'career_length_years')[
        ['player_name', 'career_length_years', 'career_start', 'career_end', 
         'total_matches', 'wins', 'best_rank']
    ].to_dict('records')
    
    for i, player in enumerate(longest[:10], 1):
        print(f"  {i:2d}. {player['player_name']:25s} - {player['career_length_years']:5.1f} years "
              f"({player['total_matches']:,} matches, Best: #{player['best_rank']})")
    
    return longest


def calculate_match_volume_stats(career_df):
    """Calculate statistics by match volume"""
    print("\n--- Match Volume Distribution ---")
    
    match_categories = {
        'less_than_50': {
            'label': 'Less than 50 matches',
            'count': len(career_df[career_df['total_matches'] < 50])
        },
        '50_to_200': {
            'label': '50-200 matches',
            'count': len(career_df[(career_df['total_matches'] >= 50) & (career_df['total_matches'] < 200)])
        },
        '200_to_500': {
            'label': '200-500 matches',
            'count': len(career_df[(career_df['total_matches'] >= 200) & (career_df['total_matches'] < 500)])
        },
        '500_to_1000': {
            'label': '500-1000 matches',
            'count': len(career_df[(career_df['total_matches'] >= 500) & (career_df['total_matches'] < 1000)])
        },
        '1000_plus': {
            'label': '1000+ matches',
            'count': len(career_df[career_df['total_matches'] >= 1000])
        }
    }
    
    total = len(career_df)
    
    for key, cat in match_categories.items():
        pct = (cat['count'] / total * 100) if total > 0 else 0
        cat['percentage'] = round(pct, 2)
        print(f"  {cat['label']:25s}: {cat['count']:6,} players ({pct:5.1f}%)")
    
    return match_categories


# =============================================================================
# SAVE OUTPUTS
# =============================================================================

def save_career_longevity_data(career_df, survival_data, categories, longest_careers, 
                                match_stats, output_dir="data/career_longevity"):
    """Save career longevity data"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Full player career summary (top 1000 by career length)
    top_careers = career_df.nlargest(1000, 'career_length_years').to_dict('records')
    
    with open(f"{output_dir}/player_careers_top1000.json", 'w') as f:
        json.dump(top_careers, f, indent=2)
    print(f"\n✓ Saved: player_careers_top1000.json ({len(top_careers)} players)")
    
    # 2. Survival curve data
    with open(f"{output_dir}/survival_curve.json", 'w') as f:
        json.dump(survival_data, f, indent=2)
    print(f"✓ Saved: survival_curve.json")
    
    # 3. Career categories
    with open(f"{output_dir}/career_categories.json", 'w') as f:
        json.dump(categories, f, indent=2)
    print(f"✓ Saved: career_categories.json")
    
    # 4. Longest careers
    with open(f"{output_dir}/longest_careers.json", 'w') as f:
        json.dump(longest_careers, f, indent=2)
    print(f"✓ Saved: longest_careers.json ({len(longest_careers)} players)")
    
    # 5. Match volume statistics
    with open(f"{output_dir}/match_volume_stats.json", 'w') as f:
        json.dump(match_stats, f, indent=2)
    print(f"✓ Saved: match_volume_stats.json")
    
    # 6. Summary statistics
    summary = {
        'total_players': len(career_df),
        'avg_career_length_years': round(career_df['career_length_years'].mean(), 2),
        'median_career_length_years': round(career_df['career_length_years'].median(), 2),
        'avg_total_matches': round(career_df['total_matches'].mean(), 2),
        'median_total_matches': round(career_df['total_matches'].median(), 2),
        'players_less_than_2_years': len(career_df[career_df['career_length_years'] < 2]),
        'percentage_less_than_2_years': round(len(career_df[career_df['career_length_years'] < 2]) / len(career_df) * 100, 2),
        'players_10_plus_years': len(career_df[career_df['career_length_years'] >= 10]),
        'percentage_10_plus_years': round(len(career_df[career_df['career_length_years'] >= 10]) / len(career_df) * 100, 2),
        'generation_date': datetime.now().strftime('%Y-%m-%d')
    }
    
    with open(f"{output_dir}/summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✓ Saved: summary.json")


def generate_career_longevity_aggregation(base_data_path="data/base/atp_matches_raw.parquet",
                                           output_dir="data/career_longevity"):
    """
    Generate career longevity and survival analysis data
    """
    print("\n" + "="*60)
    print("GENERATING CAREER LONGEVITY DATA")
    print("="*60)
    
    # Load base data (now Parquet format)
    print("\nLoading base data...")
    if base_data_path.endswith('.parquet'):
        df = pd.read_parquet(base_data_path)
    else:
        df = pd.read_pickle(base_data_path)
    
    print(f"✓ Loaded {len(df):,} matches")
    
    # Calculate career statistics
    career_df = calculate_career_stats(df)
    
    # Calculate survival data
    survival_data = calculate_survival_data(career_df)
    
    # Calculate career categories
    categories = calculate_career_categories(career_df)
    
    # Get longest careers
    longest_careers = get_longest_careers(career_df, top_n=100)
    
    # Calculate match volume stats
    match_stats = calculate_match_volume_stats(career_df)
    
    # Save all data
    save_career_longevity_data(
        career_df, survival_data, categories, 
        longest_careers, match_stats, output_dir
    )
    
    print("\n" + "="*60)
    print("✅ CAREER LONGEVITY AGGREGATION COMPLETE")
    print("="*60)


if __name__ == "__main__":
    generate_career_longevity_aggregation()
