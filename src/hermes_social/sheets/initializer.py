"""Workbook initialization and formatting."""

import logging
from typing import List

import gspread

from hermes_social.sheets.formatter import apply_header_formatting, auto_resize_columns

logger = logging.getLogger(__name__)

# Required tabs and their headers
TABS = {
    "Topics": ["ID", "Canonical Topic", "Category", "Pillar", "Status", "Opp. Score", "Trend Velocity", "Created At", "Updated At"],
    "Content Ideas": ["ID", "Topic ID", "Angle", "Format", "Status", "Brand Fit", "Created At"],
    "Posts": ["ID", "Topic ID", "Platform", "Format", "Hook", "Word Count", "Quality Score", "Status", "Approval Status", "Scheduled At", "Published At", "Created At"],
    "Research Runs": ["ID", "Topic ID", "Status", "Confidence", "Model", "Started At"],
    "Strategy Rules": ["ID", "Platform", "Rule", "Confidence", "Status", "Sample Size", "Last Validated"],
    "Experiments": ["ID", "Platform", "Variable", "Variant A", "Variant B", "Status", "Confidence", "Conclusion"],
    "Assets": ["ID", "Post ID", "Type", "Path", "QA Status", "Created At"],
    "Model Runs": ["ID", "Task Type", "Model Route", "Prompt Tokens", "Completion Tokens", "Cost", "Latency", "Success", "Error", "Timestamp"],
    "Performance": ["Post ID", "Platform", "Format", "Published At", "2h Impressions", "24h Impressions", "24h Likes", "72h Impressions", "7d Impressions", "Baseline Score"],
    "Sync_Status": ["Last Sync Time", "Status", "Details", "Error"]
}

def init_workbook(client: gspread.Client, sheet_title: str, share_email: str = None) -> gspread.Spreadsheet:
    """
    Creates or opens a spreadsheet.
    Ensures tabs exist and have proper headers/formatting.
    Optionally shares with an email address.
    """
    try:
        # Try to open if exists
        spreadsheet = client.open(sheet_title)
        logger.info(f"Opened existing spreadsheet: {sheet_title}")
    except gspread.exceptions.SpreadsheetNotFound:
        # Create new
        spreadsheet = client.create(sheet_title)
        logger.info(f"Created new spreadsheet: {sheet_title}")
        
        if share_email:
            spreadsheet.share(share_email, perm_type='user', role='writer')
            logger.info(f"Shared spreadsheet with {share_email}")

    _setup_tabs(spreadsheet)
    return spreadsheet

def _setup_tabs(spreadsheet: gspread.Spreadsheet):
    """Ensure all required tabs exist and are formatted."""
    existing_worksheets = {ws.title: ws for ws in spreadsheet.worksheets()}
    
    for tab_name, headers in TABS.items():
        if tab_name not in existing_worksheets:
            logger.info(f"Creating tab: {tab_name}")
            ws = spreadsheet.add_worksheet(title=tab_name, rows="1000", cols=str(len(headers) + 5))
        else:
            ws = existing_worksheets[tab_name]
            
        # Set headers
        ws.update(range_name='A1', values=[headers])
        
        # Apply nice formatting
        num_cols = len(headers)
        apply_header_formatting(ws, num_cols)
        auto_resize_columns(ws, num_cols)
    
    # Remove default 'Sheet1' if it exists and we aren't using it
    if "Sheet1" in existing_worksheets and "Sheet1" not in TABS:
        try:
            spreadsheet.del_worksheet(existing_worksheets["Sheet1"])
        except Exception:
            pass
