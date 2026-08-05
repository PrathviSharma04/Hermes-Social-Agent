"""Database to Sheets Synchronization."""

import logging
import sqlite3
import datetime
import time
from typing import List, Dict, Any

import gspread

from hermes_social.sheets.models import TabSyncResult, SyncResult

logger = logging.getLogger(__name__)


def _fetch_table(conn: sqlite3.Connection, query: str) -> List[List[Any]]:
    """Fetch data from SQLite and format it as a list of lists (strings)."""
    cursor = conn.execute(query)
    rows = cursor.fetchall()
    # Convert all elements to strings to avoid Sheets JSON formatting issues
    return [[str(item) if item is not None else "" for item in row] for row in rows]


def _sync_tab(ws: gspread.Worksheet, conn: sqlite3.Connection, query: str, clear_range: str, data_range_prefix: str) -> TabSyncResult:
    start_time = time.time()
    tab_name = ws.title
    result = TabSyncResult(tab_name=tab_name)
    
    try:
        data = _fetch_table(conn, query)
        if data:
            ws.batch_clear([clear_range])
            ws.update(range_name=f"{data_range_prefix}{len(data)+1}", values=data)
            result.rows_synced = len(data)
            result.status = "SUCCESS"
            logger.info(f"Synced {len(data)} rows to {tab_name}.")
        else:
            ws.batch_clear([clear_range])
            result.status = "SKIPPED"
            result.error_message = "No data found."
    except Exception as e:
        logger.error(f"Error syncing tab {tab_name}: {e}")
        result.status = "FAILED"
        result.error_message = str(e)
        
    result.duration_ms = (time.time() - start_time) * 1000
    return result


def sync_database_to_sheets(conn: sqlite3.Connection, spreadsheet: gspread.Spreadsheet, row_limit: int = 1000) -> SyncResult:
    """
    Pulls data from SQLite and performs a bulk overwrite of the relevant tabs.
    Returns a SyncResult structured object.
    """
    logger.info("Starting SQLite -> Sheets sync...")
    start_time = time.time()
    sync_res = SyncResult()
    
    worksheets = {ws.title: ws for ws in spreadsheet.worksheets()}
    
    # 1. Sync Topics
    if "Topics" in worksheets:
        res = _sync_tab(
            worksheets["Topics"], conn,
            f"SELECT id, canonical_topic, category, content_pillar, status, opportunity_score, trend_velocity, created_at, updated_at FROM topics ORDER BY id DESC LIMIT {row_limit}",
            f"A2:I{row_limit+1}", "A2:I"
        )
        sync_res.tab_results.append(res)
        
    # 2. Sync Content Ideas
    if "Content Ideas" in worksheets:
        res = _sync_tab(
            worksheets["Content Ideas"], conn,
            f"SELECT id, topic_id, angle, format_recommendation, status, brand_fit_score, created_at FROM content_ideas ORDER BY id DESC LIMIT {row_limit}",
            f"A2:G{row_limit+1}", "A2:G"
        )
        sync_res.tab_results.append(res)

    # 3. Sync Posts
    if "Posts" in worksheets:
        res = _sync_tab(
            worksheets["Posts"], conn,
            f"SELECT id, content_idea_id, platform, format, hook, word_count, quality_score, status, approval_status, scheduled_at, published_at, created_at FROM posts ORDER BY id DESC LIMIT {row_limit}",
            f"A2:L{row_limit+1}", "A2:L"
        )
        sync_res.tab_results.append(res)
        
    # 4. Sync Research Runs
    if "Research Runs" in worksheets:
        res = _sync_tab(
            worksheets["Research Runs"], conn,
            f"SELECT id, topic_id, status, confidence, model_route, started_at FROM research_runs ORDER BY id DESC LIMIT {row_limit}",
            f"A2:F{row_limit+1}", "A2:F"
        )
        sync_res.tab_results.append(res)
        
    # 5. Sync Strategy Rules
    if "Strategy Rules" in worksheets:
        res = _sync_tab(
            worksheets["Strategy Rules"], conn,
            f"SELECT id, platform, rule, confidence, status, sample_size, last_validated_at FROM strategy_rules ORDER BY id DESC LIMIT {row_limit}",
            f"A2:G{row_limit+1}", "A2:G"
        )
        sync_res.tab_results.append(res)
        
    # 6. Sync Experiments
    if "Experiments" in worksheets:
        res = _sync_tab(
            worksheets["Experiments"], conn,
            f"SELECT id, platform, variable, variant_a, variant_b, status, confidence, conclusion FROM experiments ORDER BY id DESC LIMIT {row_limit}",
            f"A2:H{row_limit+1}", "A2:H"
        )
        sync_res.tab_results.append(res)

    # 7. Sync Assets
    if "Assets" in worksheets:
        res = _sync_tab(
            worksheets["Assets"], conn,
            f"SELECT id, post_id, asset_type, path, qa_status, created_at FROM assets ORDER BY id DESC LIMIT {row_limit}",
            f"A2:F{row_limit+1}", "A2:F"
        )
        sync_res.tab_results.append(res)
            
    # 8. Sync Model Runs
    if "Model Runs" in worksheets:
        res = _sync_tab(
            worksheets["Model Runs"], conn,
            "SELECT id, task_type, model_route, prompt_tokens, completion_tokens, cost, latency, success, error, timestamp FROM model_runs ORDER BY id DESC LIMIT 500",
            "A2:J501", "A2:J"
        )
        sync_res.tab_results.append(res)
        
    # 9. Sync Performance
    if "Performance" in worksheets:
        res = _sync_performance_tab(worksheets["Performance"], conn)
        sync_res.tab_results.append(res)

    # 10. Update Sync Status
    now = datetime.datetime.utcnow().isoformat()
    sync_res.sync_timestamp = now
    
    if "Sync_Status" in worksheets:
        ws = worksheets["Sync_Status"]
        # Clear existing
        ws.batch_clear([f"A2:F{len(sync_res.tab_results) + 2}"])
        
        status_data = []
        for tab_res in sync_res.tab_results:
            status_data.append([
                tab_res.tab_name,
                tab_res.status,
                tab_res.rows_synced,
                now,
                f"{tab_res.duration_ms:.2f}",
                tab_res.error_message or ""
            ])
            
        if status_data:
            ws.update(range_name=f"A2:F{len(status_data)+1}", values=status_data)
        logger.info(f"Sync completed at {now} UTC.")
        
    # Determine overall status
    if any(tr.status == "FAILED" for tr in sync_res.tab_results):
        sync_res.overall_status = "PARTIAL_SUCCESS"
    else:
        sync_res.overall_status = "SUCCESS"
        
    sync_res.total_duration_ms = (time.time() - start_time) * 1000
        
    return sync_res


def _sync_performance_tab(ws: gspread.Worksheet, conn: sqlite3.Connection) -> TabSyncResult:
    """Special sync for Performance which requires pivoting snapshots."""
    start_time = time.time()
    try:
        from hermes_social.constants import PostStatus
        from hermes_social.metrics.analyzer import evaluate_post

        cursor = conn.execute(
            """
            SELECT p.id, p.platform, p.format, COALESCE(p.scheduled_at, p.updated_at) as pub_time
            FROM posts p
            WHERE p.status = ?
            ORDER BY p.id DESC LIMIT 100
            """,
            (PostStatus.PUBLISHED.value,)
        )
        posts = cursor.fetchall()
        
        # Prepare rows
        rows = []
        for p in posts:
            post_id = p["id"]
            
            # Fetch snapshots
            snaps = conn.execute(
                "SELECT window, impressions, likes FROM performance_snapshots WHERE post_id = ?",
                (post_id,)
            ).fetchall()
            
            snap_dict = {s["window"]: s for s in snaps}
            
            imp_2h = snap_dict.get("2h", {}).get("impressions") or ""
            imp_24h = snap_dict.get("24h", {}).get("impressions") or ""
            likes_24h = snap_dict.get("24h", {}).get("likes") or ""
            imp_72h = snap_dict.get("72h", {}).get("impressions") or ""
            imp_7d = snap_dict.get("7d", {}).get("impressions") or ""
            
            _, score = evaluate_post(post_id, conn)
            
            rows.append([
                post_id,
                p["platform"],
                p["format"],
                p["pub_time"],
                imp_2h,
                imp_24h,
                likes_24h,
                imp_72h,
                imp_7d,
                score
            ])
            
        if rows:
            ws.batch_clear(["A2:J"])
            ws.update(range_name="A2", values=rows)
            
        duration = (time.time() - start_time) * 1000
        return TabSyncResult(tab_name=ws.title, status="SUCCESS", rows_synced=len(rows), duration_ms=duration)
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"Failed to sync Performance tab: {e}")
        return TabSyncResult(tab_name=ws.title, status="FAILED", rows_synced=0, duration_ms=duration, error_message=str(e))

