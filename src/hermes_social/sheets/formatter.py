"""Google Sheets formatting utilities."""

import logging
import gspread

logger = logging.getLogger(__name__)

def apply_header_formatting(worksheet: gspread.Worksheet, num_cols: int) -> None:
    """
    Applies bold text, frozen row, and light grey background to the first row.
    """
    try:
        # Freeze the first row
        worksheet.freeze(rows=1)
        
        # Apply formatting to A1 to the last column
        # Using batch_update with repeatCell request for efficiency
        spreadsheet = worksheet.spreadsheet
        sheet_id = worksheet.id
        
        body = {
            "requests": [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": num_cols
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {
                                    "red": 0.9,
                                    "green": 0.9,
                                    "blue": 0.9
                                },
                                "textFormat": {
                                    "bold": True
                                }
                            }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat)"
                    }
                }
            ]
        }
        spreadsheet.batch_update(body)
    except Exception as e:
        logger.warning(f"Failed to apply formatting to {worksheet.title}: {e}")

def auto_resize_columns(worksheet: gspread.Worksheet, num_cols: int) -> None:
    """
    Auto-resizes columns to fit their content.
    """
    try:
        spreadsheet = worksheet.spreadsheet
        sheet_id = worksheet.id
        
        body = {
            "requests": [
                {
                    "autoResizeDimensions": {
                        "dimensions": {
                            "sheetId": sheet_id,
                            "dimension": "COLUMNS",
                            "startIndex": 0,
                            "endIndex": num_cols
                        }
                    }
                }
            ]
        }
        spreadsheet.batch_update(body)
    except Exception as e:
        logger.warning(f"Failed to resize columns for {worksheet.title}: {e}")
