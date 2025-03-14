"""Fix for the segment links in HTML report generation."""

import json
import os
import re
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def ensure_segment_pages(output_dir):
    """Ensure that segment pages are created for the report.
    
    Args:
        output_dir: The output directory containing the report and context data
    """
    try:
        # Check if context directory exists
        context_dir = os.path.join(output_dir, "context")
        if not os.path.exists(context_dir):
            logger.warning(f"Context directory not found: {context_dir}")
            return
            
        # Check if segments.json and segment_summaries.json exist
        segments_path = os.path.join(context_dir, "segments.json")
        summaries_path = os.path.join(context_dir, "segment_summaries.json")
        
        if not os.path.exists(segments_path) or not os.path.exists(summaries_path):
            logger.warning(f"Missing segment data files in {context_dir}")
            return
            
        # Load segments and summaries
        with open(segments_path, 'r', encoding='utf-8') as f:
            segments = json.load(f)
        
        with open(summaries_path, 'r', encoding='utf-8') as f:
            summaries = json.load(f)
        
        # Create segments directory if it doesn't exist
        segments_dir = os.path.join(output_dir, "segments")
        os.makedirs(segments_dir, exist_ok=True)
        
        # Check if any segment pages already exist
        if len(os.listdir(segments_dir)) > 0:
            logger.info(f"Segment pages already exist in {segments_dir}")
            return
            
        # Template for segment pages with proper escaping
        segment_template = (
            "<!DOCTYPE html>\n"
            "<html lang=\"ru\">\n"
            "<head>\n"
            "    <meta charset=\"UTF-8\">\n"
            "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
            "    <title>{title}</title>\n"
            "    <style>\n"
            "        body {\n"
            "            font-family: Arial, sans-serif;\n"
            "            line-height: 1.6;\n"
            "            color: #333;\n"
            "            background-color: #fff;\n"
            "            margin: 0 auto;\n"
            "            padding: 1rem;\n"
            "            max-width: 1000px;\n"
            "        }\n"
            "        h1 {\n"
            "            font-size: 1.5rem;\n"
            "            border-bottom: 1px solid #e0e0e0;\n"
            "            padding-bottom: 0.5rem;\n"
            "        }\n"
            "        .segment-text {\n"
            "            background-color: #f9f9f9;\n"
            "            padding: 1rem;\n"
            "            border-radius: 4px;\n"
            "            white-space: pre-wrap;\n"
            "        }\n"
            "        .segment-metadata {\n"
            "            margin-top: 1rem;\n"
            "            padding: 1rem;\n"
            "            background-color: #f5f5f5;\n"
            "            border-radius: 4px;\n"
            "        }\n"
            "        .back-link {\n"
            "            margin-top: 1rem;\n"
            "            display: inline-block;\n"
            "        }\n"
            "    </style>\n"
            "</head>\n"
            "<body>\n"
            "    <h1>{title}</h1>\n"
            "    \n"
            "    <div class=\"segment-text\">{text}</div>\n"
            "    \n"
            "    <div class=\"segment-metadata\">\n"
            "        <p><strong>ID:</strong> {id}</p>\n"
            "        <p><strong>Роль:</strong> {role}</p>\n"
            "    </div>\n"
            "    \n"
            "    <a href=\"{report_path}\" class=\"back-link\">Вернуться к отчету</a>\n"
            "</body>\n"
            "</html>"
        )
        
        # Generate segment pages
        created_count = 0
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
                    created_count += 1
        
        logger.info(f"Created {created_count} segment pages in {segments_dir}")
        
        # Fix the links in the report file if it exists
        fix_report_segment_links(output_dir)
        
    except Exception as e:
        logger.error(f"Error ensuring segment pages: {str(e)}")


def fix_report_segment_links(output_dir):
    """Fix segment links in existing report files.
    
    Args:
        output_dir: The output directory containing the report file
    """
    try:
        report_path = os.path.join(output_dir, "report.html")
        if not os.path.exists(report_path):
            logger.warning(f"Report file not found: {report_path}")
            return
            
        # Read the report file
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Fix the segment links (both English and Russian versions)
        content = re.sub(r'href="segments/', r'href="./segments/', content)
        
        # Write the updated content back
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info(f"Fixed segment links in report file: {report_path}")
        
    except Exception as e:
        logger.error(f"Error fixing report segment links: {str(e)}")