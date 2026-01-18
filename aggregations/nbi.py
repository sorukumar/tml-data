#!/usr/bin/env python3
"""
NBI (Nailbiter Index) Calculator
Calculates drama scores for Grand Slam Finals and Semi-Finals
Now uses pre-enriched match data with parsed scores
"""

import pandas as pd
import numpy as np
import json
import os


# =============================================================================
# NBI FORMULA WEIGHTS (Easy to modify!)
# =============================================================================
NBI_WEIGHTS = {
    'avg_set_margin': 0.25,      # Close sets matter most
    'tiebreak_count': 0.12,      # Tiebreaks add drama
    'lead_changes': 0.18,        # Momentum swings
    'comeback': 0.22,            # Coming from behind
    'bp_saved_ratio': 0.07,      # Break point drama
    'final_set_tiebreak': 0.06,  # Final set tiebreak
    'duration_score': 0.10       # Epic length
}

# Data filtering parameters
ANALYSIS_START_YEAR = 1980
TARGET_ROUNDS = ['F', 'SF']  # Finals and Semi-Finals


# =============================================================================
# DRAMA TAGGING
# =============================================================================

def tag_drama(row):
    """Generate drama tags for a match"""
    tags = []
    if row['comeback_score'] >= 2:
        tags.append('comeback')
    if row['tiebreaks_count'] >= 2:
        tags.append('tiebreaks')
    if row['lead_changes'] >= 2:
        tags.append('momentum')
    if row['bp_saved_ratio'] > 0.6:
        tags.append('bp drama')
    if row.get('duration_score_norm', 0) > 0.7:
        tags.append('epic length')
    if row.get('final_set_tiebreak', 0) > 0:
        tags.append('final set tiebreak')
    return ', '.join(tags) if tags else 'standard'


# =============================================================================
# MAIN NBI CALCULATION (USING ENRICHED MATCHES)
# =============================================================================

def calculate_nbi(df_enriched):
    """
    Calculate NBI (Nailbiter Index) for Grand Slam matches using enriched data
    
    Args:
        df_enriched: DataFrame with enriched match data (already has parsed scores)
    
    Returns:
        pd.DataFrame: Sorted nailbiter matches with NBI scores
    """
    print("\n" + "="*60)
    print("CALCULATING NBI (NAILBITER INDEX)")
    print("="*60)
    
    # Filter for Grand Slams, Finals/SF, complete matches from start year
    gs_df = df_enriched[
        (df_enriched['is_grand_slam'] == True) & 
        (df_enriched['tourney_level'] == 'G') & 
        (df_enriched['round'].isin(TARGET_ROUNDS)) & 
        (df_enriched['year'] >= ANALYSIS_START_YEAR) &
        (df_enriched['is_complete'] == True)
    ].copy()
    
    if gs_df.empty:
        print("✗ No Grand Slam Finals/SF found")
        return pd.DataFrame()
    
    print(f"✓ Found {len(gs_df)} complete GS Finals/SF matches ({ANALYSIS_START_YEAR}+)")
    
    # Enriched data already has: avg_set_margin, tiebreaks_count, lead_changes, 
    # comeback_score, final_set_tiebreak - no need to recalculate!
    
    # Break point drama
    print("Computing break point drama...")
    gs_df['bp_total'] = gs_df['w_bpFaced'].fillna(0) + gs_df['l_bpFaced'].fillna(0)
    gs_df['bp_saved_total'] = gs_df['w_bpSaved'].fillna(0) + gs_df['l_bpSaved'].fillna(0)
    gs_df['bp_saved_ratio'] = gs_df['bp_saved_total'] / gs_df['bp_total'].replace(0, np.nan)
    gs_df['bp_saved_ratio'] = gs_df['bp_saved_ratio'].fillna(0)
    
    # Duration
    gs_df['num_sets'] = gs_df['winner_sets'] + gs_df['loser_sets']
    gs_df['duration_score'] = gs_df['minutes'] / gs_df['num_sets'].replace(0, np.nan)
    
    # Normalize features (0-1 scale)
    print("Normalizing features...")
    features_to_normalize = ['avg_set_margin', 'tiebreaks_count', 'lead_changes', 
                             'comeback_score', 'bp_saved_ratio', 'duration_score']
    
    for col in features_to_normalize:
        min_val = gs_df[col].min()
        max_val = gs_df[col].max()
        if max_val == min_val:
            gs_df[col + '_norm'] = 0
        elif col == 'avg_set_margin':
            # Invert: smaller margin = higher drama
            gs_df[col + '_norm'] = (max_val - gs_df[col]) / (max_val - min_val)
        else:
            gs_df[col + '_norm'] = (gs_df[col] - min_val) / (max_val - min_val)
    
    # Calculate NBI using weighted formula
    print("Calculating NBI scores...")
    gs_df['NBI'] = (
        NBI_WEIGHTS['avg_set_margin'] * gs_df['avg_set_margin_norm'] +
        NBI_WEIGHTS['tiebreak_count'] * gs_df['tiebreaks_count_norm'] +
        NBI_WEIGHTS['lead_changes'] * gs_df['lead_changes_norm'] +
        NBI_WEIGHTS['comeback'] * gs_df['comeback_score_norm'] +
        NBI_WEIGHTS['bp_saved_ratio'] * gs_df['bp_saved_ratio_norm'] +
        NBI_WEIGHTS['final_set_tiebreak'] * gs_df['final_set_tiebreak'] +
        NBI_WEIGHTS['duration_score'] * gs_df['duration_score_norm']
    )
    
    # Sort by NBI
    nailbiters = gs_df.sort_values('NBI', ascending=False).reset_index(drop=True)
    
    # Scale to 0-100
    max_nbi = nailbiters['NBI'].max()
    nailbiters['NBI_100'] = (nailbiters['NBI'] / max_nbi) * 100 if max_nbi > 0 else 0
    
    # Add drama tags
    nailbiters['drama_tags'] = nailbiters.apply(tag_drama, axis=1)
    
    print(f"✓ NBI calculated for {len(nailbiters)} matches")
    print(f"  Top NBI: {nailbiters['NBI'].max():.3f}")
    print(f"  #1 Match: {nailbiters.iloc[0]['winner_name']} def. {nailbiters.iloc[0]['loser_name']}")
    print(f"  Tournament: {nailbiters.iloc[0]['tourney_name']} {nailbiters.iloc[0]['year']}")
    
    return nailbiters


# =============================================================================
# SAVE OUTPUTS
# =============================================================================

def save_nbi_data(nailbiters, output_dir="data/nbi"):
    """Save NBI data in multiple formats"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Filter out invalid records
    nailbiters = nailbiters.dropna(subset=['tourney_date', 'score', 'winner_name', 'loser_name']).copy()
    
    # Save CSV
    csv_output = nailbiters[[
        'tourney_name', 'tourney_date', 'round', 'minutes', 'score',
        'winner_name', 'loser_name', 'NBI', 'comeback_score', 'avg_set_margin',
        'tiebreaks_count', 'lead_changes', 'bp_saved_ratio', 'bp_total'
    ]].copy()
    
    csv_path = f"{output_dir}/gs_nailbiters.csv"
    csv_output.to_csv(csv_path, index=True)
    print(f"✓ Saved CSV: {csv_path}")
    
    # Build JSON records
    records = []
    for _, row in nailbiters.iterrows():
        def safe(val, round_to=None):
            if pd.isna(val) or (isinstance(val, float) and np.isnan(val)):
                return None
            return round(val, round_to) if round_to is not None else val
        
        record = {
            'match': f"{row['winner_name']} def. {row['loser_name']}",
            'tourney': row['tourney_name'],
            'round': row['round'],
            'date': str(row['tourney_date'])[:10],
            'score': row['score'],
            'duration': int(row['minutes']) if not pd.isna(row['minutes']) else None,
            'NBI': safe(row['NBI'], 3),
            'NBI_100': safe(row['NBI_100'], 1),
            'drama_tags': row['drama_tags'],
            'raw_stats': {
                'avg_set_margin': safe(row['avg_set_margin'], 2),
                'tiebreak_count': safe(row['tiebreaks_count'], 0),
                'lead_changes': safe(row['lead_changes'], 0),
                'comeback': safe(row['comeback_score'], 0),
                'bp_saved_ratio': safe(row['bp_saved_ratio'], 3),
                'bp_total': safe(row['bp_total'], 0)
            }
        }
        records.append(record)
    
    # Save full JSON
    json_path = f"{output_dir}/gs_nailbiters.json"
    with open(json_path, 'w') as f:
        json.dump(records, f, indent=2)
    print(f"✓ Saved JSON: {json_path} ({len(records)} matches)")
    
    # NOTE: iconic_gs_matches.json is manually curated
    iconic_path = f"{output_dir}/iconic_gs_matches.json"
    if os.path.exists(iconic_path):
        print(f"✓ Preserved curated iconic matches: {iconic_path} (not overwritten)")
    else:
        print(f"⚠ Warning: {iconic_path} not found - please add curated iconic matches manually")


def generate_nbi_aggregation(matches_enriched_path="data/base/matches_enriched.parquet",
                              output_dir="data/nbi"):
    """
    Generate NBI aggregation from enriched matches data
    """
    print("\n" + "="*60)
    print("GENERATING NBI (NAILBITER INDEX) DATA")
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
    
    nailbiters = calculate_nbi(df_enriched)
    
    if not nailbiters.empty:
        save_nbi_data(nailbiters, output_dir)
        print("="*60)
        print("✅ NBI AGGREGATION COMPLETE")
        print("="*60)
    else:
        print("="*60)
        print("❌ NBI AGGREGATION FAILED: No data")
        print("="*60)


if __name__ == "__main__":
    generate_nbi_aggregation()
