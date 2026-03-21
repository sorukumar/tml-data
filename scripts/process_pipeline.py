#!/usr/bin/env python3
"""
Part 3: Run the full analysis pipeline.
Rebuilds base metrics and regenerates all aggregations.
"""
import subprocess
import sys
import os

def run_script(script_name):
    # Ensure we look in the same directory as this script
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
    print(f"\n>>> Running {script_name} from {script_path}...")
    result = subprocess.run([sys.executable, script_path], capture_output=False)
    if result.returncode != 0:
        print(f"❌ Error: {script_name} failed with exit code {result.returncode}")
        return False
    return True

def main():
    print("=" * 60)
    print("STARTING ANALYSIS PIPELINE")
    print("=" * 60)
    
    # 1. Rebuild Base Metrics (Player stats, enriched matches, H2H)
    if not run_script("build_base_metrics.py"):
        sys.exit(1)
        
    # 2. Run All Aggregations (NBI, GSDI, Network, etc.)
    if not run_script("run_aggregations.py"):
        sys.exit(1)
        
    print("\n" + "=" * 60)
    print("✅ PIPELINE COMPLETE: All data products updated")
    print("=" * 60)

if __name__ == "__main__":
    main()
