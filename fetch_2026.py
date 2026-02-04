#!/usr/bin/env python3
"""
Part 1: Fetch 2026 data from Tennismylife stats portal.
Saves the raw CSV for auditing and ingestion.
"""
import requests
import os
import sys

def fetch_2026_csv(output_path="data/raw/2026.csv"):
    url = "https://stats.tennismylife.org/data/2026.csv"
    print(f"Fetching 2026 data from: {url}")
    
    try:
        # We use a stream to handle potential size growth gracefully
        response = requests.get(url, timeout=30, stream=True)
        
        if response.status_code == 200:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            size_kb = os.path.getsize(output_path) / 1024
            print(f"✅ Success: Saved {output_path} ({size_kb:.1f} KB)")
            return True
        else:
            print(f"❌ Error: Received HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during fetch: {e}")
        return False

if __name__ == "__main__":
    if fetch_2026_csv():
        sys.exit(0)
    else:
        sys.exit(1)
