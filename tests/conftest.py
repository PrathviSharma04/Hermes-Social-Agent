"""Shared PyTest fixtures for Hermes Social Agent test suite."""

import os
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Provide a clean environment without residual .env or system env vars affecting config."""
    keys_to_clear = [
        "APP_ENV",
        "APP_LOG_LEVEL",
        "APPROVAL_MODE",
        "AUTOPILOT_ENABLED",
        "PUBLISHING_ENABLED",
        "ALLOW_PAID_APIS",
        "DATABASE_PATH",
        "TIMEZONE",
        "GOOGLE_SHEETS_CREDENTIALS_PATH",
        "GOOGLE_SHEETS_SPREADSHEET_ID",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "LINKEDIN_CLIENT_ID",
        "LINKEDIN_CLIENT_SECRET",
        "LINKEDIN_ACCESS_TOKEN",
        "INSTAGRAM_ACCESS_TOKEN",
        "INSTAGRAM_ACCOUNT_ID",
        "X_API_KEY",
        "X_API_SECRET",
        "X_ACCESS_TOKEN",
        "X_ACCESS_TOKEN_SECRET",
        "OBSIDIAN_VAULT_PATH",
        "ASSET_PATH",
    ]
    for key in keys_to_clear:
        monkeypatch.delenv(key, raising=False)
    yield


@pytest.fixture
def temp_env_file(tmp_path: Path) -> Path:
    """Create a temporary .env file for configuration loading tests."""
    env_file = tmp_path / ".env.test"
    content = """
    APP_ENV=test
    APP_LOG_LEVEL=DEBUG
    APPROVAL_MODE=AUTO
    AUTOPILOT_ENABLED=true
    PUBLISHING_ENABLED=false
    DATABASE_PATH=./test_data/test.db
    TIMEZONE=UTC
    TELEGRAM_BOT_TOKEN=12345:TEST_TOKEN
    TELEGRAM_CHAT_ID=999999
    """
    env_file.write_text(content.strip(), encoding="utf-8")
    return env_file


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    """Return a temporary database file path."""
    return tmp_path / "test_hermes.db"


@pytest.fixture
def db_conn(db_path: Path):
    """Return an initialized database connection with schema applied."""
    from hermes_social.db.connection import get_connection, init_db

    init_db(db_path)
    conn = get_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def topic_repo(db_conn):
    from hermes_social.db.repositories.topics import TopicRepository
    return TopicRepository(db_conn)


@pytest.fixture
def research_repo(db_conn):
    from hermes_social.db.repositories.research import ResearchRepository
    return ResearchRepository(db_conn)


@pytest.fixture
def content_idea_repo(db_conn):
    from hermes_social.db.repositories.content_ideas import ContentIdeaRepository
    return ContentIdeaRepository(db_conn)


@pytest.fixture
def post_repo(db_conn):
    from hermes_social.db.repositories.posts import PostRepository
    return PostRepository(db_conn)


@pytest.fixture
def asset_repo(db_conn):
    from hermes_social.db.repositories.assets import AssetRepository
    return AssetRepository(db_conn)


@pytest.fixture
def performance_repo(db_conn):
    from hermes_social.db.repositories.performance import PerformanceRepository
    return PerformanceRepository(db_conn)


@pytest.fixture
def experiment_repo(db_conn):
    from hermes_social.db.repositories.experiments import ExperimentRepository
    return ExperimentRepository(db_conn)


@pytest.fixture
def strategy_repo(db_conn):
    from hermes_social.db.repositories.strategy import StrategyRepository
    return StrategyRepository(db_conn)


@pytest.fixture
def operations_repo(db_conn):
    from hermes_social.db.repositories.operations import OperationsRepository
    return OperationsRepository(db_conn)


@pytest.fixture
def brand_system():
    """Return the loaded BrandSystem for tests."""
    from hermes_social.services.brand import load_brand_system
    from pathlib import Path
    
    project_root = Path(__file__).resolve().parent.parent
    brand_path = project_root / "config" / "brand.yaml"
    return load_brand_system(brand_path)
@pytest.fixture
def sources_config():
    """Return the loaded sources configuration for tests."""
    from hermes_social.trends.config import load_sources_config
    from pathlib import Path
    
    project_root = Path(__file__).resolve().parent.parent
    sources_path = project_root / "config" / "sources.yaml"
    return load_sources_config(sources_path)


@pytest.fixture
def mock_fetched_sources():
    from hermes_social.research.models import FetchedSource
    return [
        FetchedSource(
            url="https://example.com/source1",
            title="Source 1",
            text_content="The new AI model is expected to be 50% faster. I think it will change the world.",
            published_at=None,
            fetch_status="ok",
            authority_score=80.0,
            source_id=1
        ),
        FetchedSource(
            url="https://example.com/source2",
            title="Source 2",
            text_content="The model is 50% faster according to benchmarks. However, it will not change the world.",
            published_at=None,
            fetch_status="ok",
            authority_score=90.0,
            source_id=2
        ),
        FetchedSource(
            url="https://example.com/source3",
            title="Source 3",
            text_content="This source is completely different and talks about web development $10M funding.",
            published_at=None,
            fetch_status="ok",
            authority_score=70.0,
            source_id=3
        )
    ]

@pytest.fixture
def vault_path(tmp_path: Path) -> Path:
    """Return a temporary path for the Obsidian vault."""
    vault = tmp_path / "vault"
    vault.mkdir()
    return vault
