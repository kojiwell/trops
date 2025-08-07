"""
Tests for the main module.
"""
import argparse
import sys
import pytest
from io import StringIO
from unittest.mock import patch, MagicMock

from trops.main import hello, main


class TestHelloFunction:
    """Test cases for the hello function."""

    def test_hello_default(self):
        """Test hello function with default argument."""
        assert hello() == "Hello, World!"

    def test_hello_custom(self):
        """Test hello function with custom name."""
        assert hello("Python") == "Hello, Python!"

    def test_hello_empty_string(self):
        """Test hello function with empty string."""
        assert hello("") == "Hello, !"

    def test_hello_special_characters(self):
        """Test hello function with special characters."""
        assert hello("Test-User_123") == "Hello, Test-User_123!"


class TestMainFunction:
    """Test cases for the main function and CLI setup."""

    def test_main_no_args_shows_help(self, capsys):
        """Test that main() shows help when no arguments are provided."""
        with patch.object(sys, 'argv', ['main.py']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # argparse exits with 0 for help
            assert exc_info.value.code == 0

        captured = capsys.readouterr()
        output = captured.out
        assert "usage:" in output
        assert "Trops command-line tool" in output
        assert "Available commands" in output

    def test_main_hello_command_default(self, capsys):
        """Test main() with hello command using default name."""
        with patch.object(sys, 'argv', ['main.py', 'hello']):
            main()

        captured = capsys.readouterr()
        assert captured.out.strip() == "Hello, World!"

    def test_main_hello_command_with_name(self, capsys):
        """Test main() with hello command and custom name."""
        with patch.object(sys, 'argv', ['main.py', 'hello', '--name', 'Alice']):
            main()

        captured = capsys.readouterr()
        assert captured.out.strip() == "Hello, Alice!"

    def test_main_hello_command_short_flag(self, capsys):
        """Test main() with hello command using short flag."""
        with patch.object(sys, 'argv', ['main.py', 'hello', '-n', 'Bob']):
            main()

        captured = capsys.readouterr()
        assert captured.out.strip() == "Hello, Bob!"

    def test_main_invalid_command(self, capsys):
        """Test main() with invalid command."""
        with patch.object(sys, 'argv', ['main.py', 'invalid']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # argparse exits with 2 for invalid arguments
            assert exc_info.value.code == 2

        captured = capsys.readouterr()
        error_output = captured.err
        assert "invalid choice" in error_output

    @patch('trops.capcmd.handle_capcmd')
    def test_main_capcmd_integration(self, mock_handle_capcmd):
        """Test that main() properly integrates with capcmd subcommand."""
        with patch.object(sys, 'argv', ['main.py', 'capcmd', '0', 'ls', '-la']):
            main()

        # Verify that the capcmd handler was called
        mock_handle_capcmd.assert_called_once()
        args = mock_handle_capcmd.call_args[0][0]
        assert args.exit_code == 0
        assert args.executed_command == ['ls', '-la']

    @patch('trops.initialize.handle_init')
    def test_main_init_integration(self, mock_handle_init):
        """Test that main() properly integrates with init subcommand."""
        with patch.object(sys, 'argv', ['main.py', 'init', 'bash']):
            main()

        # Verify that the init handler was called
        mock_handle_init.assert_called_once()
        args = mock_handle_init.call_args[0][0]
        assert args.shell == 'bash'

    @patch('trops.utils.handle_gensid')
    def test_main_gensid_integration(self, mock_handle_gensid):
        """Test that main() properly integrates with gensid subcommand."""
        with patch.object(sys, 'argv', ['main.py', 'gensid']):
            main()

        # Verify that the gensid handler was called
        mock_handle_gensid.assert_called_once()

    def test_main_version_short_flag(self, capsys):
        """Test main() with -v flag shows version."""
        with patch.object(sys, 'argv', ['main.py', '-v']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # argparse exits with 0 for version
            assert exc_info.value.code == 0

        captured = capsys.readouterr()
        output = captured.out
        assert "trops 0.3.1" in output

    def test_main_version_long_flag(self, capsys):
        """Test main() with --version flag shows version."""
        with patch.object(sys, 'argv', ['main.py', '--version']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # argparse exits with 0 for version
            assert exc_info.value.code == 0

        captured = capsys.readouterr()
        output = captured.out
        assert "trops 0.3.1" in output


class TestCLIParser:
    """Test cases for the CLI parser setup."""

    def test_parser_has_all_subcommands(self):
        """Test that the parser includes all expected subcommands."""
        # Create parser like main() does
        parser = argparse.ArgumentParser(description="Trops command-line tool")
        subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)
        
        # Import and add all parsers
        from trops.capcmd import add_capcmd_parser
        from trops.initialize import add_init_parser
        from trops.utils import add_gensid_parser
        
        hello_parser = subparsers.add_parser("hello", help="Greet someone")
        hello_parser.add_argument("--name", "-n", default="World", help="Name to greet (default: World)")
        
        add_capcmd_parser(subparsers)
        add_init_parser(subparsers)
        add_gensid_parser(subparsers)
        
        # Test that all subcommands are recognized
        test_cases = [
            (['hello'], 'hello'),
            (['capcmd', '0', 'test'], 'capcmd'),
            (['init', 'bash'], 'init'),
            (['gensid'], 'gensid'),
        ]
        
        for args, expected_command in test_cases:
            parsed_args = parser.parse_args(args)
            assert parsed_args.command == expected_command

    def test_help_message_content(self, capsys):
        """Test that help message contains expected content."""
        with patch.object(sys, 'argv', ['main.py', '--help']):
            with pytest.raises(SystemExit):
                main()

        captured = capsys.readouterr()
        help_output = captured.out
        
        # Check for main description
        assert "Trops command-line tool" in help_output
        
        # Check for subcommands
        assert "hello" in help_output
        assert "capcmd" in help_output
        assert "init" in help_output
        assert "gensid" in help_output
        
        # Check for help text
        assert "Greet someone" in help_output
        assert "Capture command execution" in help_output
        assert "Initialize trops for a specific shell" in help_output
        assert "Generate a session ID" in help_output
        
        # Check for version flag
        assert "-v, --version" in help_output
        assert "show program's version number and exit" in help_output

    def test_subcommand_help(self, capsys):
        """Test help for individual subcommands."""
        test_cases = [
            (['hello', '--help'], "Name to greet"),
            (['capcmd', '--help'], "Exit code of the executed command"),
            (['init', '--help'], "Shell type to initialize"),
            (['gensid', '--help'], "show this help message"),
        ]
        
        for args, expected_text in test_cases:
            with patch.object(sys, 'argv', ['main.py'] + args):
                with pytest.raises(SystemExit):
                    main()

            captured = capsys.readouterr()
            help_output = captured.out
            assert expected_text in help_output


class TestIntegration:
    """Integration tests for the main module."""

    def test_main_entry_point(self):
        """Test that main can be called as entry point."""
        # This tests that the main function can be imported and called
        from trops.main import main
        assert callable(main)

    def test_argument_parsing_edge_cases(self, capsys):
        """Test edge cases in argument parsing."""
        # Test just program name (should show help)
        with patch.object(sys, 'argv', ['main.py']):
            with pytest.raises(SystemExit):
                main()

    def test_all_imports_work(self):
        """Test that all module imports work correctly."""
        # This test ensures all the imports in main.py are valid
        try:
            from trops.main import main, hello
            from trops.capcmd import add_capcmd_parser
            from trops.initialize import add_init_parser
            from trops.utils import add_gensid_parser
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    def test_sys_argv_manipulation(self, capsys):
        """Test that sys.argv manipulation works correctly."""
        original_argv = sys.argv.copy()
        
        try:
            # Test that main() modifies sys.argv when no args provided
            sys.argv = ['main.py']
            with pytest.raises(SystemExit):
                main()
            
            # sys.argv should have been modified to include --help
            assert '--help' in sys.argv
            
        finally:
            # Restore original sys.argv
            sys.argv = original_argv 