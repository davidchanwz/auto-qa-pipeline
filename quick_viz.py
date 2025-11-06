#!/usr/bin/env python3

"""
Quick Codebook Visualizer

A simple script to quickly generate a visualization for any codebook JSON file.
"""

import sys
import os
from visualize_codebook import create_codebook_visualization


def main():
    """Main function to handle command line usage."""

    if len(sys.argv) < 2:
        print("📊 Quick Codebook Visualizer")
        print("\nUsage:")
        print("  python quick_viz.py <codebook_path> [output_path]")
        print("\nExample:")
        print("  python quick_viz.py data/updated_codebook.json")
        print("  python quick_viz.py data/updated_codebook.json my_viz.html")
        print("\nAvailable codebook files:")

        # Look for JSON files in common locations
        search_paths = [".", "data/", "logs/"]
        found_files = []

        for path in search_paths:
            if os.path.exists(path):
                for file in os.listdir(path):
                    if file.endswith(".json") and (
                        "codebook" in file.lower() or "codes" in file.lower()
                    ):
                        found_files.append(os.path.join(path, file))

        if found_files:
            for file in found_files:
                print(f"  • {file}")
        else:
            print("  (No codebook files found)")

        return

    # Get arguments
    codebook_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    # Check if file exists
    if not os.path.exists(codebook_path):
        print(f"❌ Error: File '{codebook_path}' not found")
        return

    # Generate visualization
    print(f"🚀 Generating visualization for: {codebook_path}")
    viz_path = create_codebook_visualization(codebook_path, output_path)

    if viz_path:
        print(f"\n🎉 Success! Visualization ready:")
        print(f"   File: {viz_path}")
        print(f"   Size: {os.path.getsize(viz_path):,} bytes")

        # Try to open automatically on macOS
        if sys.platform == "darwin":
            try:
                os.system(f"open '{viz_path}'")
                print(f"   📱 Opened in default browser")
            except:
                print(f"   🌐 Open '{viz_path}' in your browser")
        else:
            print(f"   🌐 Open '{viz_path}' in your browser")


if __name__ == "__main__":
    main()
