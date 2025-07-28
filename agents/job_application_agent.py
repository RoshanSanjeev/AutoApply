"""
Main Job Application Agent using NVIDIA NeMo Agent Toolkit
"""
import os
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
# from agentiq import AgentIQ  # Commented out for now
from utils.resume_generator import ResumeGenerator
from utils.cover_letter_generator import CoverLetterGenerator
from utils.form_filler import FormFiller
from utils.sheets_manager import SheetsManager
from utils.logger import setup_logger

class JobApplicationAgent:
    """AI Agent that automates job applications with customized resumes and cover letters"""
    
    def __init__(self):
        self.logger = setup_logger("job_application_agent")
        
        # Initialize components
        self.resume_generator = ResumeGenerator()
        self.cover_letter_generator = CoverLetterGenerator()
        self.form_filler = FormFiller(headless=os.getenv("HEADLESS_BROWSER", "true").lower() == "true")
        self.sheets_manager = SheetsManager()
        
        # Initialize NVIDIA Agent IQ for optimization (disabled for now)
        self.agent_iq = None
        # self._setup_agent_iq()
        
        # Load user profile
        self.user_profile = self._load_user_profile()
        
        # Application tracking
        self.applications_today = 0
        self.max_applications_per_day = 10  # Reasonable limit
        
        # Create necessary directories
        os.makedirs("data/resumes", exist_ok=True)
        os.makedirs("data/cover_letters", exist_ok=True)
        os.makedirs("data/screenshots", exist_ok=True)
        
    def _setup_agent_iq(self):
        """Initialize NVIDIA Agent IQ for performance monitoring"""
        try:
            self.agent_iq = AgentIQ()
            self.logger.info("NVIDIA Agent IQ initialized successfully")
        except Exception as e:
            self.logger.warning(f"Could not initialize Agent IQ: {e}")
            self.agent_iq = None
    
    def _load_user_profile(self) -> Dict[str, Any]:
        """Load user profile from file or environment variables"""
        profile_file = "data/user_profile.json"
        
        if os.path.exists(profile_file):
            try:
                with open(profile_file, 'r') as f:
                    profile = json.load(f)
                self.logger.info("User profile loaded from file")
                return profile
            except Exception as e:
                self.logger.warning(f"Could not load profile from file: {e}")
        
        # Default profile from environment variables
        default_profile = {
            "name": os.getenv("USER_NAME", "Your Name"),
            "email": os.getenv("USER_EMAIL", "your.email@example.com"),
            "phone": os.getenv("USER_PHONE", "+1234567890"),
            "linkedin": os.getenv("USER_LINKEDIN", "https://linkedin.com/in/yourprofile"),
            "current_role": "Software Engineer",
            "experience_years": 5,
            "skills": ["Python", "Machine Learning", "AI", "Web Development", "Data Analysis"],
            "achievements": [
                "Led development of ML-powered recommendation system",
                "Improved application performance by 40%",
                "Mentored junior developers"
            ],
            "preferred_locations": ["Remote", "San Francisco", "New York"],
            "salary_range": "$100k-150k",
            "job_preferences": {
                "remote_ok": True,
                "full_time": True,
                "contract": False,
                "min_salary": 100000
            }
        }
        
        # Save default profile
        os.makedirs("data", exist_ok=True)
        try:
            with open(profile_file, 'w') as f:
                json.dump(default_profile, f, indent=2)
            self.logger.info("Default user profile created")
        except Exception as e:
            self.logger.warning(f"Could not save default profile: {e}")
        
        return default_profile
    
    def process_job_application(self, job_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single job application end-to-end"""
        start_time = time.time()
        
        try:
            # Check daily application limit
            if self.applications_today >= self.max_applications_per_day:
                self.logger.warning("Daily application limit reached")
                return {"status": "skipped", "reason": "daily_limit_reached"}
            
            self.logger.info(f"Processing application for {job_info.get('position')} at {job_info.get('company')}")
            
            # Step 1: Generate customized resume
            self.logger.info("Generating customized resume...")
            base_resume = self.resume_generator.load_base_resume("data/base_resume.json")
            customized_resume = self.resume_generator.customize_resume(
                base_resume, 
                job_info.get('description', '')
            )
            
            # Generate LaTeX content (don't save to file, return content)
            resume_latex = self.resume_generator._create_latex_template(customized_resume)
            
            # Also save to file for backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            resume_filename = f"data/resumes/resume_{job_info.get('company', 'unknown')}_{timestamp}.tex"
            os.makedirs("data/resumes", exist_ok=True)
            resume_path = self.resume_generator.generate_latex(customized_resume, resume_filename)
            
            # Step 2: Generate cover letter
            self.logger.info("Generating cover letter...")
            cover_letter_text = self.cover_letter_generator.generate_cover_letter(
                job_info, 
                self.user_profile
            )
            
            # Generate clean cover letter text for Google Docs (no LaTeX formatting)
            cover_letter_clean = self._clean_cover_letter_for_docs(cover_letter_text)
            
            # Also save LaTeX version for backup
            cover_letter_filename = f"data/cover_letters/cover_letter_{job_info.get('company', 'unknown')}_{timestamp}.tex"
            os.makedirs("data/cover_letters", exist_ok=True)
            cover_letter_path = self.cover_letter_generator.generate_latex(
                cover_letter_text, 
                job_info, 
                self.user_profile,
                cover_letter_filename
            )
            
            # Step 3: Fill out application form (if URL provided)
            form_filled = False
            if job_info.get('application_url'):
                self.logger.info("Filling out application form...")
                
                form_data = {
                    'personal_info': {
                        'first_name': self.user_profile.get('name', '').split()[0],
                        'last_name': ' '.join(self.user_profile.get('name', '').split()[1:]),
                        'email': self.user_profile.get('email', ''),
                        'phone': self.user_profile.get('phone', ''),
                        'linkedin': self.user_profile.get('linkedin', '')
                    },
                    'experience': customized_resume.get('experience', []),
                    'education': customized_resume.get('education', []),
                    'documents': {
                        'resume': resume_path,
                        'cover_letter': cover_letter_path
                    },
                    'agreements': {
                        'terms': True,
                        'privacy': True,
                        'consent': True
                    }
                }
                
                try:
                    form_filled = self.form_filler.fill_application_form(
                        job_info['application_url'], 
                        form_data
                    )
                    
                    if form_filled:
                        # Ask for user confirmation before submitting
                        self.logger.info("Form filled. Taking screenshot for review...")
                        screenshot_path = f"data/screenshots/application_{job_info.get('company', 'unknown')}_{timestamp}.png"
                        os.makedirs("data/screenshots", exist_ok=True)
                        self.form_filler.take_screenshot(screenshot_path)
                        
                        # For now, don't auto-submit - let user review
                        self.logger.info("Application ready for review. Screenshot saved.")
                        
                except Exception as e:
                    self.logger.error(f"Error filling form: {e}")
                    form_filled = False
            
            # Step 4: Record in Google Sheets
            self.logger.info("Recording application in Google Sheets...")
            application_record = {
                'company': job_info.get('company', ''),
                'position': job_info.get('position', ''),
                'job_url': job_info.get('job_url', ''),
                'status': 'Applied' if form_filled else 'Documents Ready',
                'resume_version': resume_filename,
                'cover_letter_generated': True,
                'application_method': 'Automated' if form_filled else 'Manual',
                'notes': f"Resume: {resume_filename}, Cover Letter: {cover_letter_filename}",
                'location': job_info.get('location', ''),
                'salary_range': job_info.get('salary_range', ''),
                'remote_option': job_info.get('remote_ok', '')
            }
            
            sheets_success = self.sheets_manager.add_application(application_record)
            
            # Update application count
            self.applications_today += 1
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Prepare Google Sheets data for copy/paste
            sheets_data = self._prepare_sheets_data(job_info, timestamp)
            
            result = {
                "status": "success",
                "company": job_info.get('company'),
                "position": job_info.get('position'),
                "resume_latex": resume_latex,
                "cover_letter_text": cover_letter_clean,
                "sheets_data": sheets_data,
                "resume_path": resume_path,
                "cover_letter_path": cover_letter_path,
                "form_filled": form_filled,
                "sheets_recorded": sheets_success,
                "processing_time": processing_time
            }
            
            self.logger.info(f"Application processed successfully in {processing_time:.2f} seconds")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing application: {e}")
            return {
                "status": "error",
                "error": str(e),
                "company": job_info.get('company'),
                "position": job_info.get('position')
            }
    
    def process_multiple_jobs(self, job_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process multiple job applications"""
        results = []
        
        self.logger.info(f"Processing {len(job_list)} job applications...")
        
        for i, job_info in enumerate(job_list, 1):
            self.logger.info(f"Processing job {i}/{len(job_list)}")
            
            result = self.process_job_application(job_info)
            results.append(result)
            
            # Add delay between applications to avoid being flagged
            if i < len(job_list):
                delay = 30 + (i * 10)  # Increasing delay
                self.logger.info(f"Waiting {delay} seconds before next application...")
                time.sleep(delay)
        
        return results
    
    def run_daily_check(self):
        """Run daily check for new applications and follow-ups"""
        self.logger.info("Running daily application check...")
        
        # Get application statistics
        stats = self.sheets_manager.get_application_stats()
        self.logger.info(f"Application Stats: {stats}")
        
        # Check for follow-ups needed
        applications = self.sheets_manager.get_applications()
        follow_ups_needed = []
        
        for app in applications:
            if app.get('Status') == 'Applied' and not app.get('Response Date'):
                app_date = app.get('Application Date')
                if app_date:
                    try:
                        app_datetime = datetime.strptime(app_date, '%Y-%m-%d %H:%M:%S')
                        days_since = (datetime.now() - app_datetime).days
                        
                        if days_since >= 7:  # Follow up after a week
                            follow_ups_needed.append(app)
                    except ValueError:
                        continue
        
        if follow_ups_needed:
            self.logger.info(f"Found {len(follow_ups_needed)} applications needing follow-up")
            # Here you could implement automated follow-up email generation
        
        return stats
    
    def load_jobs_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Load job listings from a JSON file"""
        try:
            with open(file_path, 'r') as f:
                jobs = json.load(f)
            self.logger.info(f"Loaded {len(jobs)} jobs from {file_path}")
            return jobs
        except Exception as e:
            self.logger.error(f"Could not load jobs from file: {e}")
            return []
    
    def run(self):
        """Main entry point for the agent"""
        self.logger.info("AutoApply Agent started")
        
        try:
            # Check if there's a jobs file to process
            jobs_file = "data/jobs_to_apply.json"
            if os.path.exists(jobs_file):
                jobs = self.load_jobs_from_file(jobs_file)
                if jobs:
                    results = self.process_multiple_jobs(jobs)
                    
                    # Summary
                    successful = len([r for r in results if r.get('status') == 'success'])
                    self.logger.info(f"Processed {len(results)} applications. {successful} successful.")
                    
                    # Archive processed jobs
                    archive_file = f"data/processed_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    os.rename(jobs_file, archive_file)
                    self.logger.info(f"Jobs file archived to {archive_file}")
            else:
                # Run daily check instead
                self.run_daily_check()
                
        except KeyboardInterrupt:
            self.logger.info("Agent stopped by user")
        except Exception as e:
            self.logger.error(f"Agent error: {e}")
        finally:
            # Cleanup
            if self.form_filler:
                self.form_filler.close()
            self.logger.info("Agent shutdown complete")
    
    def _clean_cover_letter_for_docs(self, cover_letter_text: str) -> str:
        """Clean cover letter text for Google Docs (remove LaTeX commands)"""
        import re
        
        # Remove common LaTeX artifacts that might be in the AI-generated text
        clean_text = cover_letter_text
        
        # Remove any LaTeX commands that might have snuck in
        clean_text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', clean_text)
        clean_text = re.sub(r'\\[a-zA-Z]+', '', clean_text)
        
        # Clean up multiple newlines and spaces
        clean_text = re.sub(r'\n\s*\n\s*\n', '\n\n', clean_text)
        clean_text = re.sub(r'[ \t]+', ' ', clean_text)
        
        # Ensure proper formatting
        lines = clean_text.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                formatted_lines.append(line)
            elif formatted_lines and formatted_lines[-1] != '':
                formatted_lines.append('')
        
        return '\n'.join(formatted_lines)
    
    def _prepare_sheets_data(self, job_info: Dict[str, Any], timestamp: str) -> Dict[str, str]:
        """Prepare data formatted for Google Sheets copy/paste"""
        from datetime import datetime
        
        # Format data for easy copy/paste into Google Sheets
        sheets_data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "company": job_info.get('company', ''),
            "position": job_info.get('position', ''),
            "location": job_info.get('location', ''),
            "salary": job_info.get('salary_range', ''),
            "remote": "Yes" if job_info.get('remote_ok') else "No",
            "status": "Applied",
            "job_url": job_info.get('job_url', ''),
            "notes": f"Resume customized on {timestamp}",
            "skills_required": ', '.join(job_info.get('required_skills', [])) if job_info.get('required_skills') else '',
            "application_method": "AutoApply"
        }
        
        return sheets_data

    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, 'form_filler') and self.form_filler:
            self.form_filler.close()