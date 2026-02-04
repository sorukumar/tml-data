#!/usr/bin/env python3
"""
Part 3: Run the full analysis pipeline.
Rebuilds base metrics and regenerates all aggregations.
"""
import subprocess
import sys

def run_script(script_name):
    print(f"\n>>> Running {script_name}...")
    result = subprocess.run([sys.executable, script_name], capture_output=False)
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
