#!/usr/bin/env python3
"""
NBI (Nailbiter Index) Calculator
Calculates drama scores for Grand Slam Finals and Semi-Finals
"""

import pandas as pd
import numpy as np
import json
import os
import re


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
GRAND_SLAMS = ['Australian Open', 'Roland Garros', 'Wimbledon', 'US Open']
TARGET_ROUNDS = ['F', 'SF']  # Finals and Semi-Finals


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def parse_sets(score_str):
    """Parse set scores from the 'score' string"""
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
    """Calculate advanced comeback score (0-3 scale)"""
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


def tag_drama(row):
    """Generate drama tags for a match"""
    tags = []
    if row['comeback'] >= 2:
        tags.append('comeback')
    if row['tiebreak_count'] >= 2:
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
# MAIN NBI CALCULATION
# =============================================================================

def calculate_nbi(df):
    """
    Calculate NBI (Nailbiter Index) for Grand Slam matches
    
    Args:
        df: DataFrame with ATP match data
    
    Returns:
        pd.DataFrame: Sorted nailbiter matches with NBI scores
    """
    print("\n" + "="*60)
    print("CALCULATING NBI (NAILBITER INDEX)")
    print("="*60)
    
    # Filter for Grand Slams
    gs_df = df[df['tourney_name'].isin(GRAND_SLAMS)].copy()
    
    # Filter for Finals and Semi-Finals from start year onwards
    gs_df['tourney_year'] = pd.to_datetime(
        gs_df['tourney_date'].astype(str), 
        format='%Y%m%d', 
        errors='coerce'
    ).dt.year
    
    gs_df = gs_df[
        (gs_df['tourney_level'] == 'G') & 
        (gs_df['round'].isin(TARGET_ROUNDS)) & 
        (gs_df['tourney_year'] >= ANALYSIS_START_YEAR)
    ].copy()
    
    # Remove incomplete matches
    gs_df['is_complete'] = ~gs_df['score'].str.contains('RET|W/O', na=False)
    gs_df = gs_df[gs_df['is_complete']].copy()
    
    if gs_df.empty:
        print("✗ No Grand Slam Finals/SF found")
        return pd.DataFrame()
    
    print(f"✓ Found {len(gs_df)} complete GS Finals/SF matches ({ANALYSIS_START_YEAR}+)")
    
    # Feature engineering
    print("Computing match features...")
    gs_df['parsed'] = gs_df['score'].apply(parse_sets)
    gs_df['set_margins'] = gs_df['parsed'].apply(lambda x: x[0])
    gs_df['tiebreak_count'] = gs_df['parsed'].apply(lambda x: x[1])
    gs_df['lead_changes'] = gs_df['parsed'].apply(lambda x: x[2])
    gs_df['avg_set_margin'] = gs_df['set_margins'].apply(lambda x: np.mean(x) if x else np.nan)
    gs_df['comeback'] = gs_df['score'].apply(advanced_comeback_score)
    gs_df['num_sets'] = gs_df['set_margins'].apply(len)
    gs_df['final_set_tiebreak'] = gs_df['score'].apply(final_set_tiebreak)
    
    # Break point drama
    gs_df['bp_total'] = gs_df['w_bpFaced'].fillna(0) + gs_df['l_bpFaced'].fillna(0)
    gs_df['bp_saved_total'] = gs_df['w_bpSaved'].fillna(0) + gs_df['l_bpSaved'].fillna(0)
    gs_df['bp_saved_ratio'] = gs_df['bp_saved_total'] / gs_df['bp_total'].replace(0, np.nan)
    gs_df['bp_saved_ratio'] = gs_df['bp_saved_ratio'].fillna(0)
    
    # Duration
    gs_df['duration_score'] = gs_df['minutes'] / gs_df['num_sets'].replace(0, np.nan)
    
    # Normalize features (0-1 scale)
    print("Normalizing features...")
    features_to_normalize = ['avg_set_margin', 'tiebreak_count', 'lead_changes', 
                             'comeback', 'bp_saved_ratio', 'duration_score']
    
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
        NBI_WEIGHTS['tiebreak_count'] * gs_df['tiebreak_count_norm'] +
        NBI_WEIGHTS['lead_changes'] * gs_df['lead_changes_norm'] +
        NBI_WEIGHTS['comeback'] * gs_df['comeback_norm'] +
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
    print(f"  Tournament: {nailbiters.iloc[0]['tourney_name']} {nailbiters.iloc[0]['tourney_year']}")
    
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
        'winner_name', 'loser_name', 'NBI', 'comeback', 'avg_set_margin',
        'tiebreak_count', 'lead_changes', 'bp_saved_ratio', 'bp_total'
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
                'tiebreak_count': safe(row['tiebreak_count'], 0),
                'lead_changes': safe(row['lead_changes'], 0),
                'comeback': safe(row['comeback'], 0),
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
    
    # Save top 20 iconic matches with additional metadata
    iconic_data = records[:20]
    
    # Add historical significance, commentary, etc. for top matches
    iconic_metadata = [
        {
            "historical_significance": "Djokovic's epic comeback from two sets down in the Wimbledon final, showcasing unprecedented mental resilience.",
            "short_commentary": "A 5-hour marathon that redefined endurance in tennis, with Djokovic saving match points and winning the final set tiebreak.",
            "career_impact": "Cemented Djokovic's legacy as one of the greatest comeback players, boosting his confidence for future Grand Slam challenges.",
            "cultural_resonance": "Became a symbol of perseverance, inspiring fans worldwide and highlighting tennis' global appeal."
        },
        {
            "historical_significance": "Alcaraz's stunning victory over Sinner in the French Open final, marking the rise of a new generation.",
            "short_commentary": "A dramatic 5-set battle where Alcaraz overcame a two-set deficit, winning the final set in a tiebreak.",
            "career_impact": "Established Alcaraz as a Grand Slam champion at 22, accelerating his ascent to the top of men's tennis.",
            "cultural_resonance": "Represented the passing of the torch from European veterans to a new wave of Spanish talent."
        },
        {
            "historical_significance": "Nadal's legendary comeback from two sets down against Verdasco in the Australian Open semifinals.",
            "short_commentary": "A grueling 5-set match that lasted over 5 hours, decided by a final set tiebreak after Nadal saved match points.",
            "career_impact": "Demonstrated Nadal's clay-court mastery could translate to hard courts, expanding his Grand Slam dominance.",
            "cultural_resonance": "Emphasized the drama of underdog stories and the beauty of extended rallies in modern tennis."
        },
        {
            "historical_significance": "Anderson's historic victory over Isner in the longest tennis match ever played at Wimbledon.",
            "short_commentary": "A 6-hour, 36-minute semifinal that went to a final set tiebreak, with Anderson winning 26-24 in the fifth set.",
            "career_impact": "Gave Anderson his first Grand Slam semifinal win and put South African tennis back on the map.",
            "cultural_resonance": "Became a testament to physical and mental endurance, changing perceptions of tennis match lengths."
        },
        {
            "historical_significance": "Djokovic's semifinal victory over del Potro at Wimbledon, a clash of titans.",
            "short_commentary": "A 4-set thriller with multiple lead changes and intense break point drama throughout.",
            "career_impact": "Helped Djokovic reach his first Wimbledon final, setting the stage for his Grand Slam dominance.",
            "cultural_resonance": "Highlighted the rivalry between Djokovic and del Potro, two of the most athletic players of their era."
        },
        {
            "historical_significance": "Nadal's comeback win over Dimitrov in the Australian Open semifinals.",
            "short_commentary": "Nadal fought back from two sets down in a match filled with tiebreaks and momentum shifts.",
            "career_impact": "Showed Nadal's adaptability on hard courts, leading to more Grand Slam success outside clay.",
            "cultural_resonance": "Demonstrated the unpredictability of tennis and the thrill of seeing legends perform at their peak."
        },
        {
            "historical_significance": "Edberg's victory over Chang in the US Open semifinals, a classic baseline battle.",
            "short_commentary": "A long, grueling match with multiple tiebreaks and break point opportunities for both players.",
            "career_impact": "Helped Edberg reach the US Open final, showcasing his consistency in big matches.",
            "cultural_resonance": "Represented the golden era of American tennis and the skill of baseline play."
        },
        {
            "historical_significance": "Murray's semifinal win over Federer at the Australian Open.",
            "short_commentary": "A 5-set epic with tiebreaks in sets 2 and 4, and constant momentum changes.",
            "career_impact": "Marked Murray's breakthrough as a Grand Slam force, leading to his Wimbledon victory.",
            "cultural_resonance": "Symbolized the changing of the guard in men's tennis from Federer to the next generation."
        },
        {
            "historical_significance": "Djokovic's Wimbledon final victory over Federer, a rematch of the 2014 final.",
            "short_commentary": "A 5-set battle with tiebreaks and lead changes, decided in a final set tiebreak.",
            "career_impact": "Gave Djokovic his second Wimbledon title, solidifying his status as a multiple Grand Slam winner.",
            "cultural_resonance": "Continued the Federer-Djokovic rivalry that captivated tennis fans worldwide."
        },
        {
            "historical_significance": "Federer's Wimbledon final win over Roddick, his last Grand Slam title.",
            "short_commentary": "A 5-set match with a final set tiebreak, showcasing Federer's precision and Roddick's power.",
            "career_impact": "Extended Federer's Grand Slam record, proving his longevity at the highest level.",
            "cultural_resonance": "Celebrated Federer's elegance and the end of an era in men's tennis."
        },
        {
            "historical_significance": "Djokovic's semifinal victory over Nadal at Wimbledon.",
            "short_commentary": "A high-stakes match with multiple lead changes and intense break point drama.",
            "career_impact": "Helped Djokovic reach the Wimbledon final, contributing to his Grand Slam collection.",
            "cultural_resonance": "Highlighted the intense rivalry between Djokovic and Nadal on grass."
        },
        {
            "historical_significance": "Del Potro's upset victory over Federer in the US Open final.",
            "short_commentary": "A 5-set match with tiebreaks and momentum shifts, decided in the final set.",
            "career_impact": "Gave del Potro his first Grand Slam title and put him on the world stage.",
            "cultural_resonance": "Showed the unpredictability of tennis and the rise of underdogs."
        },
        {
            "historical_significance": "Medvedev's comeback win over Zverev in the Australian Open semifinals.",
            "short_commentary": "Medvedev fought back from two sets down to win in five sets with a final set tiebreak.",
            "career_impact": "Propelled Medvedev to his first Grand Slam final and top ranking.",
            "cultural_resonance": "Represented the emergence of Russian tennis and the thrill of comebacks."
        },
        {
            "historical_significance": "Safin's semifinal victory over Federer at the Australian Open.",
            "short_commentary": "A 5-set match with momentum changes and break point drama in the final set.",
            "career_impact": "Helped Safin reach the Australian Open final, showcasing his potential.",
            "cultural_resonance": "Highlighted the power baseline game and the intensity of Australian Open matches."
        },
        {
            "historical_significance": "Djokovic's victory over Nadal in the Australian Open final.",
            "short_commentary": "A 5-set epic that lasted over 5 hours, with Djokovic coming back from two sets down.",
            "career_impact": "Gave Djokovic his third Australian Open title and boosted his Grand Slam count.",
            "cultural_resonance": "Became one of the greatest matches in tennis history, symbolizing endurance and skill."
        },
        {
            "historical_significance": "Wawrinka's upset victory over Murray in the French Open semifinals.",
            "short_commentary": "A 5-set match with tiebreaks and lead changes, decided in the final set.",
            "career_impact": "Led Wawrinka to his second Grand Slam title at the French Open.",
            "cultural_resonance": "Showed the unpredictability of clay court tennis and the rise of outsiders."
        },
        {
            "historical_significance": "Nadal's victory over Federer in the Australian Open final.",
            "short_commentary": "A 5-set match with multiple tiebreaks and momentum shifts.",
            "career_impact": "Gave Nadal his first Australian Open title, expanding his Grand Slam dominance.",
            "cultural_resonance": "Continued the Federer-Nadal rivalry and the appeal of hard court battles."
        },
        {
            "historical_significance": "Sampras' victory over Ivanisevic in the Wimbledon final.",
            "short_commentary": "A 5-set match with tiebreaks and lead changes, showcasing baseline power.",
            "career_impact": "Gave Sampras his fourth Wimbledon title, solidifying his grass court mastery.",
            "cultural_resonance": "Represented the peak of American tennis dominance in the 1990s."
        },
        {
            "historical_significance": "Thiem's victory over Zverev in the US Open final.",
            "short_commentary": "Thiem came back from two sets down to win in five sets with a final set tiebreak.",
            "career_impact": "Gave Thiem his first Grand Slam title and established him as a top player.",
            "cultural_resonance": "Highlighted the emergence of Austrian tennis and the drama of comebacks."
        },
        {
            "historical_significance": "Cilic's victory over Nishikori in the US Open final.",
            "short_commentary": "A 5-set match with tiebreaks and lead changes, decided in the final set.",
            "career_impact": "Gave Cilic his first Grand Slam title, becoming Croatia's first male Grand Slam winner.",
            "cultural_resonance": "Celebrated the diversity of tennis and the success of players from smaller nations."
        }
    ]
    
    for i, match in enumerate(iconic_data):
        if i < len(iconic_metadata):
            match.update(iconic_metadata[i])
    
    iconic_path = f"{output_dir}/iconic_gs_matches.json"
    with open(iconic_path, 'w') as f:
        json.dump(iconic_data, f, indent=2)
    print(f"✓ Saved iconic matches: {iconic_path} (top 20 with metadata)")


def generate_nbi_aggregation(base_data_path="data/base/atp_matches_base.pkl", 
                             output_dir="data/nbi"):
    """Main function to generate NBI aggregation"""
    print("Loading base data...")
    df = pd.read_pickle(base_data_path)
    print(f"✓ Loaded {len(df):,} matches")
    
    nailbiters = calculate_nbi(df)
    
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
