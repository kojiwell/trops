"""
Utility functions for trops.
"""
import argparse
import hashlib
import socket
from datetime import datetime


def generate_sid() -> str:
    """
    Generate a session ID by hashing the combination of date, time, and hostname.
    
    Returns:
        A 6-digit hash string.
    """
    # Get current date and time
    now = datetime.now()
    date_time_str = now.strftime("%Y%m%d%H%M%S")
    
    # Get hostname
    hostname = socket.gethostname()
    
    # Combine date, time, and hostname
    combined = f"{date_time_str}{hostname}"
    
    # Create hash and take first 6 characters
    hash_obj = hashlib.md5(combined.encode())
    hash_hex = hash_obj.hexdigest()
    
    return hash_hex[:6]


def handle_gensid(args: argparse.Namespace) -> None:
    """
    Handle the gensid subcommand.
    
    Args:
        args: Command line arguments.
    """
    sid = generate_sid()
    print(sid)


def add_gensid_parser(subparsers: argparse._SubParsersAction) -> None:
    """
    Add the gensid subcommand parser.
    
    Args:
        subparsers: The subparsers object from the main parser.
    """
    gensid_parser = subparsers.add_parser("gensid", help="Generate a session ID")
    gensid_parser.set_defaults(func=handle_gensid)
