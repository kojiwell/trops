"""
Capcmd module for handling capcmd-related functionality.
"""
import argparse


def process_message(message: str) -> str:
    """
    Process a message for the capcmd command.

    Args:
        message: The message to process.

    Returns:
        The processed message.
    """
    return f"Capcmd command with message: {message}"


def handle_capcmd(args: argparse.Namespace) -> None:
    """
    Handle the capcmd subcommand.

    Args:
        args: Command line arguments.
    """
    result = process_message(args.message)
    print(result)


def add_capcmd_parser(subparsers: argparse._SubParsersAction) -> None:
    """
    Add the capcmd subcommand parser.

    Args:
        subparsers: The subparsers object from the main parser.
    """
    capcmd_parser = subparsers.add_parser("capcmd", help="Capcmd command")
    capcmd_parser.add_argument(
        "--message",
        "-m",
        required=True,
        help="Message to process",
    )
    capcmd_parser.set_defaults(func=handle_capcmd) 