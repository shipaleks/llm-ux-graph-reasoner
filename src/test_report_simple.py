import json
import os
from pathlib import Path

def generate_simple_report(output_dir):
    """Generate a simple HTML report that links to segment pages."""
    
    # Load summaries
    context_dir = os.path.join(output_dir, "context")
    summaries_path = os.path.join(context_dir, "segment_summaries.json")
    
    with open(summaries_path, 'r', encoding='utf-8') as f:
        summaries = json.load(f)
    
    # Create report template
    report_template = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Knowledge Graph Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #fff; margin: 0 auto; padding: 1rem; max-width: 1200px; }}
        h1 {{ font-size: 2rem; text-align: center; margin-bottom: 2rem; }}
        h2 {{ font-size: 1.5rem; border-bottom: 1px solid #e0e0e0; padding-bottom: 0.5rem; margin-top: 2rem; }}
        .segment-summary {{ background-color: #f5f5f5; padding: 1rem; margin-bottom: 1rem; border-radius: 4px; }}
        .segment-summary h3 {{ margin-top: 0; }}
        .segment-link {{ display: inline-block; margin-top: 0.5rem; color: #0366d6; text-decoration: none; }}
        .segment-link:hover {{ text-decoration: underline; }}
        .metadata {{ background-color: #e8f4f8; padding: 1rem; margin-bottom: 2rem; border-radius: 4px; }}
        iframe {{ width: 100%; height: 600px; border: 1px solid #ddd; margin-bottom: 2rem; }}
    </style>
</head>
<body>
    <h1>Knowledge Graph Analysis Report</h1>
    
    <div class="metadata">
        <p><strong>Date:</strong> 2025-03-06</p>
        <p><strong>Source:</strong> tests/data/samples/sample_ru.txt</p>
    </div>
    
    <h2>Knowledge Graph Visualization</h2>
    <iframe src="graphs/knowledge_graph.html" frameborder="0"></iframe>
    
    <h2>Expanded Graph Visualization</h2>
    <iframe src="graphs/expanded/expanded_graph.html" frameborder="0"></iframe>
    
    <h2>Segment Summaries</h2>
    {segment_summaries}
</body>
</html>
"""
    
    # Generate segment summary HTML
    segment_summaries_html = ""
    for segment_id, summary in summaries.items():
        title = summary.get('title', f"Segment {segment_id}")
        summary_text = summary.get('summary', '')
        role = summary.get('role', '')
        
        segment_html = f"""
    <div class="segment-summary">
        <h3>{title}</h3>
        <p><strong>Summary:</strong> {summary_text}</p>
        <p><strong>Role:</strong> {role}</p>
        <a href="segments/{segment_id}.html" class="segment-link">View full segment</a>
    </div>
"""
        segment_summaries_html += segment_html
    
    # Create the full report
    report_html = report_template.format(segment_summaries=segment_summaries_html)
    
    # Write the report
    report_path = os.path.join(output_dir, "report.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_html)
        print(f"Created report: {report_path}")

if __name__ == "__main__":
    # Set the output directory
    output_dir = "output/20250306_062746"
    generate_simple_report(output_dir)
    print("Done!")