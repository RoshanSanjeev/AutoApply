"""
Automated job application form filling using Selenium
"""
import os
import time
from typing import Dict, List, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from utils.logger import setup_logger

class FormFiller:
    """Automate filling out job application forms"""
    
    def __init__(self, headless: bool = True):
        self.logger = setup_logger("form_filler")
        self.driver = None
        self.headless = headless
        self.setup_driver()
        
    def setup_driver(self):
        """Initialize Chrome webdriver with appropriate options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add user agent to appear more human-like
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 10)
        except Exception as e:
            self.logger.error(f"Failed to initialize webdriver: {e}")
            raise
    
    def fill_application_form(self, url: str, form_data: Dict[str, Any]) -> bool:
        """Fill out a job application form at the given URL"""
        try:
            self.logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            time.sleep(3)  # Allow page to load
            
            # Fill basic information fields
            self._fill_personal_info(form_data.get('personal_info', {}))
            
            # Fill experience and education
            self._fill_experience(form_data.get('experience', []))
            self._fill_education(form_data.get('education', []))
            
            # Upload resume and cover letter if file inputs exist
            self._upload_documents(form_data.get('documents', {}))
            
            # Fill additional questions
            self._fill_additional_questions(form_data.get('additional_questions', {}))
            
            # Handle consent and agreements
            self._handle_checkboxes(form_data.get('agreements', {}))
            
            self.logger.info("Form filled successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error filling form: {e}")
            return False
    
    def _fill_personal_info(self, personal_info: Dict[str, str]):
        """Fill personal information fields"""
        field_mappings = {
            'first_name': ['firstName', 'first_name', 'fname', 'first-name'],
            'last_name': ['lastName', 'last_name', 'lname', 'last-name'],
            'email': ['email', 'emailAddress', 'email_address'],
            'phone': ['phone', 'phoneNumber', 'phone_number', 'mobile'],
            'address': ['address', 'street_address', 'address1'],
            'city': ['city'],
            'state': ['state', 'region'],
            'zip_code': ['zip', 'zipCode', 'postal_code', 'postcode'],
            'linkedin': ['linkedin', 'linkedinUrl', 'linkedin_profile']
        }
        
        for field_key, selectors in field_mappings.items():
            if field_key in personal_info:
                self._fill_field_by_selectors(selectors, personal_info[field_key])
    
    def _fill_experience(self, experience_list: List[Dict[str, Any]]):
        """Fill work experience section"""
        # This is a simplified implementation - real forms vary greatly
        if not experience_list:
            return
            
        # Look for common experience field patterns
        experience_selectors = [
            'textarea[name*="experience"]',
            'textarea[id*="experience"]',
            'textarea[placeholder*="experience"]'
        ]
        
        # Combine all experience into a text block
        experience_text = ""
        for exp in experience_list:
            experience_text += f"{exp.get('position', '')} at {exp.get('company', '')} ({exp.get('duration', '')})\n"
            for responsibility in exp.get('responsibilities', []):
                experience_text += f"• {responsibility}\n"
            experience_text += "\n"
        
        self._fill_field_by_selectors(experience_selectors, experience_text.strip())
    
    def _fill_education(self, education_list: List[Dict[str, Any]]):
        """Fill education section"""
        if not education_list:
            return
            
        education_selectors = [
            'input[name*="education"]',
            'input[id*="education"]',
            'select[name*="degree"]'
        ]
        
        # Use the highest/most recent education
        if education_list:
            latest_education = education_list[0]
            education_text = f"{latest_education.get('degree', '')} - {latest_education.get('institution', '')}"
            self._fill_field_by_selectors(education_selectors, education_text)
    
    def _upload_documents(self, documents: Dict[str, str]):
        """Upload resume and cover letter files"""
        upload_mappings = {
            'resume': ['input[type="file"][name*="resume"]', 'input[type="file"][id*="resume"]'],
            'cover_letter': ['input[type="file"][name*="cover"]', 'input[type="file"][id*="cover"]']
        }
        
        for doc_type, selectors in upload_mappings.items():
            if doc_type in documents and os.path.exists(documents[doc_type]):
                try:
                    for selector in selectors:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if elements:
                            elements[0].send_keys(documents[doc_type])
                            self.logger.info(f"Uploaded {doc_type}: {documents[doc_type]}")
                            break
                except Exception as e:
                    self.logger.warning(f"Could not upload {doc_type}: {e}")
    
    def _fill_additional_questions(self, questions: Dict[str, str]):
        """Fill additional application questions"""
        for question_key, answer in questions.items():
            # Look for text areas or inputs that might contain this question
            possible_selectors = [
                f'textarea[name*="{question_key}"]',
                f'input[name*="{question_key}"]',
                f'textarea[id*="{question_key}"]',
                f'input[id*="{question_key}"]'
            ]
            self._fill_field_by_selectors(possible_selectors, answer)
    
    def _handle_checkboxes(self, agreements: Dict[str, bool]):
        """Handle consent checkboxes and agreements"""
        for agreement_key, should_check in agreements.items():
            if should_check:
                selectors = [
                    f'input[type="checkbox"][name*="{agreement_key}"]',
                    f'input[type="checkbox"][id*="{agreement_key}"]',
                    'input[type="checkbox"][name*="terms"]',
                    'input[type="checkbox"][name*="privacy"]',
                    'input[type="checkbox"][name*="consent"]'
                ]
                
                for selector in selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if not element.is_selected():
                                element.click()
                                self.logger.info(f"Checked agreement checkbox: {selector}")
                    except Exception as e:
                        self.logger.warning(f"Could not check checkbox {selector}: {e}")
    
    def _fill_field_by_selectors(self, selectors: List[str], value: str):
        """Try multiple selectors to find and fill a field"""
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    element = elements[0]
                    
                    # Clear field first
                    element.clear()
                    
                    # Fill with value
                    if element.tag_name.lower() == 'select':
                        select = Select(element)
                        # Try to select by visible text first, then by value
                        try:
                            select.select_by_visible_text(value)
                        except:
                            select.select_by_value(value)
                    else:
                        element.send_keys(value)
                    
                    self.logger.debug(f"Filled field {selector} with: {value}")
                    return True
                    
            except Exception as e:
                self.logger.debug(f"Could not fill field {selector}: {e}")
                continue
        
        self.logger.warning(f"Could not find field for selectors: {selectors}")
        return False
    
    def submit_form(self) -> bool:
        """Submit the application form"""
        submit_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button[name*="submit"]',
            'button[id*="submit"]',
            'button:contains("Submit")',
            'button:contains("Apply")'
        ]
        
        for selector in submit_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    elements[0].click()
                    self.logger.info("Form submitted successfully")
                    return True
            except Exception as e:
                self.logger.debug(f"Could not submit with selector {selector}: {e}")
        
        self.logger.warning("Could not find submit button")
        return False
    
    def take_screenshot(self, filename: str):
        """Take a screenshot for debugging"""
        try:
            self.driver.save_screenshot(filename)
            self.logger.info(f"Screenshot saved: {filename}")
        except Exception as e:
            self.logger.error(f"Could not take screenshot: {e}")
    
    def close(self):
        """Close the webdriver"""
        if self.driver:
            self.driver.quit()
            self.logger.info("Webdriver closed")