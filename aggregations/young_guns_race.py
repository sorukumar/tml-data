#!/usr/bin/env python3
"""
Young Guns Race Aggregation
Generates cumulative career trajectories for breakthrough stars vs Alcaraz/Sinner
X-Axis: Age
Y-Axis: Cumulative Wins / Titles (including ATP 250, 500)
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime
import math

# =============================================================================
# CONFIGURATION
# =============================================================================

TARGET_PLAYERS = {
    "Carlos Alcaraz": "2003-05-05",
    "Jannik Sinner": "2001-08-16",
    "Joao Fonseca": "2006-08-21",
    "Jakub Mensik": "2005-09-01",
    "Learner Tien": "2005-12-02"
}

OUTPUT_DIR = "data/greatness"

# =============================================================================
# LOGIC
# =============================================================================

def calculate_age_decimal(dob, dateval):
    """Calculate age in decimal years"""
    if pd.isna(dob) or pd.isna(dateval):
        return 0.0
    delta = dateval - dob
    return delta.days / 365.25

def process_player_career(player_name, dob_str, matches_df):
    """Process a single player's career with quarterly aggregation and enhanced metrics"""
    
    dob = pd.to_datetime(dob_str)
    
    # Filter matches where player participated
    p_matches = matches_df[
        (matches_df['winner_name'] == player_name) | 
        (matches_df['loser_name'] == player_name)
    ].copy()
    
    if p_matches.empty:
        print(f"⚠ Warning: No matches found for {player_name}")
        return None

    # Sort by date
    p_matches = p_matches.sort_values('tourney_date')
    
    trajectory = []
    milestones = []
    
    # Cumulative counters
    cum_matches = 0
    cum_wins = 0
    cum_titles = 0
    cum_gs = 0
    cum_masters = 0
    cum_atp500 = 0
    cum_atp250 = 0
    cum_atp_main_wins = 0 # ATP level wins (250+)
    
    # Advanced Metrics
    cum_top5_wins = 0
    cum_top5_matches = 0
    cum_top10_wins = 0
    cum_top10_matches = 0
    cum_top30_wins = 0
    cum_top30_matches = 0
    
    has_first_win = False
    has_first_title = False
    has_top_100 = False
    has_top_50 = False
    
    # Quarterly Hook Setup
    first_match_date = p_matches['tourney_date'].iloc[0]
    first_match_age = calculate_age_decimal(dob, first_match_date)
    
    current_hook_age = math.floor(first_match_age * 4) / 4.0
    
    for _, match in p_matches.iterrows():
        match_date = match['tourney_date']
        match_age = calculate_age_decimal(dob, match_date)
        
        while match_age >= current_hook_age:
            hook_date = dob + pd.Timedelta(days=int(current_hook_age * 365.25))
            
            # Calculate percentages for the current snapshot
            def get_pct(wins, total):
                return round((wins / total * 100), 1) if total > 0 else 0.0

            trajectory.append({
                "age": float(f"{current_hook_age:.2f}"),
                "wins": cum_wins,
                "atp_main_wins": cum_atp_main_wins,
                "win_pct": get_pct(cum_wins, cum_matches),
                "titles": cum_titles,
                "gs": cum_gs,
                "masters": cum_masters,
                "atp500": cum_atp500,
                "atp250": cum_atp250,
                "top5_wins": cum_top5_wins,
                "top5_win_pct": get_pct(cum_top5_wins, cum_top5_matches),
                "top10_wins": cum_top10_wins,
                "top10_win_pct": get_pct(cum_top10_wins, cum_top10_matches),
                "top30_wins": cum_top30_wins,
                "top30_win_pct": get_pct(cum_top30_wins, cum_top30_matches),
                "date": hook_date.strftime('%Y-%m-%d')
            })
            
            current_hook_age += 0.25

        is_winner = (match['winner_name'] == player_name)
        cum_matches += 1
        
        # Determine opponent rank category
        opp_rank = match.get('loser_rank') if is_winner else match.get('winner_rank')
        try:
            opp_rank = float(opp_rank)
            if not pd.isna(opp_rank) and opp_rank > 0:
                if opp_rank <= 5:
                    cum_top5_matches += 1
                    if is_winner: cum_top5_wins += 1
                if opp_rank <= 10:
                    cum_top10_matches += 1
                    if is_winner: cum_top10_wins += 1
                if opp_rank <= 30:
                    cum_top30_matches += 1
                    if is_winner: cum_top30_wins += 1
        except: pass

        # Ranking Milestones (Player's own rank)
        player_rank = match.get('winner_rank') if is_winner else match.get('loser_rank')
        try:
            player_rank = float(player_rank)
            if not pd.isna(player_rank) and player_rank > 0:
                if player_rank <= 100 and not has_top_100:
                    has_top_100 = True
                    milestones.append({
                        "type": "Top 100",
                        "name": f"Rank #{int(player_rank)}",
                        "age": match_age,
                        "date": match_date.strftime('%Y-%m-%d')
                    })
                if player_rank <= 50 and not has_top_50:
                    has_top_50 = True
                    milestones.append({
                        "type": "Top 50",
                        "name": f"Rank #{int(player_rank)}",
                        "age": match_age,
                        "date": match_date.strftime('%Y-%m-%d')
                    })
        except: pass

        if is_winner:
            cum_wins += 1
            
            # Count ATP level wins (Main Draw)
            if match['tourney_level'] in ['G', 'M', 'A']:
                cum_atp_main_wins += 1
                if not has_first_win:
                    has_first_win = True
                    milestones.append({
                        "type": "First ATP Win",
                        "name": match['tourney_name'],
                        "age": match_age,
                        "date": match_date.strftime('%Y-%m-%d')
                    })

            # Check for title
            if match['round'] == 'F':
                cum_titles += 1
                if match['tourney_level'] == 'G':
                    cum_gs += 1
                elif match['tourney_level'] == 'M':
                    cum_masters += 1
                elif match['tourney_level'] == 'A':
                    name_lower = match['tourney_name'].lower()
                    if '500' in name_lower:
                        cum_atp500 += 1
                    else:
                        cum_atp250 += 1
                
                if not has_first_title:
                    has_first_title = True
                    milestones.append({
                        "type": "First ATP Title",
                        "name": match['tourney_name'],
                        "age": match_age,
                        "date": match_date.strftime('%Y-%m-%d')
                    })

    # Final point
    actual_last_age = calculate_age_decimal(dob, p_matches['tourney_date'].iloc[-1])
    
    def get_pct(wins, total):
        return round((wins / total * 100), 1) if total > 0 else 0.0

    trajectory.append({
        "age": float(f"{actual_last_age:.2f}"),
        "wins": cum_wins,
        "atp_main_wins": cum_atp_main_wins,
        "win_pct": get_pct(cum_wins, cum_matches),
        "titles": cum_titles,
        "gs": cum_gs,
        "masters": cum_masters,
        "atp500": cum_atp500,
        "atp250": cum_atp250,
        "top5_wins": cum_top5_wins,
        "top5_win_pct": get_pct(cum_top5_wins, cum_top5_matches),
        "top10_wins": cum_top10_wins,
        "top10_win_pct": get_pct(cum_top10_wins, cum_top10_matches),
        "top30_wins": cum_top30_wins,
        "top30_win_pct": get_pct(cum_top30_wins, cum_top30_matches),
        "date": p_matches['tourney_date'].iloc[-1].strftime('%Y-%m-%d')
    })

    return {
        "name": player_name,
        "trajectory": trajectory,
        "milestones": milestones,
        "current_stats": {
            "wins": cum_wins,
            "atp_main_wins": cum_atp_main_wins,
            "win_pct": get_pct(cum_wins, cum_matches),
            "titles": cum_titles,
            "top10_wins": cum_top10_wins,
            "age": actual_last_age
        }
    }

def generate_young_guns_data(matches_enriched_path="data/base/matches_enriched.parquet",
                              output_dir=OUTPUT_DIR):
    
    print("\n" + "="*60)
    print("GENERATING YOUNG GUNS RACE DATA")
    print("="*60)
    
    if not os.path.exists(matches_enriched_path):
        print(f"Error: {matches_enriched_path} not found")
        return

    matches_df = pd.read_parquet(matches_enriched_path)
    matches_df['tourney_date'] = pd.to_datetime(matches_df['tourney_date'], format='%Y%m%d', errors='coerce')

    data_output = { "players": {} }
    
    for name, dob_str in TARGET_PLAYERS.items():
        print(f"Processing {name}...")
        career_data = process_player_career(name, dob_str, matches_df)
        if career_data:
            data_output["players"][name] = career_data
            
    os.makedirs(output_dir, exist_ok=True)
    out_path = f"{output_dir}/young_guns_race.json"
    
    def convert(o):
        if isinstance(o, np.int64): return int(o)
        if isinstance(o, np.float64): return float(o)
        if isinstance(o, np.bool_): return bool(o)
        return str(o)

    with open(out_path, 'w') as f:
        json.dump(data_output, f, default=convert, indent=None)
        
    print(f"\n✓ Saved: {out_path}")
    print("="*60)

if __name__ == "__main__":
    generate_young_guns_data()
