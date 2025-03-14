"""Create a simple report HTML file."""

import os
import sys
from pathlib import Path
import argparse

def create_report_html(output_dir):
    """Create a simple HTML report file."""
    report_path = os.path.join(output_dir, "report.html")
    
    report_html = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Knowledge Graph Analysis Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #fff;
            margin: 0 auto;
            padding: 1rem;
            max-width: 1200px;
        }
        h1 {
            font-size: 2rem;
            text-align: center;
            margin-bottom: 2rem;
        }
        h2 {
            font-size: 1.5rem;
            border-bottom: 1px solid #e0e0e0;
            padding-bottom: 0.5rem;
            margin-top: 2rem;
        }
        .section {
            margin-bottom: 2rem;
            padding-bottom: 1rem;
        }
        .graph-container {
            width: 100%;
            height: 600px;
            border: 1px solid #ddd;
            margin-bottom: 2rem;
        }
        .segment-summary {
            background-color: #f5f5f5;
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 4px;
        }
        .segment-link {
            display: inline-block;
            padding: 0.5rem;
            background-color: #0366d6;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            margin-top: 0.5rem;
        }
        .segment-link:hover {
            background-color: #0255b3;
        }
    </style>
</head>
<body>
    <h1>Knowledge Graph Analysis Report</h1>
    
    <div class="section">
        <h2>Graph Visualization</h2>
        <div class="graph-container">
            <iframe src="graphs/knowledge_graph.html" width="100%" height="600px" frameborder="0"></iframe>
        </div>
    </div>
    
    <div class="section">
        <h2>Expanded Graph</h2>
        <div class="graph-container">
            <iframe src="graphs/expanded/expanded_graph.html" width="100%" height="600px" frameborder="0"></iframe>
        </div>
        <p>The graph expansion process asked questions to understand more about key entities.</p>
        <a href="graphs/expanded/expansion_process.md" class="segment-link">View Expansion Process Report</a>
    </div>
    
    <div class="section">
        <h2>Text Segments</h2>
        <p>The following segments were analyzed:</p>
        
        <div class="segment-summary">
            <h3>Сегмент 1</h3>
            <a href="segments/9eba21e8-9b7c-457c-9114-0c3ed82227b6.html" class="segment-link">View Segment</a>
        </div>
        
        <div class="segment-summary">
            <h3>Сегмент 2</h3>
            <a href="segments/485998b5-f090-4263-a7b0-e44898ac6e38.html" class="segment-link">View Segment</a>
        </div>
        
        <div class="segment-summary">
            <h3>Сегмент 3</h3>
            <a href="segments/9a1bf100-ef22-496a-8cde-6f04e1e3580f.html" class="segment-link">View Segment</a>
        </div>
        
        <div class="segment-summary">
            <h3>Сегмент 4</h3>
            <a href="segments/9e26e76a-7985-4029-9040-3b525e6c07cd.html" class="segment-link">View Segment</a>
        </div>
        
        <div class="segment-summary">
            <h3>Сегмент 5</h3>
            <a href="segments/96d81b97-8f73-4392-96fd-818a83f11c9c.html" class="segment-link">View Segment</a>
        </div>
    </div>
</body>
</html>
"""
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_html)
    
    print(f"Created report HTML: {report_path}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Create a simple HTML report")
    parser.add_argument(
        "--dir", "-d",
        help="Output directory to process",
        default=None
    )
    
    args = parser.parse_args()
    
    # Find the latest output directory if not specified
    if args.dir is None:
        base_output_dir = "output"
        subdirs = [os.path.join(base_output_dir, d) for d in os.listdir(base_output_dir) 
                  if os.path.isdir(os.path.join(base_output_dir, d)) and d.startswith("2025")]
        
        if subdirs:
            # Sort by modification time (newest first)
            subdirs.sort(key=lambda d: os.path.getmtime(d), reverse=True)
            output_dir = subdirs[0]
            print(f"Using latest output directory: {output_dir}")
        else:
            print("No output directories found")
            exit(1)
    else:
        output_dir = args.dir
    
    create_report_html(output_dir)
    print("Done!")

if __name__ == "__main__":
    main()