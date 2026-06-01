"""
tennis-analytics MCP Server
============================
by sorukumar (https://sorukumar.github.io/tennis-analytics/)

Exposes ATP tennis data for AI-assisted analysis and visualization.

Data sources:
  - ATP match history: Tennis My Life (stats.tennismylife.org)
  - Point-by-point charting: Jeff Sackmann / Match Charting Project
    (github.com/JeffSackmann/tennis_MatchChartingProject) — CC BY-NC-SA 4.0

Usage (local stdio):
  python server.py
"""

import json
import os
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
# DATA_DIR is the tml-data/data/ folder, resolved relative to this file.
DATA_DIR = Path(__file__).parent.parent / "data"

# ---------------------------------------------------------------------------
# Server init
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "tennis-analytics",
    instructions=(
        "tennis-analytics MCP Server by sorukumar. "
        "Provides rich ATP tennis data for plotting and analysis. "
        "Data sources: Tennis My Life (stats.tennismylife.org) and "
        "Jeff Sackmann / Match Charting Project (CC BY-NC-SA 4.0). "
        "Use list_datasets() first to discover available data."
    ),
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(relative_path: str) -> object:
    """Load a JSON file from DATA_DIR. Raises FileNotFoundError if missing."""
    path = DATA_DIR / relative_path
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {relative_path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_csv_as_records(relative_path: str) -> list[dict]:
    """Load a CSV file from DATA_DIR as a list of row dicts."""
    import csv
    path = DATA_DIR / relative_path
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {relative_path}")
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Resources — static data blobs accessible by URI
# ---------------------------------------------------------------------------

@mcp.resource("tennis://attribution")
def attribution() -> str:
    """Attribution information for the tennis-analytics data sources."""
    return (
        "tennis-analytics MCP Server\n"
        "Created by: sorukumar\n"
        "Website: https://sorukumar.github.io/tennis-analytics/\n"
        "\n"
        "Data Sources\n"
        "------------\n"
        "1. ATP Match History\n"
        "   Source: Tennis My Life\n"
        "   URL: https://stats.tennismylife.org\n"
        "   Coverage: 198,063 ATP matches, 1968–2026\n"
        "\n"
        "2. Point-by-Point Match Charting\n"
        "   Source: Jeff Sackmann / Match Charting Project\n"
        "   URL: https://github.com/JeffSackmann/tennis_MatchChartingProject\n"
        "   License: CC BY-NC-SA 4.0\n"
        "   Note: Non-commercial use only. Attribution required.\n"
        "\n"
        "When using or publishing analysis from this server, please credit both "
        "Tennis My Life (TML) and Jeff Sackmann's Match Charting Project."
    )


@mcp.resource("tennis://greatness/race-to-greatness")
def greatness_race() -> str:
    """
    Career trajectory data for tennis legends (Djokovic, Federer, Nadal, Borg,
    Sampras, McEnroe, Lendl, Agassi, Alcaraz, Sinner).

    Schema: {players: {name: {trajectory: [{age, match_count, wins, titles,
    gs, masters, finals, big_titles, date}], milestones: [...],
    current_stats: {...}}}}
    """
    data = _load_json("greatness/race_to_greatness.json")
    return json.dumps(data)


@mcp.resource("tennis://greatness/young-guns")
def young_guns() -> str:
    """Young players career trajectory comparison data."""
    data = _load_json("greatness/young_guns_race.json")
    return json.dumps(data)


@mcp.resource("tennis://gsdi/rankings")
def gsdi_rankings() -> str:
    """
    Grand Slam Dominance Index rankings — the most dominant Grand Slam
    campaigns in the Open Era.

    Schema: [{rank, player, tournament, year, dominance_score, sets_won,
    sets_won_pct, games_won_pct, points_won_pct, pct_top30_opponents,
    speed_score, avg_match_minutes, top5_wins, perfect_campaign, ...}]
    """
    data = _load_json("gsdi/gs_dominance_rankings.json")
    return json.dumps(data)


@mcp.resource("tennis://nbi/nail-biters")
def nail_biters() -> str:
    """
    Nail-Biter Index — most dramatic Grand Slam matches (requires MCP charting data).

    Schema: [{match, tourney, round, date, score, duration, NBI, NBI_100,
    drama_tags, raw_stats: {avg_set_margin, tiebreak_count, lead_changes,
    comeback, bp_saved_ratio, bp_total}}]
    """
    data = _load_json("nbi/gs_nailbiters.json")
    return json.dumps(data)


@mcp.resource("tennis://nbi/iconic-matches")
def iconic_matches() -> str:
    """Iconic Grand Slam matches with detailed narrative context."""
    data = _load_json("nbi/iconic_gs_matches.json")
    return json.dumps(data)


@mcp.resource("tennis://network/rivalries")
def rivalries() -> str:
    """
    Tennis legends rivalry network (1968–present).
    Nodes are players, edges are head-to-head records with win/loss counts.
    """
    data = _load_json("network/tennis_legends_rivalries_1968.json")
    return json.dumps(data)


@mcp.resource("tennis://network/summary")
def network_summary() -> str:
    """Summary statistics for the tennis rivalry network."""
    data = _load_json("network/network_summary.json")
    return json.dumps(data)


@mcp.resource("tennis://globaltop100/timeline")
def global_timeline() -> str:
    """
    Global top-100 player evolution timeline — player rankings over decades,
    showing the rise and fall of nations in professional tennis.
    """
    data = _load_json("globaltop100evolution/top_tennis_players_timeline.json")
    return json.dumps(data)


@mcp.resource("tennis://globaltop100/country-profiles")
def country_profiles() -> str:
    """Country-level profiles for tennis dominance in the ATP top 100."""
    data = _load_json("globaltop100evolution/tennis_country_profiles.json")
    return json.dumps(data)


@mcp.resource("tennis://career/longest-careers")
def longest_careers() -> str:
    """
    Longest professional ATP careers — players ranked by career length
    and match volume.
    """
    data = _load_json("career_longevity/longest_careers.json")
    return json.dumps(data)


@mcp.resource("tennis://career/survival-curve")
def survival_curve() -> str:
    """
    Career survival curve — probability of still being active at each
    career age, across all ATP players since 1968.
    """
    data = _load_json("career_longevity/survival_curve.json")
    return json.dumps(data)


@mcp.resource("tennis://indian/players-summary")
def indian_players_summary() -> str:
    """
    Summary statistics for Indian ATP players — career stats, peak rankings,
    tournament participation, surface performance.
    """
    data = _load_json("indian/players_summary.json")
    return json.dumps(data)


@mcp.resource("tennis://base/metadata")
def base_metadata() -> str:
    """
    Metadata for the ATP match history base dataset.
    198,063 matches, 1968–2026, 50 columns.
    """
    data = _load_json("base/metadata.json")
    return json.dumps(data)


# ---------------------------------------------------------------------------
# Tools — query and filter operations
# ---------------------------------------------------------------------------

@mcp.tool()
def list_datasets() -> dict:
    """
    List all available tennis datasets in this server with their descriptions.

    Returns a catalogue of resource URIs and tool names you can use.
    """
    return {
        "resources": {
            "tennis://attribution": "Data source credits and licensing info",
            "tennis://greatness/race-to-greatness": "Career trajectories of tennis legends (age vs titles/GS/masters)",
            "tennis://greatness/young-guns": "Young player career trajectory comparisons",
            "tennis://gsdi/rankings": "Grand Slam Dominance Index — most dominant Slam campaigns",
            "tennis://nbi/nail-biters": "Nail-Biter Index — most dramatic Grand Slam matches",
            "tennis://nbi/iconic-matches": "Iconic Grand Slam matches with narrative context",
            "tennis://network/rivalries": "Tennis legends rivalry network (nodes=players, edges=H2H records)",
            "tennis://network/summary": "Network summary statistics",
            "tennis://globaltop100/timeline": "Global top-100 evolution timeline by country/decade",
            "tennis://globaltop100/country-profiles": "Country-level ATP top-100 dominance profiles",
            "tennis://career/longest-careers": "Longest ATP careers ranked by duration and match volume",
            "tennis://career/survival-curve": "Career survival probability curve across all players",
            "tennis://indian/players-summary": "Indian ATP players summary statistics",
            "tennis://base/metadata": "Base dataset metadata (198,063 matches, 1968–2026)",
        },
        "tools": {
            "list_datasets": "This tool — catalogue of all available data",
            "get_player_trajectory": "Get career trajectory for a specific player from the greatness dataset",
            "list_greatness_players": "List all players available in the race-to-greatness dataset",
            "get_gsdi_top_n": "Get top-N most dominant Grand Slam campaigns, optionally filtered by tournament",
            "get_top_nail_biters": "Get top-N most dramatic Grand Slam matches by Nail-Biter Index",
            "get_head_to_head": "Get head-to-head record between two players from the rivalry network",
            "get_indian_player_stats": "Get stats for a specific Indian ATP player",
            "get_country_tennis_history": "Get ATP top-100 history for a specific country",
            "suggest_visualization": "Get D3.js / Chart.js plotting suggestions for a dataset",
        },
        "data_coverage": {
            "matches": 198063,
            "years": "1968–2026",
            "sources": ["Tennis My Life (stats.tennismylife.org)", "Jeff Sackmann Match Charting Project (CC BY-NC-SA 4.0)"],
        },
    }


@mcp.tool()
def list_greatness_players() -> list[str]:
    """
    List all player names available in the race-to-greatness dataset.
    Use these names with get_player_trajectory().
    """
    data = _load_json("greatness/race_to_greatness.json")
    return sorted(data.get("players", {}).keys())


@mcp.tool()
def get_player_trajectory(player_name: str) -> dict:
    """
    Get the complete career trajectory for a specific tennis player.

    Returns age-by-age progression of match counts, wins, titles, Grand Slams,
    Masters titles, career milestones, and current stats.

    Args:
        player_name: Player name (use list_greatness_players() for valid names).
                     Case-insensitive partial match supported.

    Example: get_player_trajectory("Federer") or get_player_trajectory("Roger Federer")
    """
    data = _load_json("greatness/race_to_greatness.json")
    players = data.get("players", {})

    # Exact match first
    if player_name in players:
        return players[player_name]

    # Case-insensitive partial match
    name_lower = player_name.lower()
    matches = [k for k in players if name_lower in k.lower()]
    if len(matches) == 1:
        return players[matches[0]]
    elif len(matches) > 1:
        return {"error": f"Ambiguous name '{player_name}'. Matches: {matches}"}

    return {"error": f"Player '{player_name}' not found. Use list_greatness_players() to see available names."}


@mcp.tool()
def get_gsdi_top_n(n: int = 20, tournament: Optional[str] = None) -> list[dict]:
    """
    Get the top-N most dominant Grand Slam campaigns by Dominance Score.

    The Grand Slam Dominance Index (GSDI) combines sets won %, games won %,
    points won %, opponent quality, and match speed.

    Args:
        n: Number of results to return (default 20, max 100).
        tournament: Optional filter — one of: "Roland Garros", "Wimbledon",
                    "US Open", "Australian Open" (case-insensitive partial match).

    Returns list of campaigns sorted by dominance_score descending.
    """
    data = _load_json("gsdi/gs_dominance_rankings.json")
    if tournament:
        t_lower = tournament.lower()
        data = [d for d in data if t_lower in d.get("tournament", "").lower()]
    return data[:min(n, 100)]


@mcp.tool()
def get_top_nail_biters(n: int = 20) -> list[dict]:
    """
    Get the top-N most dramatic Grand Slam matches by Nail-Biter Index (NBI).

    NBI combines set margin tightness, tiebreak count, lead changes, comebacks,
    and break point drama. NBI_100 is normalized to 0–100.

    Args:
        n: Number of matches to return (default 20, max 200).

    Returns list sorted by NBI descending (1st = most dramatic ever recorded).
    """
    data = _load_json("nbi/gs_nailbiters.json")
    return data[:min(n, 200)]


@mcp.tool()
def get_head_to_head(player1: str, player2: str) -> dict:
    """
    Get the head-to-head rivalry record between two players.

    Args:
        player1: First player name (partial case-insensitive match supported).
        player2: Second player name (partial case-insensitive match supported).

    Returns edge data with win/loss counts, key matches, and rivalry stats.
    """
    data = _load_json("network/tennis_legends_rivalries_1968.json")

    p1_lower = player1.lower()
    p2_lower = player2.lower()

    # Search edges
    edges = data.get("edges", [])
    for edge in edges:
        source = edge.get("source", "").lower()
        target = edge.get("target", "").lower()
        if (p1_lower in source or p1_lower in target) and (
            p2_lower in source or p2_lower in target
        ):
            return edge

    # Fallback: list available nodes
    nodes = [n.get("id", "") for n in data.get("nodes", [])]
    return {
        "error": f"No rivalry found between '{player1}' and '{player2}'.",
        "available_players": nodes,
    }


@mcp.tool()
def get_indian_player_stats(player_name: Optional[str] = None) -> object:
    """
    Get stats for Indian ATP players.

    Args:
        player_name: Optional player name filter (partial match). If omitted,
                     returns summary for all tracked Indian players.

    Returns career stats, peak ranking, surface performance, and match history.
    """
    data = _load_json("indian/players_summary.json")

    if player_name is None:
        return data

    # Handle both list and dict formats
    if isinstance(data, list):
        name_lower = player_name.lower()
        results = [p for p in data if name_lower in str(p.get("name", "")).lower()]
        if results:
            return results[0] if len(results) == 1 else results
        return {"error": f"Player '{player_name}' not found in Indian players dataset."}

    if isinstance(data, dict):
        name_lower = player_name.lower()
        matches = {k: v for k, v in data.items() if name_lower in k.lower()}
        if matches:
            return list(matches.values())[0] if len(matches) == 1 else matches
        return {"error": f"Player '{player_name}' not found.", "available": list(data.keys())}

    return data


@mcp.tool()
def get_country_tennis_history(country: str) -> dict:
    """
    Get the ATP top-100 history and profile for a specific country.

    Args:
        country: Country name or ISO code (e.g., "Spain", "USA", "ESP").
                 Case-insensitive partial match.

    Returns year-by-year player counts in top 100, peak players, and country stats.
    """
    data = _load_json("globaltop100evolution/tennis_country_profiles.json")

    country_lower = country.lower()

    # Handle list or dict
    if isinstance(data, list):
        results = [
            c for c in data
            if country_lower in str(c.get("country", "")).lower()
            or country_lower in str(c.get("country_code", "")).lower()
        ]
        if results:
            return results[0] if len(results) == 1 else {"results": results}
        available = [c.get("country") or c.get("country_code") for c in data[:20]]
        return {"error": f"Country '{country}' not found.", "sample_countries": available}

    if isinstance(data, dict):
        matches = {
            k: v for k, v in data.items()
            if country_lower in k.lower()
        }
        if matches:
            return list(matches.values())[0] if len(matches) == 1 else matches
        return {"error": f"Country '{country}' not found.", "available_sample": list(data.keys())[:20]}

    return data


@mcp.tool()
def suggest_visualization(dataset: str) -> dict:
    """
    Get D3.js / Chart.js visualization suggestions for a specific tennis dataset.

    The tennis-analytics project uses:
    - Primary green: #1e5631
    - Accent yellow: #f9c74f
    - Fonts: Playfair Display (headings) + Montserrat (body)

    Args:
        dataset: Dataset name or topic. Examples: "race to greatness",
                 "nail biters", "gsdi", "rivalry network", "career longevity",
                 "indian players", "global evolution", "young guns".

    Returns chart type suggestions, key fields to encode, and D3 guidance.
    """
    ds = dataset.lower()

    suggestions: dict = {
        "dataset": dataset,
        "brand": {
            "primary_color": "#1e5631",
            "accent_color": "#f9c74f",
            "fonts": {"heading": "Playfair Display", "body": "Montserrat"},
        },
    }

    if any(k in ds for k in ("greatness", "trajectory", "career", "race")):
        suggestions.update({
            "recommended_chart": "Multi-series line chart (age on x-axis)",
            "x_axis": "age",
            "y_axis_options": ["gs", "titles", "big_titles", "masters", "wins"],
            "color_encoding": "player name",
            "interactivity": "Hover tooltip with player name, age, milestone",
            "d3_approach": "d3.line() with voronoi hover, d3.scaleLinear() for both axes",
            "notes": "Use trajectory[] array. Plot multiple players as overlapping lines. Mark milestones with circle annotations.",
            "example_encoding": "x: d.age, y: d.gs (Grand Slam titles accumulated by age)",
        })
    elif any(k in ds for k in ("nail", "nbi", "drama", "tiebreak")):
        suggestions.update({
            "recommended_chart": "Horizontal bar chart or bubble chart",
            "primary_field": "NBI_100 (0–100 normalized drama score)",
            "label_field": "match (e.g. 'Djokovic def. Federer')",
            "secondary_encodings": {"bubble_size": "duration", "color": "tourney"},
            "d3_approach": "d3.scaleBand() for y-axis labels, d3.scaleLinear() for NBI bar length",
            "notes": "Top-right quadrant: long matches with high NBI. Add drama_tags as tooltips.",
        })
    elif any(k in ds for k in ("gsdi", "dominance", "slam campaign")):
        suggestions.update({
            "recommended_chart": "Scatter plot or ranked bar chart",
            "x_axis": "year",
            "y_axis": "dominance_score",
            "color": "player",
            "size": "sets_won_pct",
            "d3_approach": "d3.scaleLinear() x/y, d3.scaleOrdinal() color by player",
            "notes": "Mark perfect_campaign=true with a star glyph. Filter by tournament using get_gsdi_top_n().",
        })
    elif any(k in ds for k in ("network", "rival", "h2h", "head")):
        suggestions.update({
            "recommended_chart": "Force-directed network graph",
            "nodes": "players (size = total wins)",
            "edges": "rivalry strength (thickness = total matches played)",
            "color": "era / country / dominance",
            "d3_approach": "d3.forceSimulation() with d3.forceManyBody(), d3.forceLink()",
            "notes": "Use tennis://network/rivalries resource. Node radius proportional to titles. Edge weight = match count.",
        })
    elif any(k in ds for k in ("india", "indian")):
        suggestions.update({
            "recommended_chart": "Timeline + small multiples",
            "x_axis": "year",
            "y_axis": "peak_ranking",
            "facet": "player",
            "d3_approach": "d3.line() per player with shared x-axis, d3.scaleLog() for ranking (inverted)",
            "notes": "Invert y-axis (rank 1 at top). Use players_time_series.json for time-series view.",
        })
    elif any(k in ds for k in ("global", "country", "evolution", "top 100")):
        suggestions.update({
            "recommended_chart": "Stacked area chart or streamgraph",
            "x_axis": "year",
            "y_axis": "number of players in top 100",
            "color": "country",
            "d3_approach": "d3.stack() with d3.area(), d3.scaleOrdinal() for countries",
            "notes": "Streamgraph gives dramatic flow between country dominance eras. Use tennis://globaltop100/timeline.",
        })
    elif any(k in ds for k in ("longevity", "survival", "career length")):
        suggestions.update({
            "recommended_chart": "Survival curve (Kaplan-Meier style) + histogram",
            "x_axis": "career_age_years",
            "y_axis": "survival_probability (0–1)",
            "d3_approach": "d3.line() step function for survival, d3.histogram() for career length distribution",
            "notes": "Use tennis://career/survival-curve. Overlay specific players' career end points.",
        })
    elif any(k in ds for k in ("young", "gun", "next gen")):
        suggestions.update({
            "recommended_chart": "Line chart with age-aligned trajectories",
            "x_axis": "age",
            "y_axis_options": ["gs", "titles", "big_titles"],
            "notes": "Same as race-to-greatness but filtered to younger cohort. Good for comparing Alcaraz vs Sinner early careers.",
        })
    else:
        suggestions.update({
            "recommended_chart": "Explore the data structure first",
            "tip": "Use list_datasets() to find the right resource, then load the data to understand the schema.",
            "generic_advice": "Most datasets work well as line charts (time-series), bar charts (rankings), or scatter plots (multi-metric).",
        })

    return suggestions


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run()
