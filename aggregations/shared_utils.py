#!/usr/bin/env python3
"""
Shared Utilities for Tennis Data Aggregations
Common functions used across multiple aggregation modules
"""

import pandas as pd
import numpy as np
import re


# =============================================================================
# GRAND SLAM IDENTIFICATION
# =============================================================================

GRAND_SLAMS = ['Australian Open', 'Roland Garros', 'Wimbledon', 'US Open']


def is_grand_slam(tourney_name):
    """
    Check if tournament is a Grand Slam (flexible matching)
    
    Args:
        tourney_name: Tournament name string
    
    Returns:
        bool: True if Grand Slam
    """
    if pd.isna(tourney_name):
        return False
    tourney_name = str(tourney_name)
    return (
        'Australian Open' in tourney_name or
        'Roland Garros' in tourney_name or
        tourney_name == 'Wimbledon' or
        'US Open' in tourney_name
    )


def get_grand_slam_name(tourney_name):
    """
    Normalize Grand Slam tournament name
    
    Args:
        tourney_name: Tournament name string
    
    Returns:
        str: Normalized GS name or original name
    """
    if pd.isna(tourney_name):
        return None
    tourney_name = str(tourney_name)
    
    if 'Australian Open' in tourney_name:
        return 'Australian Open'
    elif 'Roland Garros' in tourney_name:
        return 'Roland Garros'
    elif tourney_name == 'Wimbledon':
        return 'Wimbledon'
    elif 'US Open' in tourney_name:
        return 'US Open'
    
    return tourney_name


# =============================================================================
# SCORE PARSING
# =============================================================================

def parse_score(score_str):
    """
    Parse tennis score to extract sets won/lost and games won/lost
    
    Args:
        score_str: Score string like "6-4 3-6 7-6(3) 6-4"
    
    Returns:
        dict: {
            'winner_sets': int,
            'loser_sets': int,
            'winner_games': int,
            'loser_games': int,
            'set_scores': list of (winner, loser) tuples,
            'tiebreaks': list of tiebreak scores
        }
    """
    if pd.isna(score_str) or not isinstance(score_str, str):
        return {
            'winner_sets': 0,
            'loser_sets': 0,
            'winner_games': 0,
            'loser_games': 0,
            'set_scores': [],
            'tiebreaks': [],
            'is_complete': False
        }
    
    # Handle retirements, walkovers, defaults
    is_complete = not any(x in score_str.upper() for x in ['RET', 'W/O', 'DEF', 'ABD'])
    
    winner_sets = 0
    loser_sets = 0
    winner_games = 0
    loser_games = 0
    set_scores = []
    tiebreaks = []
    
    # Extract set scores like "6-4", "7-6(3)", "6-7(5)"
    set_pattern = r'(\d+)-(\d+)(?:\((\d+)\))?'
    matches = re.findall(set_pattern, score_str)
    
    for match in matches:
        w = int(match[0])
        l = int(match[1])
        tb = match[2] if len(match) > 2 and match[2] else None
        
        winner_games += w
        loser_games += l
        set_scores.append((w, l))
        
        if tb:
            tiebreaks.append(int(tb))
        
        # Determine set winner
        if w > l:
            winner_sets += 1
        else:
            loser_sets += 1
    
    return {
        'winner_sets': winner_sets,
        'loser_sets': loser_sets,
        'winner_games': winner_games,
        'loser_games': loser_games,
        'set_scores': set_scores,
        'tiebreaks': tiebreaks,
        'is_complete': is_complete
    }


def parse_sets(score_str):
    """
    Parse set scores from the 'score' string (for NBI)
    
    Returns:
        tuple: (set_margins, tiebreak_count, lead_changes)
    """
    if pd.isna(score_str):
        return [], 0, 0
    
    score_str = score_str.replace("RET", "").replace("W/O", "")
    sets = re.findall(r"(\d+)-(\d+)(?:\((\d+)\))?", score_str)
    
    set_margins = [abs(int(s1) - int(s2)) for s1, s2, *_ in sets]
    tiebreaks = sum(1 for _, _, tb in sets if tb not in [None, ''])
    
    lead_changes = sum([
        1 for i in range(1, len(sets))
        if (int(sets[i-1][0]) > int(sets[i-1][1])) != (int(sets[i][0]) > int(sets[i][1]))
    ])
    
    return set_margins, tiebreaks, lead_changes


def advanced_comeback_score(score_str):
    """
    Calculate advanced comeback score (0-3 scale)
    
    Returns:
        int: 0 = no comeback, 1-3 = increasing drama
    """
    if pd.isna(score_str):
        return 0
    
    score_str = score_str.replace("RET", "").replace("W/O", "")
    sets = re.findall(r"(\d+)-(\d+)", score_str)
    
    if len(sets) < 3:
        return 0
    
    set_winners = [1 if int(s1) > int(s2) else 2 for s1, s2 in sets]
    p1_sets = set_winners.count(1)
    p2_sets = set_winners.count(2)
    
    if p1_sets == p2_sets:
        return 0
    
    winner = 1 if p1_sets > p2_sets else 2
    loser = 2 if winner == 1 else 1
    
    winner_set_wins = 0
    loser_set_wins = 0
    lead_diffs = []
    
    for val in set_winners:
        if val == winner:
            winner_set_wins += 1
        else:
            loser_set_wins += 1
        lead_diffs.append(loser_set_wins - winner_set_wins)
    
    # Down 0-2 comeback = 3 points
    if len(lead_diffs) > 1 and lead_diffs[1] == 2:
        return 3
    
    # Non-consecutive set losses = 2 points
    losing_indices = [i for i, val in enumerate(set_winners) if val == loser]
    if len(losing_indices) >= 2 and (losing_indices[-1] - losing_indices[0] > 1):
        return 2
    
    # Won only 1 of first 3 sets but won = 2 points
    if len(set_winners) == 5 and set_winners[:3].count(winner) == 1:
        return 2
    
    # 5-setter decided in final set = 1 point
    if len(set_winners) == 5 and set_winners[-1] == winner:
        return 1
    
    return 0


def final_set_tiebreak(score_str):
    """Check if the final set was decided by a tiebreak"""
    if pd.isna(score_str):
        return 0
    
    score_str = score_str.replace("RET", "").replace("W/O", "")
    sets = re.findall(r"(\d+)-(\d+)(?:\((\d+)\))?", score_str)
    
    if not sets:
        return 0
    
    last_set = sets[-1]
    return 1 if len(last_set) > 2 and last_set[2] not in [None, ''] else 0


# =============================================================================
# DATA FILTERING
# =============================================================================

def filter_grand_slams(df):
    """Filter DataFrame to only Grand Slam matches"""
    return df[df['tourney_name'].apply(is_grand_slam)].copy()


def filter_by_year(df, min_year=None, max_year=None):
    """Filter DataFrame by year range"""
    df = df.copy()
    df['year'] = df['tourney_date'].astype(str).str[:4].astype(int)
    
    if min_year is not None:
        df = df[df['year'] >= min_year]
    if max_year is not None:
        df = df[df['year'] <= max_year]
    
    return df


def filter_by_rounds(df, rounds):
    """Filter DataFrame by match rounds"""
    if not rounds:
        return df
    return df[df['round'].isin(rounds)].copy()


def filter_by_tournaments(df, tournaments):
    """Filter DataFrame by tournament names"""
    if not tournaments:
        return df
    return df[df['tourney_name'].isin(tournaments)].copy()


# =============================================================================
# STATISTICAL CALCULATIONS
# =============================================================================

def calculate_win_percentage(wins, total):
    """Calculate win percentage safely"""
    if total == 0:
        return 0.0
    return round(wins / total * 100, 2)


def safe_mean(series, default=0):
    """Calculate mean safely with default for empty/NaN"""
    if series is None or len(series) == 0:
        return default
    clean = series.dropna()
    if len(clean) == 0:
        return default
    return clean.mean()


def safe_round(value, decimals=2):
    """Round value safely, handling None/NaN"""
    if pd.isna(value):
        return None
    return round(value, decimals)


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
# PLAYER STATISTICS
# =============================================================================

def get_player_peak_ranking(df, player_name):
    """Get peak ranking for a player from winner/loser rank columns"""
    peak = 9999
    
    # Check winner rank
    winner_ranks = df[df['winner_name'] == player_name]['winner_rank'].dropna()
    if len(winner_ranks) > 0:
        peak = min(peak, winner_ranks.min())
    
    # Check loser rank
    loser_ranks = df[df['loser_name'] == player_name]['loser_rank'].dropna()
    if len(loser_ranks) > 0:
        peak = min(peak, loser_ranks.min())
    
    return peak if peak < 9999 else None


def get_player_country(df, player_name):
    """Get player country code"""
    # Check winner_ioc first
    winner_countries = df[df['winner_name'] == player_name]['winner_ioc'].dropna()
    if len(winner_countries) > 0:
        return winner_countries.iloc[0]
    
    # Check loser_ioc
    loser_countries = df[df['loser_name'] == player_name]['loser_ioc'].dropna()
    if len(loser_countries) > 0:
        return loser_countries.iloc[0]
    
    return 'UNK'


# =============================================================================
# MATCH QUALITY METRICS
# =============================================================================

def calculate_opponent_quality(opponent_ranks):
    """Calculate opponent quality metrics"""
    if len(opponent_ranks) == 0:
        return {
            'avg_rank': None,
            'top5_count': 0,
            'top10_count': 0,
            'top30_count': 0,
            'top30_pct': 0.0
        }
    
    clean_ranks = opponent_ranks.dropna()
    if len(clean_ranks) == 0:
        return {
            'avg_rank': None,
            'top5_count': 0,
            'top10_count': 0,
            'top30_count': 0,
            'top30_pct': 0.0
        }
    
    total = len(opponent_ranks)
    
    return {
        'avg_rank': round(clean_ranks.mean(), 1),
        'top5_count': int((clean_ranks <= 5).sum()),
        'top10_count': int((clean_ranks <= 10).sum()),
        'top30_count': int((clean_ranks <= 30).sum()),
        'top30_pct': round((clean_ranks <= 30).sum() / total * 100, 1)
    }


# =============================================================================
# SURFACE AND TOURNAMENT BREAKDOWN
# =============================================================================

def calculate_surface_breakdown(matches_df, player_name):
    """Calculate player statistics by surface"""
    surfaces = {}
    
    # Wins as winner
    wins = matches_df[matches_df['winner_name'] == player_name]
    # Losses as loser  
    losses = matches_df[matches_df['loser_name'] == player_name]
    
    all_surfaces = set(wins['surface'].unique()) | set(losses['surface'].unique())
    
    for surface in all_surfaces:
        if pd.isna(surface):
            continue
        
        surface_wins = len(wins[wins['surface'] == surface])
        surface_losses = len(losses[losses['surface'] == surface])
        surface_total = surface_wins + surface_losses
        
        surfaces[surface] = {
            'wins': surface_wins,
            'losses': surface_losses,
            'total': surface_total,
            'win_pct': calculate_win_percentage(surface_wins, surface_total)
        }
    
    return surfaces


def calculate_tournament_breakdown(matches_df, player_name):
    """Calculate player statistics by tournament"""
    tournaments = {}
    
    # Wins as winner
    wins = matches_df[matches_df['winner_name'] == player_name]
    # Losses as loser
    losses = matches_df[matches_df['loser_name'] == player_name]
    
    all_tourneys = set(wins['tourney_name'].unique()) | set(losses['tourney_name'].unique())
    
    for tourney in all_tourneys:
        if pd.isna(tourney):
            continue
        
        tourney_wins = len(wins[wins['tourney_name'] == tourney])
        tourney_losses = len(losses[losses['tourney_name'] == tourney])
        tourney_total = tourney_wins + tourney_losses
        
        tournaments[tourney] = {
            'wins': tourney_wins,
            'losses': tourney_losses,
            'total': tourney_total,
            'win_pct': calculate_win_percentage(tourney_wins, tourney_total)
        }
    
    return tournaments


# =============================================================================
# DATA VALIDATION
# =============================================================================

def validate_required_columns(df, required_cols, context="operation"):
    """Validate that DataFrame has required columns"""
    missing = [col for col in required_cols if col not in df.columns]
    
    if missing:
        print(f"⚠️  Warning: Missing columns for {context}: {missing}")
        return False
    
    return True


def safe_get_column(df, col_name, default=None):
    """Safely get column from DataFrame with fallback"""
    if col_name in df.columns:
        return df[col_name]
    return pd.Series([default] * len(df))
