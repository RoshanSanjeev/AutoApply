"""
Job Information Scraper for extracting job details from URLs
"""
import re
import time
from typing import Dict, Optional, List
from urllib.parse import urlparse, urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
from openai import OpenAI
from utils.logger import setup_logger

class JobScraper:
    """Extract job information from job posting URLs"""
    
    def __init__(self):
        self.logger = setup_logger("job_scraper")
        self.client = OpenAI()
        self.driver = None
        self.setup_driver()
        
    def setup_driver(self):
        """Initialize Chrome webdriver for JavaScript-heavy sites"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 15)
        except Exception as e:
            self.logger.error(f"Failed to initialize webdriver: {e}")
            self.driver = None
    
    def scrape_job_info(self, url: str) -> Dict[str, str]:
        """Extract job information from a job posting URL"""
        try:
            self.logger.info(f"Scraping job information from: {url}")
            
            # Try different scraping methods based on the domain
            domain = urlparse(url).netloc.lower()
            
            if any(site in domain for site in ['linkedin.com', 'workday', 'greenhouse', 'lever.co']):
                # Use Selenium for JavaScript-heavy sites
                job_info = self._scrape_with_selenium(url)
            else:
                # Try simple HTTP request first
                job_info = self._scrape_with_requests(url)
                if not job_info.get('description'):
                    # Fallback to Selenium if needed
                    job_info = self._scrape_with_selenium(url)
            
            # Use AI to clean up and structure the extracted information
            if job_info.get('description'):
                job_info = self._enhance_with_ai(job_info, url)
            
            return job_info
            
        except Exception as e:
            self.logger.error(f"Error scraping job info: {e}")
            return {"error": str(e), "url": url}
    
    def _scrape_with_requests(self, url: str) -> Dict[str, str]:
        """Scrape using simple HTTP requests"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic information
            job_info = {
                'url': url,
                'title': self._extract_title(soup),
                'company': self._extract_company(soup),
                'location': self._extract_location(soup),
                'description': self._extract_description(soup),
                'application_url': self._find_application_url(soup, url)
            }
            
            return job_info
            
        except Exception as e:
            self.logger.warning(f"HTTP scraping failed: {e}")
            return {}
    
    def _scrape_with_selenium(self, url: str) -> Dict[str, str]:
        """Scrape using Selenium for JavaScript-heavy sites"""
        if not self.driver:
            return {}
            
        try:
            self.driver.get(url)
            time.sleep(3)  # Wait for page to load
            
            # Wait for main content to load
            try:
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            except:
                pass
            
            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            job_info = {
                'url': url,
                'title': self._extract_title_selenium(),
                'company': self._extract_company_selenium(),
                'location': self._extract_location_selenium(),
                'description': self._extract_description_selenium(),
                'application_url': self._find_application_url_selenium(url)
            }
            
            return job_info
            
        except Exception as e:
            self.logger.error(f"Selenium scraping failed: {e}")
            return {}
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract job title from HTML"""
        selectors = [
            'h1[data-automation-id="jobPostingHeader"]',  # Workday
            'h1.job-title',
            'h1.jobsearch-JobInfoHeader-title',  # Indeed
            '.job-title h1',
            'h1[class*="job"]',
            'h1[class*="title"]',
            '.top-card-layout__title',  # LinkedIn
            'h1'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)
        
        # Fallback to page title
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
            # Clean up common title patterns
            title = re.sub(r'\s*\|\s*.*$', '', title)  # Remove "| Company Name" etc.
            return title
        
        return ""
    
    def _extract_company(self, soup: BeautifulSoup) -> str:
        """Extract company name from HTML"""
        selectors = [
            '[data-automation-id="jobPostingCompanyName"]',  # Workday
            '.company-name',
            '.jobsearch-CompanyInfoContainer',  # Indeed
            '.company h2',
            '.top-card-layout__entity-info',  # LinkedIn
            '[class*="company"]',
            '[data-testid="employer-name"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)
        
        return ""
    
    def _extract_location(self, soup: BeautifulSoup) -> str:
        """Extract job location from HTML"""
        selectors = [
            '[data-automation-id="jobPostingLocation"]',  # Workday
            '.location',
            '.jobsearch-JobInfoHeader-subtitle',  # Indeed
            '.job-location',
            '.top-card-layout__entity-info .topcard__flavor',  # LinkedIn
            '[class*="location"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                return element.get_text(strip=True)
        
        return ""
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract job description from HTML"""
        selectors = [
            '[data-automation-id="jobPostingDescription"]',  # Workday
            '.job-description',
            '#jobDescriptionText',  # Indeed
            '.description',
            '.show-more-less-html__markup',  # LinkedIn
            '[class*="description"]',
            '.content',
            'main'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                # Get text and clean it up
                description = element.get_text(separator=' ', strip=True)
                if len(description) > 100:  # Only return substantial descriptions
                    return description
        
        # Fallback to body text if no specific description found
        body = soup.find('body')
        if body:
            text = body.get_text(separator=' ', strip=True)
            if len(text) > 500:
                return text[:5000]  # Limit to reasonable length
        
        return ""
    
    def _find_application_url(self, soup: BeautifulSoup, base_url: str) -> str:
        """Find application URL from HTML"""
        # Look for apply buttons or links
        apply_selectors = [
            'a[data-automation-id="jobPostingApplyButton"]',  # Workday
            'a[href*="apply"]',
            'a[class*="apply"]',
            'button[class*="apply"]',
            '.apply-button',
            '.job-apply-button'
        ]
        
        for selector in apply_selectors:
            element = soup.select_one(selector)
            if element:
                href = element.get('href')
                if href:
                    # Convert relative URLs to absolute
                    return urljoin(base_url, href)
                # For buttons, the application might be on the same page
                return base_url
        
        # If no specific apply button found, assume application is on same page
        return base_url
    
    def _extract_title_selenium(self) -> str:
        """Extract job title using Selenium"""
        selectors = [
            'h1[data-automation-id="jobPostingHeader"]',
            'h1.job-title',
            '.job-title h1',
            'h1[class*="job"]',
            'h1[class*="title"]',
            'h1'
        ]
        
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element and element.text.strip():
                    return element.text.strip()
            except:
                continue
        
        return ""
    
    def _extract_company_selenium(self) -> str:
        """Extract company name using Selenium"""
        selectors = [
            '[data-automation-id="jobPostingCompanyName"]',
            '.company-name',
            '.company h2',
            '[class*="company"]'
        ]
        
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element and element.text.strip():
                    return element.text.strip()
            except:
                continue
        
        return ""
    
    def _extract_location_selenium(self) -> str:
        """Extract location using Selenium"""
        selectors = [
            '[data-automation-id="jobPostingLocation"]',
            '.location',
            '.job-location',
            '[class*="location"]'
        ]
        
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element and element.text.strip():
                    return element.text.strip()
            except:
                continue
        
        return ""
    
    def _extract_description_selenium(self) -> str:
        """Extract description using Selenium"""
        selectors = [
            '[data-automation-id="jobPostingDescription"]',
            '.job-description',
            '#jobDescriptionText',
            '.description',
            '[class*="description"]'
        ]
        
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element and element.text.strip():
                    text = element.text.strip()
                    if len(text) > 100:
                        return text
            except:
                continue
        
        return ""
    
    def _find_application_url_selenium(self, base_url: str) -> str:
        """Find application URL using Selenium"""
        apply_selectors = [
            'a[data-automation-id="jobPostingApplyButton"]',
            'a[href*="apply"]',
            'a[class*="apply"]',
            '.apply-button',
            '.job-apply-button'
        ]
        
        for selector in apply_selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                href = element.get_attribute('href')
                if href:
                    return href
            except:
                continue
        
        return base_url
    
    def _enhance_with_ai(self, job_info: Dict[str, str], url: str) -> Dict[str, str]:
        """Use AI to extract structured information from job description"""
        try:
            description = job_info.get('description', '')
            if not description:
                return job_info
            
            prompt = f"""
            Extract structured information from this job posting:
            
            URL: {url}
            Title: {job_info.get('title', '')}
            Company: {job_info.get('company', '')}
            Location: {job_info.get('location', '')}
            
            Description:
            {description}
            
            Please extract and return ONLY a JSON object with these fields:
            {{
                "position": "cleaned job title",
                "company": "company name",
                "location": "location",
                "description": "concise summary of role and responsibilities",
                "required_skills": ["skill1", "skill2", "skill3"],
                "experience_level": "entry/mid/senior",
                "employment_type": "full-time/part-time/contract",
                "remote_ok": true/false,
                "salary_range": "salary range if mentioned or empty string"
            }}
            
            Only include information that is clearly stated or strongly implied in the posting.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured job information. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content.strip()
            
            # Clean up response to ensure it's valid JSON
            if ai_response.startswith('```json'):
                ai_response = ai_response[7:]
            if ai_response.endswith('```'):
                ai_response = ai_response[:-3]
            
            import json
            structured_info = json.loads(ai_response)
            
            # Merge with original info
            enhanced_info = {
                'url': url,
                'job_url': url,
                'application_url': job_info.get('application_url', url),
                **structured_info
            }
            
            self.logger.info("Successfully enhanced job info with AI")
            return enhanced_info
            
        except Exception as e:
            self.logger.warning(f"AI enhancement failed: {e}")
            # Return original info if AI enhancement fails
            return {
                'url': url,
                'job_url': url,
                'application_url': job_info.get('application_url', url),
                'position': job_info.get('title', ''),
                'company': job_info.get('company', ''),
                'location': job_info.get('location', ''),
                'description': job_info.get('description', ''),
                'required_skills': [],
                'remote_ok': False,
                'salary_range': ''
            }
    
    def close(self):
        """Close the webdriver"""
        if self.driver:
            self.driver.quit()
            self.logger.info("Job scraper webdriver closed")
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()