"""
Autonomous Application Agent - Submits job applications automatically
"""
import os
import json
import time
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests

from utils.logger import setup_logger
from agents.job_application_agent import JobApplicationAgent
from agents.learning_adaptation_agent import LearningAdaptationAgent


class AutonomousApplicationAgent:
    """Agent that autonomously submits job applications"""
    
    def __init__(self):
        self.logger = setup_logger("autonomous_application")
        
        # Initialize sub-agents
        self.job_application_agent = JobApplicationAgent()
        self.learning_agent = LearningAdaptationAgent()
        
        # Load configuration
        self.config = self._load_config()
        self.application_queue = self._load_application_queue()
        
        # Initialize web driver for form filling
        self.driver = None
        self._setup_driver()
        
        # Safety mechanisms
        self.daily_application_limit = self.config.get('daily_application_limit', 10)
        self.applications_today = self._count_applications_today()
        self.safety_checks_enabled = True
        
        # Application templates and strategies
        self.application_strategies = self._load_application_strategies()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load autonomous application configuration"""
        config_file = "data/autonomous_config.json"
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load config: {e}")
        
        # Default configuration
        default_config = {
            "auto_apply_enabled": False,  # Start disabled for safety
            "daily_application_limit": 5,
            "quality_threshold": 0.8,  # Only apply to high-quality matches
            "safety_checks": {
                "require_human_approval": True,
                "max_applications_per_company": 1,
                "cooldown_between_applications": 300,  # 5 minutes
                "blacklisted_companies": [],
                "required_confidence_score": 0.7
            },
            "application_methods": {
                "prefer_direct_company_sites": True,
                "use_job_boards": True,
                "linkedin_apply": False,  # Requires LinkedIn Premium
                "indeed_apply": True,
                "glassdoor_apply": False
            },
            "form_filling": {
                "auto_fill_basic_info": True,
                "auto_upload_documents": True,
                "auto_answer_basic_questions": True,
                "skip_complex_forms": True,
                "take_screenshots": True
            },
            "monitoring": {
                "track_application_status": True,
                "follow_up_enabled": False,
                "email_monitoring": False
            }
        }
        
        # Save default config
        os.makedirs("data", exist_ok=True)
        try:
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Could not save default config: {e}")
        
        return default_config
    
    def _load_application_queue(self) -> List[Dict[str, Any]]:
        """Load pending applications queue"""
        queue_file = "data/application_queue.json"
        
        if os.path.exists(queue_file):
            try:
                with open(queue_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load application queue: {e}")
        
        return []
    
    def _load_application_strategies(self) -> Dict[str, Any]:
        """Load application strategies and templates"""
        strategies_file = "data/application_strategies.json"
        
        if os.path.exists(strategies_file):
            try:
                with open(strategies_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load strategies: {e}")
        
        return {
            "form_field_mappings": {
                "common_fields": {
                    "first_name": ["firstName", "first_name", "fname", "given_name"],
                    "last_name": ["lastName", "last_name", "lname", "family_name", "surname"],
                    "email": ["email", "emailAddress", "email_address", "contact_email"],
                    "phone": ["phone", "phoneNumber", "phone_number", "mobile", "telephone"],
                    "linkedin": ["linkedin", "linkedinUrl", "linkedin_url", "profile_url"],
                    "portfolio": ["portfolio", "website", "portfolioUrl", "personal_website"],
                    "resume": ["resume", "cv", "resumeFile", "resume_file"],
                    "cover_letter": ["coverLetter", "cover_letter", "coverLetterFile"]
                },
                "question_responses": {
                    "authorized_to_work": "Yes",
                    "require_sponsorship": "No",
                    "willing_to_relocate": "Yes",
                    "salary_expectations": "Competitive",
                    "start_date": "Immediately",
                    "notice_period": "2 weeks"
                }
            },
            "application_flow_patterns": {
                "standard_flow": [
                    "fill_basic_info",
                    "upload_resume",
                    "upload_cover_letter",
                    "answer_screening_questions",
                    "review_application",
                    "submit_application"
                ],
                "simple_flow": [
                    "upload_resume",
                    "fill_basic_info",
                    "submit_application"
                ]
            }
        }
    
    def _setup_driver(self):
        """Setup Selenium WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            # Add stealth options to avoid detection
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Don't run headless by default for safety
            if self.config.get('headless_mode', False):
                chrome_options.add_argument("--headless")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Execute script to remove automation indicators
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("WebDriver initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            self.driver = None
    
    def add_to_application_queue(self, job_info: Dict[str, Any], priority: str = "normal"):
        """Add a job to the application queue"""
        application_id = str(uuid.uuid4())
        
        queue_item = {
            "application_id": application_id,
            "job_info": job_info,
            "priority": priority,  # high, normal, low
            "status": "queued",
            "created_at": datetime.now().isoformat(),
            "attempts": 0,
            "max_attempts": 3,
            "scheduled_for": datetime.now().isoformat(),
            "confidence_score": job_info.get('score', 0),
            "metadata": {
                "source": job_info.get('source', 'manual'),
                "added_by": "autonomous_search"
            }
        }
        
        # Check if this job is worth applying to
        if self._should_add_to_queue(job_info):
            self.application_queue.append(queue_item)
            self._save_application_queue()
            
            self.logger.info(f"Added job to queue: {job_info.get('company')} - {job_info.get('position')}")
            return application_id
        else:
            self.logger.info(f"Job did not meet queue criteria: {job_info.get('company')} - {job_info.get('position')}")
            return None
    
    def _should_add_to_queue(self, job_info: Dict[str, Any]) -> bool:
        """Determine if a job should be added to the application queue"""
        # Check quality threshold
        score = job_info.get('score', 0)
        if score < self.config.get('quality_threshold', 0.8):
            return False
        
        # Check blacklisted companies
        company = job_info.get('company', '').lower()
        blacklisted = self.config.get('safety_checks', {}).get('blacklisted_companies', [])
        if any(blocked.lower() in company for blocked in blacklisted):
            return False
        
        # Check if we've already applied to this company recently
        if self._recently_applied_to_company(company):
            return False
        
        # Use learning agent to predict success
        prediction = self.learning_agent.predict_application_success(job_info)
        if prediction['success_probability'] < self.config.get('safety_checks', {}).get('required_confidence_score', 0.7):
            return False
        
        return True
    
    def process_application_queue(self) -> Dict[str, Any]:
        """Process pending applications in the queue"""
        if not self.config.get('auto_apply_enabled', False):
            self.logger.info("Autonomous application is disabled")
            return {"status": "disabled", "message": "Autonomous application is disabled"}
        
        if self.applications_today >= self.daily_application_limit:
            self.logger.info("Daily application limit reached")
            return {"status": "limit_reached", "applications_today": self.applications_today}
        
        if not self.application_queue:
            self.logger.info("Application queue is empty")
            return {"status": "empty_queue", "message": "No applications in queue"}
        
        results = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "applications": []
        }
        
        # Sort queue by priority and confidence score
        sorted_queue = sorted(
            self.application_queue, 
            key=lambda x: (
                {"high": 3, "normal": 2, "low": 1}.get(x['priority'], 1),
                x.get('confidence_score', 0)
            ),
            reverse=True
        )
        
        for application in sorted_queue[:5]:  # Process up to 5 at a time
            if self.applications_today >= self.daily_application_limit:
                break
            
            if application['status'] != 'queued':
                continue
            
            result = self._process_single_application(application)
            results['applications'].append(result)
            results['processed'] += 1
            
            if result['status'] == 'success':
                results['successful'] += 1
                self.applications_today += 1
            elif result['status'] == 'failed':
                results['failed'] += 1
            else:
                results['skipped'] += 1
            
            # Cooldown between applications
            cooldown = self.config.get('safety_checks', {}).get('cooldown_between_applications', 300)
            if cooldown > 0 and results['processed'] < len(sorted_queue):
                self.logger.info(f"Cooling down for {cooldown} seconds...")
                time.sleep(cooldown)
        
        self._save_application_queue()
        
        self.logger.info(f"Queue processing complete: {results['successful']} successful, {results['failed']} failed")
        return results
    
    def _process_single_application(self, application: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single application from the queue"""
        application_id = application['application_id']
        job_info = application['job_info']
        
        self.logger.info(f"Processing application: {job_info.get('company')} - {job_info.get('position')}")
        
        try:
            # Update status
            application['status'] = 'processing'
            application['attempts'] += 1
            application['last_attempt'] = datetime.now().isoformat()
            
            # Safety check before proceeding
            if not self._safety_check(job_info):
                application['status'] = 'skipped'
                return {
                    "application_id": application_id,
                    "status": "skipped",
                    "reason": "Failed safety check"
                }
            
            # Generate documents
            document_result = self.job_application_agent.process_job_application(job_info)
            
            if document_result.get('status') != 'success':
                application['status'] = 'failed'
                application['error'] = document_result.get('error', 'Document generation failed')
                return {
                    "application_id": application_id,
                    "status": "failed",
                    "reason": "Document generation failed",
                    "error": document_result.get('error')
                }
            
            # Attempt to submit application
            submission_result = self._submit_application(job_info, document_result)
            
            if submission_result['success']:
                application['status'] = 'completed'
                application['submitted_at'] = datetime.now().isoformat()
                application['submission_method'] = submission_result.get('method', 'unknown')
                
                # Record successful application for learning
                self._record_application_for_learning(job_info, document_result, submission_result)
                
                return {
                    "application_id": application_id,
                    "status": "success",
                    "company": job_info.get('company'),
                    "position": job_info.get('position'),
                    "submission_method": submission_result.get('method'),
                    "documents_generated": True
                }
            else:
                # Check if we should retry
                if application['attempts'] < application['max_attempts']:
                    application['status'] = 'queued'
                    application['scheduled_for'] = (datetime.now() + timedelta(hours=1)).isoformat()
                else:
                    application['status'] = 'failed'
                
                return {
                    "application_id": application_id,
                    "status": "failed",
                    "reason": submission_result.get('error', 'Submission failed'),
                    "will_retry": application['attempts'] < application['max_attempts']
                }
                
        except Exception as e:
            self.logger.error(f"Error processing application {application_id}: {e}")
            application['status'] = 'failed'
            application['error'] = str(e)
            
            return {
                "application_id": application_id,
                "status": "failed",
                "reason": "Processing error",
                "error": str(e)
            }
    
    def _safety_check(self, job_info: Dict[str, Any]) -> bool:
        """Perform safety checks before applying"""
        safety_config = self.config.get('safety_checks', {})
        
        # Check if human approval is required
        if safety_config.get('require_human_approval', True):
            # For now, we'll skip auto-application if human approval is required
            # This could be enhanced with a human-in-the-loop system
            self.logger.info("Human approval required - skipping auto-application")
            return False
        
        # Check daily limit
        if self.applications_today >= self.daily_application_limit:
            return False
        
        # Check company blacklist
        company = job_info.get('company', '').lower()
        blacklisted = safety_config.get('blacklisted_companies', [])
        if any(blocked.lower() in company for blocked in blacklisted):
            self.logger.warning(f"Company {company} is blacklisted")
            return False
        
        # Check confidence score
        required_confidence = safety_config.get('required_confidence_score', 0.7)
        prediction = self.learning_agent.predict_application_success(job_info)
        if prediction['success_probability'] < required_confidence:
            self.logger.info(f"Confidence score too low: {prediction['success_probability']}")
            return False
        
        return True
    
    def _submit_application(self, job_info: Dict[str, Any], document_result: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to submit the application"""
        job_url = job_info.get('job_url', '')
        
        if not job_url or not self.driver:
            return {"success": False, "error": "No job URL or WebDriver not available"}
        
        try:
            # Navigate to job posting
            self.driver.get(job_url)
            time.sleep(3)
            
            # Take screenshot for monitoring
            if self.config.get('form_filling', {}).get('take_screenshots', True):
                screenshot_path = f"data/screenshots/application_{job_info.get('company', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                os.makedirs("data/screenshots", exist_ok=True)
                self.driver.save_screenshot(screenshot_path)
            
            # Detect application method
            application_method = self._detect_application_method()
            
            if application_method == 'direct_apply':
                return self._handle_direct_application(job_info, document_result)
            elif application_method == 'external_redirect':
                return self._handle_external_application(job_info, document_result)
            elif application_method == 'linkedin_easy_apply':
                return self._handle_linkedin_easy_apply(job_info, document_result)
            else:
                return {"success": False, "error": "Could not detect application method"}
                
        except Exception as e:
            self.logger.error(f"Error submitting application: {e}")
            return {"success": False, "error": str(e)}
    
    def _detect_application_method(self) -> str:
        """Detect how to apply for this job"""
        try:
            # Check for LinkedIn Easy Apply
            if "linkedin.com" in self.driver.current_url:
                easy_apply_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Easy Apply')]")
                if easy_apply_buttons:
                    return 'linkedin_easy_apply'
            
            # Check for direct application forms
            apply_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Apply') or contains(text(), 'Submit Application')]")
            application_forms = self.driver.find_elements(By.TAG_NAME, "form")
            
            if apply_buttons or application_forms:
                return 'direct_apply'
            
            # Check for external redirects
            external_links = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Apply') or contains(text(), 'View Job')]")
            if external_links:
                return 'external_redirect'
            
            return 'unknown'
            
        except Exception as e:
            self.logger.warning(f"Error detecting application method: {e}")
            return 'unknown'
    
    def _handle_direct_application(self, job_info: Dict[str, Any], document_result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle direct application on the same page"""
        try:
            # Look for application form
            form_elements = self.driver.find_elements(By.TAG_NAME, "form")
            
            if not form_elements:
                # Look for apply button that might open a form
                apply_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Apply')]")
                if apply_buttons:
                    apply_buttons[0].click()
                    time.sleep(3)
                    form_elements = self.driver.find_elements(By.TAG_NAME, "form")
            
            if not form_elements:
                return {"success": False, "error": "No application form found"}
            
            # Fill out the form
            form_filled = self._fill_application_form(job_info, document_result)
            
            if form_filled:
                # For safety, don't actually submit in autonomous mode
                # Instead, save the filled form state for human review
                self.logger.info("Form filled successfully - ready for human review")
                return {
                    "success": True,
                    "method": "direct_apply",
                    "note": "Form filled but not submitted - human review required"
                }
            else:
                return {"success": False, "error": "Failed to fill application form"}
                
        except Exception as e:
            self.logger.error(f"Error in direct application: {e}")
            return {"success": False, "error": str(e)}
    
    def _fill_application_form(self, job_info: Dict[str, Any], document_result: Dict[str, Any]) -> bool:
        """Fill out application form fields"""
        try:
            field_mappings = self.application_strategies.get('form_field_mappings', {}).get('common_fields', {})
            user_profile = self.job_application_agent.user_profile
            
            # Fill basic information fields
            for field_type, field_names in field_mappings.items():
                for field_name in field_names:
                    elements = self.driver.find_elements(By.NAME, field_name) + \
                              self.driver.find_elements(By.ID, field_name)
                    
                    if elements:
                        element = elements[0]
                        value = self._get_field_value(field_type, user_profile)
                        
                        if value and element.is_enabled():
                            element.clear()
                            element.send_keys(value)
                            break
            
            # Handle file uploads
            self._handle_file_uploads(document_result)
            
            # Answer screening questions
            self._answer_screening_questions()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error filling form: {e}")
            return False
    
    def _get_field_value(self, field_type: str, user_profile: Dict[str, Any]) -> str:
        """Get the appropriate value for a form field"""
        field_values = {
            'first_name': user_profile.get('name', '').split()[0] if user_profile.get('name') else '',
            'last_name': ' '.join(user_profile.get('name', '').split()[1:]) if user_profile.get('name') else '',
            'email': user_profile.get('email', ''),
            'phone': user_profile.get('phone', ''),
            'linkedin': user_profile.get('linkedin', ''),
            'portfolio': user_profile.get('portfolio', ''),
        }
        
        return field_values.get(field_type, '')
    
    def _handle_file_uploads(self, document_result: Dict[str, Any]):
        """Handle resume and cover letter uploads"""
        try:
            # Look for file upload inputs
            file_inputs = self.driver.find_elements(By.XPATH, "//input[@type='file']")
            
            for file_input in file_inputs:
                input_name = file_input.get_attribute('name') or file_input.get_attribute('id') or ''
                input_name = input_name.lower()
                
                if 'resume' in input_name or 'cv' in input_name:
                    resume_path = document_result.get('resume_path')
                    if resume_path and os.path.exists(resume_path):
                        file_input.send_keys(resume_path)
                
                elif 'cover' in input_name or 'letter' in input_name:
                    cover_letter_path = document_result.get('cover_letter_path')
                    if cover_letter_path and os.path.exists(cover_letter_path):
                        file_input.send_keys(cover_letter_path)
                        
        except Exception as e:
            self.logger.warning(f"Error handling file uploads: {e}")
    
    def _answer_screening_questions(self):
        """Answer common screening questions"""
        try:
            question_responses = self.application_strategies.get('form_field_mappings', {}).get('question_responses', {})
            
            # Look for common screening questions
            questions = [
                ("authorized to work", "Yes"),
                ("require sponsorship", "No"),
                ("willing to relocate", "Yes"),
                ("start date", "Immediately"),
                ("salary", "Competitive")
            ]
            
            for question_keyword, answer in questions:
                # Look for elements containing the question keyword
                elements = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{question_keyword}')]")
                
                for element in elements:
                    # Look for nearby input fields
                    parent = element.find_element(By.XPATH, "./..")
                    inputs = parent.find_elements(By.TAG_NAME, "input") + parent.find_elements(By.TAG_NAME, "select")
                    
                    for input_elem in inputs:
                        if input_elem.get_attribute('type') in ['text', 'select-one']:
                            input_elem.clear()
                            input_elem.send_keys(answer)
                            break
                        elif input_elem.get_attribute('type') == 'radio' and answer.lower() in input_elem.get_attribute('value').lower():
                            input_elem.click()
                            
        except Exception as e:
            self.logger.warning(f"Error answering screening questions: {e}")
    
    def _handle_external_application(self, job_info: Dict[str, Any], document_result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle application that redirects to external site"""
        # For now, we'll record these for manual processing
        return {
            "success": False,
            "error": "External application requires manual processing",
            "method": "external_redirect"
        }
    
    def _handle_linkedin_easy_apply(self, job_info: Dict[str, Any], document_result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle LinkedIn Easy Apply"""
        # LinkedIn Easy Apply requires LinkedIn Premium and specific handling
        return {
            "success": False,
            "error": "LinkedIn Easy Apply not yet implemented",
            "method": "linkedin_easy_apply"
        }
    
    def _record_application_for_learning(self, job_info: Dict[str, Any], document_result: Dict[str, Any], submission_result: Dict[str, Any]):
        """Record application for learning purposes"""
        try:
            application_record = {
                "application_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "company": job_info.get('company'),
                "position": job_info.get('position'),
                "required_skills": job_info.get('required_skills', []),
                "location": job_info.get('location'),
                "salary_range": job_info.get('salary_range'),
                "application_method": submission_result.get('method', 'unknown'),
                "customization_score": document_result.get('processing_time', 0) / 60,  # Simple proxy
                "personalization_score": 0.8,  # Default high since we customize everything
                "source": job_info.get('source', 'autonomous')
            }
            
            # The learning agent will track the outcome separately when we get responses
            self.learning_agent.learn_from_application_outcome(
                application_record,
                {"response_received": False, "application_submitted": True}  # We'll update this later
            )
            
        except Exception as e:
            self.logger.error(f"Error recording application for learning: {e}")
    
    def _count_applications_today(self) -> int:
        """Count applications submitted today"""
        today = datetime.now().date()
        count = 0
        
        for application in self.application_queue:
            if application.get('status') == 'completed':
                submitted_at = application.get('submitted_at')
                if submitted_at:
                    try:
                        submitted_date = datetime.fromisoformat(submitted_at).date()
                        if submitted_date == today:
                            count += 1
                    except:
                        continue
        
        return count
    
    def _recently_applied_to_company(self, company: str) -> bool:
        """Check if we recently applied to this company"""
        cutoff_date = datetime.now() - timedelta(days=30)  # 30 days
        
        for application in self.application_queue:
            if application.get('status') == 'completed':
                app_company = application.get('job_info', {}).get('company', '').lower()
                if company.lower() in app_company or app_company in company.lower():
                    submitted_at = application.get('submitted_at')
                    if submitted_at:
                        try:
                            submitted_date = datetime.fromisoformat(submitted_at)
                            if submitted_date > cutoff_date:
                                return True
                        except:
                            continue
        
        return False
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status and statistics"""
        status_counts = {}
        for application in self.application_queue:
            status = application.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_in_queue": len(self.application_queue),
            "status_breakdown": status_counts,
            "applications_today": self.applications_today,
            "daily_limit": self.daily_application_limit,
            "auto_apply_enabled": self.config.get('auto_apply_enabled', False),
            "safety_checks_enabled": self.safety_checks_enabled
        }
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update autonomous application configuration"""
        self.config.update(new_config)
        
        # Save updated config
        try:
            with open("data/autonomous_config.json", 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info("Configuration updated successfully")
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
    
    def _save_application_queue(self):
        """Save application queue to file"""
        try:
            with open("data/application_queue.json", 'w') as f:
                json.dump(self.application_queue, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving application queue: {e}")
    
    def __del__(self):
        """Cleanup WebDriver on deletion"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass