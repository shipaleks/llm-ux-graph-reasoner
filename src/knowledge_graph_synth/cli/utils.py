"""Command-line interface utilities for the knowledge graph synthesis system."""

import logging
import sys
import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from rich.syntax import Syntax
from rich.markdown import Markdown

from ..config import settings

logger = logging.getLogger(__name__)
console = Console()


def print_header(text: str):
    """Print a header with formatting.
    
    Args:
        text: Header text
    """
    console.print(f"\n[bold blue]{text}[/bold blue]")
    console.print("=" * len(text))


def print_success(text: str):
    """Print a success message with formatting.
    
    Args:
        text: Success message
    """
    console.print(f"[bold green]✓ {text}[/bold green]")


def print_error(text: str):
    """Print an error message with formatting.
    
    Args:
        text: Error message
    """
    console.print(f"[bold red]✗ {text}[/bold red]")


def print_warning(text: str):
    """Print a warning message with formatting.
    
    Args:
        text: Warning message
    """
    console.print(f"[bold yellow]⚠ {text}[/bold yellow]")


def print_table(title: str, columns: List[str], rows: List[List[Any]]):
    """Print a table with formatting.
    
    Args:
        title: Table title
        columns: Column headers
        rows: Table rows
    """
    table = Table(title=title)
    
    # Add columns
    for column in columns:
        table.add_column(column)
    
    # Add rows
    for row in rows:
        table.add_row(*[str(cell) for cell in row])
    
    console.print(table)


def create_progress_bar(description: str, total: int) -> Progress:
    """Create a progress bar.
    
    Args:
        description: Description of the task
        total: Total number of steps
        
    Returns:
        Progress bar instance
    """
    progress = Progress()
    task = progress.add_task(description, total=total)
    return progress, task


def verify_file_exists(file_path: str) -> bool:
    """Verify that a file exists.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if the file exists, False otherwise
    """
    path = Path(file_path)
    if not path.exists():
        print_error(f"File not found: {file_path}")
        return False
    
    if not path.is_file():
        print_error(f"Not a file: {file_path}")
        return False
    
    return True


def ensure_directory_exists(dir_path: str) -> bool:
    """Ensure that a directory exists, creating it if necessary.
    
    Args:
        dir_path: Path to the directory
        
    Returns:
        True if the directory exists or was created, False otherwise
    """
    path = Path(dir_path)
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print_error(f"Error creating directory {dir_path}: {str(e)}")
        return False
        
        
def create_timestamped_dir(base_dir: str) -> Tuple[str, str]:
    """Create a timestamped directory within the base directory.
    
    Args:
        base_dir: Base directory path
        
    Returns:
        Tuple containing:
          - Full path to the created timestamped directory
          - Timestamp string that was used
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(base_dir, timestamp)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    logger.info(f"Created timestamped output directory: {output_dir}")
    return output_dir, timestamp


def get_subdirectory_path(base_dir: str, subdir_name: str) -> str:
    """Get path to a subdirectory, creating it if it doesn't exist.
    
    Args:
        base_dir: Base directory path
        subdir_name: Name of the subdirectory
        
    Returns:
        Path to the subdirectory
    """
    subdir_path = os.path.join(base_dir, subdir_name)
    Path(subdir_path).mkdir(parents=True, exist_ok=True)
    return subdir_path


def get_relative_path(from_path: str, to_path: str, validate: bool = True) -> str:
    """Get a relative path from one file to another.
    
    Args:
        from_path: Source file path
        to_path: Target file path
        validate: Whether to validate that both paths exist
        
    Returns:
        Relative path from source to target
    """
    if validate:
        if not os.path.exists(from_path) and not os.path.isdir(from_path):
            logger.warning(f"Source path doesn't exist: {from_path}")
        if not os.path.exists(to_path):
            logger.warning(f"Target path doesn't exist: {to_path}")
    
    from_dir = os.path.dirname(from_path) if not os.path.isdir(from_path) else from_path
    return os.path.relpath(to_path, from_dir)


def resolve_asset_path(output_dir: str, asset_path: str) -> str:
    """Resolve an asset path regardless of whether it's in a timestamped directory.
    
    This function finds a file in the output directory structure, even if the
    output_dir is a timestamped directory.
    
    Args:
        output_dir: Output directory path (may be timestamped)
        asset_path: Relative path to the asset from the output directory
        
    Returns:
        Absolute path to the asset
    """
    # First check if the asset exists directly under output_dir
    direct_path = os.path.join(output_dir, asset_path)
    if os.path.exists(direct_path):
        return direct_path
    
    # Check if output_dir is already a timestamped directory
    if os.path.basename(output_dir).find("_") > 0 and os.path.basename(output_dir)[:8].isdigit():
        # We're already in a timestamped directory, look in parent
        parent_dir = os.path.dirname(output_dir)
        parent_path = os.path.join(parent_dir, asset_path)
        if os.path.exists(parent_path):
            return parent_path
    
    # Check subdirectories for timestamped directories
    for item in os.listdir(output_dir):
        item_path = os.path.join(output_dir, item)
        if os.path.isdir(item_path):
            # Check if this might be a timestamped directory
            if item.find("_") > 0 and item[:8].isdigit():
                # Look in this timestamped directory
                timestamped_path = os.path.join(item_path, asset_path)
                if os.path.exists(timestamped_path):
                    return timestamped_path
    
    # Asset not found, return the direct path anyway
    logger.warning(f"Asset not found: {asset_path} in {output_dir}")
    return direct_path


def is_timestamped_dir(dir_path: str) -> bool:
    """Check if a directory path is a timestamped directory.
    
    Args:
        dir_path: Directory path to check
        
    Returns:
        True if the directory name follows the timestamp pattern
    """
    if not os.path.isdir(dir_path):
        return False
    
    dir_name = os.path.basename(dir_path)
    # Check for pattern like "20250306_121530"
    return (len(dir_name) >= 15 and 
            dir_name.find("_") == 8 and 
            dir_name[:8].isdigit() and 
            dir_name[9:].isdigit())


def find_output_files(output_dir: str) -> Dict[str, List[str]]:
    """Find all output files in the given directory.
    
    Args:
        output_dir: Path to the output directory
        
    Returns:
        Dictionary mapping file categories to file paths
    """
    result = {
        "entities": [],
        "relationships": [],
        "graphs": [],
        "theories": [],
        "contextual": [],
        "reports": [],
        "other": []
    }
    
    # Map extensions to categories
    extension_map = {
        ".json": "other",
        ".html": "graphs",
        ".md": "reports",
        ".txt": "other"
    }
    
    # Map directories to categories
    directory_map = {
        "entities": "entities",
        "relationships": "relationships",
        "graphs": "graphs",
        "theories": "theories",
        "context": "contextual"
    }
    
    # Find all files
    for root, dirs, files in os.walk(output_dir):
        relative_root = os.path.relpath(root, output_dir)
        
        # Determine category based on directory
        category = "other"
        for dir_key, dir_category in directory_map.items():
            if dir_key in relative_root:
                category = dir_category
                break
        
        for file in files:
            file_path = os.path.join(root, file)
            
            # Determine category based on file extension and name
            ext = os.path.splitext(file)[1].lower()
            file_category = extension_map.get(ext, "other")
            
            # Override category for specific file names
            if "entity" in file.lower() or "entities" in file.lower():
                file_category = "entities"
            elif "relationship" in file.lower() or "relations" in file.lower():
                file_category = "relationships"
            elif "graph" in file.lower():
                file_category = "graphs"
            elif "theory" in file.lower() or "theories" in file.lower():
                file_category = "theories"
            elif "segment" in file.lower() or "context" in file.lower() or "summary" in file.lower() or "connection" in file.lower():
                file_category = "contextual"
            elif ext == ".md" or "report" in file.lower():
                file_category = "reports"
            
            # Use directory category if more specific
            if category != "other":
                file_category = category
                
            result[file_category].append(file_path)
    
    return result


def display_output_summary(output_dir: str):
    """Display a summary of output files.
    
    Args:
        output_dir: Path to the output directory
    """
    if not os.path.exists(output_dir):
        print_error(f"Output directory not found: {output_dir}")
        return
    
    files = find_output_files(output_dir)
    
    print_header("Output Summary")
    
    total_files = sum(len(files[category]) for category in files)
    
    if total_files == 0:
        print_warning("No output files found.")
        return
    
    rows = []
    for category, paths in files.items():
        if paths:
            rows.append([category.capitalize(), len(paths)])
    
    print_table("Files Generated", ["Category", "Count"], rows)
    
    # Print details about main outputs
    # Check for research report first
    report_paths = [p for p in files.get("other", []) if p.endswith("report.html")]
    if report_paths:
        print_header("Research Report")
        for path in report_paths:
            print_success(f"Comprehensive research report")
            print(f"  View in browser: file://{os.path.abspath(path)}")
    
    if files["graphs"]:
        print_header("Graph Visualizations")
        for path in files["graphs"]:
            if path.endswith(".html"):
                print_success(f"Graph: {os.path.basename(path)}")
                print(f"  View in browser: file://{os.path.abspath(path)}")
    
    if files["contextual"]:
        print_header("Contextual Analysis")
        for path in files["contextual"]:
            if path.endswith(".json"):
                print_success(f"Contextual data: {os.path.basename(path)}")
    
    if files["reports"]:
        print_header("Reports")
        for path in files["reports"]:
            if path.endswith(".md"):
                print_success(f"Report: {os.path.basename(path)}")
                
    if files["theories"]:
        print_header("Theories")
        for path in files["theories"]:
            if "theories.md" in path.lower():
                print_success(f"Theories report: {os.path.basename(path)}")
    
    print("\nTo view output files, navigate to:")
    print(f"  {os.path.abspath(output_dir)}")