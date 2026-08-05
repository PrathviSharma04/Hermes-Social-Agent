"""Tests for CLI entry point and subcommands."""

from pathlib import Path

import pytest
from hermes_social.cli import main


def test_cli_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    """Test printing package version with --version flag."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    out, _ = capsys.readouterr()
    assert "hermes-social" in out


def test_cli_version_subcommand(capsys: pytest.CaptureFixture[str]) -> None:
    """Test printing package version with 'version' subcommand."""
    ret_code = main(["version"])
    assert ret_code == 0
    out, _ = capsys.readouterr()
    assert "hermes-social" in out


def test_cli_config_subcommand(
    clean_env: None, temp_env_file: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test 'config' subcommand outputs non-secret configuration summary."""
    ret_code = main(["--env-file", str(temp_env_file), "config"])
    assert ret_code == 0
    out, _ = capsys.readouterr()
    assert "Hermes Social Agent — Configuration Summary" in out
    assert "Environment:        test" in out
    assert "Approval Mode:      AUTO" in out
    # Ensure secrets are not printed
    assert "12345:TEST_TOKEN" not in out


def test_cli_run_once(clean_env: None, temp_env_file: Path) -> None:
    """Test running a single pipeline pass with 'run --once'."""
    ret_code = main(["--env-file", str(temp_env_file), "run", "--once"])
    assert ret_code == 0


def test_cli_no_command(capsys: pytest.CaptureFixture[str]) -> None:
    """Test default behavior when no subcommand is provided."""
    ret_code = main([])
    assert ret_code == 1
    out, _ = capsys.readouterr()
    assert "usage:" in out
