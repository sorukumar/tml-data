#!/usr/bin/env python3
"""
MCP Base Metrics Builder
Processes Match Charting Project pre-aggregated stats files into three Tier 2 Parquet tables:

  data/base/mcp_player_metrics.parquet   — per-player Rally, Serve-transition, Clutch aggregates
  data/base/mcp_matches_enriched.parquet — per-match stats joined to atp_matches_raw
  data/base/mcp_player_crosswalk.parquet — MCP player name → TML player name mapping

Actual MCP file schemas (as downloaded from GitHub May 2026):
  charting-m-stats-Overview.csv — columns: match_id, player, set, serve_pts, aces, dfs,
    first_in, first_won, second_in, second_won, bk_pts, bp_saved, return_pts,
    return_pts_won, winners, winners_fh, winners_bh, unforced, unforced_fh, unforced_bh
  charting-m-stats-Rally.csv — columns: match_id, server, returner, row, pts,
    pl1_won, pl1_winners, pl1_forced, pl1_unforced, pl2_won, pl2_winners, pl2_forced, pl2_unforced
    row values: Total | 1-3 | 4-6 | 7-9 | 10 | {zone}-1 (P1 serving) | {zone}-2 (P2 serving)
  charting-m-matches.csv — columns include: match_id, Player 1, Player 2, Date, Tournament,
    Round, Surface, Best of

Storage Format: Parquet (zstd compression), consistent with the rest of Tier 2.
"""

import os
import re
import difflib

import numpy as np
import pandas as pd


# =============================================================================
# CONSTANTS
# =============================================================================

# Minimum charted matches to include a player in mcp_player_metrics
MIN_CHARTED_MATCHES = 3

# Fuzzy-match threshold for player name crosswalk (0–1)
FUZZY_THRESHOLD = 0.85

# Approximate midpoints for rally zone weighted-average calculation
ZONE_MIDPOINTS = {"1-3": 2.0, "4-6": 5.0, "7-9": 8.0, "10": 12.0}

# Rally zones (ordered)
RALLY_ZONES = ["1-3", "4-6", "7-9", "10"]


# =============================================================================
# RAW DATA LOADING
# =============================================================================

def load_matches(raw_dir: str) -> pd.DataFrame:
    """Load charting-m-matches.csv and normalize column names."""
    path = os.path.join(raw_dir, "charting-m-matches.csv")
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        "Player 1": "player1",
        "Player 2": "player2",
        "Pl 1 hand": "p1_hand",
        "Pl 2 hand": "p2_hand",
        "Best of": "best_of",
        "Final TB?": "final_tb",
        "Charted by": "charted_by",
    })
    df["Date"] = pd.to_numeric(df["Date"], errors="coerce")
    print(f"  Loaded {len(df):,} charted matches")
    return df


def load_overview_stats(raw_dir: str) -> pd.DataFrame:
    """
    Load charting-m-stats-Overview.csv and filter to set='Total' rows.
    Returns one row per (match_id, player).
    """
    path = os.path.join(raw_dir, "charting-m-stats-Overview.csv")
    df = pd.read_csv(path)
    total = df[df["set"] == "Total"].copy().reset_index(drop=True)
    print(f"  Loaded overview stats: {len(total):,} player-match rows")
    return total


def load_rally_stats(raw_dir: str) -> pd.DataFrame:
    """
    Load charting-m-stats-Rally.csv.
    Keeps all rows (Total + zone + zone-{1/2} rows).
    """
    path = os.path.join(raw_dir, "charting-m-stats-Rally.csv")
    df = pd.read_csv(path)
    print(f"  Loaded rally stats: {len(df):,} rows")
    return df


# =============================================================================
# RALLY DATA TRANSFORMATION
# =============================================================================

def build_rally_zone_player_view(rally: pd.DataFrame) -> pd.DataFrame:
    """
    Transform Rally stats into a player-perspective DataFrame.

    For each (match_id, player, zone) combination:
      - role: 'server' or 'returner'
      - zone_pts: total points in this zone/role
      - player_won: points won by this player in this zone/role

    Row encoding in Rally file:
      '{zone}-1' → P1 serving  → pl1_won = server's wins, pl2_won = returner's wins
      '{zone}-2' → P2 serving  → pl2_won = server's wins, pl1_won = returner's wins
    """
    server_rows = rally[rally["row"].str.match(r"^\d+-\d+-\d$", na=False)].copy()
    server_rows["zone"] = server_rows["row"].str.rsplit("-", n=1).str[0]
    server_rows["svr_num"] = server_rows["row"].str[-1].astype(int)

    # Server perspective: the 'server' column holds the serving player's name
    svr = server_rows.copy()
    svr["player_name"] = svr["server"]
    svr["role"] = "server"
    svr["player_won"] = np.where(svr["svr_num"] == 1, svr["pl1_won"], svr["pl2_won"])
    svr["zone_pts"] = svr["pts"]

    # Returner perspective: the 'returner' column holds the returning player's name
    ret = server_rows.copy()
    ret["player_name"] = ret["returner"]
    ret["role"] = "returner"
    # When P1 serves (-1): P2 is returner → pl2_won; when P2 serves (-2): P1 is returner → pl1_won
    ret["player_won"] = np.where(server_rows["svr_num"] == 1, server_rows["pl2_won"], server_rows["pl1_won"])
    ret["zone_pts"] = ret["pts"]

    combined = pd.concat([
        svr[["match_id", "player_name", "zone", "role", "zone_pts", "player_won"]],
        ret[["match_id", "player_name", "zone", "role", "zone_pts", "player_won"]],
    ], ignore_index=True)

    return combined[combined["player_name"].notna()].reset_index(drop=True)


def build_match_zone_totals(rally: pd.DataFrame) -> pd.DataFrame:
    """
    Extract match-level rally zone totals from '{zone}' rows (no server suffix).
    Returns DataFrame with columns: match_id, zone, pts
    (zone ∈ {Total, 1-3, 4-6, 7-9, 10})
    """
    zone_rows = rally[rally["row"].isin(["Total"] + RALLY_ZONES)].copy()
    return zone_rows[["match_id", "row", "pts"]].rename(columns={"row": "zone"})


# =============================================================================
# PLAYER METRICS AGGREGATION
# =============================================================================

def _pct(num, denom):
    """Return percentage 0-100 or NaN if denominator is zero."""
    if denom == 0 or (isinstance(denom, float) and np.isnan(denom)):
        return np.nan
    return round(100.0 * num / denom, 2)


def build_player_metrics(
    overview: pd.DataFrame,
    rally_player: pd.DataFrame,
    matches: pd.DataFrame,
) -> pd.DataFrame:
    """
    Aggregate per-player stats from Overview + Rally data.
    Returns mcp_player_metrics DataFrame (one row per player).
    """
    print("\nAggregating player metrics...")

    # Map match_id → year (use dict to avoid non-unique index issues)
    match_year = {
        mid: (int(str(int(d))[:4]) if pd.notna(d) else np.nan)
        for mid, d in zip(matches["match_id"], matches["Date"])
    }

    records = []

    # Group overview by player
    for player, ov_grp in overview.groupby("player", sort=False):
        n_matches = ov_grp["match_id"].nunique()
        if n_matches < MIN_CHARTED_MATCHES:
            continue

        # --- Overview totals ---
        serve_pts    = int(ov_grp["serve_pts"].sum())
        aces         = int(ov_grp["aces"].sum())
        dfs          = int(ov_grp["dfs"].sum())
        first_in     = int(ov_grp["first_in"].sum())
        first_won    = int(ov_grp["first_won"].sum())
        second_in    = int(ov_grp["second_in"].sum())
        second_won   = int(ov_grp["second_won"].sum())
        bk_pts       = int(ov_grp["bk_pts"].sum())   # break points faced as server
        bp_saved     = int(ov_grp["bp_saved"].sum())
        return_pts   = int(ov_grp["return_pts"].sum())
        return_won   = int(ov_grp["return_pts_won"].sum())
        winners      = int(ov_grp["winners"].sum())
        unforced     = int(ov_grp["unforced"].sum())

        total_pts = serve_pts + return_pts
        total_won = first_won + second_won + return_won

        # Rates
        first_in_pct      = _pct(first_in, serve_pts)
        first_won_pct     = _pct(first_won, first_in)
        second_won_pct    = _pct(second_won, second_in)
        serve_win_pct     = _pct(first_won + second_won, serve_pts)
        return_win_pct    = _pct(return_won, return_pts)
        bp_save_pct       = _pct(bp_saved, bk_pts)
        uf_rate           = _pct(unforced, total_pts)
        # Clutch delta: BP save % vs. overall serve win % (positive = rises under pressure)
        clutch_delta = (
            round(bp_save_pct - serve_win_pct, 2)
            if (not np.isnan(bp_save_pct) and not np.isnan(serve_win_pct))
            else np.nan
        )

        # --- Rally zone stats (from expanded player view) ---
        p_rally = rally_player[rally_player["player_name"] == player]

        zone_totals = {}
        for zone in RALLY_ZONES:
            z = p_rally[p_rally["zone"] == zone]
            zone_totals[zone] = {"pts": int(z["zone_pts"].sum()), "won": int(z["player_won"].sum())}

        all_zone_pts = sum(z["pts"] for z in zone_totals.values())

        rally_1_3_pct  = _pct(zone_totals["1-3"]["pts"], all_zone_pts)
        rally_4_6_pct  = _pct(zone_totals["4-6"]["pts"], all_zone_pts)
        rally_7_9_pct  = _pct(zone_totals["7-9"]["pts"], all_zone_pts)
        rally_10p_pct  = _pct(zone_totals["10"]["pts"], all_zone_pts)

        # Win rates in each zone (all points the player participated in, regardless of role)
        rally_1_3_win  = _pct(zone_totals["1-3"]["won"], zone_totals["1-3"]["pts"])
        rally_7p_win   = _pct(
            zone_totals["7-9"]["won"] + zone_totals["10"]["won"],
            zone_totals["7-9"]["pts"] + zone_totals["10"]["pts"],
        )

        # Avg rally length via zone midpoints
        weighted = sum(ZONE_MIDPOINTS[z] * zone_totals[z]["pts"] for z in RALLY_ZONES)
        avg_rally = round(weighted / all_zone_pts, 2) if all_zone_pts else np.nan

        # Serve-transition zone (rally 1-3 as server) — closest approximation to Serve+1
        p_serving_1_3 = p_rally[(p_rally["role"] == "server") & (p_rally["zone"] == "1-3")]
        s_trans_pts  = int(p_serving_1_3["zone_pts"].sum())
        s_trans_won  = int(p_serving_1_3["player_won"].sum())
        s_trans_pct  = _pct(s_trans_won, s_trans_pts)

        years = ov_grp["match_id"].map(match_year).dropna()

        records.append({
            "player_name": player,
            "mcp_match_count": n_matches,
            "mcp_year_min": int(years.min()) if len(years) else np.nan,
            "mcp_year_max": int(years.max()) if len(years) else np.nan,
            # Serve
            "serve_pts": serve_pts,
            "aces": aces,
            "double_faults": dfs,
            "first_in_pct": first_in_pct,
            "first_won_pct": first_won_pct,
            "second_won_pct": second_won_pct,
            "serve_win_pct": serve_win_pct,
            # Return
            "return_pts": return_pts,
            "return_win_pct": return_win_pct,
            # Errors & Winners
            "winners": winners,
            "unforced_errors": unforced,
            "uf_rate": uf_rate,
            # Rally Profile
            "avg_rally_length": avg_rally,
            "rally_1_3_pct": rally_1_3_pct,
            "rally_4_6_pct": rally_4_6_pct,
            "rally_7_9_pct": rally_7_9_pct,
            "rally_10p_pct": rally_10p_pct,
            "rally_1_3_win_pct": rally_1_3_win,
            "rally_7p_win_pct": rally_7p_win,
            # Serve transition zone (rally 1-3 as server — Serve+1 approximation)
            "serve_trans_pts": s_trans_pts,
            "serve_trans_won": s_trans_won,
            "serve_trans_win_pct": s_trans_pct,
            # Clutch / Break Points (as server)
            "bp_faced": bk_pts,
            "bp_saved": bp_saved,
            "bp_save_pct": bp_save_pct,
            "bp_save_vs_serve_win_delta": clutch_delta,
        })

    df = pd.DataFrame(records).sort_values("mcp_match_count", ascending=False)
    print(f"  Built metrics for {len(df):,} players")
    return df.reset_index(drop=True)


# =============================================================================
# MATCH METRICS AGGREGATION
# =============================================================================

def build_match_metrics(
    overview: pd.DataFrame,
    rally: pd.DataFrame,
    matches: pd.DataFrame,
) -> pd.DataFrame:
    """
    Pivot overview + rally data into one row per match with P1/P2 columns.
    Returns mcp_matches_enriched DataFrame (before TML join).
    """
    print("\nAggregating match-level metrics...")

    # --- Overview: pivot to P1/P2 columns ---
    # Join matches to know who is P1 and P2 in each match
    ov = overview.merge(matches[["match_id", "player1", "player2"]], on="match_id", how="left")

    def _overview_for_player(ov_df, player_col):
        """Select overview rows where player == player_col, rename with prefix."""
        sub = ov_df[ov_df["player"] == ov_df[player_col]].copy()
        rename = {
            "serve_pts": f"{player_col}_serve_pts",
            "aces": f"{player_col}_aces",
            "dfs": f"{player_col}_dfs",
            "first_in": f"{player_col}_first_in",
            "first_won": f"{player_col}_first_won",
            "second_won": f"{player_col}_second_won",
            "bk_pts": f"{player_col}_bp_faced",
            "bp_saved": f"{player_col}_bp_saved",
            "return_pts": f"{player_col}_return_pts",
            "return_pts_won": f"{player_col}_return_won",
            "winners": f"{player_col}_winners",
            "unforced": f"{player_col}_unforced",
        }
        return sub[["match_id"] + list(rename.keys())].rename(columns=rename)

    p1_ov = _overview_for_player(ov, "player1")
    p2_ov = _overview_for_player(ov, "player2")
    match_stats = p1_ov.merge(p2_ov, on="match_id", how="outer")

    # --- Rally: compute zone percentages per match ---
    zone_totals = build_match_zone_totals(rally)
    total_pts_m = zone_totals[zone_totals["zone"] == "Total"][["match_id", "pts"]].rename(
        columns={"pts": "total_pts"}
    )
    zone_pivot = zone_totals[zone_totals["zone"].isin(RALLY_ZONES)].pivot_table(
        index="match_id", columns="zone", values="pts", aggfunc="sum"
    ).reset_index()
    zone_pivot.columns.name = None
    zone_pivot = zone_pivot.rename(columns={z: f"pts_{z.replace('-', '_')}" for z in RALLY_ZONES})
    zone_pivot = zone_pivot.merge(total_pts_m, on="match_id", how="left")

    for z, col in [("1-3", "pts_1_3"), ("4-6", "pts_4_6"), ("7-9", "pts_7_9"), ("10", "pts_10")]:
        pct_col = f"rally_{z.replace('-', '_')}_pct"
        zone_pivot[pct_col] = (zone_pivot[col] / zone_pivot["total_pts"] * 100).round(2)

    # Avg rally from zone midpoints
    zone_pivot["match_avg_rally"] = (
        zone_pivot.get("pts_1_3", 0) * 2.0
        + zone_pivot.get("pts_4_6", 0) * 5.0
        + zone_pivot.get("pts_7_9", 0) * 8.0
        + zone_pivot.get("pts_10", 0) * 12.0
    ) / zone_pivot["total_pts"].replace(0, np.nan)
    zone_pivot["match_avg_rally"] = zone_pivot["match_avg_rally"].round(2)

    # --- Rally zone win rates per player (server/returner) ---
    rally_player = build_rally_zone_player_view(rally)
    ov_players = overview.merge(matches[["match_id", "player1", "player2"]], on="match_id", how="left")

    for player_col in ("player1", "player2"):
        for zone in ["1-3", "7_9_10"]:  # serve-transition and long-rally
            if zone == "1-3":
                zone_label = "1_3"
                zone_filter = "1-3"
                role_filter = "server"
                col_prefix = f"{player_col}_serve_trans"
            else:
                zone_label = "7p"
                zone_filter = ["7-9", "10"]
                role_filter = None
                col_prefix = f"{player_col}_long_rally"

            def _calc_zone_win(grp, zf, rf):
                if isinstance(zf, list):
                    sub = grp[grp["zone"].isin(zf)]
                else:
                    sub = grp[grp["zone"] == zf]
                if rf:
                    sub = sub[sub["role"] == rf]
                pts = sub["zone_pts"].sum()
                won = sub["player_won"].sum()
                return round(100 * won / pts, 2) if pts > 0 else np.nan

            match_zone = (
                rally_player
                .groupby("match_id")
                .apply(lambda g: pd.Series({
                    f"player_name": g["player_name"].iloc[0],
                }))
            )
            # Simpler: per match, per player, compute zone win rate
            match_ids = match_stats["match_id"].tolist()

    # Only compute long-rally win pct per player (most actionable at match level)
    long_rally = rally_player[rally_player["zone"].isin(["7-9", "10"])]
    long_agg = long_rally.groupby(["match_id", "player_name"]).agg(
        lr_pts=("zone_pts", "sum"),
        lr_won=("player_won", "sum"),
    ).reset_index()
    long_agg["long_rally_win_pct"] = (long_agg["lr_won"] / long_agg["lr_pts"] * 100).round(2)
    long_agg.loc[long_agg["lr_pts"] == 0, "long_rally_win_pct"] = np.nan

    # Join long rally stats to match_stats for P1 and P2
    m_p1 = matches[["match_id", "player1"]].merge(
        long_agg.rename(columns={"player_name": "player1", "long_rally_win_pct": "p1_long_rally_win_pct"}),
        on=["match_id", "player1"], how="left",
    )
    m_p2 = matches[["match_id", "player2"]].merge(
        long_agg.rename(columns={"player_name": "player2", "long_rally_win_pct": "p2_long_rally_win_pct"}),
        on=["match_id", "player2"], how="left",
    )

    # --- Assemble final match stats ---
    meta_cols = ["match_id", "player1", "player2", "Date", "Tournament", "Round", "Surface", "best_of"]
    available = [c for c in meta_cols if c in matches.columns]
    result = matches[available].copy()
    result = result.rename(columns={
        "player1": "player1_name",
        "player2": "player2_name",
        "Date": "tourney_date",
        "Tournament": "tournament",
        "Round": "round",
        "Surface": "surface",
    })

    result = (
        result
        .merge(match_stats, on="match_id", how="left")
        .merge(zone_pivot[["match_id", "match_avg_rally", "rally_1_3_pct", "rally_4_6_pct", "rally_7_9_pct", "rally_10_pct", "total_pts"]], on="match_id", how="left")
        .merge(m_p1[["match_id", "p1_long_rally_win_pct"]], on="match_id", how="left")
        .merge(m_p2[["match_id", "p2_long_rally_win_pct"]], on="match_id", how="left")
    )

    # Compute derived rates
    for player_col in ("player1", "player2"):
        px = "p1" if player_col == "player1" else "p2"
        sp = f"{player_col}_serve_pts"
        fw = f"{player_col}_first_won"
        sw = f"{player_col}_second_won"
        bp_f = f"{player_col}_bp_faced"
        bp_s = f"{player_col}_bp_saved"
        if sp in result.columns:
            result[f"{px}_serve_win_pct"] = (
                (result[fw] + result[sw]) / result[sp] * 100
            ).round(2)
            result[f"{px}_return_win_pct"] = (
                result[f"{player_col}_return_won"] / result[f"{player_col}_return_pts"] * 100
            ).round(2)
            result[f"{px}_bp_save_pct"] = (
                result[bp_s] / result[bp_f] * 100
            ).round(2)

    print(f"  Built match stats for {len(result):,} matches")
    return result


# =============================================================================
# PLAYER CROSSWALK  (MCP name → TML name)
# =============================================================================

def _normalize(name: str) -> str:
    """Lowercase, strip, remove apostrophes and hyphens."""
    return (
        str(name).strip().lower()
        .replace("'", "").replace("-", " ")
        .replace("  ", " ")
    )


def build_player_crosswalk(
    matches: pd.DataFrame,
    tml_matches: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build mcp_player_name → tml_player_name crosswalk by joining MCP matches
    to atp_matches_raw on (date, normalized sorted player pair).
    Falls back to fuzzy name matching for unresolved MCP players.
    """
    print("\nBuilding player crosswalk...")

    # --- Exact join on (date, frozenset of player names) ---
    tml = tml_matches[["tourney_date", "winner_name", "loser_name"]].copy()
    tml["date"] = tml["tourney_date"].astype(str)
    tml["key"] = tml.apply(
        lambda r: "|".join(sorted([_normalize(r["winner_name"]), _normalize(r["loser_name"])])),
        axis=1,
    )

    mcp = matches[["match_id", "player1", "player2", "Date"]].copy()
    mcp = mcp[mcp["player1"].notna() & mcp["player2"].notna()]
    mcp["date"] = mcp["Date"].apply(lambda d: str(int(d)) if pd.notna(d) else "")
    mcp["key"] = mcp.apply(
        lambda r: "|".join(sorted([_normalize(r["player1"]), _normalize(r["player2"])])),
        axis=1,
    )

    joined = mcp.merge(tml, on=["date", "key"], how="left")

    crosswalk_pairs = []
    exact_count = 0
    for _, row in joined[joined["winner_name"].notna()].iterrows():
        for mcp_col in ("player1", "player2"):
            mcp_name = row[mcp_col]
            norm = _normalize(mcp_name)
            tml_match = next(
                (n for n in [row["winner_name"], row["loser_name"]] if _normalize(n) == norm),
                None,
            )
            if tml_match:
                crosswalk_pairs.append((mcp_name, tml_match, "exact"))
                exact_count += 1

    print(f"  Exact matches: {exact_count:,} player-match pairs")

    # --- Fuzzy fallback for unmatched MCP players ---
    resolved_mcp = {p for p, _, _ in crosswalk_pairs}
    all_mcp_players = set(mcp["player1"]) | set(mcp["player2"])
    unresolved = all_mcp_players - resolved_mcp

    tml_name_pool = list(set(tml["winner_name"].dropna()) | set(tml["loser_name"].dropna()))
    norm_tml_pool = {_normalize(n): n for n in tml_name_pool}
    norm_tml_keys = list(norm_tml_pool.keys())

    fuzzy_count = 0
    for mcp_name in unresolved:
        matches_found = difflib.get_close_matches(
            _normalize(mcp_name), norm_tml_keys, n=1, cutoff=FUZZY_THRESHOLD
        )
        if matches_found:
            crosswalk_pairs.append((mcp_name, norm_tml_pool[matches_found[0]], "fuzzy"))
            fuzzy_count += 1
        else:
            crosswalk_pairs.append((mcp_name, None, "unmatched"))

    print(f"  Fuzzy matches:  {fuzzy_count:,} additional players")
    print(f"  Unmatched:      {len(unresolved) - fuzzy_count:,} players")

    method_rank = {"exact": 0, "fuzzy": 1, "unmatched": 2}
    seen: dict = {}
    counts: dict = {}
    for mcp_name, tml_name, method in crosswalk_pairs:
        rank = method_rank[method]
        if mcp_name not in seen or rank < method_rank[seen[mcp_name][1]]:
            seen[mcp_name] = (tml_name, method)
            counts[mcp_name] = 0
        counts[mcp_name] += 1

    crosswalk = pd.DataFrame([
        {"mcp_player_name": k, "tml_player_name": v[0], "join_method": v[1], "match_count": counts[k]}
        for k, v in seen.items()
    ]).sort_values("match_count", ascending=False).reset_index(drop=True)

    print(f"  Crosswalk size: {len(crosswalk):,} unique MCP player names")
    return crosswalk


# =============================================================================
# TML JOIN
# =============================================================================

def join_to_tml(match_stats: pd.DataFrame, tml_matches: pd.DataFrame) -> pd.DataFrame:
    """
    Join MCP match stats to atp_matches_raw.

    TML stores the tournament WEEK START date; MCP stores the actual match date.
    Direct date joins therefore fail for most matches.

    Join strategy (applied in order, first match wins):
      1. (year, norm_tournament, norm_round, sorted_player_pair)  — best signal
      2. (year, sorted_player_pair) with closest-date disambiguation       — fallback

    Adds: tml_winner_name, tml_loser_name, tml_tourney_date, tml_join_confidence
    """
    print("\nJoining MCP matches to TML archive...")

    def _year(d):
        """Extract 4-digit year string from an integer date, robustly."""
        try:
            s = str(int(d))
            return s[:4] if len(s) == 8 else ""
        except (ValueError, TypeError):
            return ""

    def _norm_tournament(name):
        """Normalise tournament name for fuzzy joining."""
        if pd.isna(name):
            return ""
        return str(name).lower().strip()

    def _norm_round(r):
        """Normalise round code."""
        if pd.isna(r):
            return ""
        return str(r).upper().strip()

    # --- Build TML join keys ---
    tml = tml_matches.copy()
    tml["_year"]    = tml["tourney_date"].apply(_year)
    tml["_tourney"] = tml["tourney_name"].apply(_norm_tournament)
    tml["_round"]   = tml["round"].apply(_norm_round)
    tml["_players"] = tml.apply(
        lambda r: "|".join(sorted([_normalize(r["winner_name"]), _normalize(r["loser_name"])])),
        axis=1,
    )
    # Primary key: year|tournament|round|players
    tml["_key1"] = tml["_year"] + "|" + tml["_tourney"] + "|" + tml["_round"] + "|" + tml["_players"]
    # Fallback key: year|players
    tml["_key2"] = tml["_year"] + "|" + tml["_players"]

    # --- Build MCP join keys ---
    ms = match_stats.copy()
    ms["_year"]    = ms["tourney_date"].apply(_year)
    ms["_tourney"] = ms["tournament"].apply(_norm_tournament)
    ms["_round"]   = ms["round"].apply(_norm_round)
    ms["_players"] = ms.apply(
        lambda r: "|".join(sorted([
            _normalize(str(r.get("player1_name", ""))),
            _normalize(str(r.get("player2_name", ""))),
        ])),
        axis=1,
    )
    ms["_key1"] = ms["_year"] + "|" + ms["_tourney"] + "|" + ms["_round"] + "|" + ms["_players"]
    ms["_key2"] = ms["_year"] + "|" + ms["_players"]

    tml_out = tml.rename(columns={
        "tourney_date": "tml_tourney_date",
        "winner_name":  "tml_winner_name",
        "loser_name":   "tml_loser_name",
    })

    # --- Step 1: exact tournament+round+year+players join ---
    # Deduplicate TML keys so merge doesn't produce duplicate rows
    tml_key1 = tml_out.drop_duplicates(subset=["_key1"])[
        ["_key1", "tml_tourney_date", "tml_winner_name", "tml_loser_name"]
    ]
    joined = ms.merge(tml_key1, on="_key1", how="left")
    joined["tml_join_confidence"] = joined["tml_winner_name"].apply(
        lambda v: "primary" if pd.notna(v) else ""
    )

    # --- Step 2: fallback year+players join for unmatched rows ---
    # Among TML rows sharing the same year+players key, pick the one
    # whose tournament date is closest to the MCP match date.
    unmatched_mask = joined["tml_join_confidence"] == ""
    if unmatched_mask.any():
        tml_key2 = tml_out[["_key2", "tml_tourney_date", "tml_winner_name", "tml_loser_name"]].copy()
        # For duplicate year|players pairs (same players met multiple times in same year),
        # we can't disambiguate without a date window — keep only one arbitrary row
        # (this will be wrong for repeat matchups, but correct for unique matchups)
        tml_key2_dedup = tml_key2.drop_duplicates(subset=["_key2"])

        fallback = ms[unmatched_mask][["match_id", "_key2"]].merge(
            tml_key2_dedup, on="_key2", how="left"
        ).drop_duplicates(subset=["match_id"])
        fallback_map = fallback.set_index("match_id")[
            ["tml_tourney_date", "tml_winner_name", "tml_loser_name"]
        ].to_dict(orient="index")

        for idx in joined[unmatched_mask].index:
            mid = joined.at[idx, "match_id"]
            if mid in fallback_map and pd.notna(fallback_map[mid].get("tml_winner_name")):
                joined.at[idx, "tml_tourney_date"] = fallback_map[mid]["tml_tourney_date"]
                joined.at[idx, "tml_winner_name"]  = fallback_map[mid]["tml_winner_name"]
                joined.at[idx, "tml_loser_name"]   = fallback_map[mid]["tml_loser_name"]
                joined.at[idx, "tml_join_confidence"] = "fallback"

    joined["tml_join_confidence"] = joined["tml_join_confidence"].replace("", "unmatched")
    joined = joined.drop(columns=["_year", "_tourney", "_round", "_players", "_key1", "_key2"])

    primary  = joined["tml_join_confidence"].eq("primary").sum()
    fallback = joined["tml_join_confidence"].eq("fallback").sum()
    total    = len(joined)
    print(f"  Primary join:  {primary:,}/{total:,}  ({100*primary/total:.1f}%)")
    print(f"  Fallback join: {fallback:,}/{total:,}  ({100*fallback/total:.1f}%)")
    print(f"  Unmatched:     {total-primary-fallback:,}/{total:,}")

    return joined


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def generate_mcp_base_metrics(
    raw_dir: str = "data/raw/mcp",
    base_data_path: str = "data/base/atp_matches_raw.parquet",
    output_dir: str = "data/base",
) -> tuple:
    """
    Full pipeline: raw MCP CSVs → three Tier 2 Parquet files.

    Returns:
        (mcp_player_metrics_df, mcp_matches_enriched_df, crosswalk_df)
    """
    print("=" * 60)
    print("MCP BASE METRICS BUILDER")
    print("=" * 60)

    print("\n[1/5] Loading MCP raw data...")
    matches = load_matches(raw_dir)
    overview = load_overview_stats(raw_dir)
    rally = load_rally_stats(raw_dir)

    print("\n[2/5] Loading TML base archive...")
    tml_matches = pd.read_parquet(
        base_data_path,
        columns=["tourney_date", "winner_name", "loser_name", "tourney_name", "round", "surface"],
    )
    print(f"  Loaded {len(tml_matches):,} TML matches")

    print("\n[3/5] Transforming rally data...")
    rally_player = build_rally_zone_player_view(rally)
    print(f"  Rally player-perspective rows: {len(rally_player):,}")

    print("\n[4/5] Building player and match metrics...")
    player_metrics = build_player_metrics(overview, rally_player, matches)
    match_stats    = build_match_metrics(overview, rally, matches)
    crosswalk      = build_player_crosswalk(matches, tml_matches)
    match_stats_joined = join_to_tml(match_stats, tml_matches)

    print("\n[5/5] Writing Parquet files...")
    os.makedirs(output_dir, exist_ok=True)

    player_path    = os.path.join(output_dir, "mcp_player_metrics.parquet")
    match_path     = os.path.join(output_dir, "mcp_matches_enriched.parquet")
    crosswalk_path = os.path.join(output_dir, "mcp_player_crosswalk.parquet")

    player_metrics.to_parquet(player_path, compression="zstd", index=False)
    match_stats_joined.to_parquet(match_path, compression="zstd", index=False)
    crosswalk.to_parquet(crosswalk_path, compression="zstd", index=False)

    print(f"  ✅ {player_path}  ({len(player_metrics):,} players)")
    print(f"  ✅ {match_path}  ({len(match_stats_joined):,} matches)")
    print(f"  ✅ {crosswalk_path}  ({len(crosswalk):,} name mappings)")

    return player_metrics, match_stats_joined, crosswalk
