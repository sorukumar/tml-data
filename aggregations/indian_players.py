#!/usr/bin/env python3
"""
Indian Tennis Players Aggregation
Generates datasets about Indian players for visualization and analysis.
"""

import pandas as pd
import numpy as np
import json
import os
from collections import defaultdict

GRAND_SLAMS = ['Australian Open', 'Roland Garros', 'Wimbledon', 'US Open', 'French Open']


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def safe_str(x):
    return None if pd.isna(x) else str(x)


def get_best_performance_from_group(group, round_order):
    # Determine best performance (highest round) from a group of appearances
    # group is a DataFrame with 'round' and 'tourney_name'
    if group.empty:
        return None, None
    # Map rounds to order, ignore missing
    group = group[group['round'].isin(round_order.keys())].copy()
    if group.empty:
        return None, None
    group['round_order'] = group['round'].map(round_order)
    best_idx = group['round_order'].idxmax()
    best_row = group.loc[best_idx]
    return safe_str(best_row['round']), safe_str(best_row['tourney_name'])


# -----------------------------------------------------------------------------
# Main aggregation
# -----------------------------------------------------------------------------

def generate_indian_datasets(base_data_path="data/base/atp_matches_raw.parquet",
                              output_dir="data/indian",
                              start_year=1968,
                              country_code='IND',
                              fast_mode=False):
    """Generate datasets for Indian tennis players and save to output_dir"""
    print("\n" + "="*60)
    print("GENERATING INDIAN PLAYERS DATA")
    print("="*60)
    
    print("\nLoading base data...")
    # Load base data (now Parquet format)
    if base_data_path.endswith('.parquet'):
        df_all = pd.read_parquet(base_data_path)
    else:
        df_all = pd.read_pickle(base_data_path)
    print(f"✓ Loaded {len(df_all):,} matches")

    # Ensure year column and summarize time-window choices
    df_all['year'] = df_all['tourney_date'].astype(str).str[:4].astype(int)
    full_count = len(df_all)
    count_1990 = len(df_all[df_all['year'] >= 1990])
    count_2000 = len(df_all[df_all['year'] >= 2000])
    print(f"✓ Dataset coverage: Full={full_count:,}, Since1990={count_1990:,} ({count_1990/full_count*100:.1f}%), Since2000={count_2000:,} ({count_2000/full_count*100:.1f}%)")

    # Fast mode is useful for development; otherwise use full historical coverage (default start_year=1968)
    if fast_mode:
        print("⚡ Fast mode enabled: restricting to 1990 for faster iteration")
        start_year = 1990

    df = df_all[df_all['year'] >= start_year].copy()
    print(f"✓ Filtering to years >= {start_year}: {len(df):,} matches")

    os.makedirs(output_dir, exist_ok=True)

    round_order = {'R128': 1, 'R64': 2, 'R32': 3, 'R16': 4, 'QF': 5, 'SF': 6, 'F': 7, 'W': 8}

    # Filter matches involving Indian players
    country_matches = df[(df['winner_ioc'] == country_code) | (df['loser_ioc'] == country_code)].copy()
    print(f"✓ Found {len(country_matches):,} matches involving {country_code}")

    # Build appearances dataset (id, name, year, round, tourney_name, rank)
    winners = country_matches.loc[country_matches['winner_ioc'] == country_code, ['winner_id', 'winner_name', 'year', 'round', 'tourney_name', 'winner_rank']].rename(columns={'winner_id': 'id', 'winner_name': 'name', 'winner_rank': 'rank'})
    losers = country_matches.loc[country_matches['loser_ioc'] == country_code, ['loser_id', 'loser_name', 'year', 'round', 'tourney_name', 'loser_rank']].rename(columns={'loser_id': 'id', 'loser_name': 'name', 'loser_rank': 'rank'})

    appearances = pd.concat([winners, losers], ignore_index=True)
    appearances['id'] = appearances['id'].astype(str)

    player_ids = appearances['id'].unique().tolist()
    print(f"✓ Found {len(player_ids)} unique Indian players since {start_year}")

    # Helper: compute best performance per player per year
    best_performance_year = appearances.groupby(['id', 'year']).apply(lambda g: pd.Series(get_best_performance_from_group(g, round_order), index=['best_round','best_tourney'])).reset_index()

    # Helper: best lifetime performance
    best_performance_lifetime = appearances.groupby('id').apply(lambda g: pd.Series(get_best_performance_from_group(g, round_order), index=['best_round','best_tourney'])).reset_index()

    # Grand slam performances
    gs_matches = appearances[appearances['tourney_name'].isin(GRAND_SLAMS)]
    if not gs_matches.empty:
        best_gs = gs_matches.groupby('id').apply(lambda g: pd.Series(get_best_performance_from_group(g, round_order), index=['best_gs_round','best_gs_tourney'])).reset_index()
    else:
        best_gs = pd.DataFrame(columns=['id','best_gs_round','best_gs_tourney'])

    # Matches per player (across filtered years)
    match_counts = appearances.groupby('id').size().reset_index(name='matches_played')

    # Best rank for player from appearances
    best_ranks = appearances.groupby('id')['rank'].min().reset_index().rename(columns={'rank': 'best_rank'})

    # Merge to create players summary
    players = pd.DataFrame({'id': player_ids})
    players = players.merge(match_counts, on='id', how='left')
    players = players.merge(best_performance_lifetime.rename(columns={'best_round':'best_performance_lifetime','best_tourney':'best_tourney_lifetime'}), on='id', how='left')
    players = players.merge(best_gs, on='id', how='left')
    players = players.merge(best_ranks, on='id', how='left')

    # Years, min/max, matches by year, best_performance_each_year
    years_by_player = appearances.groupby('id')['year'].apply(lambda x: sorted(set(x))).reset_index().rename(columns={'year':'years'})
    players = players.merge(years_by_player, on='id', how='left')

    # Build best_performance_each_year mapping and matches_by_year
    bp_year_map = best_performance_year.copy()
    bp_year_map['best_performance_each_year'] = bp_year_map.apply(lambda r: f"{int(r['year'])}: {safe_str(r['best_round'])} at {safe_str(r['best_tourney'])}" if pd.notna(r['best_round']) else None, axis=1)
    bp_agg = bp_year_map.groupby('id').agg({'best_performance_each_year': lambda x: ', '.join(filter(None, x)), 'year': lambda x: sorted(set(x))}).reset_index()
    bp_agg.rename(columns={'year':'years_detail'}, inplace=True)

    players = players.merge(bp_agg[['id','best_performance_each_year']], on='id', how='left')

    # Add min and max years and years_played
    players['years'] = players['years'].apply(lambda x: x if isinstance(x, list) else [])
    players['years_played'] = players['years'].apply(len)
    players['min_year'] = players['years'].apply(lambda x: min(x) if x else None)
    players['max_year'] = players['years'].apply(lambda x: max(x) if x else None)

    # Compute additional metrics per player: wins, losses, top_100_wins, top_50_wins
    wins = country_matches[country_matches['winner_ioc'] == country_code].copy()
    wins['winner_id'] = wins['winner_id'].astype(str)
    losses = country_matches[country_matches['loser_ioc'] == country_code].copy()
    losses['loser_id'] = losses['loser_id'].astype(str)

    wins_count = wins.groupby('winner_id').size().reset_index(name='wins').rename(columns={'winner_id':'id'})
    losses_count = losses.groupby('loser_id').size().reset_index(name='losses').rename(columns={'loser_id':'id'})

    # top-ranked opponent wins (opponent rank <= 100 for example)
    wins['opp_rank'] = wins['loser_rank'].fillna(9999)
    wins['beat_top100'] = (wins['opp_rank'] <= 100).astype(int)
    top100_wins = wins.groupby('winner_id')['beat_top100'].sum().reset_index().rename(columns={'winner_id':'id','beat_top100':'top100_wins'})

    # Merge counts
    players = players.merge(wins_count, on='id', how='left')
    players = players.merge(losses_count, on='id', how='left')
    players = players.merge(top100_wins, on='id', how='left')

    players['wins'] = players['wins'].fillna(0).astype(int)
    players['losses'] = players['losses'].fillna(0).astype(int)
    players['top100_wins'] = players['top100_wins'].fillna(0).astype(int)
    players['matches_played'] = players['matches_played'].fillna(0).astype(int)

    # Best GS performance formatting
    players['best_grand_slam_performance'] = players.apply(lambda r: f"{safe_str(r.get('best_gs_round'))} at {safe_str(r.get('best_gs_tourney'))}" if pd.notna(r.get('best_gs_round')) else 'No Grand Slam Matches', axis=1)

    # Convert best_performance_lifetime to friendly string
    players['best_performance_lifetime'] = players.apply(lambda r: f"{safe_str(r.get('best_performance_lifetime'))} at {safe_str(r.get('best_tourney_lifetime'))}" if pd.notna(r.get('best_performance_lifetime')) else None, axis=1)

    # Best rank as int or None
    players['best_rank'] = players['best_rank'].apply(lambda x: int(x) if pd.notna(x) and x < 9999 else None)

    # Final players summary list
    players_summary = []
    for _, row in players.sort_values(['matches_played','best_rank'], ascending=[False,True]).iterrows():
        players_summary.append({
            'id': row['id'],
            'name': row.get('name') if pd.notna(row.get('name')) else None,
            'years': row['years'],
            'years_played': int(row['years_played']),
            'min_year': int(row['min_year']) if row['min_year'] is not None else None,
            'max_year': int(row['max_year']) if row['max_year'] is not None else None,
            'matches_played': int(row['matches_played']),
            'wins': int(row['wins']),
            'losses': int(row['losses']),
            'win_pct': round((row['wins'] / row['matches_played'] * 100) if row['matches_played'] > 0 else 0, 2),
            'best_performance_lifetime': row.get('best_performance_lifetime'),
            'best_performance_each_year': row.get('best_performance_each_year'),
            'best_grand_slam_performance': row.get('best_grand_slam_performance'),
            'best_rank': row.get('best_rank'),
            'top100_wins': int(row['top100_wins'])
        })

    # Save players_summary.json
    with open(f"{output_dir}/players_summary.json", 'w') as f:
        json.dump(players_summary, f, indent=2)
    print(f"✓ Saved: players_summary.json ({len(players_summary)} players)")

    # --- Players time series (players per year) ---
    years = sorted(df['year'].unique().tolist())
    ts = []
    for y in years:
        country_players = country_matches[country_matches['year'] == y]
        country_unique = pd.concat([country_players['winner_id'], country_players['loser_id']]).astype(str).nunique()
        global_players = pd.concat([df[df['year'] == y]['winner_id'], df[df['year'] == y]['loser_id']]).astype(str).nunique()
        ts.append({'year': int(y), 'country_unique_players': int(country_unique), 'global_unique_players': int(global_players), 'ratio': round(country_unique / global_players if global_players>0 else 0, 4)})

    with open(f"{output_dir}/players_time_series.json", 'w') as f:
        json.dump(ts, f, indent=2)
    print(f"✓ Saved: players_time_series.json ({len(ts)} years)")

    # --- Win/Loss by year ---
    wins_by_year = wins.groupby('year').size().reset_index(name='wins')
    losses_by_year = losses.groupby('year').size().reset_index(name='losses')
    total_by_year = df.groupby('year').size().reset_index(name='total_matches')

    wl = pd.merge(total_by_year, wins_by_year, on='year', how='left').merge(losses_by_year, on='year', how='left').fillna(0)
    wl['wins'] = wl['wins'].astype(int)
    wl['losses'] = wl['losses'].astype(int)

    win_loss_list = wl.to_dict('records')
    with open(f"{output_dir}/win_loss_by_year.json", 'w') as f:
        json.dump(win_loss_list, f, indent=2)
    print(f"✓ Saved: win_loss_by_year.json ({len(win_loss_list)} years)")

    # --- Tournament participation by level ---
    country_participation = country_matches.groupby(['year','tourney_level']).size().unstack(fill_value=0).astype(int)
    global_participation = df.groupby(['year','tourney_level']).size().unstack(fill_value=0).astype(int)

    # Convert to year-centric list of dicts
    country_part_list = []
    for y in sorted(country_participation.index.tolist()):
        d = {'year': int(y)}
        d.update({lvl: int(country_participation.loc[y,lvl]) for lvl in country_participation.columns})
        country_part_list.append(d)

    global_part_list = []
    for y in sorted(global_participation.index.tolist()):
        d = {'year': int(y)}
        d.update({lvl: int(global_participation.loc[y,lvl]) for lvl in global_participation.columns})
        global_part_list.append(d)

    with open(f"{output_dir}/tournament_participation_country.json", 'w') as f:
        json.dump(country_part_list, f, indent=2)
    with open(f"{output_dir}/tournament_participation_global.json", 'w') as f:
        json.dump(global_part_list, f, indent=2)
    print(f"✓ Saved: tournament participation by level (country & global)")

    # --- Sample matches for interactive visualization ---
    matches_sample = country_matches.sort_values(['tourney_date']).loc[:, ['tourney_date','tourney_name','tourney_level','surface','round','winner_name','loser_name','score','winner_rank','loser_rank','minutes']].copy()
    # Format date
    matches_sample['tourney_date'] = matches_sample['tourney_date'].astype(str)

    sample_records = matches_sample.to_dict('records')
    with open(f"{output_dir}/indian_matches.json", 'w') as f:
        json.dump(sample_records, f, indent=2)
    print(f"✓ Saved: indian_matches.json ({len(sample_records)} matches)")

    # --- Notable players (top 10 by matches_played) ---
    notable = sorted(players_summary, key=lambda x: x['matches_played'], reverse=True)[:20]
    with open(f"{output_dir}/notable_players.json", 'w') as f:
        json.dump(notable, f, indent=2)
    print(f"✓ Saved: notable_players.json ({len(notable)} players)")

    # --- Additional datasets for deeper analysis ---
    # Player milestones: first match, age at first match, first GS, first top100 win, titles
    milestones = []
    for pid in player_ids:
        p_matches = df[(df['winner_id'].astype(str) == pid) | (df['loser_id'].astype(str) == pid)].copy()
        if p_matches.empty:
            continue
        p_matches['tourney_date_dt'] = pd.to_datetime(p_matches['tourney_date'].astype(str), format='%Y%m%d', errors='coerce')
        first_match_row = p_matches.sort_values('tourney_date_dt').iloc[0]
        first_match_date = str(first_match_row['tourney_date_dt'].date()) if pd.notna(first_match_row['tourney_date_dt']) else None
        if str(first_match_row.get('winner_id')) == pid:
            age_first = first_match_row.get('winner_age') if 'winner_age' in first_match_row else None
        else:
            age_first = first_match_row.get('loser_age') if 'loser_age' in first_match_row else None
        # first grand slam
        gs_rows = p_matches[p_matches['tourney_name'].isin(GRAND_SLAMS)].copy()
        if not gs_rows.empty:
            gs_first = gs_rows.sort_values('tourney_date_dt').iloc[0]
            first_gs_date = str(gs_first['tourney_date_dt'].date()) if pd.notna(gs_first['tourney_date_dt']) else None
        else:
            first_gs_date = None
        # first top100 win
        top100_win_rows = p_matches[(p_matches['winner_id'].astype(str) == pid) & (p_matches['loser_rank'].fillna(9999) <= 100)].copy()
        if not top100_win_rows.empty:
            t100_first = top100_win_rows.sort_values('tourney_date_dt').iloc[0]
            first_top100_win_date = str(t100_first['tourney_date_dt'].date()) if pd.notna(t100_first['tourney_date_dt']) else None
        else:
            first_top100_win_date = None
        # titles (finals won)
        finals_won = p_matches[(p_matches['round'] == 'F') & (p_matches['winner_id'].astype(str) == pid)]
        titles_total = len(finals_won)
        titles_by_level = finals_won.groupby('tourney_level').size().to_dict() if not finals_won.empty else {}
        # career length precise
        career_start = p_matches['tourney_date_dt'].min()
        career_end = p_matches['tourney_date_dt'].max()
        career_length_years = round(((career_end - career_start).days / 365.25), 2) if pd.notna(career_start) and pd.notna(career_end) else None

        milestones.append({
            'id': pid,
            'name': players_summary[[p['id'] for p in players_summary].index(pid)]['name'] if pid in [p['id'] for p in players_summary] else None,
            'first_match_date': first_match_date,
            'age_at_first_match': round(age_first,2) if age_first is not None and not pd.isna(age_first) else None,
            'first_grand_slam_date': first_gs_date,
            'first_top100_win_date': first_top100_win_date,
            'titles_total': int(titles_total),
            'titles_by_level': {k: int(v) for k, v in titles_by_level.items()},
            'career_length_years': career_length_years
        })

    with open(f"{output_dir}/player_milestones.json", 'w') as f:
        json.dump(milestones, f, indent=2)
    print(f"✓ Saved: player_milestones.json ({len(milestones)} players)")

    # Head-to-head vs top50 opponents (match-level top-ranked opponents at time of match)
    h2h_top50 = []
    for pid in player_ids:
        p_matches = country_matches[(country_matches['winner_id'].astype(str) == pid) | (country_matches['loser_id'].astype(str) == pid)].copy()
        if p_matches.empty:
            continue
        # opponent rank at match
        p_matches['opp_rank'] = p_matches.apply(lambda r: r['loser_rank'] if str(r['winner_id']) == pid else r['winner_rank'], axis=1).fillna(9999)
        top50_matches = p_matches[p_matches['opp_rank'] <= 50]
        top50_total = len(top50_matches)
        top50_wins = len(top50_matches[(top50_matches['winner_id'].astype(str) == pid)])
        top50_losses = len(top50_matches[(top50_matches['loser_id'].astype(str) == pid)])
        # notable upsets vs top10
        upsets = top50_matches[(top50_matches['winner_id'].astype(str) == pid) & (top50_matches['opp_rank'] <= 10)].copy()
        upsets_list = []
        for _, u in upsets.sort_values('tourney_date').iterrows():
            upsets_list.append({'date': str(u['tourney_date']), 'opponent': u['loser_name'] if str(u['winner_id']) == pid else u['winner_name'], 'opponent_rank': int(u['opp_rank']), 'tournament': u['tourney_name'], 'round': u['round'], 'score': u['score']})

        h2h_top50.append({
            'id': pid,
            'name': next((p['name'] for p in players_summary if p['id'] == pid), None),
            'top50_matches': int(top50_total),
            'top50_wins': int(top50_wins),
            'top50_losses': int(top50_losses),
            'notable_upsets_vs_top10': upsets_list
        })

    with open(f"{output_dir}/head_to_head_top50.json", 'w') as f:
        json.dump(h2h_top50, f, indent=2)
    print(f"✓ Saved: head_to_head_top50.json ({len(h2h_top50)} players)")

    # Surface performance per player
    surface_perf = []
    surfaces = ['Hard','Clay','Grass']
    for pid in player_ids:
        wins = df[(df['winner_id'].astype(str) == pid)].groupby('surface').size().to_dict()
        matches = df[(df['winner_id'].astype(str) == pid) | (df['loser_id'].astype(str) == pid)].groupby('surface').size().to_dict()
        perf = {'id': pid, 'name': next((p['name'] for p in players_summary if p['id'] == pid), None), 'surface_stats': {}}
        for s in surfaces:
            w = int(wins.get(s, 0))
            m = int(matches.get(s, 0))
            perf['surface_stats'][s] = {'wins': w, 'matches': m, 'win_pct': round((w / m * 100) if m>0 else 0, 2)}
        surface_perf.append(perf)

    with open(f"{output_dir}/surface_performance_by_player.json", 'w') as f:
        json.dump(surface_perf, f, indent=2)
    print(f"✓ Saved: surface_performance_by_player.json ({len(surface_perf)} players)")

    # Yearly best rank trajectory for each player (best rank observed per year from appearances)
    rank_traj = []
    app_with_rank = appearances[appearances['rank'].notna()].copy()
    if not app_with_rank.empty:
        best_rank_year = app_with_rank.groupby(['id','year'])['rank'].min().reset_index()
        for pid in player_ids:
            pr = best_rank_year[best_rank_year['id']==pid]
            traj = [{'year': int(r['year']), 'best_rank': int(r['rank'])} for _, r in pr.sort_values('year').iterrows()]
            rank_traj.append({'id': pid, 'name': next((p['name'] for p in players_summary if p['id'] == pid), None), 'rank_trajectory': traj})

    with open(f"{output_dir}/player_yearly_rank.json", 'w') as f:
        json.dump(rank_traj, f, indent=2)
    print(f"✓ Saved: player_yearly_rank.json ({len(rank_traj)} players)")

    # Career lengths for Indian players (precision using dates)
    career_lengths = []
    for pid in player_ids:
        p_matches = df[(df['winner_id'].astype(str) == pid) | (df['loser_id'].astype(str) == pid)].copy()
        if p_matches.empty:
            continue
        p_matches['tourney_date_dt'] = pd.to_datetime(p_matches['tourney_date'].astype(str), format='%Y%m%d', errors='coerce')
        start = p_matches['tourney_date_dt'].min(); end = p_matches['tourney_date_dt'].max()
        length_years = round(((end - start).days/365.25), 2) if pd.notna(start) and pd.notna(end) else None
        career_lengths.append({'id': pid, 'name': next((p['name'] for p in players_summary if p['id'] == pid), None), 'career_start': str(start.date()) if pd.notna(start) else None, 'career_end': str(end.date()) if pd.notna(end) else None, 'career_length_years': length_years})

    with open(f"{output_dir}/career_lengths_indian.json", 'w') as f:
        json.dump(career_lengths, f, indent=2)
    print(f"✓ Saved: career_lengths_indian.json ({len(career_lengths)} players)")

    # --- Create 1990-limited subset files for backward compatibility with older visualizations ---
    df_1990 = df_all[df_all['year'] >= 1990].copy()
    country_matches_1990 = df_1990[(df_1990['winner_ioc'] == country_code) | (df_1990['loser_ioc'] == country_code)].copy()

    # Build appearances and players summary for 1990+ window
    winners_90 = country_matches_1990.loc[country_matches_1990['winner_ioc'] == country_code, ['winner_id', 'winner_name', 'year', 'round', 'tourney_name', 'winner_rank']].rename(columns={'winner_id': 'id', 'winner_name': 'name', 'winner_rank': 'rank'})
    losers_90 = country_matches_1990.loc[country_matches_1990['loser_ioc'] == country_code, ['loser_id', 'loser_name', 'year', 'round', 'tourney_name', 'loser_rank']].rename(columns={'loser_id': 'id', 'loser_name': 'name', 'loser_rank': 'rank'})
    appearances_90 = pd.concat([winners_90, losers_90], ignore_index=True)
    appearances_90['id'] = appearances_90['id'].astype(str)

    player_ids_90 = appearances_90['id'].unique().tolist()

    # minimal fields: years, matches_played, wins, losses, best_rank
    match_counts_90 = appearances_90.groupby('id').size().reset_index(name='matches_played')
    wins_90 = country_matches_1990[country_matches_1990['winner_ioc'] == country_code].copy()
    wins_count_90 = wins_90.groupby(wins_90['winner_id'].astype(str)).size().reset_index(name='wins').rename(columns={'winner_id':'id'})
    losses_90 = country_matches_1990[country_matches_1990['loser_ioc'] == country_code].copy()
    losses_count_90 = losses_90.groupby(losses_90['loser_id'].astype(str)).size().reset_index(name='losses').rename(columns={'loser_id':'id'})

    best_ranks_90 = appearances_90.groupby('id')['rank'].min().reset_index().rename(columns={'rank':'best_rank'})

    players_90 = pd.DataFrame({'id': player_ids_90})
    players_90 = players_90.merge(match_counts_90, on='id', how='left')
    players_90 = players_90.merge(wins_count_90, on='id', how='left')
    players_90 = players_90.merge(losses_count_90, on='id', how='left')
    players_90 = players_90.merge(best_ranks_90, on='id', how='left')
    players_90['wins'] = players_90['wins'].fillna(0).astype(int)
    players_90['losses'] = players_90['losses'].fillna(0).astype(int)
    players_90['matches_played'] = players_90['matches_played'].fillna(0).astype(int)
    players_90['best_rank'] = players_90['best_rank'].apply(lambda x: int(x) if pd.notna(x) and x < 9999 else None)

    players_summary_90 = []
    # For display name prefer most common name in appearances_90
    name_map_90 = appearances_90.groupby('id')['name'].agg(lambda x: x.mode().iat[0] if not x.mode().empty else None).to_dict()
    years_by_player_90 = appearances_90.groupby('id')['year'].apply(lambda x: sorted(set(x))).to_dict()

    for pid in players_90['id'].tolist():
        p = players_90[players_90['id'] == pid].iloc[0]
        years_list = years_by_player_90.get(pid, [])
        players_summary_90.append({
            'id': pid,
            'name': name_map_90.get(pid),
            'years': years_list,
            'years_played': int(len(years_list)),
            'min_year': int(min(years_list)) if years_list else None,
            'max_year': int(max(years_list)) if years_list else None,
            'matches_played': int(p['matches_played']),
            'wins': int(p['wins']),
            'losses': int(p['losses']),
            'win_pct': round((p['wins'] / p['matches_played'] * 100) if p['matches_played']>0 else 0, 2),
            'best_rank': p['best_rank']
        })

    with open(f"{output_dir}/players_summary_1990.json", 'w') as f:
        json.dump(players_summary_90, f, indent=2)
    print(f"✓ Saved: players_summary_1990.json ({len(players_summary_90)} players)")

    # players_time_series_1990
    years_1990 = sorted(df_1990['year'].unique().tolist())
    ts_90 = []
    for y in years_1990:
        country_players = country_matches_1990[country_matches_1990['year'] == y]
        country_unique = pd.concat([country_players['winner_id'], country_players['loser_id']]).astype(str).nunique()
        global_players = pd.concat([df_1990[df_1990['year'] == y]['winner_id'], df_1990[df_1990['year'] == y]['loser_id']]).astype(str).nunique()
        ts_90.append({'year': int(y), 'country_unique_players': int(country_unique), 'global_unique_players': int(global_players), 'ratio': round(country_unique / global_players if global_players>0 else 0, 4)})

    with open(f"{output_dir}/players_time_series_1990.json", 'w') as f:
        json.dump(ts_90, f, indent=2)
    print(f"✓ Saved: players_time_series_1990.json ({len(ts_90)} years)")

    # indian matches 1990
    matches_sample_90 = country_matches_1990.sort_values(['tourney_date']).loc[:, ['tourney_date','tourney_name','tourney_level','surface','round','winner_name','loser_name','score','winner_rank','loser_rank','minutes']].copy()
    matches_sample_90['tourney_date'] = matches_sample_90['tourney_date'].astype(str)
    sample_records_90 = matches_sample_90.to_dict('records')
    with open(f"{output_dir}/indian_matches_1990.json", 'w') as f:
        json.dump(sample_records_90, f, indent=2)
    print(f"✓ Saved: indian_matches_1990.json ({len(sample_records_90)} matches)")

    notable_90 = sorted(players_summary_90, key=lambda x: x['matches_played'], reverse=True)[:20]
    with open(f"{output_dir}/notable_players_1990.json", 'w') as f:
        json.dump(notable_90, f, indent=2)
    print(f"✓ Saved: notable_players_1990.json ({len(notable_90)} players)")

    print("\nIndian Players aggregation complete")


if __name__ == '__main__':
    generate_indian_datasets()
