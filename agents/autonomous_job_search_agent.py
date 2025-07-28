"""
Autonomous Job Search Agent - Intelligently searches and filters job opportunities
"""
import os
import json
import time
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import re

from utils.logger import setup_logger
from utils.job_text_parser import JobTextParser


class AutonomousJobSearchAgent:
    """Autonomous agent that searches for relevant job opportunities"""
    
    def __init__(self):
        self.logger = setup_logger("autonomous_job_search")
        self.job_parser = JobTextParser()
        
        # Load user preferences and search criteria
        self.preferences = self._load_search_preferences()
        self.search_history = self._load_search_history()
        
        # Initialize web driver for scraping
        self.driver = None
        self._setup_driver()
        
        # Job board configurations
        self.job_boards = {
            'linkedin': {
                'enabled': True,
                'search_url': 'https://www.linkedin.com/jobs/search',
                'rate_limit': 10,  # seconds between requests
                'max_daily_searches': 50
            },
            'indeed': {
                'enabled': True,
                'search_url': 'https://www.indeed.com/jobs',
                'rate_limit': 8,
                'max_daily_searches': 100
            },
            'glassdoor': {
                'enabled': False,  # Requires more complex auth
                'search_url': 'https://www.glassdoor.com/Job/jobs.htm',
                'rate_limit': 15,
                'max_daily_searches': 30
            }
        }
        
        # Learning and adaptation
        self.performance_metrics = self._load_performance_metrics()
        
    def _setup_driver(self):
        """Setup Selenium WebDriver for web scraping"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.logger.info("WebDriver initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            self.driver = None
    
    def _load_search_preferences(self) -> Dict[str, Any]:
        """Load user search preferences and criteria"""
        prefs_file = "data/search_preferences.json"
        
        if os.path.exists(prefs_file):
            try:
                with open(prefs_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load search preferences: {e}")
        
        # Default preferences
        default_prefs = {
            "target_roles": [
                "Software Engineer", "Software Developer", "Python Developer",
                "Full Stack Developer", "Backend Developer", "Frontend Developer"
            ],
            "preferred_companies": [],
            "excluded_companies": [],
            "locations": ["Remote", "San Francisco", "New York", "Austin", "Seattle"],
            "salary_min": 80000,
            "salary_max": 200000,
            "experience_level": ["entry", "mid", "senior"],
            "required_skills": ["Python", "JavaScript", "React", "SQL"],
            "preferred_skills": ["AWS", "Docker", "Kubernetes", "Machine Learning"],
            "company_size": ["startup", "medium", "large"],
            "remote_preference": "hybrid",  # remote, onsite, hybrid, any
            "max_daily_applications": 10,
            "quality_threshold": 0.7,  # 0-1 score for job matching
            "search_frequency": "daily",  # hourly, daily, weekly
            "auto_apply": False,  # Start conservative
            "learning_enabled": True
        }
        
        # Save default preferences
        os.makedirs("data", exist_ok=True)
        try:
            with open(prefs_file, 'w') as f:
                json.dump(default_prefs, f, indent=2)
            self.logger.info("Default search preferences created")
        except Exception as e:
            self.logger.warning(f"Could not save default preferences: {e}")
        
        return default_prefs
    
    def _load_search_history(self) -> List[Dict[str, Any]]:
        """Load historical search data for learning"""
        history_file = "data/search_history.json"
        
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load search history: {e}")
        
        return []
    
    def _load_performance_metrics(self) -> Dict[str, Any]:
        """Load performance metrics for learning and optimization"""
        metrics_file = "data/performance_metrics.json"
        
        if os.path.exists(metrics_file):
            try:
                with open(metrics_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load performance metrics: {e}")
        
        return {
            "total_searches": 0,
            "jobs_found": 0,
            "jobs_applied": 0,
            "responses_received": 0,
            "interviews_scheduled": 0,
            "offers_received": 0,
            "response_rate_by_company": {},
            "response_rate_by_role": {},
            "successful_keywords": [],
            "best_performing_locations": [],
            "optimal_application_times": []
        }
    
    def search_jobs_autonomously(self) -> List[Dict[str, Any]]:
        """Main autonomous job search function"""
        self.logger.info("Starting autonomous job search...")
        
        # Check if we should search based on preferences and history
        if not self._should_search_now():
            self.logger.info("Skipping search based on frequency settings")
            return []
        
        all_jobs = []
        search_session = {
            "timestamp": datetime.now().isoformat(),
            "search_criteria": self.preferences.copy(),
            "results": []
        }
        
        # Search across enabled job boards
        for board_name, board_config in self.job_boards.items():
            if not board_config['enabled']:
                continue
                
            self.logger.info(f"Searching on {board_name}...")
            
            try:
                if board_name == 'linkedin':
                    jobs = self._search_linkedin()
                elif board_name == 'indeed':
                    jobs = self._search_indeed()
                elif board_name == 'glassdoor':
                    jobs = self._search_glassdoor()
                else:
                    continue
                
                # Add source information
                for job in jobs:
                    job['source'] = board_name
                    job['found_at'] = datetime.now().isoformat()
                
                all_jobs.extend(jobs)
                search_session["results"].extend(jobs)
                
                self.logger.info(f"Found {len(jobs)} jobs on {board_name}")
                
                # Rate limiting
                time.sleep(board_config['rate_limit'])
                
            except Exception as e:
                self.logger.error(f"Error searching {board_name}: {e}")
                continue
        
        # Filter and rank jobs using AI
        filtered_jobs = self._filter_and_rank_jobs(all_jobs)
        
        # Learn from search results
        if self.preferences.get('learning_enabled', True):
            self._learn_from_search_results(filtered_jobs)
        
        # Save search history
        self.search_history.append(search_session)
        self._save_search_history()
        
        # Update performance metrics
        self._update_search_metrics(len(all_jobs), len(filtered_jobs))
        
        self.logger.info(f"Autonomous search complete: {len(filtered_jobs)} qualified jobs found")
        
        return filtered_jobs
    
    def _should_search_now(self) -> bool:
        """Determine if we should search now based on preferences and history"""
        frequency = self.preferences.get('search_frequency', 'daily')
        
        if not self.search_history:
            return True
        
        last_search = self.search_history[-1]
        last_search_time = datetime.fromisoformat(last_search['timestamp'])
        now = datetime.now()
        
        if frequency == 'hourly':
            return (now - last_search_time) >= timedelta(hours=1)
        elif frequency == 'daily':
            return (now - last_search_time) >= timedelta(days=1)
        elif frequency == 'weekly':
            return (now - last_search_time) >= timedelta(weeks=1)
        
        return True
    
    def _search_linkedin(self) -> List[Dict[str, Any]]:
        """Search LinkedIn for job opportunities"""
        if not self.driver:
            return []
        
        jobs = []
        
        try:
            # Build search URL with preferences
            search_params = {
                'keywords': ' OR '.join(self.preferences.get('target_roles', [])),
                'location': self.preferences.get('locations', ['Remote'])[0],
                'f_TPR': 'r86400',  # Past 24 hours
                'f_WT': '2' if self.preferences.get('remote_preference') == 'remote' else '',
            }
            
            # Navigate to LinkedIn jobs
            self.driver.get("https://www.linkedin.com/jobs/search?" + 
                           "&".join([f"{k}={v}" for k, v in search_params.items() if v]))
            
            time.sleep(3)
            
            # Wait for job listings to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-search-results-list"))
            )
            
            # Extract job listings
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, ".job-search-card")
            
            for job_elem in job_elements[:20]:  # Limit to first 20 results
                try:
                    title = job_elem.find_element(By.CSS_SELECTOR, ".sr-only").text
                    company = job_elem.find_element(By.CSS_SELECTOR, ".hidden-nested-link").text
                    location = job_elem.find_element(By.CSS_SELECTOR, ".job-search-card__location").text
                    link = job_elem.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                    
                    # Get job description by clicking on the job
                    description = self._get_linkedin_job_description(job_elem, link)
                    
                    job_data = {
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": location.strip(),
                        "job_url": link,
                        "description": description,
                        "source": "linkedin",
                        "raw_data": {}
                    }
                    
                    jobs.append(job_data)
                    
                except Exception as e:
                    self.logger.warning(f"Error parsing LinkedIn job: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error searching LinkedIn: {e}")
        
        return jobs
    
    def _get_linkedin_job_description(self, job_elem, job_url) -> str:
        """Get detailed job description from LinkedIn"""
        try:
            # Click on the job to load description
            job_elem.click()
            time.sleep(2)
            
            # Wait for description to load
            description_elem = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".description__text"))
            )
            
            return description_elem.text.strip()
            
        except Exception as e:
            self.logger.warning(f"Could not get LinkedIn job description: {e}")
            return ""
    
    def _search_indeed(self) -> List[Dict[str, Any]]:
        """Search Indeed for job opportunities"""
        if not self.driver:
            return []
        
        jobs = []
        
        try:
            # Build Indeed search URL
            what = ' OR '.join(self.preferences.get('target_roles', []))
            where = self.preferences.get('locations', ['Remote'])[0]
            
            url = f"https://www.indeed.com/jobs?q={what}&l={where}&fromage=1&sort=date"
            
            self.driver.get(url)
            time.sleep(3)
            
            # Extract job listings
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, "[data-jk]")
            
            for job_elem in job_elements[:15]:  # Limit results
                try:
                    title_elem = job_elem.find_element(By.CSS_SELECTOR, "[data-testid='job-title']")
                    title = title_elem.text
                    
                    company_elem = job_elem.find_element(By.CSS_SELECTOR, "[data-testid='company-name']")
                    company = company_elem.text
                    
                    location_elem = job_elem.find_element(By.CSS_SELECTOR, "[data-testid='job-location']")
                    location = location_elem.text
                    
                    # Get job URL
                    link = title_elem.find_element(By.TAG_NAME, "a").get_attribute("href")
                    
                    # Get snippet/description
                    try:
                        snippet_elem = job_elem.find_element(By.CSS_SELECTOR, "[data-testid='job-snippet']")
                        description = snippet_elem.text
                    except:
                        description = ""
                    
                    job_data = {
                        "title": title.strip(),
                        "company": company.strip(),
                        "location": location.strip(),
                        "job_url": link,
                        "description": description,
                        "source": "indeed",
                        "raw_data": {}
                    }
                    
                    jobs.append(job_data)
                    
                except Exception as e:
                    self.logger.warning(f"Error parsing Indeed job: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error searching Indeed: {e}")
        
        return jobs
    
    def _search_glassdoor(self) -> List[Dict[str, Any]]:
        """Search Glassdoor for job opportunities (placeholder)"""
        # Glassdoor requires more complex authentication
        # This is a placeholder for future implementation
        self.logger.info("Glassdoor search not yet implemented")
        return []
    
    def _filter_and_rank_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Use AI to filter and rank jobs based on preferences and learning"""
        self.logger.info(f"Filtering and ranking {len(jobs)} jobs...")
        
        filtered_jobs = []
        
        for job in jobs:
            try:
                # Parse job with AI to extract detailed information
                job_info = self.job_parser.parse_job_text(
                    f"Title: {job['title']}\n"
                    f"Company: {job['company']}\n"
                    f"Location: {job['location']}\n"
                    f"Description: {job['description']}"
                )
                
                if 'error' in job_info:
                    continue
                
                # Calculate job score based on preferences
                score = self._calculate_job_score(job_info)
                
                if score >= self.preferences.get('quality_threshold', 0.7):
                    job_info['score'] = score
                    job_info['source'] = job['source']
                    job_info['job_url'] = job['job_url']
                    job_info['found_at'] = job.get('found_at')
                    
                    filtered_jobs.append(job_info)
                
            except Exception as e:
                self.logger.warning(f"Error filtering job: {e}")
                continue
        
        # Sort by score (highest first)
        filtered_jobs.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # Limit to max daily applications
        max_apps = self.preferences.get('max_daily_applications', 10)
        return filtered_jobs[:max_apps]
    
    def _calculate_job_score(self, job_info: Dict[str, Any]) -> float:
        """Calculate job matching score based on preferences and learning"""
        score = 0.0
        max_score = 0.0
        
        # Title matching
        title_weight = 0.3
        max_score += title_weight
        title = job_info.get('position', '').lower()
        target_roles = [role.lower() for role in self.preferences.get('target_roles', [])]
        if any(role in title for role in target_roles):
            score += title_weight
        
        # Skills matching
        skills_weight = 0.25
        max_score += skills_weight
        job_skills = [skill.lower() for skill in job_info.get('required_skills', [])]
        required_skills = [skill.lower() for skill in self.preferences.get('required_skills', [])]
        preferred_skills = [skill.lower() for skill in self.preferences.get('preferred_skills', [])]
        
        skill_matches = len(set(job_skills) & set(required_skills + preferred_skills))
        if job_skills:
            skills_match_ratio = skill_matches / len(job_skills)
            score += skills_weight * skills_match_ratio
        
        # Location matching
        location_weight = 0.2
        max_score += location_weight
        job_location = job_info.get('location', '').lower()
        preferred_locations = [loc.lower() for loc in self.preferences.get('locations', [])]
        if any(loc in job_location for loc in preferred_locations) or 'remote' in job_location:
            score += location_weight
        
        # Salary matching
        salary_weight = 0.15
        max_score += salary_weight
        salary_range = job_info.get('salary_range', '')
        if salary_range:
            # Simple salary parsing (can be improved)
            salary_numbers = re.findall(r'\d+', salary_range.replace(',', ''))
            if salary_numbers:
                avg_salary = sum(int(num) for num in salary_numbers) / len(salary_numbers)
                if avg_salary >= self.preferences.get('salary_min', 0):
                    score += salary_weight
        
        # Company preferences
        company_weight = 0.1
        max_score += company_weight
        company = job_info.get('company', '').lower()
        preferred_companies = [comp.lower() for comp in self.preferences.get('preferred_companies', [])]
        excluded_companies = [comp.lower() for comp in self.preferences.get('excluded_companies', [])]
        
        if excluded_companies and any(comp in company for comp in excluded_companies):
            score -= 0.5  # Heavy penalty for excluded companies
        elif preferred_companies and any(comp in company for comp in preferred_companies):
            score += company_weight
        
        # Normalize score
        return min(score / max_score if max_score > 0 else 0, 1.0)
    
    def _learn_from_search_results(self, jobs: List[Dict[str, Any]]):
        """Learn and adapt from search results"""
        if not jobs:
            return
        
        # Track successful keywords and patterns
        for job in jobs:
            # Update successful keywords
            job_skills = job.get('required_skills', [])
            for skill in job_skills:
                if skill not in self.performance_metrics['successful_keywords']:
                    self.performance_metrics['successful_keywords'].append(skill)
            
            # Track best performing locations
            location = job.get('location', '')
            if location and location not in self.performance_metrics['best_performing_locations']:
                self.performance_metrics['best_performing_locations'].append(location)
        
        # Adapt search preferences based on learning
        self._adapt_search_preferences(jobs)
    
    def _adapt_search_preferences(self, jobs: List[Dict[str, Any]]):
        """Adapt search preferences based on successful patterns"""
        # Add high-scoring job skills to preferred skills
        high_score_jobs = [job for job in jobs if job.get('score', 0) > 0.8]
        
        for job in high_score_jobs:
            job_skills = job.get('required_skills', [])
            for skill in job_skills:
                if skill not in self.preferences.get('preferred_skills', []):
                    self.preferences['preferred_skills'].append(skill)
        
        # Limit preferred skills to prevent infinite growth
        self.preferences['preferred_skills'] = self.preferences['preferred_skills'][-20:]
        
        # Save updated preferences
        self._save_search_preferences()
    
    def _save_search_preferences(self):
        """Save updated search preferences"""
        try:
            with open("data/search_preferences.json", 'w') as f:
                json.dump(self.preferences, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving search preferences: {e}")
    
    def _save_search_history(self):
        """Save search history"""
        try:
            # Keep only last 100 searches
            self.search_history = self.search_history[-100:]
            
            with open("data/search_history.json", 'w') as f:
                json.dump(self.search_history, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving search history: {e}")
    
    def _update_search_metrics(self, total_found: int, filtered_count: int):
        """Update performance metrics"""
        self.performance_metrics['total_searches'] += 1
        self.performance_metrics['jobs_found'] += total_found
        
        # Save metrics
        try:
            with open("data/performance_metrics.json", 'w') as f:
                json.dump(self.performance_metrics, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving performance metrics: {e}")
    
    def get_search_analytics(self) -> Dict[str, Any]:
        """Get analytics and insights from search history"""
        if not self.search_history:
            return {"message": "No search history available"}
        
        # Analyze search patterns
        total_searches = len(self.search_history)
        total_jobs_found = sum(len(search['results']) for search in self.search_history)
        avg_jobs_per_search = total_jobs_found / total_searches if total_searches > 0 else 0
        
        # Most successful keywords
        all_skills = []
        for search in self.search_history:
            for job in search['results']:
                if isinstance(job, dict) and 'required_skills' in job:
                    all_skills.extend(job['required_skills'])
        
        skill_counts = {}
        for skill in all_skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_searches": total_searches,
            "total_jobs_found": total_jobs_found,
            "average_jobs_per_search": avg_jobs_per_search,
            "top_skills": top_skills,
            "performance_metrics": self.performance_metrics,
            "current_preferences": self.preferences
        }
    
    def __del__(self):
        """Cleanup WebDriver on deletion"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass