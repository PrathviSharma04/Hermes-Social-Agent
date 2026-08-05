"""Google Sheets API Client handling."""

import logging
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_sheets_client(credentials_path: Path) -> gspread.Client:
    """
    Authenticates with Google Workspace using a Service Account JSON.
    Returns the gspread client.
    """
    if not credentials_path.exists():
        raise FileNotFoundError(
            f"Google Credentials not found at {credentials_path}. "
            "Please follow docs/Google_Sheets_Setup.md to set this up."
        )
        
    try:
        credentials = Credentials.from_service_account_file(
            str(credentials_path), scopes=SCOPES
        )
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        logger.error(f"Failed to authenticate with Google Sheets: {e}")
        raise
