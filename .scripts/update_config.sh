#!/bin/bash
#
# Update the .env file with new configuration settings
#
# Usage: ./update_config.sh [--chunk-size N] [--chunk-delay N] [--entity-batch N] [--relation-batch N] [--api-delay N] [--provider NAME]
#

# Default values - will use current ones if set, otherwise these defaults
CHUNK_SIZE=${KGS_CHUNK_SIZE:-10}
CHUNK_DELAY=${KGS_CHUNK_DELAY:-30}
ENTITY_BATCH=${KGS_ENTITY_MEGA_BATCH_SIZE:-100}
RELATION_BATCH=${KGS_RELATION_MEGA_BATCH_SIZE:-50}
API_DELAY=${KGS_API_DELAY:-5}
PROVIDER=${KGS_DEFAULT_PROVIDER:-"gemini"}

# Parse arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --chunk-size)
            CHUNK_SIZE="$2"
            shift
            shift
            ;;
        --chunk-delay)
            CHUNK_DELAY="$2"
            shift
            shift
            ;;
        --entity-batch)
            ENTITY_BATCH="$2"
            shift
            shift
            ;;
        --relation-batch)
            RELATION_BATCH="$2"
            shift
            shift
            ;;
        --api-delay)
            API_DELAY="$2"
            shift
            shift
            ;;
        --provider)
            PROVIDER="$2"
            shift
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Path to .env file
ENV_FILE="../.env"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found"
    exit 1
fi

# Create temporary file
TMP_FILE=$(mktemp)

# Copy existing env file
cp "$ENV_FILE" "$TMP_FILE"

# Add or update configuration settings
if grep -q "KGS_CHUNK_SIZE" "$TMP_FILE"; then
    sed -i '' "s/KGS_CHUNK_SIZE=.*/KGS_CHUNK_SIZE=$CHUNK_SIZE/" "$TMP_FILE"
else
    echo "KGS_CHUNK_SIZE=$CHUNK_SIZE" >> "$TMP_FILE"
fi

if grep -q "KGS_CHUNK_DELAY" "$TMP_FILE"; then
    sed -i '' "s/KGS_CHUNK_DELAY=.*/KGS_CHUNK_DELAY=$CHUNK_DELAY/" "$TMP_FILE"
else
    echo "KGS_CHUNK_DELAY=$CHUNK_DELAY" >> "$TMP_FILE"
fi

if grep -q "KGS_ENTITY_MEGA_BATCH_SIZE" "$TMP_FILE"; then
    sed -i '' "s/KGS_ENTITY_MEGA_BATCH_SIZE=.*/KGS_ENTITY_MEGA_BATCH_SIZE=$ENTITY_BATCH/" "$TMP_FILE"
else
    echo "KGS_ENTITY_MEGA_BATCH_SIZE=$ENTITY_BATCH" >> "$TMP_FILE"
fi

if grep -q "KGS_RELATION_MEGA_BATCH_SIZE" "$TMP_FILE"; then
    sed -i '' "s/KGS_RELATION_MEGA_BATCH_SIZE=.*/KGS_RELATION_MEGA_BATCH_SIZE=$RELATION_BATCH/" "$TMP_FILE"
else
    echo "KGS_RELATION_MEGA_BATCH_SIZE=$RELATION_BATCH" >> "$TMP_FILE"
fi

if grep -q "KGS_API_DELAY" "$TMP_FILE"; then
    sed -i '' "s/KGS_API_DELAY=.*/KGS_API_DELAY=$API_DELAY/" "$TMP_FILE"
else
    echo "KGS_API_DELAY=$API_DELAY" >> "$TMP_FILE"
fi

if grep -q "KGS_DEFAULT_PROVIDER" "$TMP_FILE"; then
    sed -i '' "s/KGS_DEFAULT_PROVIDER=.*/KGS_DEFAULT_PROVIDER=$PROVIDER/" "$TMP_FILE"
else
    echo "KGS_DEFAULT_PROVIDER=$PROVIDER" >> "$TMP_FILE"
fi

# Replace original file
mv "$TMP_FILE" "$ENV_FILE"

echo "Configuration updated successfully:"
echo "- Chunk size: $CHUNK_SIZE segments"
echo "- Chunk delay: $CHUNK_DELAY seconds"
echo "- Entity mega-batch size: $ENTITY_BATCH"
echo "- Relationship mega-batch size: $RELATION_BATCH"
echo "- API call delay: $API_DELAY seconds"
echo "- Default provider: $PROVIDER"