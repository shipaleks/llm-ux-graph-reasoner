#!/bin/bash
#
# Process multiple text files in batch mode
#
# Usage: ./batch_process.sh input_dir [output_dir] [mode]
#   input_dir: Directory containing input text files (required)
#   output_dir: Base directory for output (default: output/batch)
#   mode: Processing mode - gradual or full (default: gradual)

# Source configuration
source "$(dirname "$0")/config.sh"

# Default values
DEFAULT_OUTPUT="output/batch"
DEFAULT_MODE="gradual"

# Parse arguments
INPUT_DIR=$1
OUTPUT_DIR=${2:-$DEFAULT_OUTPUT}
MODE=${3:-$DEFAULT_MODE}

# Check if input directory is provided
if [ -z "$INPUT_DIR" ]; then
    echo "Error: Input directory is required"
    echo "Usage: ./batch_process.sh input_dir [output_dir] [mode]"
    exit 1
fi

# Check if input directory exists
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Directory '$INPUT_DIR' not found"
    exit 1
fi

# Generate a timestamp for unique batch run
TIMESTAMP=$(date "+%Y-%m-%d_%H-%M-%S")

# Create a uniquely named output directory with timestamp
if [ "$OUTPUT_DIR" = "$DEFAULT_OUTPUT" ]; then
    OUTPUT_DIR="${OUTPUT_DIR}/batch_${TIMESTAMP}"
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Find all text files in the input directory
TEXT_FILES=$(find "$INPUT_DIR" -type f -name "*.txt")
FILE_COUNT=$(echo "$TEXT_FILES" | wc -l | tr -d '[:space:]')

if [ "$FILE_COUNT" -eq 0 ]; then
    echo "Error: No text files found in '$INPUT_DIR'"
    exit 1
fi

echo "Found $FILE_COUNT text files to process"
echo "Mode: $MODE"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Process each file
COUNT=1
for FILE in $TEXT_FILES; do
    FILENAME=$(basename "$FILE")
    FILE_TIMESTAMP=$(date "+%Y-%m-%d_%H-%M-%S")
    FILE_OUTPUT_DIR="$OUTPUT_DIR/${FILENAME%.*}_${FILE_TIMESTAMP}"
    
    echo "[$COUNT/$FILE_COUNT] Processing file: $FILENAME"
    echo "Output will be saved to: $FILE_OUTPUT_DIR"
    
    # Create file-specific output directory
    mkdir -p "$FILE_OUTPUT_DIR"
    
    # Process the file
    "$(dirname "$0")/process_text.sh" "$FILE" "$FILE_OUTPUT_DIR" "$KGS_CHUNK_SIZE" "$KGS_CHUNK_DELAY" "$MODE"
    
    echo "[$COUNT/$FILE_COUNT] Completed processing: $FILENAME"
    echo ""
    
    COUNT=$((COUNT + 1))
done

echo "Batch processing complete!"
echo "Results are available in the '$OUTPUT_DIR' directory"