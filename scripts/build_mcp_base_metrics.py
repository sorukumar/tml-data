#!/usr/bin/env python3
"""
Build MCP Base Metrics
Processes Match Charting Project point-by-point data into Tier 2 Parquet tables:

  data/base/mcp_player_metrics.parquet   — Rally profile, Serve+1, Clutch stats per player
  data/base/mcp_matches_enriched.parquet — Match-level stats joined to TML archive
  data/base/mcp_player_crosswalk.parquet — MCP player name → TML player name mapping

Run this AFTER build_base_metrics.py (requires data/base/atp_matches_raw.parquet).
"""

import sys
import os
import traceback

# Add project root to path so 'aggregations' can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aggregations.mcp_base_metrics import generate_mcp_base_metrics


if __name__ == "__main__":
    try:
        player_metrics_df, matches_enriched_df, crosswalk_df = generate_mcp_base_metrics(
            raw_dir="data/raw/mcp",
            base_data_path="data/base/atp_matches_raw.parquet",
            output_dir="data/base",
        )

        print("\n✅ SUCCESS: MCP base metrics generated successfully")
        print("\nOutputs:")
        print(f"  {len(player_metrics_df):,} players in mcp_player_metrics.parquet")
        print(f"  {len(matches_enriched_df):,} matches in mcp_matches_enriched.parquet")
        print(f"  {len(crosswalk_df):,} name mappings in mcp_player_crosswalk.parquet")
        print("\nNext step: Run aggregations with:")
        print("  python scripts/run_aggregations.py")

    except FileNotFoundError as e:
        print(f"\n❌ ERROR: Required file not found")
        print(f"   {e}")
        print("\nEnsure the following steps have been run first:")
        print("  1. python scripts/fetch_mcp.py        (downloads MCP raw data)")
        print("  2. python scripts/build_base_metrics.py  (builds atp_matches_raw.parquet)")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ ERROR: Failed to build MCP base metrics")
        print(f"   {e}")
        traceback.print_exc()
        sys.exit(1)
