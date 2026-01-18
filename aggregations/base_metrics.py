#!/usr/bin/env python3
"""
Base Metrics Builder
Pre-aggregates player statistics and enriches match data for all analyses
Creates reusable base tables that feed all downstream aggregations

Storage Format: Parquet (compact, fast, portable)
"""

import pandas as pd
import numpy as np
import os
import json
from collections import defaultdict
from .shared_utils import (
    is_grand_slam,
    get_grand_slam_name,
    parse_score,
    parse_sets,
    advanced_comeback_score,
    final_set_tiebreak,
    calculate_win_percentage,
    get_player_peak_ranking,
    get_player_country
)


# =============================================================================
# PLAYER CAREER METRICS
# =============================================================================

def build_player_career_metrics(df):
    """
    Build comprehensive player-level career statistics
    
    Returns:
        pd.DataFrame: One row per player with all career metrics
    """
    print("\n" + "="*60)
    print("BUILDING PLAYER CAREER METRICS")
    print("="*60)
    
    player_stats = {}
    
    # Initialize all players
    all_players = set(df['winner_name'].dropna().unique()) | set(df['loser_name'].dropna().unique())
    
    for player in all_players:
        player_stats[player] = {
            'player_name': player,
            'country': None,
            
            # Career span
            'first_match_date': None,
            'last_match_date': None,
            'career_start_year': None,
            'career_end_year': None,
            'career_span_years': 0,
            
            # Overall match statistics
            'total_matches': 0,
            'total_wins': 0,
            'total_losses': 0,
            'win_pct': 0.0,
            
            # Grand Slam statistics
            'gs_matches': 0,
            'gs_wins': 0,
            'gs_losses': 0,
            'gs_win_pct': 0.0,
            'gs_titles': 0,
            'gs_finals': 0,
            'gs_semifinals': 0,
            'gs_quarterfinals': 0,
            
            # First Grand Slam title (for breakthrough analysis)
            'first_gs_title_date': None,
            'first_gs_title_age': None,
            'first_gs_title_year': None,
            'matches_before_first_gs': 0,
            'wins_before_first_gs': 0,
            'win_pct_before_first_gs': 0.0,
            'years_to_first_gs': 0,
            
            # Rankings
            'peak_ranking': None,
            'peak_ranking_date': None,
            'peak_ranking_before_first_gs': None,
            
            # Surface breakdown
            'hard_matches': 0,
            'hard_wins': 0,
            'hard_win_pct': 0.0,
            'clay_matches': 0,
            'clay_wins': 0,
            'clay_win_pct': 0.0,
            'grass_matches': 0,
            'grass_wins': 0,
            'grass_win_pct': 0.0,
            'carpet_matches': 0,
            'carpet_wins': 0,
            'carpet_win_pct': 0.0,
            
            # Opponent quality
            'top5_matches': 0,
            'top5_wins': 0,
            'top5_win_pct': 0.0,
            'top10_matches': 0,
            'top10_wins': 0,
            'top10_win_pct': 0.0,
            'top30_matches': 0,
            'top30_wins': 0,
            'top30_win_pct': 0.0,
            'avg_opponent_rank': None,
            
            # Match quality
            'unique_opponents': 0,
            'avg_match_duration': None,
            'total_match_minutes': 0,
            'matches_with_duration': 0,
            
            # Career category
            'has_gs_title': False,
            'was_top_5': False,
            'was_top_10': False
        }
    
    print(f"✓ Initialized {len(all_players):,} unique players")
    
    # First pass: Process all matches for basic stats
    print("Processing matches (pass 1/2)...")
    
    for idx, row in df.iterrows():
        if idx % 10000 == 0 and idx > 0:
            print(f"  Processed {idx:,} matches...")
        
        winner = row['winner_name']
        loser = row['loser_name']
        
        if pd.isna(winner) or pd.isna(loser):
            continue
        
        tourney_date = row['tourney_date']
        surface = row.get('surface', 'Unknown')
        winner_rank = row.get('winner_rank', 999)
        loser_rank = row.get('loser_rank', 999)
        is_gs = is_grand_slam(row['tourney_name'])
        round_code = row.get('round', '')
        
        # Update winner stats
        w = player_stats[winner]
        
        # Career span
        if w['first_match_date'] is None or tourney_date < w['first_match_date']:
            w['first_match_date'] = tourney_date
        if w['last_match_date'] is None or tourney_date > w['last_match_date']:
            w['last_match_date'] = tourney_date
        
        # Match counts
        w['total_matches'] += 1
        w['total_wins'] += 1
        
        # Country
        if w['country'] is None and pd.notna(row.get('winner_ioc')):
            w['country'] = row['winner_ioc']
        
        # Surface
        if surface == 'Hard':
            w['hard_matches'] += 1
            w['hard_wins'] += 1
        elif surface == 'Clay':
            w['clay_matches'] += 1
            w['clay_wins'] += 1
        elif surface == 'Grass':
            w['grass_matches'] += 1
            w['grass_wins'] += 1
        elif surface == 'Carpet':
            w['carpet_matches'] += 1
            w['carpet_wins'] += 1
        
        # Grand Slam stats
        if is_gs:
            w['gs_matches'] += 1
            w['gs_wins'] += 1
            
            if round_code == 'F':
                w['gs_titles'] += 1
                w['gs_finals'] += 1
                w['has_gs_title'] = True
                
                # Track first GS title
                if w['first_gs_title_date'] is None:
                    w['first_gs_title_date'] = tourney_date
                    w['first_gs_title_age'] = row.get('winner_age', None)
            elif round_code == 'F':
                w['gs_finals'] += 1
            elif round_code == 'SF':
                w['gs_semifinals'] += 1
            elif round_code == 'QF':
                w['gs_quarterfinals'] += 1
        
        # Opponent quality (winner beat loser)
        if pd.notna(loser_rank) and loser_rank < 999:
            if loser_rank <= 5:
                w['top5_matches'] += 1
                w['top5_wins'] += 1
            if loser_rank <= 10:
                w['top10_matches'] += 1
                w['top10_wins'] += 1
            if loser_rank <= 30:
                w['top30_matches'] += 1
                w['top30_wins'] += 1
        
        # Winner ranking tracking
        if pd.notna(winner_rank) and winner_rank < 999:
            if winner_rank <= 5:
                w['was_top_5'] = True
                w['was_top_10'] = True
            elif winner_rank <= 10:
                w['was_top_10'] = True
        
        # Duration
        if pd.notna(row.get('minutes')):
            w['total_match_minutes'] += row['minutes']
            w['matches_with_duration'] += 1
        
        # Update loser stats
        l = player_stats[loser]
        
        # Career span
        if l['first_match_date'] is None or tourney_date < l['first_match_date']:
            l['first_match_date'] = tourney_date
        if l['last_match_date'] is None or tourney_date > l['last_match_date']:
            l['last_match_date'] = tourney_date
        
        # Match counts
        l['total_matches'] += 1
        l['total_losses'] += 1
        
        # Country
        if l['country'] is None and pd.notna(row.get('loser_ioc')):
            l['country'] = row['loser_ioc']
        
        # Surface
        if surface == 'Hard':
            l['hard_matches'] += 1
        elif surface == 'Clay':
            l['clay_matches'] += 1
        elif surface == 'Grass':
            l['grass_matches'] += 1
        elif surface == 'Carpet':
            l['carpet_matches'] += 1
        
        # Grand Slam stats (loser in final still counts as finalist)
        if is_gs:
            l['gs_matches'] += 1
            l['gs_losses'] += 1
            
            if round_code == 'F':
                l['gs_finals'] += 1
            elif round_code == 'SF':
                l['gs_semifinals'] += 1
            elif round_code == 'QF':
                l['gs_quarterfinals'] += 1
        
        # Opponent quality (loser played against winner)
        if pd.notna(winner_rank) and winner_rank < 999:
            if winner_rank <= 5:
                l['top5_matches'] += 1
            if winner_rank <= 10:
                l['top10_matches'] += 1
            if winner_rank <= 30:
                l['top30_matches'] += 1
        
        # Loser ranking tracking
        if pd.notna(loser_rank) and loser_rank < 999:
            if loser_rank <= 5:
                l['was_top_5'] = True
                l['was_top_10'] = True
            elif loser_rank <= 10:
                l['was_top_10'] = True
    
    print(f"✓ Pass 1 complete: Basic stats calculated")
    
    # Second pass: Calculate metrics before first GS title
    print("Processing breakthrough metrics (pass 2/2)...")
    
    champions = {name: stats for name, stats in player_stats.items() if stats['has_gs_title']}
    print(f"  Found {len(champions)} Grand Slam champions")
    
    for player_name, stats in champions.items():
        first_gs_date = stats['first_gs_title_date']
        if first_gs_date is None:
            continue
        
        # Count matches before first GS
        before_gs = df[
            ((df['winner_name'] == player_name) | (df['loser_name'] == player_name)) &
            (df['tourney_date'] < first_gs_date)
        ]
        
        wins_before = len(before_gs[before_gs['winner_name'] == player_name])
        total_before = len(before_gs)
        
        stats['matches_before_first_gs'] = total_before
        stats['wins_before_first_gs'] = wins_before
        stats['win_pct_before_first_gs'] = calculate_win_percentage(wins_before, total_before)
    
    print(f"✓ Pass 2 complete: Breakthrough metrics calculated")
    
    # Calculate derived metrics and build DataFrame
    print("Calculating derived metrics...")
    
    records = []
    for player_name, stats in player_stats.items():
        # Career span
        if stats['first_match_date']:
            stats['career_start_year'] = int(str(stats['first_match_date'])[:4])
        if stats['last_match_date']:
            stats['career_end_year'] = int(str(stats['last_match_date'])[:4])
        if stats['career_start_year'] and stats['career_end_year']:
            stats['career_span_years'] = stats['career_end_year'] - stats['career_start_year']
        
        # First GS title year
        if stats['first_gs_title_date']:
            stats['first_gs_title_year'] = int(str(stats['first_gs_title_date'])[:4])
            if stats['career_start_year']:
                stats['years_to_first_gs'] = stats['first_gs_title_year'] - stats['career_start_year']
        
        # Win percentages
        stats['win_pct'] = calculate_win_percentage(stats['total_wins'], stats['total_matches'])
        stats['gs_win_pct'] = calculate_win_percentage(stats['gs_wins'], stats['gs_matches'])
        
        # Surface win percentages
        stats['hard_win_pct'] = calculate_win_percentage(stats['hard_wins'], stats['hard_matches'])
        stats['clay_win_pct'] = calculate_win_percentage(stats['clay_wins'], stats['clay_matches'])
        stats['grass_win_pct'] = calculate_win_percentage(stats['grass_wins'], stats['grass_matches'])
        stats['carpet_win_pct'] = calculate_win_percentage(stats['carpet_wins'], stats['carpet_matches'])
        
        # Opponent quality win percentages
        stats['top5_win_pct'] = calculate_win_percentage(stats['top5_wins'], stats['top5_matches'])
        stats['top10_win_pct'] = calculate_win_percentage(stats['top10_wins'], stats['top10_matches'])
        stats['top30_win_pct'] = calculate_win_percentage(stats['top30_wins'], stats['top30_matches'])
        
        # Average match duration
        if stats['matches_with_duration'] > 0:
            stats['avg_match_duration'] = round(stats['total_match_minutes'] / stats['matches_with_duration'], 1)
        
        # Unique opponents
        player_matches = df[(df['winner_name'] == player_name) | (df['loser_name'] == player_name)]
        opponents = set()
        opponents.update(player_matches[player_matches['winner_name'] == player_name]['loser_name'].dropna())
        opponents.update(player_matches[player_matches['loser_name'] == player_name]['winner_name'].dropna())
        stats['unique_opponents'] = len(opponents)
        
        # Peak ranking
        peak = get_player_peak_ranking(df, player_name)
        if peak:
            stats['peak_ranking'] = int(peak)
        
        # Peak ranking before first GS
        if stats['first_gs_title_date']:
            df_before_gs = df[df['tourney_date'] < stats['first_gs_title_date']]
            peak_before = get_player_peak_ranking(df_before_gs, player_name)
            if peak_before:
                stats['peak_ranking_before_first_gs'] = int(peak_before)
        
        records.append(stats)
    
    player_metrics_df = pd.DataFrame(records)
    
    print(f"✓ Built player metrics table: {len(player_metrics_df):,} players")
    print(f"  Grand Slam champions: {player_metrics_df['has_gs_title'].sum()}")
    print(f"  Players with 200+ matches: {(player_metrics_df['total_matches'] >= 200).sum()}")
    
    return player_metrics_df


# =============================================================================
# MATCH ENRICHMENT
# =============================================================================

def enrich_match_data(df, player_metrics_df):
    """
    Enrich match data with parsed scores, player career context, and derived metrics
    
    Returns:
        pd.DataFrame: Original match data plus enriched columns
    """
    print("\n" + "="*60)
    print("ENRICHING MATCH DATA")
    print("="*60)
    
    df_enriched = df.copy()
    
    # Parse scores
    print("Parsing match scores...")
    score_parsed = df_enriched['score'].apply(parse_score)
    
    df_enriched['winner_sets'] = score_parsed.apply(lambda x: x['winner_sets'])
    df_enriched['loser_sets'] = score_parsed.apply(lambda x: x['loser_sets'])
    df_enriched['winner_games'] = score_parsed.apply(lambda x: x['winner_games'])
    df_enriched['loser_games'] = score_parsed.apply(lambda x: x['loser_games'])
    df_enriched['tiebreaks_count'] = score_parsed.apply(lambda x: len(x['tiebreaks']))
    df_enriched['is_complete'] = score_parsed.apply(lambda x: x['is_complete'])
    
    # NBI-specific score parsing
    print("Computing drama metrics...")
    sets_parsed = df_enriched['score'].apply(parse_sets)
    df_enriched['set_margins'] = sets_parsed.apply(lambda x: x[0])
    df_enriched['avg_set_margin'] = df_enriched['set_margins'].apply(lambda x: np.mean(x) if x else np.nan)
    df_enriched['lead_changes'] = sets_parsed.apply(lambda x: x[2])
    df_enriched['comeback_score'] = df_enriched['score'].apply(advanced_comeback_score)
    df_enriched['final_set_tiebreak'] = df_enriched['score'].apply(final_set_tiebreak)
    
    # Grand Slam identification
    print("Identifying Grand Slams...")
    df_enriched['is_grand_slam'] = df_enriched['tourney_name'].apply(is_grand_slam)
    df_enriched['grand_slam_name'] = df_enriched['tourney_name'].apply(get_grand_slam_name)
    
    # Year extraction
    df_enriched['year'] = df_enriched['tourney_date'].astype(str).str[:4].astype(int)
    
    # Round categorization
    df_enriched['is_final'] = df_enriched['round'] == 'F'
    df_enriched['is_semifinal'] = df_enriched['round'] == 'SF'
    df_enriched['is_quarterfinal'] = df_enriched['round'] == 'QF'
    
    # Merge with player career metrics for context
    print("Adding player career context...")
    
    # Winner context
    winner_context = player_metrics_df[['player_name', 'total_matches', 'gs_titles', 'has_gs_title', 'peak_ranking']].copy()
    winner_context = winner_context.rename(columns={
        'player_name': 'winner_name',
        'total_matches': 'winner_career_matches',
        'gs_titles': 'winner_gs_titles',
        'has_gs_title': 'winner_has_gs_title',
        'peak_ranking': 'winner_peak_ranking'
    })
    
    df_enriched = df_enriched.merge(winner_context, on='winner_name', how='left')
    
    # Loser context
    loser_context = player_metrics_df[['player_name', 'total_matches', 'gs_titles', 'has_gs_title', 'peak_ranking']].copy()
    loser_context = loser_context.rename(columns={
        'player_name': 'loser_name',
        'total_matches': 'loser_career_matches',
        'gs_titles': 'loser_gs_titles',
        'has_gs_title': 'loser_has_gs_title',
        'peak_ranking': 'loser_peak_ranking'
    })
    
    df_enriched = df_enriched.merge(loser_context, on='loser_name', how='left')
    
    print(f"✓ Enriched {len(df_enriched):,} matches with {len(df_enriched.columns)} total columns")
    
    return df_enriched


# =============================================================================
# HEAD-TO-HEAD MATRIX
# =============================================================================

def build_head_to_head_matrix(df):
    """
    Build head-to-head records for all player matchups
    
    Returns:
        pd.DataFrame: H2H records as DataFrame (for Parquet storage)
    """
    print("\n" + "="*60)
    print("BUILDING HEAD-TO-HEAD MATRIX")
    print("="*60)
    
    h2h = {}
    
    for _, row in df.iterrows():
        winner = row['winner_name']
        loser = row['loser_name']
        
        if pd.isna(winner) or pd.isna(loser):
            continue
        
        # Use sorted tuple as key for undirected matchup
        key = tuple(sorted([winner, loser]))
        player1, player2 = key
        
        surface = row.get('surface', 'Unknown')
        
        # Initialize if not exists
        if key not in h2h:
            h2h[key] = {
                'player1': player1,
                'player2': player2,
                'total_matches': 0,
                'player1_wins': 0,
                'player2_wins': 0,
                'hard_total': 0, 'hard_p1_wins': 0, 'hard_p2_wins': 0,
                'clay_total': 0, 'clay_p1_wins': 0, 'clay_p2_wins': 0,
                'grass_total': 0, 'grass_p1_wins': 0, 'grass_p2_wins': 0,
                'carpet_total': 0, 'carpet_p1_wins': 0, 'carpet_p2_wins': 0,
            }
        
        # Update totals
        h2h[key]['total_matches'] += 1
        
        # Surface mapping
        surface_key = surface.lower() if surface in ['Hard', 'Clay', 'Grass', 'Carpet'] else None
        
        # Track who won
        if winner == player1:
            h2h[key]['player1_wins'] += 1
            if surface_key:
                h2h[key][f'{surface_key}_total'] += 1
                h2h[key][f'{surface_key}_p1_wins'] += 1
        else:
            h2h[key]['player2_wins'] += 1
            if surface_key:
                h2h[key][f'{surface_key}_total'] += 1
                h2h[key][f'{surface_key}_p2_wins'] += 1
    
    # Convert to DataFrame for Parquet storage
    h2h_df = pd.DataFrame(list(h2h.values()))
    
    print(f"✓ Built H2H matrix: {len(h2h_df):,} unique matchups")
    
    return h2h_df


# =============================================================================
# MAIN AGGREGATION FUNCTION
# =============================================================================

def generate_base_metrics(base_data_path="data/base/atp_matches_raw.parquet",
                          output_dir="data/base"):
    """
    Main function to generate all base metrics tables
    All outputs saved as Parquet for compact storage and fast loading.
    """
    print("="*60)
    print("GENERATING BASE METRICS TABLES")
    print("="*60)
    
    # Load raw data
    print("\nLoading base data...")
    df = pd.read_parquet(base_data_path)
    print(f"✓ Loaded {len(df):,} matches from {df['tourney_date'].min()} to {df['tourney_date'].max()}")
    
    # Build player metrics
    player_metrics_df = build_player_career_metrics(df)
    
    # Enrich match data
    df_enriched = enrich_match_data(df, player_metrics_df)
    
    # Build head-to-head matrix (now returns DataFrame)
    h2h_df = build_head_to_head_matrix(df)
    
    # Save outputs
    print("\n" + "="*60)
    print("SAVING BASE METRICS (Parquet format)")
    print("="*60)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Save player metrics as Parquet
    player_metrics_path = f"{output_dir}/player_metrics.parquet"
    player_metrics_df.to_parquet(player_metrics_path, compression='zstd', index=False)
    size_mb = os.path.getsize(player_metrics_path) / 1024 / 1024
    print(f"✓ Saved: {player_metrics_path} ({len(player_metrics_df):,} players, {size_mb:.1f} MB)")
    
    # Save enriched matches as Parquet
    # Note: Need to handle list columns (set_margins) - convert to string for Parquet compatibility
    df_enriched_save = df_enriched.copy()
    if 'set_margins' in df_enriched_save.columns:
        df_enriched_save['set_margins'] = df_enriched_save['set_margins'].apply(
            lambda x: json.dumps(x) if isinstance(x, list) else str(x)
        )
    
    enriched_path = f"{output_dir}/matches_enriched.parquet"
    df_enriched_save.to_parquet(enriched_path, compression='zstd', index=False)
    size_mb = os.path.getsize(enriched_path) / 1024 / 1024
    print(f"✓ Saved: {enriched_path} ({len(df_enriched):,} matches, {size_mb:.1f} MB)")
    
    # Save head-to-head as Parquet
    h2h_path = f"{output_dir}/head_to_head.parquet"
    h2h_df.to_parquet(h2h_path, compression='zstd', index=False)
    size_mb = os.path.getsize(h2h_path) / 1024 / 1024
    print(f"✓ Saved: {h2h_path} ({len(h2h_df):,} matchups, {size_mb:.1f} MB)")
    
    # Print summary statistics
    print("\n" + "="*60)
    print("BASE METRICS SUMMARY")
    print("="*60)
    print(f"\n📊 Player Metrics:")
    print(f"   Total players: {len(player_metrics_df):,}")
    print(f"   Grand Slam champions: {player_metrics_df['has_gs_title'].sum()}")
    print(f"   Players with 200+ matches: {(player_metrics_df['total_matches'] >= 200).sum()}")
    print(f"   Players who reached Top 5: {player_metrics_df['was_top_5'].sum()}")
    
    print(f"\n📊 Match Data:")
    print(f"   Total matches: {len(df_enriched):,}")
    print(f"   Grand Slam matches: {df_enriched['is_grand_slam'].sum():,}")
    print(f"   Complete matches: {df_enriched['is_complete'].sum():,}")
    
    print(f"\n📊 Head-to-Head:")
    print(f"   Unique matchups: {len(h2h_df):,}")
    
    print("\n" + "="*60)
    print("✅ BASE METRICS GENERATION COMPLETE")
    print("="*60)
    
    return player_metrics_df, df_enriched, h2h_df


if __name__ == "__main__":
    generate_base_metrics()
