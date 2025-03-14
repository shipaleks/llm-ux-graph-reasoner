#!/usr/bin/env python3
"""
Run analysis on synthetic text with proper path setup.
"""

import os
import sys

# Add src directory to path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, src_dir)

# Now import from the knowledge_graph_synth package
from knowledge_graph_synth.cli.commands import main

if __name__ == "__main__":
    # Define the arguments for the analysis
    args = [
        "process",
        "-f", "test_synthetic_text.txt",
        "-e",  # extract entities
        "-b",  # build graph
        "-g",  # generate theories
        "--contextual-analysis",
        "--generate-report",
        "--expand-graph",
        "--provider", "gemini"
    ]
    
    # Run the command
    sys.exit(main(args))