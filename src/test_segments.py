import json
import os
from pathlib import Path

def generate_segment_pages(output_dir):
    """Generate HTML pages for each segment."""
    
    # Load segments and summaries
    context_dir = os.path.join(output_dir, "context")
    segments_path = os.path.join(context_dir, "segments.json")
    summaries_path = os.path.join(context_dir, "segment_summaries.json")
    
    with open(segments_path, 'r', encoding='utf-8') as f:
        segments = json.load(f)
    
    with open(summaries_path, 'r', encoding='utf-8') as f:
        summaries = json.load(f)
    
    # Create segments directory
    segments_dir = os.path.join(output_dir, "segments")
    os.makedirs(segments_dir, exist_ok=True)
    
    # Template for segment pages with simpler formatting
    segment_template = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; background-color: #fff; margin: 0 auto; padding: 1rem; max-width: 1000px; }}
        h1 {{ font-size: 1.5rem; border-bottom: 1px solid #e0e0e0; padding-bottom: 0.5rem; }}
        .segment-text {{ background-color: #f9f9f9; padding: 1rem; border-radius: 4px; white-space: pre-wrap; }}
        .segment-metadata {{ margin-top: 1rem; padding: 1rem; background-color: #f5f5f5; border-radius: 4px; }}
        .back-link {{ margin-top: 1rem; display: inline-block; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    
    <div class="segment-text">{text}</div>
    
    <div class="segment-metadata">
        <p><strong>ID:</strong> {id}</p>
        <p><strong>Роль:</strong> {role}</p>
    </div>
    
    <a href="{report_path}" class="back-link">Вернуться к отчету</a>
</body>
</html>
"""
    
    # Generate a page for each segment
    for segment_id, segment_text in segments.items():
        if segment_id in summaries:
            summary = summaries[segment_id]
            
            # Get title and role
            title = summary.get('title', f"Сегмент {segment_id}")
            role = summary.get('role', '')
            
            # Create the segment page
            segment_path = os.path.join(segments_dir, f"{segment_id}.html")
            
            # Relative path to report
            report_rel_path = "../report.html"
            
            # Fill the template
            segment_html = segment_template.format(
                title=title,
                text=segment_text,
                id=segment_id,
                role=role,
                report_path=report_rel_path
            )
            
            # Write the segment page
            with open(segment_path, "w", encoding="utf-8") as f:
                f.write(segment_html)
                print(f"Created segment page: {segment_path}")
        else:
            print(f"Warning: No summary found for segment {segment_id}")

if __name__ == "__main__":
    # Set the output directory
    # Find the latest output directory
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
    
    generate_segment_pages(output_dir)
    print("Done!")