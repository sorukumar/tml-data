#!/usr/bin/env python3
"""
Run All Aggregations
Main runner script that orchestrates all tennis data aggregations
Now uses pre-aggregated base metrics (Parquet format) for faster processing
"""

import sys
import os
from datetime import datetime

# Import aggregation modules
from aggregations.nbi import generate_nbi_aggregation
from aggregations.gsdi import generate_gsdi_aggregation
from aggregations.gs_breakthrough import generate_breakthrough_aggregation
from aggregations.global_evolution import generate_global_evolution_aggregation
from aggregations.network_graph import generate_network_aggregation
from aggregations.career_longevity import generate_career_longevity_aggregation
from aggregations.indian_players import generate_indian_datasets


def run_all_aggregations(matches_enriched_path="data/base/matches_enriched.parquet",
                         player_metrics_path="data/base/player_metrics.parquet",
                         base_data_path="data/base/atp_matches_raw.parquet"):
    """
    Run all aggregation pipelines using pre-aggregated base metrics
    
    Args:
        matches_enriched_path: Path to enriched matches data (Parquet)
        player_metrics_path: Path to player metrics data (Parquet)
        base_data_path: Path to raw base data (Parquet)
    """
    print("=" * 80)
    print("TENNIS DATA AGGREGATION PIPELINE")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Check if base metrics exist
    metrics_exist = os.path.exists(player_metrics_path) and os.path.exists(matches_enriched_path)
    
    if not metrics_exist:
        print(f"\n⚠️  WARNING: Base metrics not found")
        print(f"  Missing: {player_metrics_path} or {matches_enriched_path}")
        print(f"\n🔧 Please run first: python build_base_metrics.py")
        print(f"   This will generate player-level and enriched match data tables.")
        return 1
    
    print(f"✓ Found enriched matches: {matches_enriched_path}")
    print(f"✓ Found player metrics: {player_metrics_path}")
    
    success_count = 0
    fail_count = 0
    
    # List of aggregations to run (now using base metrics)
    aggregations = [
        ("NBI (Nailbiter Index)", lambda: generate_nbi_aggregation(matches_enriched_path)),
        ("GSDI (Grand Slam Dominance Index)", lambda: generate_gsdi_aggregation(matches_enriched_path)),
        ("Breakthrough Analysis (Stan The Man)", lambda: generate_breakthrough_aggregation(player_metrics_path)),
        ("Network Graph Data", lambda: generate_network_aggregation(matches_enriched_path, player_metrics_path)),
        ("Global Top 100 Evolution", lambda: generate_global_evolution_aggregation(base_data_path)),
        ("Career Longevity & Survival Analysis", lambda: generate_career_longevity_aggregation(base_data_path)),
        ("Indian Players Data", lambda: generate_indian_datasets(base_data_path)),
    ]
    
    # Run each aggregation
    for name, func in aggregations:
        try:
            print(f"\n{'='*80}")
            print(f"Running: {name}")
            func()
            success_count += 1
        except Exception as e:
            print(f"\n❌ FAILED: {name}")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            fail_count += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("PIPELINE SUMMARY")
    print("=" * 80)
    print(f"✅ Successful: {success_count}/{len(aggregations)}")
    print(f"❌ Failed: {fail_count}/{len(aggregations)}")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    print("\n📂 Generated Files:")
    print("  data/base/")
    print("    ├── atp_matches_raw.parquet (raw fetched data)")
    print("    ├── player_metrics.parquet (player-level career stats)")
    print("    ├── matches_enriched.parquet (matches with parsed scores)")
    print("    ├── head_to_head.parquet (H2H matchup records)")
    print("    └── metadata.json")
    print("\n  data/nbi/")
    print("    ├── gs_nailbiters.json")
    print("    ├── gs_nailbiters.csv")
    print("    └── iconic_gs_matches.json")
    print("  data/gsdi/")
    print("    └── gs_dominance_rankings.json")
    print("\n  data/gs-breakthrough/")
    print("    └── gs_breakthrough_comparison.csv")
    print("  data/globaltop100evolution/")
    print("    ├── country_code_mapping.json")
    print("    ├── tennis_country_profiles.json")
    print("    ├── global_timeline_dataset.json")
    print("    └── top_tennis_players_timeline.json")
    print("  data/network/")
    print("    ├── grand_slam_finals_2003.json")
    print("    ├── australian_open_finals_1982.json")
    print("    ├── roland_garros_finals_1982.json")
    print("    ├── wimbledon_finals_1982.json")
    print("    ├── us_open_finals_1982.json")
    print("    ├── high_volume_players_2000.json")
    print("    └── network_summary.json")
    print("  data/career_longevity/")
    print("    ├── player_careers_top1000.json")
    print("    ├── survival_curve.json")
    print("    └── summary.json")
    print("  data/indian/")
    print("    ├── players_summary.json")
    print("    ├── indian_matches.json")
    print("    └── player_milestones.json")
    
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all_aggregations())
