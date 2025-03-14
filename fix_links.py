#!/usr/bin/env python3
"""
Fix segment links in all reports.
This standalone script fixes broken segment links in existing reports.
"""

import os
import re
import json
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def fix_segment_links(report_dir):
    """Fix segment links in a report file.
    
    Args:
        report_dir: Directory containing the report.html file
    """
    report_path = os.path.join(report_dir, "report.html")
    if not os.path.exists(report_path):
        logger.warning(f"Report file not found: {report_path}")
        return False
        
    try:
        # Read the report file
        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Fix the segment links
        fixed_content = re.sub(r'href="segments/', r'href="./segments/', content)
        
        # Only write if changes were made
        if fixed_content != content:
            # Write the updated content back
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
                
            logger.info(f"Fixed segment links in report file: {report_path}")
            return True
        else:
            logger.info(f"No segment links needed fixing in: {report_path}")
            return True
    except Exception as e:
        logger.error(f"Error fixing report segment links in {report_path}: {str(e)}")
        return False

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
            return False
            
        # Check if segments.json and segment_summaries.json exist
        segments_path = os.path.join(context_dir, "segments.json")
        summaries_path = os.path.join(context_dir, "segment_summaries.json")
        
        if not os.path.exists(segments_path) or not os.path.exists(summaries_path):
            logger.warning(f"Missing segment data files in {context_dir}")
            return False
            
        # Load segments and summaries
        with open(segments_path, 'r', encoding='utf-8') as f:
            segments = json.load(f)
        
        with open(summaries_path, 'r', encoding='utf-8') as f:
            summaries = json.load(f)
        
        # Create segments directory if it doesn't exist
        segments_dir = os.path.join(output_dir, "segments")
        os.makedirs(segments_dir, exist_ok=True)
        
        # Check if any segment pages are missing
        missing_segments = []
        for segment_id in summaries.keys():
            segment_path = os.path.join(segments_dir, f"{segment_id}.html")
            if not os.path.exists(segment_path):
                missing_segments.append(segment_id)
        
        if not missing_segments:
            logger.info(f"All segment pages exist in {segments_dir}")
            return True
        else:
            logger.info(f"Found {len(missing_segments)} missing segment pages, creating them now...")
            
        # Template for segment pages
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
        
        # Generate segment pages for missing segments
        created_count = 0
        for segment_id in missing_segments:
            if segment_id in segments and segment_id in summaries:
                segment_text = segments[segment_id]
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
        
        logger.info(f"Created {created_count} missing segment pages in {segments_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Error ensuring segment pages: {str(e)}")
        return False

def fix_all_reports(base_dir, recursive=True):
    """Fix segment links in all reports in a directory.
    
    Args:
        base_dir: Base directory to search for reports
        recursive: Whether to search recursively
    """
    fixed_count = 0
    error_count = 0
    
    if recursive:
        logger.info(f"Recursively searching for reports in {base_dir}...")
        for root, dirs, files in os.walk(base_dir):
            if "report.html" in files:
                logger.info(f"Found report in: {root}")
                if fix_segment_links(root):
                    fixed_count += 1
                else:
                    error_count += 1
                
                # Ensure segment pages exist
                ensure_segment_pages(root)
    else:
        logger.info(f"Fixing report in {base_dir}...")
        if fix_segment_links(base_dir):
            fixed_count += 1
        else:
            error_count += 1
        
        # Ensure segment pages exist
        ensure_segment_pages(base_dir)
    
    logger.info(f"Fixed {fixed_count} reports, encountered {error_count} errors")
    return fixed_count, error_count

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix segment links in reports")
    parser.add_argument(
        "--dir", "-d",
        help="Directory containing reports (default: output)",
        default="output"
    )
    parser.add_argument(
        "--recursive", "-r",
        help="Recursively search for reports in subdirectories",
        action="store_true",
        default=True
    )
    
    args = parser.parse_args()
    
    fixed, errors = fix_all_reports(args.dir, args.recursive)
    
    if errors > 0:
        sys.exit(1)
    sys.exit(0)