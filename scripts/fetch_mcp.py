#!/usr/bin/env python3
"""
fetch_mcp.py — Tier 1: Fetch Match Charting Project data from GitHub.

Downloads all required MCP CSV files from Jeff Sackmann's public repository
and saves them to data/raw/mcp/. Each run performs a full overwrite because
MCP files are cumulatively appended (no versioning), so a fresh copy is always
the correct source of truth.

License note: MCP data is CC BY-NC-SA 4.0 (non-commercial use only).
See https://github.com/JeffSackmann/tennis_MatchChartingProject
"""

import os
import sys
import requests

MCP_BASE_URL = (
    "https://raw.githubusercontent.com/"
    "JeffSackmann/tennis_MatchChartingProject/master/"
)

# Files to fetch — men's tour only (we focus on ATP analytics)
MCP_FILES = [
    "charting-m-matches.csv",
    "charting-m-points-to-2009.csv",
    "charting-m-points-2010s.csv",
    "charting-m-points-2020s.csv",
    "charting-m-stats-Overview.csv",
    "charting-m-stats-Rally.csv",
]

DEFAULT_OUTPUT_DIR = "data/raw/mcp"


def fetch_file(filename: str, output_dir: str, timeout: int = 120) -> bool:
    """Download a single MCP CSV file and save it to output_dir."""
    url = MCP_BASE_URL + filename
    output_path = os.path.join(output_dir, filename)

    print(f"  Fetching: {filename}")
    try:
        response = requests.get(url, timeout=timeout, stream=True)
        if response.status_code != 200:
            print(f"    ❌ HTTP {response.status_code} for {url}")
            return False

        with open(output_path, "wb") as fh:
            for chunk in response.iter_content(chunk_size=65536):
                fh.write(chunk)

        size_kb = os.path.getsize(output_path) / 1024
        print(f"    ✅ Saved {output_path} ({size_kb:.0f} KB)")
        return True

    except requests.exceptions.Timeout:
        print(f"    ❌ Timeout fetching {filename} (>{timeout}s)")
        return False
    except Exception as exc:
        print(f"    ❌ Error fetching {filename}: {exc}")
        return False


def fetch_mcp(output_dir: str = DEFAULT_OUTPUT_DIR) -> bool:
    """
    Download all required MCP files to output_dir.

    Returns:
        True if all files fetched successfully, False otherwise.
    """
    os.makedirs(output_dir, exist_ok=True)

    print(f"Fetching MCP data from GitHub → {output_dir}/")
    print(f"Source: {MCP_BASE_URL}")
    print("-" * 60)

    results = []
    for filename in MCP_FILES:
        ok = fetch_file(filename, output_dir)
        results.append((filename, ok))

    print("\n" + "=" * 60)
    failed = [f for f, ok in results if not ok]
    if failed:
        print(f"❌ {len(failed)} file(s) failed to download:")
        for f in failed:
            print(f"   • {f}")
        return False

    print(f"✅ All {len(MCP_FILES)} MCP files fetched successfully.")
    print(f"\nNext step: Build MCP base metrics with:")
    print("  python scripts/build_mcp_base_metrics.py")
    return True


if __name__ == "__main__":
    output_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUTPUT_DIR
    success = fetch_mcp(output_dir=output_dir)
    sys.exit(0 if success else 1)
