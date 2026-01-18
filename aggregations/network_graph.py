#!/usr/bin/env python3
"""
Network Graph Data Aggregator
Creates network graph data showing player-to-player matchups and statistics
Now uses pre-aggregated player metrics and enriched match data
"""

import pandas as pd
import numpy as np
import json
import os
from collections import defaultdict


# =============================================================================
# CONSTANTS
# =============================================================================

GRAND_SLAMS = ['Australian Open', 'Roland Garros', 'Wimbledon', 'US Open']


def calculate_win_percentage(wins, total):
    """Calculate win percentage safely"""
    if total == 0:
        return 0.0
    return round(wins / total * 100, 2)


def categorize_win_percentage(win_pct):
    """Categorize win percentage into buckets"""
    if win_pct > 70:
        return 'Above 70%'
    elif win_pct > 60:
        return '61% - 70%'
    elif win_pct > 50:
        return '51% - 60%'
    elif win_pct > 40:
        return '41% - 50%'
    else:
        return '40% or below'


# =============================================================================
# NETWORK GRAPH BUILDER (USING BASE METRICS)
# =============================================================================

def build_network_data(df_enriched, player_metrics_df, year_filter=None, tourney_filter=None, round_filter=None):
    """
    Build network graph data from enriched match data and player metrics
    
    Args:
        df_enriched: DataFrame with enriched match data
        player_metrics_df: DataFrame with player career metrics
        year_filter: Filter by year (e.g., >= 2000)
        tourney_filter: List of tournament names to include
        round_filter: List of rounds to include (e.g., ['F', 'SF'])
    
    Returns:
        dict: Network data with nodes and edges
    """
    # Apply filters
    filtered_df = df_enriched.copy()
    
    if year_filter is not None:
        if isinstance(year_filter, dict):
            if 'min' in year_filter:
                filtered_df = filtered_df[filtered_df['year'] >= year_filter['min']]
            if 'max' in year_filter:
                filtered_df = filtered_df[filtered_df['year'] <= year_filter['max']]
        else:
            filtered_df = filtered_df[filtered_df['year'] >= year_filter]
    
    if tourney_filter:
        filtered_df = filtered_df[filtered_df['tourney_name'].isin(tourney_filter)]
    
    if round_filter:
        filtered_df = filtered_df[filtered_df['round'].isin(round_filter)]
    
    print(f"  Building graph from {len(filtered_df):,} matches...")
    
    # Get player metrics for the players in filtered matches
    players_in_matches = set(filtered_df['winner_name'].unique()) | set(filtered_df['loser_name'].unique())
    player_metrics_lookup = player_metrics_df[player_metrics_df['player_name'].isin(players_in_matches)].set_index('player_name')
    
    # Initialize nodes and edges storage
    nodes = {}
    edges = defaultdict(lambda: {
        'matches': 0,
        'surface_matches': defaultdict(int),
        'tourney_matches': defaultdict(int),
        'winner_wins_by_surface': defaultdict(int),
        'loser_wins_by_surface': defaultdict(int),
        'winner_wins_by_tourney': defaultdict(int),
        'loser_wins_by_tourney': defaultdict(int)
    })
    
    # Process each match
    for _, row in filtered_df.iterrows():
        winner = row['winner_name']
        loser = row['loser_name']
        surface = str(row.get('surface', 'Unknown'))
        tourney = str(row.get('tourney_name', 'Unknown'))
        winner_country = row.get('winner_ioc', 'UNK')
        loser_country = row.get('loser_ioc', 'UNK')
        winner_rank = row.get('winner_rank', 999)
        loser_rank = row.get('loser_rank', 999)
        
        # Initialize nodes if not exist - pull from pre-aggregated metrics
        if winner not in nodes:
            if winner in player_metrics_lookup.index:
                pm = player_metrics_lookup.loc[winner]
                nodes[winner] = {
                    'name': winner,
                    'country': pm['country'] if pd.notna(pm['country']) else winner_country,
                    'matches_won': 0,  # Will count in filtered set
                    'matches_played': 0,  # Will count in filtered set
                    'career_total_matches': int(pm['total_matches']),
                    'career_win_pct': pm['win_pct'],
                    'gs_titles': int(pm['gs_titles']),
                    'peak_ranking': int(pm['peak_ranking']) if pd.notna(pm['peak_ranking']) else None,
                    'surface_wins': defaultdict(int),
                    'surface_matches': defaultdict(int),
                    'tourney_wins': defaultdict(int),
                    'tourney_matches': defaultdict(int),
                    'top_5_wins': 0,
                    'top_5_matches': 0,
                    'was_top_5': bool(pm['was_top_5']),
                    'opponents': set()
                }
            else:
                # Fallback if not in metrics (shouldn't happen)
                nodes[winner] = {
                    'name': winner,
                    'country': winner_country,
                    'matches_won': 0,
                    'matches_played': 0,
                    'career_total_matches': 0,
                    'career_win_pct': 0,
                    'gs_titles': 0,
                    'peak_ranking': None,
                    'surface_wins': defaultdict(int),
                    'surface_matches': defaultdict(int),
                    'tourney_wins': defaultdict(int),
                    'tourney_matches': defaultdict(int),
                    'top_5_wins': 0,
                    'top_5_matches': 0,
                    'was_top_5': False,
                    'opponents': set()
                }
        
        if loser not in nodes:
            if loser in player_metrics_lookup.index:
                pm = player_metrics_lookup.loc[loser]
                nodes[loser] = {
                    'name': loser,
                    'country': pm['country'] if pd.notna(pm['country']) else loser_country,
                    'matches_won': 0,
                    'matches_played': 0,
                    'career_total_matches': int(pm['total_matches']),
                    'career_win_pct': pm['win_pct'],
                    'gs_titles': int(pm['gs_titles']),
                    'peak_ranking': int(pm['peak_ranking']) if pd.notna(pm['peak_ranking']) else None,
                    'surface_wins': defaultdict(int),
                    'surface_matches': defaultdict(int),
                    'tourney_wins': defaultdict(int),
                    'tourney_matches': defaultdict(int),
                    'top_5_wins': 0,
                    'top_5_matches': 0,
                    'was_top_5': bool(pm['was_top_5']),
                    'opponents': set()
                }
            else:
                nodes[loser] = {
                    'name': loser,
                    'country': loser_country,
                    'matches_won': 0,
                    'matches_played': 0,
                    'career_total_matches': 0,
                    'career_win_pct': 0,
                    'gs_titles': 0,
                    'peak_ranking': None,
                    'surface_wins': defaultdict(int),
                    'surface_matches': defaultdict(int),
                    'tourney_wins': defaultdict(int),
                    'tourney_matches': defaultdict(int),
                    'top_5_wins': 0,
                    'top_5_matches': 0,
                    'was_top_5': False,
                    'opponents': set()
                }
        
        # Update winner node stats (for filtered dataset)
        nodes[winner]['matches_won'] += 1
        nodes[winner]['matches_played'] += 1
        nodes[winner]['surface_wins'][surface] += 1
        nodes[winner]['surface_matches'][surface] += 1
        nodes[winner]['tourney_wins'][tourney] += 1
        nodes[winner]['tourney_matches'][tourney] += 1
        nodes[winner]['opponents'].add(loser)
        
        if loser_rank <= 5:
            nodes[winner]['top_5_wins'] += 1
            nodes[winner]['top_5_matches'] += 1
        
        # Update loser node stats (for filtered dataset)
        nodes[loser]['matches_played'] += 1
        nodes[loser]['surface_matches'][surface] += 1
        nodes[loser]['tourney_matches'][tourney] += 1
        nodes[loser]['opponents'].add(winner)
        
        if winner_rank <= 5:
            nodes[loser]['top_5_matches'] += 1
        
        # Update edge (undirected - use sorted tuple as key)
        edge_key = tuple(sorted([winner, loser]))
        edge = edges[edge_key]
        edge['matches'] += 1
        edge['surface_matches'][surface] += 1
        edge['tourney_matches'][tourney] += 1
        
        # Track who won on which surface/tourney
        if edge_key[0] == winner:
            edge['winner_wins_by_surface'][surface] += 1
            edge['winner_wins_by_tourney'][tourney] += 1
        else:
            edge['loser_wins_by_surface'][surface] += 1
            edge['loser_wins_by_tourney'][tourney] += 1
    
    # Calculate derived stats for nodes
    node_list = []
    for name, data in nodes.items():
        win_pct = calculate_win_percentage(data['matches_won'], data['matches_played'])
        top_5_win_pct = calculate_win_percentage(data['top_5_wins'], data['top_5_matches'])
        
        # Win percentage category
        win_pct_category = categorize_win_percentage(win_pct)
        
        # Surface-specific win percentages
        surface_win_pcts = {}
        for surface, wins in data['surface_wins'].items():
            matches = data['surface_matches'][surface]
            surface_win_pcts[surface] = calculate_win_percentage(wins, matches)
        
        # Tournament-specific win percentages
        tourney_win_pcts = {}
        for tourney, wins in data['tourney_wins'].items():
            matches = data['tourney_matches'][tourney]
            tourney_win_pcts[tourney] = calculate_win_percentage(wins, matches)
        
        node_list.append({
            'name': name,
            'country': data['country'],
            'matches_won': data['matches_won'],
            'matches_played': data['matches_played'],
            'win_pct': win_pct,
            'win_pct_category': win_pct_category,
            'career_total_matches': data['career_total_matches'],
            'career_win_pct': data['career_win_pct'],
            'gs_titles': data['gs_titles'],
            'peak_ranking': data['peak_ranking'],
            'top_5_wins': data['top_5_wins'],
            'top_5_matches': data['top_5_matches'],
            'top_5_win_pct': top_5_win_pct,
            'was_top_5': data['was_top_5'],
            'unique_opponents': len(data['opponents']),
            'surface_wins': dict(data['surface_wins']),
            'surface_matches': dict(data['surface_matches']),
            'surface_win_pcts': surface_win_pcts,
            'tourney_wins': dict(data['tourney_wins']),
            'tourney_matches': dict(data['tourney_matches']),
            'tourney_win_pcts': tourney_win_pcts
        })
    
    # Convert edges to list format
    edge_list = []
    for (player1, player2), data in edges.items():
        # Calculate head-to-head
        p1_wins = sum(data['winner_wins_by_surface'].values()) if player1 < player2 else sum(data['loser_wins_by_surface'].values())
        p2_wins = data['matches'] - p1_wins
        
        edge_list.append({
            'player1': player1,
            'player2': player2,
            'total_matches': data['matches'],
            'player1_wins': p1_wins,
            'player2_wins': p2_wins,
            'surface_breakdown': dict(data['surface_matches']),
            'tourney_breakdown': dict(data['tourney_matches']),
            'surface_wins': {
                player1: dict(data['winner_wins_by_surface']) if player1 < player2 else dict(data['loser_wins_by_surface']),
                player2: dict(data['loser_wins_by_surface']) if player1 < player2 else dict(data['winner_wins_by_surface'])
            }
        })
    
    print(f"  ✓ Built graph with {len(node_list)} nodes and {len(edge_list)} edges")
    
    return {
        'nodes': node_list,
        'edges': edge_list,
        'metadata': {
            'total_matches': len(filtered_df),
            'total_players': len(node_list),
            'total_matchups': len(edge_list),
            'year_range': {
                'min': int(filtered_df['year'].min()),
                'max': int(filtered_df['year'].max())
            }
        }
    }


# =============================================================================
# GENERATE SPECIFIC NETWORK DATASETS
# =============================================================================

def generate_network_datasets(df_enriched, player_metrics_df, output_dir="data/network"):
    """Generate multiple network graph datasets"""
    print("\n" + "="*60)
    print("GENERATING NETWORK GRAPH DATASETS")
    print("="*60)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Grand Slam Finals since 2003
    print("\n1. Grand Slam Finals (2003-present)")
    gs_finals_2003 = build_network_data(
        df_enriched,
        player_metrics_df,
        year_filter={'min': 2003},
        tourney_filter=GRAND_SLAMS,
        round_filter=['F']
    )
    
    with open(f"{output_dir}/grand_slam_finals_2003.json", 'w') as f:
        json.dump(gs_finals_2003, f, indent=2)
    print(f"  ✓ Saved: grand_slam_finals_2003.json")
    
    # 2. Individual Grand Slam Finals since 1982
    print("\n2. Individual Grand Slam Finals (1982-present)")
    for slam in GRAND_SLAMS:
        slam_key = slam.lower().replace(' ', '_')
        print(f"\n  Processing {slam}...")
        slam_data = build_network_data(
            df_enriched,
            player_metrics_df,
            year_filter={'min': 1982},
            tourney_filter=[slam],
            round_filter=['F']
        )
        
        with open(f"{output_dir}/{slam_key}_finals_1982.json", 'w') as f:
            json.dump(slam_data, f, indent=2)
        print(f"  ✓ Saved: {slam_key}_finals_1982.json")
    
    # 3. All matches for players with 200+ career matches (2000-present)
    print("\n3. High-Volume Players Network (200+ matches since 2000)")
    
    # Use player_metrics to find high-volume players (much faster!)
    high_volume_players = player_metrics_df[player_metrics_df['total_matches'] >= 200]['player_name'].tolist()
    print(f"  Found {len(high_volume_players)} players with 200+ career matches")
    
    # Filter to matches from 2000+ involving these players
    high_volume_df = df_enriched[
        (df_enriched['year'] >= 2000) &
        ((df_enriched['winner_name'].isin(high_volume_players)) | 
         (df_enriched['loser_name'].isin(high_volume_players)))
    ]
    
    high_volume_network = build_network_data(high_volume_df, player_metrics_df)
    
    with open(f"{output_dir}/high_volume_players_2000.json", 'w') as f:
        json.dump(high_volume_network, f, indent=2)
    print(f"  ✓ Saved: high_volume_players_2000.json")
    
    # 4. Summary statistics
    summary = {
        'grand_slam_finals_2003': {
            'players': gs_finals_2003['metadata']['total_players'],
            'matches': gs_finals_2003['metadata']['total_matches'],
            'matchups': gs_finals_2003['metadata']['total_matchups']
        },
        'individual_slams_1982': {
            slam.lower().replace(' ', '_'): {
                'file': f"{slam.lower().replace(' ', '_')}_finals_1982.json"
            } for slam in GRAND_SLAMS
        },
        'high_volume_players_2000': {
            'players': high_volume_network['metadata']['total_players'],
            'matches': high_volume_network['metadata']['total_matches'],
            'matchups': high_volume_network['metadata']['total_matchups'],
            'min_matches_threshold': 200
        }
    }
    
    with open(f"{output_dir}/network_summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\n" + "="*60)
    print("✅ NETWORK GRAPH AGGREGATION COMPLETE")
    print("="*60)
    print(f"\nGenerated Files:")
    print(f"  - grand_slam_finals_2003.json")
    for slam in GRAND_SLAMS:
        print(f"  - {slam.lower().replace(' ', '_')}_finals_1982.json")
    print(f"  - high_volume_players_2000.json")
    print(f"  - network_summary.json")


def generate_network_aggregation(matches_enriched_path="data/base/matches_enriched.parquet",
                                  player_metrics_path="data/base/player_metrics.parquet",
                                  output_dir="data/network"):
    """
    Generate network graph data from enriched matches and player metrics
    """
    print("\n" + "="*60)
    print("GENERATING NETWORK GRAPH DATA")
    print("="*60)
    
    # Load enriched matches (now Parquet format)
    print("\nLoading enriched matches...")
    if matches_enriched_path.endswith('.parquet'):
        df_enriched = pd.read_parquet(matches_enriched_path)
    else:
        df_enriched = pd.read_pickle(matches_enriched_path)
    
    print(f"✓ Loaded {len(df_enriched):,} matches")
    
    # Load player metrics (now Parquet format)
    print("Loading player metrics...")
    if player_metrics_path.endswith('.parquet'):
        player_metrics_df = pd.read_parquet(player_metrics_path)
    else:
        player_metrics_df = pd.read_pickle(player_metrics_path)
    
    print(f"✓ Loaded metrics for {len(player_metrics_df):,} players")
    
    generate_network_datasets(df_enriched, player_metrics_df, output_dir)


if __name__ == "__main__":
    generate_network_aggregation()
