"""
Tests for the main module.
"""

from trops3.main import hello


def test_hello_default():
    """Test hello function with default argument."""
    assert hello() == "Hello, World!"


def test_hello_custom():
    """Test hello function with custom name."""
    assert hello("Python") == "Hello, Python!" 