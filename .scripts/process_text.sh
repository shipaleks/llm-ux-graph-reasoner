#!/bin/bash
#
# Process a text file with knowledge graph synthesis system
#
# Usage: ./process_text.sh file_path [output_dir] [chunk_size] [delay] [mode] [expand_flag] [metagraph_flag]
#   file_path: Path to the input text file (required)
#   output_dir: Directory to store the output (default: output)
#   chunk_size: Number of segments to process in each chunk (default: 10)
#   delay: Delay in seconds between processing chunks (default: 30)
#   mode: Processing mode - gradual or full (default: gradual)
#   expand_flag: Flag to enable graph expansion (--expand-graph)
#   metagraph_flag: Flag to enable meta-graph creation (--build-metagraph)

# Default values
DEFAULT_OUTPUT="output"
DEFAULT_CHUNK_SIZE=10
DEFAULT_DELAY=30
DEFAULT_MODE="gradual"

# Parse arguments
FILE_PATH=$1
OUTPUT_DIR=${2:-$DEFAULT_OUTPUT}
CHUNK_SIZE=${3:-$DEFAULT_CHUNK_SIZE}
DELAY=${4:-$DEFAULT_DELAY}
MODE=${5:-$DEFAULT_MODE}
EXPAND_FLAG=$6
METAGRAPH_FLAG=$7

# Check if file path is provided
if [ -z "$FILE_PATH" ]; then
    echo "Error: File path is required"
    echo "Usage: ./process_text.sh file_path [output_dir] [chunk_size] [delay] [mode] [expand_flag] [metagraph_flag]"
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

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Set gradual flag based on mode
GRADUAL_FLAG=""
if [ "$MODE" = "gradual" ]; then
    GRADUAL_FLAG="--gradual"
fi

# Set environment variables for chunk size and delay
export KGS_CHUNK_SIZE=$CHUNK_SIZE
export KGS_CHUNK_DELAY=$DELAY

echo "Starting knowledge graph synthesis with the following parameters:"
echo "- Input file: $FILE_PATH"
echo "- Output directory: $OUTPUT_DIR"
echo "- Chunk size: $CHUNK_SIZE segments"
echo "- Delay between chunks: $DELAY seconds"
echo "- Mode: $MODE"
echo ""

# Run the knowledge graph synthesis command
poetry run kgs process --file "$FILE_PATH" --extract --build-graph --generate-theories $GRADUAL_FLAG $EXPAND_FLAG $METAGRAPH_FLAG --output "$OUTPUT_DIR"

# Check if the command succeeded
if [ $? -eq 0 ]; then
    echo ""
    echo "Knowledge graph synthesis completed successfully!"
    echo "Results are available in the '$OUTPUT_DIR' directory:"
    echo "- Entities: $OUTPUT_DIR/entities/"
    echo "- Relationships: $OUTPUT_DIR/relationships/"
    echo "- Graph visualization: $OUTPUT_DIR/graphs/knowledge_graph.html"
    echo "- Graph report: $OUTPUT_DIR/graphs/knowledge_graph_report.md"
    
    # Show expanded graph path if enabled
    if [ -n "$EXPAND_FLAG" ]; then
        echo "- Expanded graph: $OUTPUT_DIR/graphs/expanded/expanded_graph.html"
    fi
    
    # Show meta-graph path if enabled
    if [ -n "$METAGRAPH_FLAG" ]; then
        echo "- Meta-graph: $OUTPUT_DIR/graphs/meta/meta_graph.html"
    fi
    
    echo "- Theories: $OUTPUT_DIR/theories/theories.md"
else
    echo ""
    echo "Knowledge graph synthesis failed with error code $?"
    echo "Check the error messages above for details."
fi