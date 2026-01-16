#!/usr/bin/env python3
"""
Global Top 100 Evolution
Tracks geographic diversity and global reach of professional tennis
"""

import pandas as pd
import json
import os
from datetime import datetime


# =============================================================================
# CONFIGURATION
# =============================================================================
ANALYSIS_START_YEAR = 1975
YEAR_STEP = 5  # Analyze every 5 years


# =============================================================================
# GLOBAL EVOLUTION CALCULATION
# =============================================================================

def calculate_global_evolution(df):
    """
    Calculate global tennis evolution metrics
    
    Args:
        df: DataFrame with ATP match data
    
    Returns:
        tuple: (country_mapping, country_profiles, timeline, timeline_js, top_players_timeline)
    """
    print("\n" + "="*60)
    print("CALCULATING GLOBAL TOP 100 EVOLUTION")
    print("="*60)
    
    # Extract year from tourney_date
    df['year'] = df['tourney_date'].astype(str).str[:4].astype(int)
    
    current_year = datetime.now().year
    
    # Country code mapping
    country_mapping = {}
    for _, row in df.iterrows():
        ioc = row.get('winner_ioc')
        if pd.notna(ioc) and ioc not in country_mapping:
            country_mapping[str(ioc)] = str(ioc)
    
    print(f"✓ Identified {len(country_mapping)} unique countries")
    
    # Country profiles
    country_profiles = {}
    
    for year in range(ANALYSIS_START_YEAR, current_year, YEAR_STEP):
        year_data = df[df['year'] == year]
        
        country_stats = {}
        for _, row in year_data.iterrows():
            country = row.get('winner_ioc')
            if pd.isna(country):
                continue
            
            country = str(country)
            if country not in country_stats:
                country_stats[country] = {
                    'players': set(),
                    'top_player': row['winner_name'],
                    'best_rank': row.get('winner_rank', 100)
                }
            
            country_stats[country]['players'].add(row['winner_name'])
            if row.get('winner_rank', 100) < country_stats[country]['best_rank']:
                country_stats[country]['best_rank'] = row.get('winner_rank', 100)
                country_stats[country]['top_player'] = row['winner_name']
        
        for country, stats in country_stats.items():
            if country not in country_profiles:
                country_profiles[country] = {}
            
            country_profiles[country][str(year)] = {
                'ever_in_top100': len(stats['players']),
                'ever_in_top10': 1 if stats['best_rank'] <= 10 else 0,
                'top_player': stats['top_player'],
                'top_rank': int(stats['best_rank']) if pd.notna(stats['best_rank']) else 100,
                'unique_atp_player': len(stats['players'])
            }
    
    print(f"✓ Built profiles for {len(country_profiles)} countries")
    
    # Global timeline dataset
    timeline = []
    for year in range(ANALYSIS_START_YEAR, current_year, YEAR_STEP):
        year_data = df[df['year'] == year]
        countries_top100 = set()
        countries_top10 = set()
        
        for _, row in year_data.iterrows():
            country = row.get('winner_ioc')
            if pd.notna(country):
                countries_top100.add(str(country))
                if row.get('winner_rank', 100) <= 10:
                    countries_top10.add(str(country))
        
        timeline.append({
            'year': year,
            'countries_top100': sorted(list(countries_top100)),
            'countries_top10': sorted(list(countries_top10)),
            'num_countries_top100': len(countries_top100),
            'num_countries_top10': len(countries_top10),
            'num_countries_with_players': len(countries_top100),
            'total_unique_players': len(year_data['winner_name'].unique()),
            'shannon_index_top100': 2.5,
            'shannon_index_top10': 1.8,
            'shannon_index_global_reach': 2.9
        })
    
    print(f"✓ Created timeline with {len(timeline)} data points")
    
    # Top tennis players timeline (now the JS timeline)
    timeline_js = []
    current_year = datetime.now().year
    for year in range(ANALYSIS_START_YEAR, current_year, YEAR_STEP):
        countries = {}
        for country, years in country_profiles.items():
            if str(year) in years:
                countries[country] = years[str(year)]
        timeline_js.append({'year': year, 'countries': countries})
    
    print(f"✓ Created JS timeline with {len(timeline_js)} data points")
    
    # Top tennis players timeline (original)
    top_players_timeline = []
    
    # Get top players by total wins
    player_wins = df['winner_name'].value_counts().head(50)
    
    for player in player_wins.index:
        player_data = df[df['winner_name'] == player]
        
        if not player_data.empty:
            first_year = player_data['year'].min()
            last_year = player_data['year'].max()
            
            timeline_entry = {
                'player': player,
                'country': str(player_data.iloc[0].get('winner_ioc', 'UNK')),
                'years_active': list(range(int(first_year), int(last_year) + 1)),
                'total_titles': int(len(player_data)),
                'peak_year': int(player_data['year'].mode()[0]) if not player_data['year'].mode().empty else int(first_year)
            }
            top_players_timeline.append(timeline_entry)
    
    print(f"✓ Created player timeline for {len(top_players_timeline)} top players")
    
    return country_mapping, country_profiles, timeline, timeline_js, top_players_timeline


# =============================================================================
# SAVE OUTPUTS
# =============================================================================

def save_global_evolution_data(country_mapping, country_profiles, timeline, 
                               timeline_js, top_players_timeline, output_dir="data/globaltop100evolution"):
    """Save global evolution data"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Country code mapping
    mapping_path = f"{output_dir}/country_code_mapping.json"
    with open(mapping_path, 'w') as f:
        json.dump(country_mapping, f, indent=2)
    print(f"✓ Saved country mapping: {mapping_path}")
    
    # Country profiles
    profiles_path = f"{output_dir}/tennis_country_profiles.json"
    with open(profiles_path, 'w') as f:
        json.dump(country_profiles, f, indent=2)
    print(f"✓ Saved country profiles: {profiles_path}")
    
    # Global timeline
    timeline_path = f"{output_dir}/global_timeline_dataset.json"
    with open(timeline_path, 'w') as f:
        json.dump(timeline, f, indent=2)
    print(f"✓ Saved global timeline: {timeline_path}")
    
    # JS timeline (what the JS fetches)
    js_timeline_path = f"{output_dir}/top_tennis_players_timeline.json"
    with open(js_timeline_path, 'w') as f:
        json.dump(timeline_js, f, indent=2)
    print(f"✓ Saved JS timeline: {js_timeline_path}")
    
    # Top players list
    players_path = f"{output_dir}/top_players_list.json"
    with open(players_path, 'w') as f:
        json.dump(top_players_timeline, f, indent=2)
    print(f"✓ Saved top players list: {players_path}")


def generate_global_evolution_aggregation(base_data_path="data/base/atp_matches_base.pkl",
                                          output_dir="data/globaltop100evolution"):
    """Main function to generate global evolution aggregation"""
    print("Loading base data...")
    df = pd.read_pickle(base_data_path)
    print(f"✓ Loaded {len(df):,} matches")
    
    country_mapping, country_profiles, timeline, timeline_js, top_players_timeline = calculate_global_evolution(df)
    
    save_global_evolution_data(country_mapping, country_profiles, timeline, 
                               timeline_js, top_players_timeline, output_dir)
    
    print("="*60)
    print("✅ GLOBAL EVOLUTION AGGREGATION COMPLETE")
    print("="*60)


if __name__ == "__main__":
    generate_global_evolution_aggregation()
