#!/bin/bash
#
# Process a large text file with optimized settings
#
# Usage: ./analyze_large_file.sh file_path [output_dir]
#   file_path: Path to the input text file (required)
#   output_dir: Directory to store the output (default: output/large_file)

# Source configuration
source "$(dirname "$0")/config.sh"

# Default values
DEFAULT_OUTPUT="output/large_file"

# Parse arguments
FILE_PATH=$1
OUTPUT_DIR=${2:-$DEFAULT_OUTPUT}

# Optimized settings for large files
CHUNK_SIZE=15       # Process 15 segments at a time
DELAY=60            # Wait 60 seconds between chunks
ENTITY_BATCH=75     # Max 75 entities per mega-batch
RELATION_BATCH=30   # Max 30 relationships per mega-batch
API_DELAY=10        # Wait 10 seconds between API calls

# Check if file path is provided
if [ -z "$FILE_PATH" ]; then
    echo "Error: File path is required"
    echo "Usage: ./analyze_large_file.sh file_path [output_dir]"
    exit 1
fi

# Check if file exists
if [ ! -f "$FILE_PATH" ]; then
    echo "Error: File '$FILE_PATH' not found"
    exit 1
fi

# Generate a timestamp for unique output directory
TIMESTAMP=$(date "+%Y-%m-%d_%H-%M-%S")
FILE_NAME=$(basename "$FILE_PATH" .txt)

# Create a uniquely named output directory with timestamp
if [ "$OUTPUT_DIR" = "$DEFAULT_OUTPUT" ]; then
    OUTPUT_DIR="${OUTPUT_DIR}/${FILE_NAME}_${TIMESTAMP}"
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Export optimized settings
export KGS_CHUNK_SIZE=$CHUNK_SIZE
export KGS_CHUNK_DELAY=$DELAY
export KGS_ENTITY_MEGA_BATCH_SIZE=$ENTITY_BATCH
export KGS_RELATION_MEGA_BATCH_SIZE=$RELATION_BATCH
export KGS_API_DELAY=$API_DELAY

echo "Starting large file analysis with optimized settings:"
echo "- Input file: $FILE_PATH"
echo "- Output directory: $OUTPUT_DIR"
echo "- Chunk size: $CHUNK_SIZE segments"
echo "- Delay between chunks: $DELAY seconds"
echo "- Entity mega-batch size: $ENTITY_BATCH"
echo "- Relationship mega-batch size: $RELATION_BATCH"
echo "- API call delay: $API_DELAY seconds"
echo ""
echo "This configuration is optimized for large files to avoid API rate limits."
echo "The process will run gradually and may take some time to complete."
echo ""

# Ask user if they want to use advanced features
echo ""
echo "Do you want to enable advanced analysis features?"
echo "1. Basic analysis (default)"
echo "2. Include recursive graph expansion"
echo "3. Include meta-graph creation"
echo "4. Full analysis (all features)"
read -p "Enter your choice [1-4]: " ANALYSIS_CHOICE

# Set feature flags based on user choice
EXPAND_FLAG=""
METAGRAPH_FLAG=""

case $ANALYSIS_CHOICE in
    2)
        EXPAND_FLAG="--expand-graph"
        echo "Enabling recursive graph expansion"
        ;;
    3)
        METAGRAPH_FLAG="--build-metagraph"
        echo "Enabling meta-graph creation"
        ;;
    4)
        EXPAND_FLAG="--expand-graph"
        METAGRAPH_FLAG="--build-metagraph"
        echo "Enabling all advanced features"
        ;;
    *)
        echo "Using basic analysis"
        ;;
esac

# Run the processing script with gradual mode and selected features
"$(dirname "$0")/process_text.sh" "$FILE_PATH" "$OUTPUT_DIR" "$CHUNK_SIZE" "$DELAY" "gradual" "$EXPAND_FLAG" "$METAGRAPH_FLAG"

echo ""
echo "✅ Large file analysis complete or interrupted"
echo "Partial results can be found in '$OUTPUT_DIR' directory"
echo ""
echo "To continue processing from where it left off, run the same command again."