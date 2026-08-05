"""Configuration loader for Hermes Social Agent."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from hermes_social.constants import ApprovalMode, Environment


@dataclass
class AppConfig:
    """Application configuration container."""
    # App General
    app_env: Environment = Environment.DEVELOPMENT
    app_log_level: str = "INFO"
    approval_mode: ApprovalMode = ApprovalMode.REQUIRED
    autopilot_enabled: bool = False
    publishing_enabled: bool = False
    allow_paid_apis: bool = False

    # Database & Storage
    database_path: Path = field(default_factory=lambda: Path("./data/hermes_social.db"))
    timezone: str = "Asia/Kolkata"

    # Google Sheets
    google_sheets_credentials_path: str = ""
    google_sheets_spreadsheet_id: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: Optional[str] = None
    
    # Platform Overrides
    linkedin_enabled: bool = False
    instagram_enabled: bool = False
    x_enabled: bool = False
    publishing_dry_run: bool = False

    # Platform Credentials - LinkedIn
    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    linkedin_access_token: str = ""

    # Social Platforms - Instagram
    instagram_access_token: str = ""
    instagram_account_id: str = ""

    # Social Platforms - X
    x_api_key: str = ""
    x_api_secret: str = ""
    x_access_token: str = ""
    x_access_token_secret: str = ""

    # Local Obsidian & Assets
    obsidian_vault_path: Path = field(default_factory=lambda: Path("./data/vault"))
    asset_path: Path = field(default_factory=lambda: Path("./data/assets"))

    def validate(self) -> None:
        """Validate critical configuration invariants."""
        # Never allow paid APIs or publishing silently in dev without explicit flags
        if self.app_env == Environment.PRODUCTION and (
            not self.database_path
            or str(self.database_path).strip() in ("", ".")
        ):
            raise ValueError("DATABASE_PATH must be set in production environment.")


def _parse_bool(val: Optional[str], default: bool = False) -> bool:
    if val is None:
        return default
    return val.strip().lower() in ("true", "1", "yes", "y", "on")


def load_config(env_path: Optional[Path] = None) -> AppConfig:
    """Load configuration from environment variables and optional .env file."""
    if env_path and env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        load_dotenv(override=False)

    try:
        app_env = Environment(os.getenv("APP_ENV", "development").lower())
    except ValueError:
        app_env = Environment.DEVELOPMENT

    try:
        approval_mode = ApprovalMode(os.getenv("APPROVAL_MODE", "REQUIRED").upper())
    except ValueError:
        approval_mode = ApprovalMode.REQUIRED

    config = AppConfig(
        app_env=app_env,
        app_log_level=os.getenv("APP_LOG_LEVEL", "INFO").upper(),
        approval_mode=approval_mode,
        autopilot_enabled=_parse_bool(os.getenv("AUTOPILOT_ENABLED"), False),
        publishing_enabled=_parse_bool(os.getenv("PUBLISHING_ENABLED"), False),
        allow_paid_apis=_parse_bool(os.getenv("ALLOW_PAID_APIS"), False),
        database_path=Path(os.getenv("DATABASE_PATH", "./data/hermes_social.db")),
        timezone=os.getenv("TIMEZONE", "Asia/Kolkata"),
        google_sheets_credentials_path=os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", ""),
        google_sheets_spreadsheet_id=os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", ""),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        linkedin_enabled=os.getenv("LINKEDIN_ENABLED", "false").lower() == "true",
        instagram_enabled=os.getenv("INSTAGRAM_ENABLED", "false").lower() == "true",
        x_enabled=os.getenv("X_ENABLED", "false").lower() == "true",
        publishing_dry_run=os.getenv("PUBLISHING_DRY_RUN", "false").lower() == "true",
        linkedin_client_id=os.getenv("LINKEDIN_CLIENT_ID", ""),
        linkedin_client_secret=os.getenv("LINKEDIN_CLIENT_SECRET", ""),
        linkedin_access_token=os.getenv("LINKEDIN_ACCESS_TOKEN", ""),
        instagram_access_token=os.getenv("INSTAGRAM_ACCESS_TOKEN", ""),
        instagram_account_id=os.getenv("INSTAGRAM_ACCOUNT_ID", ""),
        x_api_key=os.getenv("X_API_KEY", ""),
        x_api_secret=os.getenv("X_API_SECRET", ""),
        x_access_token=os.getenv("X_ACCESS_TOKEN", ""),
        x_access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET", ""),
        obsidian_vault_path=Path(os.getenv("OBSIDIAN_VAULT_PATH", "./data/vault")),
        asset_path=Path(os.getenv("ASSET_PATH", "./data/assets")),
    )
    config.validate()
    return config
