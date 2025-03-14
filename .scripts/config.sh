#!/bin/bash
#
# Configuration file for knowledge graph synthesis
#

# Processing settings
export KGS_CHUNK_SIZE=10            # Default chunk size for gradual processing
export KGS_CHUNK_DELAY=30           # Default delay between chunks (seconds)

# Mega-batch settings
export KGS_ENTITY_MEGA_BATCH_SIZE=100   # Maximum entities per mega-batch
export KGS_RELATION_MEGA_BATCH_SIZE=50  # Maximum relationships per mega-batch
export KGS_API_DELAY=5                  # Delay between API calls (seconds)

# Language model settings
export KGS_DEFAULT_PROVIDER="gemini"    # Default LLM provider