"""Tests for configuration loading and validation."""

from pathlib import Path

import pytest
from hermes_social.config import AppConfig, load_config
from hermes_social.constants import ApprovalMode, Environment


def test_default_config_loading(clean_env: None, tmp_path: Path) -> None:
    """Test that default configuration values are loaded when environment is clean."""
    # Pass a non-existent file so default env values are used
    non_existent = tmp_path / ".env.nonexistent"
    config = load_config(non_existent)

    assert config.app_env == Environment.DEVELOPMENT
    assert config.app_log_level == "INFO"
    assert config.approval_mode == ApprovalMode.REQUIRED
    assert config.autopilot_enabled is False
    assert config.publishing_enabled is False
    assert config.allow_paid_apis is False
    assert config.database_path == Path("./data/hermes_social.db")
    assert config.timezone == "Asia/Kolkata"
    assert config.obsidian_vault_path == Path("./data/vault")
    assert config.asset_path == Path("./data/assets")


def test_custom_env_file_loading(clean_env: None, temp_env_file: Path) -> None:
    """Test loading configuration overrides from a custom .env file."""
    config = load_config(temp_env_file)

    assert config.app_env == Environment.TEST
    assert config.app_log_level == "DEBUG"
    assert config.approval_mode == ApprovalMode.AUTO
    assert config.autopilot_enabled is True
    assert config.publishing_enabled is False
    assert config.database_path == Path("./test_data/test.db")
    assert config.timezone == "UTC"
    assert config.telegram_bot_token == "12345:TEST_TOKEN"
    assert config.telegram_chat_id == "999999"


def test_production_validation_error() -> None:
    """Test that missing DATABASE_PATH raises an error in production environment."""
    with pytest.raises(ValueError, match="DATABASE_PATH must be set in production"):
        config = AppConfig(
            app_env=Environment.PRODUCTION,
            database_path=Path(""),  # Empty path should fail validation
        )
        config.validate()
