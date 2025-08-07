"""
Capcmd module for handling capcmd-related functionality.
"""
import argparse
import os
import sys


def process_command(exit_code: int, executed_command: list) -> str:
    """
    Process a command for the capcmd command.

    Args:
        exit_code: The exit code of the executed command.
        executed_command: List of command parts that were executed.

    Returns:
        The processed command information.
    """
    command_str = " ".join(executed_command)
    return f"Command executed: {command_str} (exit code: {exit_code})"


def handle_capcmd(args: argparse.Namespace) -> None:
    """
    Handle the capcmd subcommand.

    Args:
        args: Command line arguments.
    """
    # Check if TROPS_DIR environment variable exists
    trops_dir = os.getenv("TROPS_DIR")
    if not trops_dir:
        print("Error: TROPS_DIR environment variable is not set.", file=sys.stderr)
        print("Please set TROPS_DIR to specify the directory for trops operations.", file=sys.stderr)
        sys.exit(1)
    
    # Check if TROPS_DIR/log directory exists
    log_dir = os.path.join(trops_dir, "log")
    if not os.path.exists(log_dir):
        print(f"Error: Log directory does not exist: {log_dir}", file=sys.stderr)
        print(f"Please create the log directory at {log_dir}", file=sys.stderr)
        sys.exit(1)
    
    if not os.path.isdir(log_dir):
        print(f"Error: {log_dir} exists but is not a directory.", file=sys.stderr)
        sys.exit(1)
    
    print(f"Using TROPS_DIR: {trops_dir}")
    print(f"Log directory: {log_dir}")
    result = process_command(args.exit_code, args.executed_command)
    print(result)


def add_capcmd_parser(subparsers: argparse._SubParsersAction) -> None:
    """
    Add the capcmd subcommand parser.

    Args:
        subparsers: The subparsers object from the main parser.
    """
    capcmd_parser = subparsers.add_parser("capcmd", help="Capture command execution")
    capcmd_parser.add_argument(
        "exit_code",
        type=int,
        help="Exit code of the executed command",
    )
    capcmd_parser.add_argument(
        "executed_command",
        nargs="+",
        help="The command that was executed (one or more arguments)",
    )
    capcmd_parser.set_defaults(func=handle_capcmd) 