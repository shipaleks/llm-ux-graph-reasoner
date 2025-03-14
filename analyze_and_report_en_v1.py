#!/usr/bin/env python3
"""
Wrapper script for running text analysis and automatically creating an improved report in English.
"""

import os
import sys
import subprocess
import logging
import time
import argparse
from pathlib import Path

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def main():
    """Main function."""
    # Create argument parser
    parser = argparse.ArgumentParser(
        description="Run text analysis with automatic report improvement in English"
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
        "--expand", "-e",
        action="store_true",
        help="Expand the graph through question asking"
    )
    
    parser.add_argument(
        "--theories", "-t",
        action="store_true",
        help="Generate theories based on the graph"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="output",
        help="Directory for output results (default: output)"
    )
    
    parser.add_argument(
        "--max-segments", "-m",
        type=int,
        default=None,
        help="Maximum number of segments to process (for testing)"
    )
    
    args = parser.parse_args()
    
    # Check if the file exists
    if not os.path.exists(args.file_path):
        logger.error(f"File not found: {args.file_path}")
        return 1
    
    # Form the command for analyze_text.py
    cmd = ["./analyze_text.py", args.file_path, "--provider", args.provider, "--output", args.output]
    
    if args.expand:
        cmd.append("--expand")
    
    if args.theories:
        cmd.append("--theories")
    
    if args.max_segments:
        cmd.extend(["--max-segments", str(args.max_segments)])
    
    # Run the analysis
    print(f"🔍 Starting text analysis: {args.file_path}")
    logger.info(f"Executing command: {' '.join(cmd)}")
    
    try:
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        analyze_duration = time.time() - start_time
        
        if result.returncode != 0:
            logger.error(f"Error executing analysis: {result.stderr}")
            print(f"❌ Error executing analysis. See log for details.")
            return 1
        
        # Output the analysis result
        print(result.stdout)
        
        # Extract the path to the output directory from the output
        output_dir = None
        for line in result.stdout.split('\n'):
            if "navigate to:" in line:
                output_dir = line.split(":")[-1].strip()
                break
        
        if not output_dir or not os.path.exists(output_dir):
            logger.warning("Could not determine the results directory")
            return 1
        
        # Run report improvement with our English generator
        print(f"\n🔄 Creating improved English report...")
        logger.info(f"Starting English report improvement for directory: {output_dir}")
        
        improve_cmd = ["./improve_report_en.py", "--dir", output_dir, "--force"]
        improve_result = subprocess.run(improve_cmd, capture_output=True, text=True)
        
        if improve_result.returncode != 0:
            logger.warning(f"Warning when improving report: {improve_result.stderr}")
            print(f"⚠️ Warning when creating improved English report.")
        else:
            # Find the path to the improved report in the output
            improved_report_path = None
            for line in improve_result.stdout.split('\n'):
                if "successfully improved:" in line:
                    improved_report_path = line.split(":")[-1].strip()
                    break
            
            if improved_report_path and os.path.exists(improved_report_path):
                total_duration = time.time() - start_time
                print(f"\n✅ Analysis and report improvement completed in {total_duration:.2f} seconds")
                print(f"📊 Improved English report created: {improved_report_path}")
                print("🌐 You can open it in your browser.")
            else:
                print(f"\n⚠️ Analysis completed, but the improved English report was not created.")
                print(f"📊 Standard report available at: {output_dir}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"❌ An error occurred: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())