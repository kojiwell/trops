"""
Main module for the project.
"""
import argparse
import sys

from trops.capcmd import add_capcmd_parser
from trops.initialize import add_init_parser
from trops.utils import add_gensid_parser


def hello(name: str = "World") -> str:
    """
    Return a greeting message.

    Args:
        name: Name to greet. Defaults to "World".

    Returns:
        A greeting message.
    """
    return f"Hello, {name}!"


def main() -> None:
    """Main entry point for the application."""
    # If no arguments are provided, show help
    if len(sys.argv) == 1:
        sys.argv.append("--help")

    parser = argparse.ArgumentParser(description="Trops command-line tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

    # Hello command
    hello_parser = subparsers.add_parser("hello", help="Greet someone")
    hello_parser.add_argument(
        "--name",
        "-n",
        default="World",
        help="Name to greet (default: World)",
    )
    hello_parser.set_defaults(func=lambda args: print(hello(args.name)))

    # Add capcmd subcommand
    add_capcmd_parser(subparsers)

    # Add init subcommand
    add_init_parser(subparsers)

    # Add gensid subcommand
    add_gensid_parser(subparsers)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main() 