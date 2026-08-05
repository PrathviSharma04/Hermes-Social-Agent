"""Tests for Google Sheets Sync (Phase 8)."""

import sqlite3
from unittest.mock import Mock, patch

from hermes_social.sheets.sync import sync_database_to_sheets
from hermes_social.constants import TopicStatus, PostStatus

def test_sync_database_to_sheets(db_conn: sqlite3.Connection):
    """Test the synchronization logic against a mocked gspread Spreadsheet."""
    
    # 1. Setup mock data in SQLite
    cursor = db_conn.cursor()
    cursor.execute("INSERT INTO topics (canonical_topic, status) VALUES ('AI Trends', ?)", (TopicStatus.RESEARCHED.value,))
    topic_id = cursor.lastrowid
    
    cursor.execute("INSERT INTO content_ideas (topic_id, angle, status) VALUES (?, 'angle', 'APPROVED')", (topic_id,))
    content_idea_id = cursor.lastrowid
    
    cursor.execute("""
        INSERT INTO posts (content_idea_id, platform, format, body, status, idempotency_key) 
        VALUES (?, 'linkedin', 'carousel', 'Mock body', ?, 'idemp_1')
    """, (content_idea_id, PostStatus.DRAFT.value))
    
    cursor.execute("""
        INSERT INTO model_runs (task_type, model_route, success, tokens_used)
        VALUES ('research', 'mock', 1, 100)
    """)
    db_conn.commit()
    
    # 2. Mock gspread components
    mock_spreadsheet = Mock()
    mock_ws_topics = Mock()
    mock_ws_topics.title = "Topics"
    mock_ws_posts = Mock()
    mock_ws_posts.title = "Posts"
    mock_ws_runs = Mock()
    mock_ws_runs.title = "Model Runs"
    mock_ws_sync = Mock()
    mock_ws_sync.title = "Sync_Status"
    mock_ws_ideas = Mock()
    mock_ws_ideas.title = "Content Ideas"
    
    mock_spreadsheet.worksheets.return_value = [
        mock_ws_topics, mock_ws_posts, mock_ws_runs, mock_ws_sync, mock_ws_ideas
    ]
    
    # 3. Execute sync
    result = sync_database_to_sheets(db_conn, mock_spreadsheet, row_limit=10)
    
    # Assert result structure
    assert result.overall_status == "SUCCESS"
    assert len(result.tab_results) == 4  # topics, posts, model runs, ideas
    
    # 4. Assert updates were called on worksheets
    assert mock_ws_topics.update.called
    assert mock_ws_posts.update.called
    assert mock_ws_runs.update.called
    assert mock_ws_sync.update.called
    assert mock_ws_ideas.update.called
    
    # Verify the Topics update was called with correct data
    call_args = mock_ws_topics.update.call_args
    assert call_args is not None
    # kwargs: range_name='A2:I11', values=[[id, 'AI Trends', ...]]
    kwargs = call_args.kwargs
    assert kwargs['range_name'].startswith('A2:I')
    assert len(kwargs['values']) == 1
    assert kwargs['values'][0][1] == 'AI Trends'
