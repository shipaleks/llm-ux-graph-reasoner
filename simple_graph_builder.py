#!/usr/bin/env python3
"""
Simpler script for generating answers to questions about a text with explanations.
This version uses fewer API calls to avoid Gemini quota limits.
"""

import os
import sys
import json
import logging
import time
import argparse
from pathlib import Path
import re

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Add src directory to path
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, src_dir)

# Import components from the knowledge_graph_synth package
from knowledge_graph_synth.llm import LLMProviderFactory

def generate_answer_with_reasoning(text, question, provider_name="gemini"):
    """Use deep reasoning to answer a question about the text."""
    try:
        # Get LLM provider
        provider = LLMProviderFactory.get_reasoning_provider()
        if not provider:
            provider = LLMProviderFactory.get_provider(provider_name)
        
        # Create the prompt
        prompt = f"""
        You are analyzing a complex narrative text and need to answer an important question about it.
        
        Text:
        {text}
        
        Question: {question}
        
        Use the following process to analyze the text and answer the question:
        
        STEP 1: EVIDENCE GATHERING
        - Identify all relevant information from the text related to the question
        - Note direct statements and implied information
        - Consider references, actions, dialog, and descriptions
        
        STEP 2: INFERENCE AND ANALYSIS
        - Connect pieces of evidence to form a coherent picture
        - Consider motivations, hidden meanings, and subtext
        - Identify gaps in information and make reasonable inferences
        - Think about what is NOT stated but can be reasonably inferred
        
        STEP 3: HYPOTHESIS FORMATION
        - Form a detailed hypothesis that answers the question
        - Consider alternative explanations and their likelihood
        - Evaluate the strength of your hypothesis based on available evidence
        
        STEP 4: ANSWER SYNTHESIS
        - Provide a comprehensive answer to the question
        - Include direct evidence and justified inferences
        - Clearly distinguish between what is explicitly stated and what is inferred
        - Rate your confidence in the answer (0-1 scale)
        
        Format your response as a structured analysis with clear headings for each step.
        """
        
        # Generate the answer
        response = provider.generate_text(prompt)
        return response
    
    except Exception as e:
        logger.error(f"Error generating answer: {str(e)}")
        return f"Error: {str(e)}"

def generate_theory(text, provider_name="gemini"):
    """Generate a comprehensive theory about the story."""
    try:
        # Get LLM provider
        provider = LLMProviderFactory.get_reasoning_provider()
        if not provider:
            provider = LLMProviderFactory.get_provider(provider_name)
        
        # Create the prompt
        prompt = f"""
        Based on the following text, generate a comprehensive theory
        that explains the central mystery or plot of the story.
        
        Text:
        {text}
        
        Your theory should:
        1. Provide a clear explanation of the central events and mystery
        2. Connect the key entities and their motivations
        3. Explain any unresolved questions or ambiguities
        4. Be well-supported by evidence from the text
        5. Consider alternative explanations where appropriate
        
        Format your response with these sections:
        1. Theory Title: A descriptive title for your theory
        2. Summary: A brief 2-3 sentence summary
        3. Detailed Explanation: A comprehensive explanation of your theory
        4. Key Evidence: Specific references from the text that support your theory
        5. Key Entities and Roles: How the main entities fit into your theory
        6. Unresolved Questions: Any aspects that remain unclear or could be explored further
        7. Confidence: Your confidence in this theory (0-1 scale)
        """
        
        # Generate the theory
        response = provider.generate_text(prompt)
        return response
    
    except Exception as e:
        logger.error(f"Error generating theory: {str(e)}")
        return f"Error: {str(e)}"

def generate_html_report(file_path, questions, answers, theory=None):
    """Generate an HTML report of the questions, answers, and theory."""
    # Get filename
    filename = os.path.basename(file_path)
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analysis: {filename}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        header {{
            background-color: #f5f5f5;
            padding: 20px;
            margin-bottom: 30px;
            border-radius: 5px;
            border-left: 5px solid #4a90e2;
        }}
        
        h1, h2, h3, h4 {{
            color: #2c3e50;
        }}
        
        .question-answer {{
            background-color: #f9f9f9;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
            border-left: 3px solid #777;
        }}
        
        .question {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 1.2rem;
        }}
        
        .answer {{
            margin-left: 0;
            padding: 10px;
            background-color: #fff;
            border-radius: 5px;
            white-space: pre-wrap;
        }}
        
        .theory {{
            background-color: #f5f5ff;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
            border-left: 5px solid #7159c1;
            white-space: pre-wrap;
        }}
    </style>
</head>
<body>
    <header>
        <h1>Deep Analysis: {filename}</h1>
        <p>Analysis Date: {time.strftime("%Y-%m-%d %H:%M:%S")}</p>
    </header>
    
    <h2>Key Questions and Insights</h2>
"""
    
    # Add questions and answers
    for i, (question, answer) in enumerate(zip(questions, answers)):
        html += f"""
    <div class="question-answer">
        <div class="question">{i+1}. {question}</div>
        <div class="answer">{answer}</div>
    </div>
"""
    
    # Add theory if provided
    if theory:
        html += f"""
    <h2>Comprehensive Theory</h2>
    <div class="theory">{theory}</div>
"""
    
    # Close HTML
    html += """
</body>
</html>
"""
    
    return html

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run deep analysis on a text file with specific questions."
    )
    
    parser.add_argument(
        "file_path",
        help="Path to the text file for analysis"
    )
    
    parser.add_argument(
        "--provider", "-p",
        default="gemini",
        choices=["gemini", "openai"],
        help="LLM provider for analysis (default: gemini)"
    )
    
    parser.add_argument(
        "--theory", "-t",
        action="store_true",
        help="Generate a comprehensive theory"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="output",
        help="Directory for output results (default: output)"
    )
    
    return parser.parse_args()

def main():
    """Main function for running the analysis."""
    args = parse_arguments()
    
    try:
        # Load the text file
        path = Path(args.file_path)
        if not path.exists():
            print(f"Error: File not found: {args.file_path}")
            return 1
        
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Define key questions about the text
        # These are more focused on story analysis and would be better for "solving" the mystery
        questions = [
            "What is the central mystery in this story, and what clues are provided throughout the text?",
            "What are the key relationships between characters, and how do these relationships contribute to the plot?",
            "What is the significance of Eleanor's disappearance, and what theories can we formulate about what actually happened to her?",
            "What role does the book 'The Silent Echo' play in the story, and how might it connect to Eleanor's disappearance?",
            "Based on all available evidence in the text, who is most likely responsible for Eleanor's disappearance, and why?"
        ]
        
        print(f"🔍 Starting deep analysis on: {args.file_path}")
        start_time = time.time()
        
        # Create output directory
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join(args.output, timestamp)
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate answers for each question
        answers = []
        for i, question in enumerate(questions):
            print(f"Analyzing question {i+1}/{len(questions)}: {question}")
            answer = generate_answer_with_reasoning(text, question, args.provider)
            answers.append(answer)
        
        # Generate a theory if requested
        theory = None
        if args.theory:
            print("Generating comprehensive theory...")
            theory = generate_theory(text, args.provider)
        
        # Generate HTML report
        report_html = generate_html_report(args.file_path, questions, answers, theory)
        report_path = os.path.join(output_dir, "deep_analysis.html")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_html)
        
        elapsed_time = time.time() - start_time
        print(f"\n✅ Analysis completed in {elapsed_time:.2f} seconds")
        print(f"📊 Report generated: {report_path}")
        print("🌐 You can view the report in your browser.")
        
        return 0
    
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())