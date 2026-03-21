#!/usr/bin/env python3
"""
Build Base Metrics
Generates player-level statistics and enriched match data
Run this before running aggregation scripts
"""

import sys
import os

# Add project root to path so 'aggregations' can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aggregations.base_metrics import generate_base_metrics


if __name__ == "__main__":
    print("="*60)
    print("TENNIS DATA - BASE METRICS BUILDER")
    print("="*60)
    
    try:
        player_metrics_df, matches_enriched_df, h2h_df = generate_base_metrics(
            base_data_path="data/base/atp_matches_raw.parquet",
            output_dir="data/base"
        )
        
        print("\n✅ SUCCESS: Base metrics generated successfully")
        print("\nNext step: Run aggregations with:")
        print("  python scripts/run_aggregations.py")
        
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: Base data file not found")
        print(f"   {e}")
        print("\nPlease run fresh data collection first:")
        print("  python scripts/fetch_2026.py")
        print("  python scripts/merge_2026.py")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: Failed to build base metrics")
        print(f"   {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
