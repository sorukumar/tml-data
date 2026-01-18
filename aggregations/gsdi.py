#!/usr/bin/env python3
"""
GSDI (Grand Slam Dominance Index) Calculator
Ranks the most dominant Grand Slam campaigns by player-tournament-year
Now uses pre-enriched match data with parsed scores
"""

import pandas as pd
import numpy as np
import json
import os


# =============================================================================
# GSDI CALCULATION (USING ENRICHED MATCHES)
# =============================================================================

def calculate_gsdi(df_enriched):
    """
    Calculate GSDI (Grand Slam Dominance Index) for tournament campaigns
    
    Ranks player-tournament-year combinations where player won title
    """
    print("\n" + "="*60)
    print("CALCULATING GSDI (GRAND SLAM DOMINANCE INDEX)")
    print("="*60)
    
    GRAND_SLAMS = ['Australian Open', 'Roland Garros', 'Wimbledon', 'US Open']
    
    # Filter Grand Slam matches (already flagged in enriched data)
    gs_df = df_enriched[
        (df_enriched['is_grand_slam'] == True) &
        (df_enriched['tourney_name'].isin(GRAND_SLAMS))
    ].copy()
    
    print(f"✓ Analyzing {len(gs_df):,} Grand Slam matches from {gs_df['year'].min()}-{gs_df['year'].max()}")
    
    # Find finals (F = Final)
    finals_df = gs_df[gs_df['round'] == 'F'].copy()
    print(f"✓ Found {len(finals_df)} Grand Slam finals")
    
    # Get all champions (winners of finals)
    champions = finals_df.groupby(['winner_name', 'tourney_name', 'year']).size().reset_index()
    champions = champions[['winner_name', 'tourney_name', 'year']].rename(columns={'winner_name': 'player'})
    
    print(f"✓ Tracking {len(champions)} championship campaigns")
    
    # Check for optional columns
    has_loser_rank = 'loser_rank' in gs_df.columns
    has_minutes = 'minutes' in gs_df.columns
    
    if not has_loser_rank:
        print("⚠️  Warning: 'loser_rank' column not found. Opponent quality metrics will be estimates.")
    if not has_minutes:
        print("⚠️  Warning: 'minutes' column not found. Speed score will be estimated.")
    
    rankings = []
    
    # For each championship campaign, analyze all matches
    for idx, row in champions.iterrows():
        player = row['player']
        tournament = row['tourney_name']
        year = row['year']
        
        # Get all matches for this player in this tournament/year
        campaign = gs_df[
            (gs_df['winner_name'] == player) & 
            (gs_df['tourney_name'] == tournament) & 
            (gs_df['year'] == year)
        ].copy()
        
        if len(campaign) == 0:
            continue
        
        # Use pre-parsed scores from enriched data
        total_sets_won = campaign['winner_sets'].sum()
        total_sets_lost = campaign['loser_sets'].sum()
        total_games_won = campaign['winner_games'].sum()
        total_games_lost = campaign['loser_games'].sum()
        
        # Calculate percentages
        total_sets = total_sets_won + total_sets_lost
        total_games = total_games_won + total_games_lost
        
        sets_won_pct = (total_sets_won / total_sets * 100) if total_sets > 0 else 0
        games_won_pct = (total_games_won / total_games * 100) if total_games > 0 else 0
        
        # Estimate points won percentage (correlation with games won)
        points_won_pct = 50 + (games_won_pct - 50) * 0.6
        
        # Opponent quality (estimate based on ranking if available)
        if has_loser_rank:
            avg_opponent_rank = campaign['loser_rank'].mean() if campaign['loser_rank'].notna().any() else 50
            pct_top30_opponents = (campaign['loser_rank'] <= 30).sum() / len(campaign) * 100
            top5_wins = (campaign['loser_rank'] <= 5).sum()
        else:
            # Use conservative estimates if ranking data not available
            avg_opponent_rank = 50
            pct_top30_opponents = 30.0  # Assume 30% top-30 opponents in GS
            top5_wins = 1 if len(campaign) >= 6 else 0  # Assume at least 1 in full tournament
        
        # Speed score (faster = more dominant)
        if has_minutes and campaign['minutes'].notna().any():
            avg_minutes = campaign['minutes'].mean()
        else:
            avg_minutes = 120  # Default estimate
        
        max_typical_minutes = 240
        speed_score = max(0, min(100, (max_typical_minutes - avg_minutes) / max_typical_minutes * 100 + 50))
        
        # Bonus points
        bonus_points = 0
        if total_sets_lost == 0:  # Perfect campaign
            bonus_points += 10
        bonus_points += top5_wins * 3
        
        # GSDI Score (weighted combination + bonus points)
        dominance_score = (
            sets_won_pct * 0.32 +
            games_won_pct * 0.25 +
            points_won_pct * 0.23 +
            pct_top30_opponents * 0.10 +
            speed_score * 0.10 +
            bonus_points
        )
        
        rankings.append({
            "rank": 0,  # Will be set after sorting
            "player": player,
            "tournament": tournament,
            "year": int(year),
            "dominance_score": round(dominance_score, 2),
            "sets_won": int(total_sets_won),
            "sets_won_pct": round(sets_won_pct, 1),
            "games_won_pct": round(games_won_pct, 1),
            "points_won_pct": round(points_won_pct, 1),
            "pct_top30_opponents": round(pct_top30_opponents, 1),
            "speed_score": round(speed_score, 1),
            "avg_match_minutes": round(avg_minutes, 1),
            "top5_wins": int(top5_wins),
            "perfect_campaign": total_sets_lost == 0,
            "sets_lost": int(total_sets_lost),
            "matches_won": len(campaign),
            "score_breakdown": {
                "sets": round(sets_won_pct * 0.32, 1),
                "games": round(games_won_pct * 0.25, 1),
                "points": round(points_won_pct * 0.23, 1),
                "opponent": round(pct_top30_opponents * 0.10, 1),
                "speed": round(speed_score * 0.10, 1),
                "bonus": round(bonus_points, 1)
            }
        })
    
    # Sort by dominance score
    rankings.sort(key=lambda x: x['dominance_score'], reverse=True)
    
    # Add ranks
    for i, r in enumerate(rankings, 1):
        r['rank'] = i
    
    print(f"✓ GSDI calculated for {len(rankings)} campaigns")
    if rankings:
        print("\n--- Top 10 Most Dominant Campaigns ---")
        for r in rankings[:10]:
            perfect = " 🏆 PERFECT" if r['perfect_campaign'] else ""
            print(f"{r['rank']:2d}. {r['player']:20s} - {r['tournament']:15s} {r['year']} | Score: {r['dominance_score']:.2f}{perfect}")
    
    return rankings


# =============================================================================
# SAVE OUTPUTS
# =============================================================================

def save_gsdi_data(rankings, output_dir="data/gsdi"):
    """Save GSDI data"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert all numpy types to Python native types for JSON serialization
    def convert_numpy_types(obj):
        """Recursively convert numpy types to Python native types"""
        if isinstance(obj, dict):
            return {key: convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        else:
            return obj
    
    rankings_clean = convert_numpy_types(rankings)
    
    json_path = f"{output_dir}/gs_dominance_rankings.json"
    with open(json_path, 'w') as f:
        json.dump(rankings_clean, f, indent=2)
    print(f"\n✓ Saved JSON: {json_path} ({len(rankings)} campaigns)")


def generate_gsdi_aggregation(matches_enriched_path="data/base/matches_enriched.parquet",
                              output_dir="data/gsdi"):
    """
    Generate GSDI aggregation from enriched matches data
    """
    print("\n" + "="*60)
    print("GENERATING GSDI (GRAND SLAM DOMINANCE INDEX) DATA")
    print("="*60)
    
    # Load enriched matches (now Parquet format)
    print("\nLoading enriched matches...")
    if matches_enriched_path.endswith('.parquet'):
        df_enriched = pd.read_parquet(matches_enriched_path)
    else:
        df_enriched = pd.read_pickle(matches_enriched_path)
    
    try:
        print(f"✓ Loaded {len(df_enriched):,} enriched matches")
    except FileNotFoundError:
        print(f"❌ ERROR: Enriched matches file not found: {matches_enriched_path}")
        print("Please run: python build_base_metrics.py")
        return
    
    rankings = calculate_gsdi(df_enriched)
    
    if rankings:
        save_gsdi_data(rankings, output_dir)
        print("\n" + "="*60)
        print("✅ GSDI AGGREGATION COMPLETE")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("❌ GSDI AGGREGATION FAILED: No data")
        print("="*60)


if __name__ == "__main__":
    generate_gsdi_aggregation()
