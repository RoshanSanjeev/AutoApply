"""
Google Sheets integration for tracking job applications
"""
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from utils.logger import setup_logger

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

class SheetsManager:
    """Manage job application data in Google Sheets"""
    
    def __init__(self):
        self.logger = setup_logger("sheets_manager")
        self.client = None
        self.sheet = None
        self.spreadsheet = None
        self.setup_client()
        
    def setup_client(self):
        """Initialize Google Sheets client"""
        if not GSPREAD_AVAILABLE:
            self.logger.warning("Google Sheets integration disabled - install gspread and google-auth to enable")
            return
        
        try:
            # Check for credentials file
            credentials_file = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "credentials.json")
            if not os.path.exists(credentials_file):
                self.logger.warning(f"Google Sheets credentials file not found: {credentials_file}")
                return
            
            # Define the scope
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # Authenticate and create the client
            credentials = Credentials.from_service_account_file(credentials_file, scopes=scope)
            self.client = gspread.authorize(credentials)
            
            # Open or create the spreadsheet
            spreadsheet_id = os.getenv("GOOGLE_SHEETS_ID")
            if spreadsheet_id:
                try:
                    self.spreadsheet = self.client.open_by_key(spreadsheet_id)
                    self.sheet = self.spreadsheet.sheet1
                    self.logger.info("Connected to existing Google Sheet")
                except gspread.SpreadsheetNotFound:
                    self.logger.error(f"Spreadsheet with ID {spreadsheet_id} not found")
                    return
            else:
                # Create a new spreadsheet
                spreadsheet_name = f"AutoApply Job Tracker - {datetime.now().strftime('%Y-%m-%d')}"
                self.spreadsheet = self.client.create(spreadsheet_name)
                self.sheet = self.spreadsheet.sheet1
                self.logger.info(f"Created new Google Sheet: {spreadsheet_name}")
                
                # Share with user's email if available
                user_email = os.getenv("USER_EMAIL")
                if user_email:
                    try:
                        self.spreadsheet.share(user_email, perm_type='user', role='writer')
                        self.logger.info(f"Shared spreadsheet with {user_email}")
                    except Exception as e:
                        self.logger.warning(f"Could not share spreadsheet: {e}")
            
            # Setup headers if this is a new sheet
            self._setup_headers()
            
        except Exception as e:
            self.logger.error(f"Failed to setup Google Sheets client: {e}")
            self.client = None
            self.sheet = None
    
    def _setup_headers(self):
        """Setup column headers in the sheet"""
        try:
            if not self.sheet:
                return
                
            # Check if headers already exist
            if self.sheet.row_count > 0:
                first_row = self.sheet.row_values(1)
                if first_row and 'Application Date' in first_row:
                    return  # Headers already exist
            
            headers = [
                'Application Date',
                'Company',
                'Position', 
                'Job URL',
                'Status',
                'Custom Resume Path',
                'Custom Cover Letter Path',
                'Simplify Export Path',
                'Application Method',
                'Salary Range',
                'Location',
                'Remote Option',
                'Employment Type',
                'Required Skills',
                'Experience Required',
                'Follow-up Date',
                'Response Date',
                'Interview Date',
                'Notes',
                'Generated On',
                'Processing Success'
            ]
            
            self.sheet.insert_row(headers, 1)
            self.logger.info("Headers added to spreadsheet")
            
        except Exception as e:
            self.logger.error(f"Failed to setup headers: {e}")
    
    def add_application(self, application_data: Dict[str, Any]) -> bool:
        """Add a new job application record"""
        try:
            if not self.sheet:
                self.logger.warning("Google Sheets not available - would record: %s", application_data.get('company', 'Unknown'))
                return True  # Return True for demo purposes
            
            # Convert list fields to comma-separated strings
            required_skills = application_data.get('required_skills', [])
            if isinstance(required_skills, list):
                required_skills = ', '.join(required_skills)
            
            # Prepare row data matching the new headers
            row_data = [
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Application Date
                application_data.get('company', ''),
                application_data.get('position', ''),
                application_data.get('job_url', ''),
                application_data.get('status', 'Generated'),
                application_data.get('custom_resume_path', ''),
                application_data.get('custom_cover_letter_path', ''),
                application_data.get('simplify_export_path', ''),
                application_data.get('application_method', 'AutoApply + Simplify'),
                application_data.get('salary_range', ''),
                application_data.get('location', ''),
                application_data.get('remote_option', ''),
                application_data.get('employment_type', ''),
                required_skills,
                application_data.get('experience_required', ''),
                application_data.get('follow_up_date', ''),
                application_data.get('response_date', ''),
                application_data.get('interview_date', ''),
                application_data.get('notes', ''),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Generated On
                'Yes' if application_data.get('processing_success', True) else 'No'
            ]
            
            self.sheet.append_row(row_data)
            self.logger.info(f"Added application for {application_data.get('position')} at {application_data.get('company')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add application: {e}")
            return False
    
    def update_application_status(self, company: str, position: str, new_status: str, notes: str = "") -> bool:
        """Update the status of an existing application"""
        try:
            if not self.sheet:
                return False
            
            # Find the row with matching company and position
            records = self.sheet.get_all_records()
            
            for idx, record in enumerate(records, start=2):  # Start from row 2 (after headers)
                if (record.get('Company', '').lower() == company.lower() and 
                    record.get('Position', '').lower() == position.lower()):
                    
                    # Update status
                    self.sheet.update_cell(idx, 5, new_status)  # Status column
                    
                    # Update notes if provided
                    if notes:
                        existing_notes = record.get('Notes', '')
                        updated_notes = f"{existing_notes}\n{datetime.now().strftime('%Y-%m-%d')}: {notes}".strip()
                        self.sheet.update_cell(idx, 10, updated_notes)  # Notes column
                    
                    # Update response date if status indicates response
                    if new_status.lower() in ['interview', 'offer', 'rejected', 'callback']:
                        self.sheet.update_cell(idx, 11, datetime.now().strftime('%Y-%m-%d'))  # Response Date
                    
                    self.logger.info(f"Updated status for {position} at {company} to: {new_status}")
                    return True
            
            self.logger.warning(f"Could not find application for {position} at {company}")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to update application status: {e}")
            return False
    
    def get_applications(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all applications, optionally filtered by status"""
        try:
            if not self.sheet:
                return []
            
            records = self.sheet.get_all_records()
            
            if status_filter:
                records = [r for r in records if r.get('Status', '').lower() == status_filter.lower()]
            
            return records
            
        except Exception as e:
            self.logger.error(f"Failed to get applications: {e}")
            return []
    
    def get_application_stats(self) -> Dict[str, Any]:
        """Get statistics about applications"""
        try:
            if not self.sheet:
                return {}
            
            records = self.sheet.get_all_records()
            
            total_applications = len(records)
            
            # Count by status
            status_counts = {}
            for record in records:
                status = record.get('Status', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Calculate response rate
            responses = sum(1 for r in records if r.get('Response Date'))
            response_rate = (responses / total_applications * 100) if total_applications > 0 else 0
            
            # Get recent applications (last 7 days)
            recent_count = 0
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - 7)
            
            for record in records:
                app_date_str = record.get('Application Date', '')
                if app_date_str:
                    try:
                        app_date = datetime.strptime(app_date_str, '%Y-%m-%d %H:%M:%S')
                        if app_date >= cutoff_date:
                            recent_count += 1
                    except ValueError:
                        continue
            
            stats = {
                'total_applications': total_applications,
                'status_breakdown': status_counts,
                'response_rate': round(response_rate, 1),
                'recent_applications': recent_count,
                'interviews_scheduled': status_counts.get('Interview', 0),
                'offers_received': status_counts.get('Offer', 0)
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get application stats: {e}")
            return {}
    
    def export_data(self, filename: str = None) -> str:
        """Export application data to CSV"""
        try:
            if not self.sheet:
                return ""
            
            if not filename:
                filename = f"job_applications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            # Get all data
            all_values = self.sheet.get_all_values()
            
            # Write to CSV
            import csv
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(all_values)
            
            self.logger.info(f"Data exported to: {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"Failed to export data: {e}")
            return ""
    
    def add_follow_up_reminder(self, company: str, position: str, follow_up_date: str) -> bool:
        """Add a follow-up reminder for an application"""
        try:
            if not self.sheet:
                return False
            
            records = self.sheet.get_all_records()
            
            for idx, record in enumerate(records, start=2):
                if (record.get('Company', '').lower() == company.lower() and 
                    record.get('Position', '').lower() == position.lower()):
                    
                    self.sheet.update_cell(idx, 9, follow_up_date)  # Follow-up Date column
                    self.logger.info(f"Added follow-up reminder for {position} at {company}: {follow_up_date}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to add follow-up reminder: {e}")
            return False