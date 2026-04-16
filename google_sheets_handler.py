"""
Google Sheets Handler for Foreclosure Scraper
Handles authentication, spreadsheet creation, and data operations
"""
import os
import json
import base64
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import traceback


class GoogleSheetsHandler:
    """Handles Google Sheets operations for foreclosure leads"""
    
    # Required Google Sheets API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    # Column headers for the spreadsheet
    COLUMN_HEADERS = [
        'Row Number',
        'Town',
        'Sale Date',
        'Docket Number',
        'Address',
        'Sale Type',
        'Docket URL',
        'View Notice URL',
        'Date Scraped',
        'Last Updated'
    ]
    
    def __init__(self, credentials_path=None, spreadsheet_id=None, credentials_json=None):
        """
        Initialize Google Sheets handler
        
        Args:
            credentials_path: Path to credentials.json file
            spreadsheet_id: Existing spreadsheet ID (optional)
            credentials_json: Base64-encoded JSON credentials string (alternative to file)
        """
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.credentials_json = credentials_json
        self.client = None
        self.spreadsheet = None
        self.worksheet = None
        self._log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        os.makedirs(self._log_dir, exist_ok=True)
    
    def _log_error(self, error_msg, exception=None):
        """Log error to file"""
        try:
            log_file = os.path.join(self._log_dir, 'google_sheets_errors.log')
            with open(log_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().isoformat()
                f.write(f"\n[{timestamp}] {error_msg}\n")
                if exception:
                    f.write(f"{traceback.format_exc()}\n")
        except Exception as e:
            print(f"Error logging to file: {e}")
    
    def authenticate(self):
        """Authenticate with Google Sheets API"""
        try:
            # Try credentials file first
            if self.credentials_path and os.path.exists(self.credentials_path):
                creds = Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=self.SCOPES
                )
            # Try base64-encoded JSON from environment
            elif self.credentials_json:
                try:
                    # Decode base64
                    credentials_bytes = base64.b64decode(self.credentials_json)
                    credentials_dict = json.loads(credentials_bytes.decode('utf-8'))
                    creds = Credentials.from_service_account_info(
                        credentials_dict,
                        scopes=self.SCOPES
                    )
                except Exception as e:
                    raise Exception(f"Failed to decode credentials JSON: {str(e)}")
            # Try environment variable
            elif os.getenv('GOOGLE_CREDENTIALS_JSON'):
                try:
                    credentials_str = os.getenv('GOOGLE_CREDENTIALS_JSON')
                    credentials_bytes = base64.b64decode(credentials_str)
                    credentials_dict = json.loads(credentials_bytes.decode('utf-8'))
                    creds = Credentials.from_service_account_info(
                        credentials_dict,
                        scopes=self.SCOPES
                    )
                except Exception as e:
                    raise Exception(f"Failed to decode GOOGLE_CREDENTIALS_JSON: {str(e)}")
            # Try default credentials.json path
            elif os.path.exists('credentials.json'):
                creds = Credentials.from_service_account_file(
                    'credentials.json',
                    scopes=self.SCOPES
                )
            else:
                raise Exception(
                    "No credentials found. Please provide one of:\n"
                    "1. credentials.json file in project root\n"
                    "2. GOOGLE_CREDENTIALS_PATH environment variable\n"
                    "3. GOOGLE_CREDENTIALS_JSON environment variable (base64-encoded)"
                )
            
            self.client = gspread.authorize(creds)
            return True
            
        except Exception as e:
            error_msg = f"Authentication failed: {str(e)}"
            self._log_error(error_msg, e)
            raise Exception(error_msg)
    
    def get_or_create_spreadsheet(self):
        """Get existing spreadsheet or create new one"""
        try:
            if not self.client:
                self.authenticate()
            
            # If spreadsheet_id provided, try to open it
            if self.spreadsheet_id:
                try:
                    self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
                    print(f"Opened existing spreadsheet: {self.spreadsheet.title}")
                except gspread.exceptions.SpreadsheetNotFound:
                    raise Exception(f"Spreadsheet with ID {self.spreadsheet_id} not found. Check ID or permissions.")
                except Exception as e:
                    raise Exception(f"Failed to open spreadsheet: {str(e)}")
            else:
                # Create new spreadsheet
                date_str = datetime.now().strftime('%Y-%m-%d')
                title = f"CT Foreclosure Leads - {date_str}"
                self.spreadsheet = self.client.create(title)
                self.spreadsheet_id = self.spreadsheet.id
                print(f"Created new spreadsheet: {title} (ID: {self.spreadsheet_id})")
                print(f"⚠️  IMPORTANT: Add this to your .env file: GOOGLE_SHEETS_ID={self.spreadsheet_id}")
            
            # Get or create worksheet (use first sheet or create one)
            try:
                self.worksheet = self.spreadsheet.sheet1
            except Exception as e:
                # If no sheet exists, create one
                self.worksheet = self.spreadsheet.add_worksheet(title="Leads", rows=1000, cols=10)
            
            # Initialize headers if sheet is empty
            existing_headers = self.worksheet.row_values(1)
            if not existing_headers or existing_headers[0] != 'Row Number':
                self.initialize_headers()
            
            return self.spreadsheet
            
        except Exception as e:
            error_msg = f"Failed to get/create spreadsheet: {str(e)}"
            self._log_error(error_msg, e)
            raise Exception(error_msg)
    
    def initialize_headers(self):
        """Initialize column headers and formatting"""
        try:
            # Set headers
            self.worksheet.append_row(self.COLUMN_HEADERS)
            
            # Format header row
            header_format = {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.7},
                'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}
            }
            
            # Apply formatting to header row (row 1)
            self.worksheet.format('1:1', header_format)
            
            # Freeze header row
            self.worksheet.freeze(rows=1)
            
            # Auto-resize columns
            try:
                # Get all column ranges
                column_ranges = [f"{chr(65+i)}:{chr(65+i)}" for i in range(len(self.COLUMN_HEADERS))]
                for col_range in column_ranges:
                    # Request auto-resize (this may not work for all columns at once)
                    pass
            except Exception as e:
                print(f"Note: Auto-resize may not be available: {e}")
            
            print("✓ Headers initialized and formatted")
            
        except Exception as e:
            error_msg = f"Failed to initialize headers: {str(e)}"
            self._log_error(error_msg, e)
            raise Exception(error_msg)
    
    def get_existing_docket_numbers(self):
        """Retrieve all existing Docket Numbers as a set"""
        try:
            if not self.worksheet:
                self.get_or_create_spreadsheet()
            
            # Get all values from the Docket Number column (column D = index 4 in 1-indexed gspread)
            # Column order: Row Number(1), Town(2), Sale Date(3), Docket Number(4), Address(5), ...
            docket_column_index = 4  # Docket Number is 4th column (gspread uses 1-indexed)
            
            # Get all values from column D (skip header)
            all_values = self.worksheet.col_values(docket_column_index)
            
            # Skip header row if present
            if all_values and all_values[0] == 'Docket Number':
                all_values = all_values[1:]
            
            # Create set of non-empty docket numbers
            existing_dockets = {docket.strip() for docket in all_values if docket and docket.strip()}
            
            print(f"Found {len(existing_dockets)} existing docket numbers in spreadsheet")
            return existing_dockets
            
        except Exception as e:
            error_msg = f"Failed to get existing docket numbers: {str(e)}"
            self._log_error(error_msg, e)
            # Return empty set if error (allows appending all records)
            print(f"Warning: {error_msg}. Continuing with empty duplicate set.")
            return set()
    
    def filter_duplicates(self, leads):
        """
        Filter out leads with existing Docket Numbers
        
        Returns:
            tuple: (new_leads, duplicate_count)
        """
        try:
            existing_dockets = self.get_existing_docket_numbers()
            
            new_leads = []
            duplicate_count = 0
            
            for lead in leads:
                docket_number = lead.get('docket_number', '').strip()
                if docket_number and docket_number not in existing_dockets:
                    new_leads.append(lead)
                    existing_dockets.add(docket_number)  # Track in this batch too
                elif docket_number:
                    duplicate_count += 1
            
            return new_leads, duplicate_count
            
        except Exception as e:
            error_msg = f"Failed to filter duplicates: {str(e)}"
            self._log_error(error_msg, e)
            raise Exception(error_msg)
    
    def format_lead_for_sheets(self, lead):
        """Convert lead dict to spreadsheet row format"""
        current_time = datetime.now().isoformat()
        
        return [
            lead.get('row_number', ''),
            lead.get('town', ''),
            lead.get('sale_date', ''),
            lead.get('docket_number', ''),
            lead.get('address', ''),
            lead.get('sale_type', ''),
            lead.get('docket_url', ''),
            lead.get('view_notice_url', ''),
            current_time,  # Date Scraped
            current_time   # Last Updated (same as Date Scraped for new records)
        ]
    
    def append_leads(self, leads):
        """Append new leads to the spreadsheet"""
        try:
            if not self.worksheet:
                self.get_or_create_spreadsheet()
            
            if not leads:
                print("No new leads to append")
                return 0
            
            # Format all leads
            rows_to_append = [self.format_lead_for_sheets(lead) for lead in leads]
            
            # Append in batches (Google Sheets API limit is 500 rows per request)
            batch_size = 100
            total_added = 0
            
            for i in range(0, len(rows_to_append), batch_size):
                batch = rows_to_append[i:i + batch_size]
                self.worksheet.append_rows(batch, value_input_option='RAW')
                total_added += len(batch)
                print(f"  ✓ Appended {total_added}/{len(rows_to_append)} rows...")
            
            print(f"✓ Successfully appended {total_added} new leads to spreadsheet")
            return total_added
            
        except Exception as e:
            error_msg = f"Failed to append leads: {str(e)}"
            self._log_error(error_msg, e)
            raise Exception(error_msg)
    
    def append_towns(self, towns):
        """Append town names to the spreadsheet (simple format: just town names)"""
        try:
            if not self.worksheet:
                self.get_or_create_spreadsheet()
            
            if not towns:
                print("No towns to append")
                return 0
            
            # Check if we need to initialize town headers (different from lead headers)
            existing_headers = self.worksheet.row_values(1)
            # Check if sheet is empty or has lead headers (Row Number) instead of town headers
            needs_town_headers = False
            if not existing_headers:
                needs_town_headers = True
            elif existing_headers and existing_headers[0] == 'Row Number':
                # Sheet has lead headers, we need town headers instead
                needs_town_headers = True
            elif existing_headers and existing_headers[0] not in ['Town Name', 'Town']:
                # Sheet has some other headers, initialize town headers
                needs_town_headers = True
            
            if needs_town_headers:
                # Initialize simple headers for towns
                town_headers = ['Town Name', 'Date Scraped']
                self.worksheet.clear()  # Clear existing content
                self.worksheet.append_row(town_headers)
                # Format header row
                try:
                    header_format = {
                        'textFormat': {'bold': True},
                        'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.7},
                        'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}
                    }
                    self.worksheet.format('1:1', header_format)
                    self.worksheet.freeze(rows=1)
                except:
                    pass  # Formatting is optional
                print("✓ Initialized town headers")
            
            # Format towns as simple rows: [Town Name, Date Scraped]
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            rows_to_append = [[town, current_time] for town in towns]
            
            # Append in batches (Google Sheets API limit is 500 rows per request)
            batch_size = 100
            total_added = 0
            
            for i in range(0, len(rows_to_append), batch_size):
                batch = rows_to_append[i:i + batch_size]
                self.worksheet.append_rows(batch, value_input_option='RAW')
                total_added += len(batch)
                print(f"  ✓ Appended {total_added}/{len(rows_to_append)} towns...")
            
            print(f"✓ Successfully appended {total_added} towns to spreadsheet")
            return total_added
            
        except Exception as e:
            error_msg = f"Failed to append towns: {str(e)}"
            self._log_error(error_msg, e)
            import traceback
            print(f"Full error traceback: {traceback.format_exc()}")
            raise Exception(error_msg)
    
    def append_leads_excel_format(self, leads):
        """Append leads in Excel format: Sale Date, Docket Number, Type of Sale & Property Address, Extraction Time"""
        try:
            if not self.worksheet:
                self.get_or_create_spreadsheet()
            
            if not leads:
                print("No leads to append")
                return 0
            
            # Check if we need to initialize Excel format headers
            existing_headers = self.worksheet.row_values(1)
            excel_headers = ['Sale Date', 'Docket Number', 'Type of Sale & Property Address', 'Extraction Time']
            needs_headers = False
            
            if not existing_headers:
                needs_headers = True
            elif existing_headers != excel_headers:
                # Different headers, need to initialize
                needs_headers = True
            
            if needs_headers:
                # Clear and initialize with Excel format headers
                self.worksheet.clear()
                self.worksheet.append_row(excel_headers)
                # Format header row
                try:
                    header_format = {
                        'textFormat': {'bold': True},
                        'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.7},
                        'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}
                    }
                    self.worksheet.format('1:1', header_format)
                    self.worksheet.freeze(rows=1)
                except:
                    pass
                print("✓ Initialized Excel format headers")
            
            # Format leads in Excel format
            rows_to_append = []
            for lead in leads:
                row = [
                    lead.get('Sale Date', ''),
                    lead.get('Docket Number', ''),
                    lead.get('Type of Sale & Property Address', ''),
                    lead.get('Extraction Time', '')
                ]
                rows_to_append.append(row)
            
            # Append in batches (Google Sheets API limit is 500 rows per request)
            batch_size = 100
            total_added = 0
            
            for i in range(0, len(rows_to_append), batch_size):
                batch = rows_to_append[i:i + batch_size]
                self.worksheet.append_rows(batch, value_input_option='RAW')
                total_added += len(batch)
                print(f"  ✓ Appended {total_added}/{len(rows_to_append)} rows...")
            
            print(f"✓ Successfully appended {total_added} leads to spreadsheet in Excel format")
            return total_added
            
        except Exception as e:
            error_msg = f"Failed to append leads in Excel format: {str(e)}"
            self._log_error(error_msg, e)
            raise Exception(error_msg)
    
    def get_spreadsheet_url(self):
        """Get the URL of the spreadsheet"""
        if self.spreadsheet:
            return self.spreadsheet.url
        elif self.spreadsheet_id:
            return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/edit"
        else:
            return None

