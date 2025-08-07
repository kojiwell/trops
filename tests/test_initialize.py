"""
Tests for the initialize module.
"""
import argparse
import os
import pytest
from io import StringIO
from unittest.mock import patch, MagicMock

from trops.initialize import handle_init, add_init_parser


class TestHandleInit:
    """Test cases for the handle_init function."""

    def test_handle_init_bash_with_trops_dir(self, capsys):
        """Test handle_init with bash shell when TROPS_DIR is set."""
        # Mock the args
        args = MagicMock()
        args.shell = "bash"
        
        with patch.dict(os.environ, {"TROPS_DIR": "/tmp/test"}):
            handle_init(args)
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Verify bash script is printed
        assert "_trops_capcmd ()" in output
        assert "trops capcmd $?" in output
        assert "ontrops()" in output
        assert "offtrops()" in output
        assert "ttags()" in output
        assert "PROMPT_COMMAND=" in output

    def test_handle_init_zsh_with_trops_dir(self, capsys):
        """Test handle_init with zsh shell when TROPS_DIR is set."""
        # Mock the args
        args = MagicMock()
        args.shell = "zsh"
        
        with patch.dict(os.environ, {"TROPS_DIR": "/tmp/test"}):
            handle_init(args)
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Verify zsh script is printed
        assert "autoload -Uz add-zsh-hook" in output
        assert "setopt INC_APPEND_HISTORY" in output
        assert "ontrops()" in output
        assert "offtrops()" in output
        assert "ttags()" in output
        assert "add-zsh-hook precmd" in output
        assert "_tr_capcmd()" in output

    def test_handle_init_without_trops_dir(self, capsys):
        """Test handle_init fails when TROPS_DIR is not set."""
        # Mock the args
        args = MagicMock()
        args.shell = "bash"
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(SystemExit) as exc_info:
                handle_init(args)
            
            assert exc_info.value.code == 1
        
        captured = capsys.readouterr()
        error_output = captured.err
        
        # Verify error messages
        assert "Error: TROPS_DIR environment variable is not set." in error_output
        assert "Please set TROPS_DIR to specify the directory for trops operations." in error_output

    def test_handle_init_bash_script_content(self, capsys):
        """Test that bash script contains expected functions and commands."""
        args = MagicMock()
        args.shell = "bash"
        
        with patch.dict(os.environ, {"TROPS_DIR": "/tmp/test"}):
            handle_init(args)
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Test specific bash features
        assert "history -a && fc -ln -0 -0" in output
        assert 'PROMPT_COMMAND="_trops_capcmd;$PROMPT_COMMAND"' in output
        assert "PROMPT_COMMAND=${PROMPT_COMMAND//_trops_capcmd\\;}" in output
        assert 'export TROPS_SID=$(trops gensid)' in output

    def test_handle_init_zsh_script_content(self, capsys):
        """Test that zsh script contains expected functions and commands."""
        args = MagicMock()
        args.shell = "zsh"
        
        with patch.dict(os.environ, {"TROPS_DIR": "/tmp/test"}):
            handle_init(args)
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Test specific zsh features
        assert "fc -ln -1 -1" in output
        assert "add-zsh-hook precmd _tr_capcmd" in output
        assert "add-zsh-hook -D precmd _tr_capcmd" in output
        assert 'export TROPS_SID=$(trops gensid)' in output

    def test_handle_init_common_functions(self, capsys):
        """Test that both bash and zsh scripts contain common functions."""
        for shell in ["bash", "zsh"]:
            args = MagicMock()
            args.shell = shell
            
            with patch.dict(os.environ, {"TROPS_DIR": "/tmp/test"}):
                handle_init(args)
            
            captured = capsys.readouterr()
            output = captured.out
            
            # Common elements in both scripts
            assert "ontrops()" in output
            assert "offtrops()" in output
            assert "ttags()" in output
            assert 'export TROPS_TAGS=$(echo $@|tr \' \' ,)' in output
            assert 'tmux rename-window "$TROPS_TAGS"' in output
            assert 'echo "# upsage: on-trops <env>"' in output


class TestAddInitParser:
    """Test cases for the add_init_parser function."""

    def test_add_init_parser_creates_subparser(self):
        """Test that add_init_parser creates the init subparser correctly."""
        # Create a mock subparsers object
        mock_subparsers = MagicMock()
        mock_parser = MagicMock()
        mock_subparsers.add_parser.return_value = mock_parser
        
        # Call the function
        add_init_parser(mock_subparsers)
        
        # Verify subparser was created
        mock_subparsers.add_parser.assert_called_once_with(
            "init", 
            help="Initialize trops for a specific shell"
        )
        
        # Verify argument was added
        mock_parser.add_argument.assert_called_once_with(
            "shell",
            choices=["bash", "zsh"],
            help="Shell type to initialize (bash or zsh)",
        )
        
        # Verify default function was set
        mock_parser.set_defaults.assert_called_once_with(func=handle_init)

    def test_add_init_parser_integration(self):
        """Test add_init_parser integration with real argparse."""
        # Create a real parser and subparsers
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        
        # Add the init parser
        add_init_parser(subparsers)
        
        # Test parsing valid arguments
        args = parser.parse_args(["init", "bash"])
        assert args.command == "init"
        assert args.shell == "bash"
        assert args.func == handle_init
        
        args = parser.parse_args(["init", "zsh"])
        assert args.command == "init"
        assert args.shell == "zsh"
        assert args.func == handle_init

    def test_add_init_parser_invalid_shell(self):
        """Test that invalid shell choices are rejected."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="command")
        add_init_parser(subparsers)
        
        # Test that invalid shell choice raises SystemExit
        with pytest.raises(SystemExit):
            parser.parse_args(["init", "fish"])
        
        with pytest.raises(SystemExit):
            parser.parse_args(["init", "invalid"])


class TestIntegration:
    """Integration tests for the initialize module."""

    def test_bash_script_formatting(self, capsys):
        """Test that bash script is properly formatted with consistent indentation."""
        args = MagicMock()
        args.shell = "bash"
        
        with patch.dict(os.environ, {"TROPS_DIR": "/tmp/test"}):
            handle_init(args)
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Check that the script has proper structure
        lines = output.split('\n')
        # First line should not have leading whitespace (function definition)
        function_lines = [line for line in lines if line.strip().endswith('() {')]
        assert len(function_lines) > 0
        for func_line in function_lines:
            assert not func_line.startswith(' ')  # Function definitions should start at column 0

    def test_zsh_script_formatting(self, capsys):
        """Test that zsh script is properly formatted with consistent indentation."""
        args = MagicMock()
        args.shell = "zsh"
        
        with patch.dict(os.environ, {"TROPS_DIR": "/tmp/test"}):
            handle_init(args)
        
        captured = capsys.readouterr()
        output = captured.out
        
        # Check that the script has proper structure
        lines = output.split('\n')
        # First line should not have leading whitespace (autoload command)
        first_line = lines[0] if lines else ""
        assert first_line.startswith("autoload")
        assert not first_line.startswith(" ")  # Should start at column 0

    def test_environment_isolation(self, capsys):
        """Test that different TROPS_DIR values don't affect script content."""
        args = MagicMock()
        args.shell = "bash"
        
        # Test with different TROPS_DIR values
        for trops_dir in ["/tmp/test1", "/home/user/trops", "/var/trops"]:
            with patch.dict(os.environ, {"TROPS_DIR": trops_dir}):
                handle_init(args)
            
            captured = capsys.readouterr()
            output = captured.out
            
            # Script content should be the same regardless of TROPS_DIR value
            assert "_trops_capcmd ()" in output
            assert "ontrops()" in output
            # TROPS_DIR value should not appear in the script itself
            assert trops_dir not in output
