#!/bin/bash
# Script to run analysis and then improve the report in English

# Check if a file path was provided
if [ -z "$1" ]; then
    echo "Usage: $0 <text_file_path> [--provider provider] [--expand] [--theories]"
    exit 1
fi

FILE_PATH="$1"
shift  # Remove the first argument

# Run the original analyze_text.py script first
echo "🔍 Running initial analysis..."
./analyze_text.py "$FILE_PATH" "$@"

# Find the latest output directory
LATEST_DIR=$(ls -td output/[0-9]*_[0-9]* | head -n 1)

if [ -z "$LATEST_DIR" ]; then
    echo "❌ Error: Could not find output directory"
    exit 1
fi

echo "📂 Found output directory: $LATEST_DIR"

# Now run the improve_report_en.py script on that directory
echo "🔄 Improving the report with English translation..."
./improve_report_en.py --dir "$LATEST_DIR" --force

# Check if the improved report was created
IMPROVED_REPORT="$LATEST_DIR/improved_report_en.html"
if [ -f "$IMPROVED_REPORT" ]; then
    echo "✅ Success! English report created at: $IMPROVED_REPORT"
    echo "🌐 You can open it in your browser."
else
    echo "❌ Error: Could not find the improved English report"
    exit 1
fi

exit 0