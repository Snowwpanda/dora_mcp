#!/usr/bin/env python3
"""Compare test results over time to detect changes."""

import json
import sys
from pathlib import Path
from datetime import datetime


def load_json(filepath):
    """Load JSON file."""
    with open(filepath) as f:
        return json.load(f)


def compare_tools(file1, file2):
    """Compare tool definitions."""
    data1 = load_json(file1)
    data2 = load_json(file2)
    
    print("\n" + "="*70)
    print("TOOL COMPARISON")
    print("="*70)
    
    print(f"\nFile 1: {file1}")
    print(f"  Timestamp: {data1.get('timestamp', 'N/A')}")
    print(f"  Tool count: {data1.get('tool_count', 0)}")
    
    print(f"\nFile 2: {file2}")
    print(f"  Timestamp: {data2.get('timestamp', 'N/A')}")
    print(f"  Tool count: {data2.get('tool_count', 0)}")
    
    # Check if tool count changed
    if data1.get('tool_count') != data2.get('tool_count'):
        print("\n⚠️  WARNING: Tool count changed!")
    else:
        print("\n✓ Tool count unchanged")
    
    # Compare tool names
    tools1 = {t['name'] for t in data1.get('tools', [])}
    tools2 = {t['name'] for t in data2.get('tools', [])}
    
    if tools1 != tools2:
        print("\n⚠️  Tool names changed!")
        print(f"  Removed: {tools1 - tools2}")
        print(f"  Added: {tools2 - tools1}")
    else:
        print("✓ Tool names unchanged")


def compare_search_results(file1, file2):
    """Compare search results."""
    data1 = load_json(file1)
    data2 = load_json(file2)
    
    print("\n" + "="*70)
    print("SEARCH RESULTS COMPARISON")
    print("="*70)
    
    print(f"\nFile 1: {file1}")
    print(f"  Timestamp: {data1.get('timestamp', 'N/A')}")
    print(f"  Publications: {data1.get('publication_count', 0)}")
    print(f"  Response time: {data1.get('elapsed_seconds', 0):.3f}s")
    print(f"  Result size: {data1.get('result_size_bytes', 0):,} bytes")
    
    print(f"\nFile 2: {file2}")
    print(f"  Timestamp: {data2.get('timestamp', 'N/A')}")
    print(f"  Publications: {data2.get('publication_count', 0)}")
    print(f"  Response time: {data2.get('elapsed_seconds', 0):.3f}s")
    print(f"  Result size: {data2.get('result_size_bytes', 0):,} bytes")
    
    # Calculate changes
    pub_diff = data2.get('publication_count', 0) - data1.get('publication_count', 0)
    time_diff = data2.get('elapsed_seconds', 0) - data1.get('elapsed_seconds', 0)
    size_diff = data2.get('result_size_bytes', 0) - data1.get('result_size_bytes', 0)
    
    print("\n" + "-"*70)
    print("CHANGES")
    print("-"*70)
    
    # Publication count
    if pub_diff > 0:
        print(f"📈 Publications increased by {pub_diff}")
    elif pub_diff < 0:
        print(f"📉 Publications decreased by {abs(pub_diff)} ⚠️")
    else:
        print("✓ Publication count unchanged")
    
    # Response time
    if abs(time_diff) > 0.5:
        if time_diff > 0:
            print(f"⚠️  Response time increased by {time_diff:.3f}s")
        else:
            print(f"⚡ Response time improved by {abs(time_diff):.3f}s")
    else:
        print(f"✓ Response time similar (±{abs(time_diff):.3f}s)")
    
    # Result size
    size_pct = (size_diff / data1.get('result_size_bytes', 1)) * 100 if data1.get('result_size_bytes') else 0
    if abs(size_pct) > 10:
        print(f"⚠️  Result size changed by {size_pct:+.1f}%")
    else:
        print(f"✓ Result size similar ({size_pct:+.1f}%)")
    
    # Compare sample publications
    samples1 = {p.get('pid') for p in data1.get('sample_publications', [])}
    samples2 = {p.get('pid') for p in data2.get('sample_publications', [])}
    
    if samples1 and samples2:
        overlap = len(samples1 & samples2)
        print(f"\nSample publications overlap: {overlap}/{len(samples1)}")


def main():
    """Main comparison function."""
    if len(sys.argv) < 3:
        print("Usage: python compare_results.py <file1> <file2>")
        print("\nExample:")
        print("  python compare_results.py \\")
        print("    test_results_old/manfred_heuberger_search.json \\")
        print("    test_results/manfred_heuberger_search.json")
        sys.exit(1)
    
    file1 = Path(sys.argv[1])
    file2 = Path(sys.argv[2])
    
    if not file1.exists():
        print(f"Error: {file1} not found")
        sys.exit(1)
    
    if not file2.exists():
        print(f"Error: {file2} not found")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("TEST RESULTS COMPARISON")
    print("="*70)
    
    # Detect file type and compare
    if "tools" in file1.name:
        compare_tools(file1, file2)
    elif "search" in file1.name:
        compare_search_results(file1, file2)
    else:
        print("Unknown file type. Expected 'tools' or 'search' in filename.")
    
    print("\n" + "="*70)
    print("END OF COMPARISON")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
