#!/usr/bin/env python3
"""
Greatness Race Aggregation
Generates cumulative career trajectories for key players to compare "Greatness"
X-Axis: Age
Y-Axis: Cumulative Matches / Wins / Titles
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

TARGET_PLAYERS = {
    "Novak Djokovic": "1987-05-22",
    "Roger Federer": "1981-08-08",
    "Rafael Nadal": "1986-06-03",
    
    "Bjorn Borg": "1956-06-06",
    "Pete Sampras": "1971-08-12",
    "John McEnroe": "1959-02-16",
    "Ivan Lendl": "1960-03-07",
    "Andre Agassi": "1970-04-29",
    
    "Carlos Alcaraz": "2003-05-05",
    "Jannik Sinner": "2001-08-16"
}

OUTPUT_DIR = "data/greatness"

# =============================================================================
# LOGIC
# =============================================================================

# ... (previous functions similar, but calculate_age slightly robust)

def calculate_age_decimal(dob, dateval):
    """Calculate age in decimal years"""
    if pd.isna(dob) or pd.isna(dateval):
        return 0.0
    # ensure datetime types
    delta = dateval - dob
    return delta.days / 365.25

def process_player_career(player_name, dob_str, matches_df):
    """Process a single player's career with quarterly aggregation"""
    
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
    cum_finals = 0
    
    has_first_title = False
    has_first_gs = False
    has_first_masters = False
    has_top_10 = False
    has_no_1 = False
    
    # Quarterly Hook Setup
    # Start checking from age 15.0 or first match age, whichever is sensible, 
    # but for "Race" we often want a common grid.
    # Let's dynamically start from the quarter BEFORE the first match.
    first_match_date = p_matches['tourney_date'].iloc[0]
    first_match_age = calculate_age_decimal(dob, first_match_date)
    
    # Start hook: Floor to nearest 0.25
    import math
    current_hook_age = math.floor(first_match_age * 4) / 4.0
    
    # Iterate matches
    for _, match in p_matches.iterrows():
        match_date = match['tourney_date']
        match_age = calculate_age_decimal(dob, match_date)
        
        # 1. Fill Trajectory Hooks crossed by this match
        # While the current match happened AFTER (or exactly at) the next hook age
        while match_age >= current_hook_age:
            # We record the state AS IT WAS before this match (or at this exact time)
            # Actually, "Race" typically shows "What have you achieved by Age X".
            # The accumulated stats so far (before this match processed) are valid for the hook
            # if the match happened AFTER the hook date.
            
            # Calculate exact date for this hook for info
            hook_date = dob + pd.Timedelta(days=int(current_hook_age * 365.25))
            
            trajectory.append({
                "age": float(f"{current_hook_age:.2f}"),
                "match_count": cum_matches,
                "wins": cum_wins,
                "titles": cum_titles,
                "gs": cum_gs,
                "masters": cum_masters,
                "finals": cum_finals,
                "date": hook_date.strftime('%Y-%m-%d')
            })
            
            current_hook_age += 0.25

        # 2. Update Stats with this match
        is_winner = (match['winner_name'] == player_name)
        cum_matches += 1
        
        # --- RANKING MILESTONES ---
        # Get player rank for this match
        player_rank = match.get('winner_rank') if is_winner else match.get('loser_rank')
        
        # Handle NaN or bad data safely
        try:
            player_rank = float(player_rank)
            if not pd.isna(player_rank) and player_rank > 0:
                # First Top 10
                if player_rank <= 10 and not has_top_10:
                    has_top_10 = True
                    milestones.append({
                        "type": "Entered Top 10",
                        "name": f"Rank #{int(player_rank)}",
                        "year": match['year'],
                        "age": match_age,
                        "match_count": cum_matches,
                        "extra_info": f"vs {match['loser_name'] if is_winner else match['winner_name']}"
                    })
                
                # First World No. 1
                if player_rank == 1 and not has_no_1:
                    has_no_1 = True
                    milestones.append({
                        "type": "Reached World No. 1",
                        "name": "World No. 1",
                        "year": match['year'],
                        "age": match_age,
                        "match_count": cum_matches,
                        "extra_info": f"vs {match['loser_name'] if is_winner else match['winner_name']}"
                    })
        except (ValueError, TypeError):
            pass # Invalid rank data, skip
            
        if is_winner:
            cum_wins += 1
            
            # Check for title (Round = 'F' and won)
            if match['round'] == 'F':
                cum_titles += 1
                
                # Grand Slam
                if match['tourney_level'] == 'G':
                    cum_gs += 1
                    if not has_first_gs:
                        has_first_gs = True
                        milestones.append({
                            "type": "First Grand Slam",
                            "name": match['tourney_name'],
                            "year": match['year'],
                            "age": match_age,
                            "match_count": cum_matches
                        })
                
                # Masters
                elif match['tourney_level'] == 'M':
                    cum_masters += 1
                    if not has_first_masters:
                        has_first_masters = True
                        milestones.append({
                            "type": "First Masters 1000",
                            "name": match['tourney_name'],
                            "year": match['year'],
                            "age": match_age,
                            "match_count": cum_matches
                        })

                # ATP Finals (Big Title)
                elif match['tourney_level'] == 'F':
                    cum_finals += 1
                
                # First ever title
                if not has_first_title:
                    has_first_title = True
                    milestones.append({
                        "type": "First ATP Title",
                        "name": match['tourney_name'],
                        "year": match['year'],
                        "age": match_age,
                        "match_count": cum_matches
                    })

    # Add one final point for 'Now' / End of Career if not exactly on a quarter
    last_age = trajectory[-1]['age'] if trajectory else 0
    actual_last_age = calculate_age_decimal(dob, p_matches['tourney_date'].iloc[-1])
    
    if actual_last_age > last_age:
        trajectory.append({
            "age": float(f"{actual_last_age:.2f}"),
            "match_count": cum_matches,
            "wins": cum_wins,
            "titles": cum_titles,
            "gs": cum_gs,
            "masters": cum_masters,
            "finals": cum_finals,
            "date": p_matches['tourney_date'].iloc[-1].strftime('%Y-%m-%d')
        })

    return {
        "name": player_name,
        "trajectory": trajectory,
        "milestones": milestones,
        "current_stats": {
            "matches": cum_matches,
            "wins": cum_wins,
            "titles": cum_titles,
            "gs": cum_gs,
            "masters": cum_masters,
            "finals": cum_finals,
            "age": actual_last_age
        }
    }

def generate_greatness_data(matches_enriched_path="data/base/matches_enriched.parquet",
                            output_dir=OUTPUT_DIR):
    
    print("\n" + "="*60)
    print("GENERATING GREATNESS RACE DATA (Quarterly Aggregation)")
    print("="*60)
    
    # 1. Load Data
    print("Loading data...")
    try:
        matches_df = pd.read_parquet(matches_enriched_path)
    except Exception as e:
        print(f"Error loading parquets: {e}")
        return

    # Ensure date columns are datetime - GLOBAL FIX
    # The date is int64 YYYYMMDD, e.g. 19680101
    try:
        matches_df['tourney_date'] = pd.to_datetime(matches_df['tourney_date'], format='%Y%m%d', errors='coerce')
    except Exception as e:
        print(f"Warning: Date conversion failed: {e}")
        # Fatal if dates are wrong
        return

    data_output = {
        "players": {}
    }
    
    # 2. Process Each Target Player
    for name, dob_str in TARGET_PLAYERS.items():
        print(f"Processing {name}...")
        career_data = process_player_career(name, dob_str, matches_df)
        
        if career_data:
            data_output["players"][name] = career_data
            
    # 3. Save JSON
    os.makedirs(output_dir, exist_ok=True)
    out_path = f"{output_dir}/race_to_greatness.json"
    
    def convert(o):
        if isinstance(o, np.int64): return int(o)
        if isinstance(o, np.float64): return float(o)
        if isinstance(o, np.bool_): return bool(o)
        return str(o)

    with open(out_path, 'w') as f:
        json.dump(data_output, f, default=convert, indent=None)
        
    print(f"\n✓ Saved: {out_path}")
    print(f"  Players: {len(data_output['players'])}")
    print("="*60)

if __name__ == "__main__":
    generate_greatness_data()
