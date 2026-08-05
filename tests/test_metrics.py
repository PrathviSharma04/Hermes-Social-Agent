"""Tests for Metrics (Phase 12)."""

import sqlite3
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, Mock

import pytest
from hermes_social.config import AppConfig
from hermes_social.constants import PerformanceWindow, PostStatus, Platform
from hermes_social.db.repositories.posts import PostRepository
from hermes_social.db.repositories.performance import PerformanceRepository
from hermes_social.metrics.collectors import MockCollector
from hermes_social.metrics.pipeline import calculate_due_windows, run_metrics_collection
from hermes_social.metrics.analyzer import calculate_median_baselines, evaluate_post


@pytest.fixture
def mock_config():
    config = AppConfig()
    return config


@pytest.fixture
def db_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    # Setup minimal schema for testing
    conn.executescript("""
        CREATE TABLE posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            format TEXT,
            status TEXT NOT NULL,
            scheduled_at TIMESTAMP,
            updated_at TIMESTAMP
        );
        CREATE TABLE performance_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            window TEXT NOT NULL,
            captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            impressions INTEGER,
            reach INTEGER,
            likes INTEGER,
            comments INTEGER,
            shares INTEGER,
            saves INTEGER,
            clicks INTEGER,
            profile_visits INTEGER,
            follows INTEGER,
            reposts INTEGER,
            other_metrics_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(post_id) REFERENCES posts(id),
            UNIQUE(post_id, window)
        );
    """)
    yield conn
    conn.close()


def test_mock_collector(mock_config):
    collector = MockCollector(mock_config)
    
    metrics_2h = collector.fetch_metrics("post1", PerformanceWindow.HOUR_2)
    metrics_24h = collector.fetch_metrics("post1", PerformanceWindow.HOUR_24)
    
    assert metrics_2h["impressions"] > 0
    assert metrics_24h["impressions"] > metrics_2h["impressions"]
    assert "mocked" in metrics_2h["other_metrics"]


def test_calculate_due_windows():
    now = datetime(2026, 1, 10, 12, 0, 0)
    
    # 1 hour ago (none due)
    pub = now - timedelta(hours=1)
    windows = calculate_due_windows(pub, now)
    assert len(windows) == 0
    
    # 3 hours ago (2h due)
    pub = now - timedelta(hours=3)
    windows = calculate_due_windows(pub, now)
    assert PerformanceWindow.HOUR_2 in windows
    assert PerformanceWindow.HOUR_24 not in windows
    
    # 25 hours ago (2h, 24h due)
    pub = now - timedelta(hours=25)
    windows = calculate_due_windows(pub, now)
    assert PerformanceWindow.HOUR_2 in windows
    assert PerformanceWindow.HOUR_24 in windows
    assert PerformanceWindow.HOUR_72 not in windows
    
    # 8 days ago (all due)
    pub = now - timedelta(days=8)
    windows = calculate_due_windows(pub, now)
    assert len(windows) == 4


def test_run_metrics_collection(db_conn, mock_config):
    # Insert a published post from 3 hours ago
    past_date = (datetime.now() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
    db_conn.execute(
        "INSERT INTO posts (platform, status, scheduled_at, updated_at) VALUES (?, ?, ?, ?)",
        (Platform.LINKEDIN.value, PostStatus.PUBLISHED.value, past_date, past_date)
    )
    db_conn.commit()
    
    run_metrics_collection(mock_config, db_conn)
    
    perf_repo = PerformanceRepository(db_conn)
    snapshots = perf_repo.list_by_post(1)
    
    # Should have 1 snapshot for 2h
    assert len(snapshots) == 1
    assert snapshots[0]["window"] == "2h"
    assert snapshots[0]["impressions"] > 0


def test_calculate_median_baselines(db_conn):
    # Insert posts
    db_conn.executescript("""
        INSERT INTO posts (id, platform, format, status) VALUES (1, 'linkedin', 'carousel', 'PUBLISHED');
        INSERT INTO posts (id, platform, format, status) VALUES (2, 'linkedin', 'carousel', 'PUBLISHED');
        INSERT INTO posts (id, platform, format, status) VALUES (3, 'linkedin', 'text', 'PUBLISHED');
        
        -- Post 1 (carousel)
        INSERT INTO performance_snapshots (post_id, window, impressions, likes) VALUES (1, '24h', 1000, 100);
        -- Post 2 (carousel)
        INSERT INTO performance_snapshots (post_id, window, impressions, likes) VALUES (2, '24h', 3000, 300);
        -- Post 3 (text)
        INSERT INTO performance_snapshots (post_id, window, impressions, likes) VALUES (3, '24h', 500, 50);
    """)
    
    baselines = calculate_median_baselines(db_conn)
    
    assert "linkedin_carousel" in baselines
    assert "linkedin_text" in baselines
    
    # Median of 1000 and 3000 is 2000.0
    assert baselines["linkedin_carousel"]["impressions"] == 2000.0
    assert baselines["linkedin_carousel"]["likes"] == 200.0


def test_evaluate_post(db_conn):
    db_conn.executescript("""
        INSERT INTO posts (id, platform, format, status) VALUES (1, 'linkedin', 'carousel', 'PUBLISHED');
        INSERT INTO performance_snapshots (post_id, window, impressions, likes) VALUES (1, '24h', 1000, 100);
    """)
    
    # Test post without baselines
    metrics, score = evaluate_post(1, db_conn)
    assert score == "1.0x median impressions"
