"""Command-line interface for the knowledge graph synthesis system.

This module provides the command-line interface for the system, including
commands for processing files, managing knowledge graphs, and interacting
with LLM providers.
"""

from .commands import main, setup_parser, process_file, list_providers
from .utils import (
    print_header, print_success, print_error, print_warning,
    print_table, verify_file_exists, ensure_directory_exists
)

__all__ = [
    "main",
    "setup_parser",
    "process_file",
    "list_providers",
    "print_header",
    "print_success",
    "print_error",
    "print_warning",
    "print_table",
    "verify_file_exists",
    "ensure_directory_exists"
]