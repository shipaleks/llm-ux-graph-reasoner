#!/usr/bin/env python3
"""
Script for improving reports by adding detailed theory descriptions
and information about the knowledge graph expansion process.
"""

import os
import sys
import json
import logging
import time
import argparse
from pathlib import Path
import glob
import re
import shutil

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def find_latest_output_dir(base_dir="output"):
    """Finds the most recent analysis output directory."""
    output_dirs = glob.glob(f"{base_dir}/[0-9]*_[0-9]*")
    if not output_dirs:
        return None
    return sorted(output_dirs)[-1]

def find_theories_file(output_dir):
    """Finds the theories file in the output directory."""
    theories_file = os.path.join(output_dir, "theories", "theories.json")
    if os.path.exists(theories_file):
        return theories_file
    return None

def find_report_file(output_dir):
    """Finds the report file in the output directory."""
    report_file = os.path.join(output_dir, "report.html")
    if os.path.exists(report_file):
        return report_file
    return None

def find_expansion_report(output_dir):
    """Finds the graph expansion report."""
    # First check the expanded graphs folder
    expansion_report = os.path.join(output_dir, "graphs", "expanded", "expansion_report.html")
    if os.path.exists(expansion_report):
        return expansion_report
    
    # Check other possible locations
    expansion_report = os.path.join(output_dir, "expansion_report.html")
    if os.path.exists(expansion_report):
        return expansion_report
    
    # Search for any HTML file related to expansion
    expansion_files = glob.glob(os.path.join(output_dir, "**", "*expansion*.html"), recursive=True)
    if expansion_files:
        return expansion_files[0]
    
    return None

def improve_theories_descriptions(theories_file):
    """Improves theory descriptions by adding details."""
    try:
        with open(theories_file, 'r', encoding='utf-8') as f:
            theories = json.load(f)
        
        if not theories:
            logger.warning("Theories file is empty")
            return False
        
        # For each theory, add an extended description if it doesn't exist
        for theory in theories:
            # If the theory doesn't have a detailed description or it's short
            if "description" not in theory or len(theory["description"]) < 100:
                # Create an extended description from available information
                name = theory.get("name", "")
                summary = theory.get("summary", "")
                
                # Get hypotheses
                hypotheses = theory.get("hypotheses", [])
                hypotheses_text = ""
                for h in hypotheses:
                    statement = h.get("statement", "")
                    if statement:
                        hypotheses_text += f"- {statement}\n"
                
                # Format the extended description
                description = f"""
{summary}

This theory is based on the analysis of the document and the relationships identified within it.

Key hypotheses of the theory:
{hypotheses_text}

The theory proposes to view the presented information as an interconnected structure,
where each element plays a role in the overall picture. This approach allows for a better
understanding of the context and reveals hidden patterns that may not be obvious from a
surface reading of the text.
                """
                
                theory["description"] = description.strip()
        
        # Save the updated theories
        with open(theories_file, 'w', encoding='utf-8') as f:
            json.dump(theories, f, ensure_ascii=False, indent=2)
        
        logger.info("Theories updated with extended descriptions")
        return True
    
    except Exception as e:
        logger.error(f"Error improving theory descriptions: {str(e)}")
        return False

def extract_expansion_info(expansion_report):
    """Extracts information about the graph expansion process."""
    if not expansion_report or not os.path.exists(expansion_report):
        return None
    
    try:
        with open(expansion_report, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract information using regular expressions
        expansion_data = {
            "questions": [],
            "answers": []
        }
        
        # Find all questions
        question_pattern = r'<div class="question">\s*<h4>(.*?)</h4>\s*<p>(.*?)</p>'
        question_matches = re.findall(question_pattern, content, re.DOTALL)
        
        for target, question in question_matches:
            expansion_data["questions"].append({
                "target": target.strip(),
                "question": question.strip()
            })
        
        # Find all answers
        answer_pattern = r'<div class="answer">\s*<h4>(.*?)</h4>\s*<p>(.*?)</p>\s*<div class="confidence">(.*?)</div>'
        answer_matches = re.findall(answer_pattern, content, re.DOTALL)
        
        for question, answer, confidence in answer_matches:
            expansion_data["answers"].append({
                "question": question.strip(),
                "answer": answer.strip(),
                "confidence": confidence.strip()
            })
        
        return expansion_data
    
    except Exception as e:
        logger.error(f"Error extracting expansion information: {str(e)}")
        return None

def create_expansion_section(expansion_data):
    """Creates an HTML section with information about the graph expansion."""
    if not expansion_data:
        return ""
    
    html = """
    <div class="expansion-section">
        <h2>Knowledge Graph Expansion Process</h2>
        <p>During the analysis, the system asked additional questions to expand the knowledge graph.
        This process helps reveal hidden relationships and provides a more complete picture.</p>
        
        <h3>Analysis Questions</h3>
        <div class="expansion-questions">
    """
    
    # Add questions
    questions = expansion_data.get("questions", [])
    if questions:
        html += "<ul>"
        for q in questions:
            html += f'<li><strong>{q.get("target", "")}</strong>: {q.get("question", "")}</li>'
        html += "</ul>"
    else:
        html += "<p>No question information available</p>"
    
    html += """
        </div>
        
        <h3>Answers and New Knowledge</h3>
        <div class="expansion-answers">
    """
    
    # Add answers
    answers = expansion_data.get("answers", [])
    if answers:
        for i, a in enumerate(answers):
            html += f"""
            <div class="expansion-answer">
                <h4>Question {i+1}: {a.get("question", "")}</h4>
                <div class="answer-content">
                    <p>{a.get("answer", "")}</p>
                </div>
                <div class="answer-confidence">Confidence: {a.get("confidence", "")}</div>
            </div>
            """
    else:
        html += "<p>No answer information available</p>"
    
    html += """
        </div>
    </div>
    """
    
    return html

def improve_report(report_file, theories_file, expansion_data):
    """Improves the HTML report by adding detailed information."""
    if not os.path.exists(report_file):
        logger.error(f"Report file not found: {report_file}")
        return False
    
    try:
        # Read the current report
        with open(report_file, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        # Create a backup
        backup_file = report_file + ".bak"
        shutil.copy2(report_file, backup_file)
        logger.info(f"Created report backup: {backup_file}")
        
        # Read updated theories
        theories = []
        if theories_file and os.path.exists(theories_file):
            with open(theories_file, 'r', encoding='utf-8') as f:
                theories = json.load(f)
        
        # Find the theories section in HTML and replace it
        theories_section_pattern = r'<div class="theories-section">.*?</div>\s*<!-- End theories section -->'
        
        if theories:
            # Create a new theories section
            theories_html = """
            <div class="theories-section">
                <h2>Theories and Interpretations</h2>
                <p>Based on the knowledge graph analysis, the system has formulated the following theories:</p>
            """
            
            for i, theory in enumerate(theories):
                name = theory.get("name", f"Theory {i+1}")
                description = theory.get("description", "")
                confidence = theory.get("confidence", 0.0)
                
                theories_html += f"""
                <div class="theory">
                    <h3>{name}</h3>
                    <div class="theory-confidence">Confidence: {confidence:.2f}</div>
                    <div class="theory-description">
                        {description.replace("\n", "<br>")}
                    </div>
                """
                
                # Add hypotheses if they exist
                hypotheses = theory.get("hypotheses", [])
                if hypotheses:
                    theories_html += """
                    <div class="theory-hypotheses">
                        <h4>Key Hypotheses:</h4>
                        <ul>
                    """
                    
                    for h in hypotheses:
                        statement = h.get("statement", "")
                        if statement:
                            theories_html += f"<li>{statement}</li>"
                    
                    theories_html += """
                        </ul>
                    </div>
                    """
                
                theories_html += "</div>"
            
            theories_html += """
            </div><!-- End theories section -->
            """
            
            # Replace the theories section
            if re.search(theories_section_pattern, report_content, re.DOTALL):
                report_content = re.sub(theories_section_pattern, theories_html, report_content, flags=re.DOTALL)
            else:
                # If there's no theories section, add before the closing body tag
                report_content = report_content.replace("</body>", f"{theories_html}\n</body>")
        
        # Add the graph expansion information section
        expansion_html = create_expansion_section(expansion_data)
        if expansion_html:
            # Check if there's already an expansion section
            expansion_section_pattern = r'<div class="expansion-section">.*?</div>\s*<!-- End expansion section -->'
            
            if re.search(expansion_section_pattern, report_content, re.DOTALL):
                report_content = re.sub(expansion_section_pattern, expansion_html, report_content, flags=re.DOTALL)
            else:
                # Add before the closing body tag, but after the theories section
                expansion_html += "<!-- End expansion section -->"
                report_content = report_content.replace("</body>", f"{expansion_html}\n</body>")
        
        # Add CSS for the new sections
        css_styles = """
        <style>
            .expansion-section {
                margin: 20px 0;
                padding: 15px;
                background-color: #f5f9ff;
                border-left: 4px solid #4a90e2;
                border-radius: 4px;
            }
            .expansion-questions ul {
                list-style-type: disc;
                margin-left: 20px;
            }
            .expansion-answer {
                margin-bottom: 20px;
                background-color: #f8f8f8;
                padding: 15px;
                border-left: 3px solid #666;
                border-radius: 4px;
            }
            .answer-content {
                margin: 10px 0;
            }
            .answer-confidence {
                font-style: italic;
                color: #666;
            }
            .theory {
                margin-bottom: 30px;
                background-color: #f5f9ff;
                padding: 15px;
                border-left: 4px solid #4a90e2;
                border-radius: 4px;
            }
            .theory-description {
                margin: 15px 0;
                line-height: 1.6;
            }
            .theory-confidence {
                font-style: italic;
                color: #555;
                margin-bottom: 10px;
            }
            .theory-hypotheses {
                background-color: #f8f8f8;
                padding: 15px;
                border-radius: 4px;
                margin-top: 15px;
            }
            .theory-hypotheses ul {
                list-style-type: disc;
                margin-left: 20px;
            }
        </style>
        """
        
        # Add styles before the closing head tag
        if "</head>" in report_content and not "<style>" in report_content:
            report_content = report_content.replace("</head>", f"{css_styles}\n</head>")
        
        # Save the updated report
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        # Create the improved version of the report
        improved_report_file = os.path.join(os.path.dirname(report_file), "improved_report.html")
        with open(improved_report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Report improved and saved: {improved_report_file}")
        return improved_report_file
    
    except Exception as e:
        logger.error(f"Error improving report: {str(e)}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Improve report by adding details about theories and graph expansion")
    parser.add_argument(
        "--dir", "-d",
        help="Directory with analysis results (defaults to finding the most recent)",
        default=None
    )
    parser.add_argument(
        "--force", "-f",
        help="Force create an improved report, even if it already exists",
        action="store_true"
    )
    
    args = parser.parse_args()
    
    # Determine the results directory
    output_dir = args.dir
    if not output_dir:
        output_dir = find_latest_output_dir()
        if not output_dir:
            logger.error("Could not find analysis results directory")
            return 1
    
    logger.info(f"Working with directory: {output_dir}")
    
    # Check if an improved report already exists
    improved_report = os.path.join(output_dir, "improved_report.html")
    if os.path.exists(improved_report) and not args.force:
        logger.info(f"Improved report already exists: {improved_report}")
        print(f"\nImproved report already exists: {improved_report}")
        return 0
    
    # Find necessary files
    theories_file = find_theories_file(output_dir)
    if not theories_file:
        logger.warning("Theories file not found")
    
    report_file = find_report_file(output_dir)
    if not report_file:
        logger.error("Report file not found")
        return 1
    
    expansion_report = find_expansion_report(output_dir)
    if expansion_report:
        logger.info(f"Found graph expansion report: {expansion_report}")
        expansion_data = extract_expansion_info(expansion_report)
    else:
        logger.warning("Graph expansion report not found")
        expansion_data = None
    
    # Improve theory descriptions
    if theories_file:
        improve_theories_descriptions(theories_file)
    
    # Improve the report
    result = improve_report(report_file, theories_file, expansion_data)
    
    if result:
        print(f"\n✅ Report successfully improved: {result}")
        print("You can open it in your browser.")
        return 0
    else:
        print("\n❌ Failed to improve report.")
        return 1

if __name__ == "__main__":
    sys.exit(main())