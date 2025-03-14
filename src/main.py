"""Main entry point for the knowledge graph synthesis system."""

import sys
from knowledge_graph_synth.cli.commands import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))