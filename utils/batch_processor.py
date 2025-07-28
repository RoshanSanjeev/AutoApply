"""
Batch Job Processor - Process multiple jobs at once
"""
import os
import json
import csv
from typing import Dict, List, Any, Optional
from datetime import datetime
import time
from pathlib import Path

from utils.job_text_parser import JobTextParser
from utils.resume_generator import ResumeGenerator
from utils.cover_letter_generator import CoverLetterGenerator
from utils.sheets_manager import SheetsManager
from utils.logger import setup_logger


class BatchJobProcessor:
    """Process multiple job applications in batch"""
    
    def __init__(self):
        self.logger = setup_logger("batch_processor")
        self.job_parser = JobTextParser()
        self.resume_generator = ResumeGenerator()
        self.cover_letter_generator = CoverLetterGenerator()
        self.sheets_manager = SheetsManager()
        
        # Create output directories
        self.output_dir = Path("output")
        self.resume_dir = self.output_dir / "resumes" 
        self.cover_letter_dir = self.output_dir / "cover_letters"
        self.simplify_dir = self.output_dir / "simplify_export"
        
        for dir_path in [self.output_dir, self.resume_dir, self.cover_letter_dir, self.simplify_dir]:
            dir_path.mkdir(exist_ok=True)
    
    def process_jobs_from_file(self, file_path: str, job_format: str = "auto") -> Dict[str, Any]:
        """Process jobs from a file (CSV, JSON, or TXT)"""
        
        if job_format == "auto":
            job_format = self._detect_file_format(file_path)
        
        try:
            if job_format == "csv":
                jobs = self._load_jobs_from_csv(file_path)
            elif job_format == "json":
                jobs = self._load_jobs_from_json(file_path)
            elif job_format == "txt":
                jobs = self._load_jobs_from_txt(file_path)
            else:
                raise ValueError(f"Unsupported file format: {job_format}")
            
            return self.process_job_batch(jobs)
            
        except Exception as e:
            self.logger.error(f"Failed to process jobs from file: {e}")
            return {"error": str(e)}
    
    def process_job_batch(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a batch of jobs"""
        
        start_time = time.time()
        results = {
            "total_jobs": len(jobs),
            "successful": 0,
            "failed": 0,
            "processing_time": 0,
            "job_results": [],
            "errors": []
        }
        
        self.logger.info(f"Starting batch processing of {len(jobs)} jobs")
        
        # Load user profile and master resume
        user_profile = self._load_user_profile()
        master_resume = self._load_master_resume()
        
        for i, job in enumerate(jobs, 1):
            self.logger.info(f"Processing job {i}/{len(jobs)}: {job.get('position', 'Unknown')} at {job.get('company', 'Unknown')}")
            
            try:
                job_result = self._process_single_job(job, user_profile, master_resume, i)
                
                if job_result.get("success"):
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(job_result.get("error", "Unknown error"))
                
                results["job_results"].append(job_result)
                
                # Add delay between jobs to avoid rate limiting
                if i < len(jobs):
                    time.sleep(2)
                    
            except Exception as e:
                error_msg = f"Failed to process job {i}: {str(e)}"
                self.logger.error(error_msg)
                results["failed"] += 1
                results["errors"].append(error_msg)
                results["job_results"].append({
                    "job_index": i,
                    "success": False,
                    "error": error_msg
                })
        
        results["processing_time"] = time.time() - start_time
        
        # Generate summary report
        self._generate_batch_report(results)
        
        self.logger.info(f"Batch processing complete: {results['successful']} successful, {results['failed']} failed")
        
        return results
    
    def _process_single_job(self, job: Dict[str, Any], user_profile: Dict[str, Any], 
                           master_resume: Dict[str, Any], job_index: int) -> Dict[str, Any]:
        """Process a single job application"""
        
        result = {
            "job_index": job_index,
            "company": job.get("company", "Unknown"),
            "position": job.get("position", "Unknown"),
            "success": False,
            "resume_path": "",
            "cover_letter_path": "",
            "simplify_exported": False,
            "sheets_recorded": False,
            "error": ""
        }
        
        try:
            # If job data is raw text, parse it first
            if "job_text" in job and not job.get("parsed"):
                parsed_info = self.job_parser.parse_job_text(job["job_text"])
                if "error" in parsed_info:
                    result["error"] = f"Job parsing failed: {parsed_info['error']}"
                    return result
                job.update(parsed_info)
            
            # Generate custom resume
            job_description = job.get("description", "") or job.get("job_text", "")
            customized_resume = self.resume_generator.customize_resume(master_resume, job_description)
            
            # Generate resume LaTeX
            resume_filename = f"resume_{job.get('company', 'unknown').replace(' ', '_')}_{job_index}.tex"
            resume_path = self.resume_dir / resume_filename
            self.resume_generator.generate_latex(customized_resume, str(resume_path))
            result["resume_path"] = str(resume_path)
            
            # Generate cover letter
            cover_letter_text = self.cover_letter_generator.generate_cover_letter(job, user_profile)
            
            # Generate cover letter LaTeX
            cover_letter_filename = f"cover_letter_{job.get('company', 'unknown').replace(' ', '_')}_{job_index}.tex"
            cover_letter_path = self.cover_letter_dir / cover_letter_filename
            self.cover_letter_generator.generate_latex(cover_letter_text, job, user_profile, str(cover_letter_path))
            result["cover_letter_path"] = str(cover_letter_path)
            
            # Export for Simplify
            simplify_exported = self._export_for_simplify(job, result, job_index)
            result["simplify_exported"] = simplify_exported
            
            # Record in Google Sheets
            sheets_data = {
                "company": job.get("company", ""),
                "position": job.get("position", ""),
                "job_url": job.get("job_url", ""),
                "status": "Generated",
                "custom_resume_path": result["resume_path"],
                "custom_cover_letter_path": result["cover_letter_path"],
                "simplify_export_path": str(self.simplify_dir / f"simplify_export_{job.get('company', 'unknown').replace(' ', '_')}_{job_index}.json"),
                "application_method": "AutoApply + Simplify",
                "salary_range": job.get("salary_range", ""),
                "location": job.get("location", ""),
                "remote_option": "Yes" if job.get("remote_ok") else "No",
                "employment_type": job.get("employment_type", ""),
                "required_skills": job.get("required_skills", []),
                "experience_required": job.get("experience_years", ""),
                "processing_success": True,
                "notes": f"Auto-generated on {datetime.now().strftime('%Y-%m-%d %H:%M')} | Batch job #{job_index}"
            }
            
            sheets_recorded = self.sheets_manager.add_application(sheets_data)
            result["sheets_recorded"] = sheets_recorded
            
            result["success"] = True
            
            self.logger.info(f"Successfully processed: {job.get('position')} at {job.get('company')}")
            
        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"Error processing job {job_index}: {e}")
        
        return result
    
    def _export_for_simplify(self, job: Dict[str, Any], result: Dict[str, Any], job_index: int) -> bool:
        """Export job data and generated files for Simplify"""
        
        try:
            export_data = {
                "job_info": {
                    "company": job.get("company", ""),
                    "position": job.get("position", ""),
                    "job_url": job.get("job_url", ""),
                    "location": job.get("location", ""),
                    "salary_range": job.get("salary_range", ""),
                    "remote_ok": job.get("remote_ok", False),
                    "application_deadline": job.get("application_deadline", ""),
                    "employment_type": job.get("employment_type", "")
                },
                "generated_files": {
                    "resume_latex": result["resume_path"],
                    "cover_letter_latex": result["cover_letter_path"],
                    "generation_date": datetime.now().isoformat()
                },
                "instructions": {
                    "resume": "Upload the resume LaTeX file to Overleaf, compile to PDF, then upload PDF to Simplify",
                    "cover_letter": "Upload the cover letter LaTeX file to Overleaf, compile to PDF, then use in Simplify application",
                    "application": "Use Simplify browser extension to apply with generated documents"
                }
            }
            
            export_filename = f"simplify_export_{job.get('company', 'unknown').replace(' ', '_')}_{job_index}.json"
            export_path = self.simplify_dir / export_filename
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            self.logger.info(f"Exported for Simplify: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export for Simplify: {e}")
            return False
    
    def _load_jobs_from_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """Load jobs from CSV file"""
        jobs = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                jobs.append(dict(row))
        
        return jobs
    
    def _load_jobs_from_json(self, file_path: str) -> List[Dict[str, Any]]:
        """Load jobs from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both list of jobs and single job object
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            if "jobs" in data:
                return data["jobs"]
            else:
                return [data]
        else:
            raise ValueError("Invalid JSON format")
    
    def _load_jobs_from_txt(self, file_path: str) -> List[Dict[str, Any]]:
        """Load jobs from text file (one job posting per section, separated by '---')"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by separator
        job_texts = content.split('---')
        
        jobs = []
        for i, job_text in enumerate(job_texts, 1):
            job_text = job_text.strip()
            if job_text:
                jobs.append({
                    "job_text": job_text,
                    "source": "text_file",
                    "parsed": False,
                    "job_index": i
                })
        
        return jobs
    
    def _detect_file_format(self, file_path: str) -> str:
        """Detect file format from extension"""
        ext = Path(file_path).suffix.lower()
        
        if ext == '.csv':
            return 'csv'
        elif ext == '.json':
            return 'json'
        elif ext in ['.txt', '.text']:
            return 'txt'
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
    
    def _load_user_profile(self) -> Dict[str, Any]:
        """Load user profile from data directory"""
        try:
            with open('data/user_profile.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning("User profile not found, using default")
            return {
                "name": os.getenv("USER_NAME", "Your Name"),
                "email": os.getenv("USER_EMAIL", "your.email@example.com"),
                "phone": os.getenv("USER_PHONE", "+1234567890"),
                "linkedin": os.getenv("USER_LINKEDIN", ""),
                "current_role": "Software Engineer",
                "experience_years": 3,
                "skills": ["Python", "JavaScript", "React"],
                "key_achievements": ["Built scalable applications", "Led development teams"]
            }
    
    def _load_master_resume(self) -> Dict[str, Any]:
        """Load master resume from data directory"""
        try:
            with open('data/master_resume.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning("Master resume not found, using default")
            return self.resume_generator.load_base_resume("data/master_resume.json")
    
    def _generate_batch_report(self, results: Dict[str, Any]) -> str:
        """Generate a summary report of batch processing"""
        
        report_filename = f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_path = self.output_dir / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("="*60 + "\n")
            f.write("AUTOAPPLY BATCH PROCESSING REPORT\n")
            f.write("="*60 + "\n\n")
            
            f.write(f"Processing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Jobs Processed: {results['total_jobs']}\n")
            f.write(f"Successful: {results['successful']}\n")
            f.write(f"Failed: {results['failed']}\n")
            f.write(f"Success Rate: {(results['successful']/results['total_jobs']*100):.1f}%\n")
            f.write(f"Total Processing Time: {results['processing_time']:.2f} seconds\n\n")
            
            f.write("JOB RESULTS:\n")
            f.write("-" * 40 + "\n")
            
            for job_result in results['job_results']:
                status = "✅ SUCCESS" if job_result['success'] else "❌ FAILED"
                f.write(f"{status}: {job_result['position']} at {job_result['company']}\n")
                
                if job_result['success']:
                    f.write(f"  Resume: {job_result['resume_path']}\n")
                    f.write(f"  Cover Letter: {job_result['cover_letter_path']}\n")
                    f.write(f"  Simplify Export: {'Yes' if job_result['simplify_exported'] else 'No'}\n")
                    f.write(f"  Sheets Recorded: {'Yes' if job_result['sheets_recorded'] else 'No'}\n")
                else:
                    f.write(f"  Error: {job_result['error']}\n")
                f.write("\n")
            
            if results['errors']:
                f.write("ERRORS ENCOUNTERED:\n")
                f.write("-" * 40 + "\n")
                for error in results['errors']:
                    f.write(f"• {error}\n")
                f.write("\n")
            
            f.write("FILES GENERATED:\n")
            f.write("-" * 40 + "\n")
            f.write(f"• Resumes: {self.resume_dir}\n")
            f.write(f"• Cover Letters: {self.cover_letter_dir}\n")
            f.write(f"• Simplify Exports: {self.simplify_dir}\n")
            f.write(f"• Report: {report_path}\n")
        
        self.logger.info(f"Batch report generated: {report_path}")
        return str(report_path)
    
    def create_sample_job_file(self, format_type: str = "json") -> str:
        """Create a sample job file for testing"""
        
        sample_jobs = [
            {
                "company": "Tech Innovations Inc",
                "position": "Senior Software Engineer",
                "location": "San Francisco, CA",
                "job_url": "https://example.com/job1",
                "salary_range": "$120,000 - $160,000",
                "remote_ok": True,
                "employment_type": "full-time",
                "description": "We are looking for a Senior Software Engineer to join our growing team. You will work on developing scalable web applications using modern technologies including React, Node.js, and AWS.",
                "required_skills": ["JavaScript", "React", "Node.js", "AWS", "Docker"],
                "experience_years": "5+"
            },
            {
                "company": "Data Science Corp",
                "position": "Python Developer",
                "location": "Austin, TX",
                "job_url": "https://example.com/job2",
                "salary_range": "$90,000 - $130,000",
                "remote_ok": False,
                "employment_type": "full-time",
                "description": "Join our data science team as a Python Developer. You'll be building data pipelines, machine learning models, and analytics dashboards using Python, pandas, and scikit-learn.",
                "required_skills": ["Python", "pandas", "scikit-learn", "SQL", "Git"],
                "experience_years": "3+"
            }
        ]
        
        if format_type == "json":
            filename = "sample_jobs.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({"jobs": sample_jobs}, f, indent=2)
        
        elif format_type == "csv":
            filename = "sample_jobs.csv"
            fieldnames = sample_jobs[0].keys()
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for job in sample_jobs:
                    # Convert lists to comma-separated strings for CSV
                    job_copy = job.copy()
                    if isinstance(job_copy.get('required_skills'), list):
                        job_copy['required_skills'] = ', '.join(job_copy['required_skills'])
                    writer.writerow(job_copy)
        
        elif format_type == "txt":
            filename = "sample_jobs.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                for i, job in enumerate(sample_jobs):
                    if i > 0:
                        f.write("\n---\n\n")
                    
                    f.write(f"Position: {job['position']}\n")
                    f.write(f"Company: {job['company']}\n")
                    f.write(f"Location: {job['location']}\n")
                    f.write(f"Salary: {job['salary_range']}\n")
                    f.write(f"Remote: {'Yes' if job['remote_ok'] else 'No'}\n")
                    f.write(f"Employment Type: {job['employment_type']}\n")
                    f.write(f"\nDescription:\n{job['description']}\n")
                    f.write(f"\nRequired Skills: {', '.join(job['required_skills'])}\n")
                    f.write(f"Experience Required: {job['experience_years']}\n")
        
        self.logger.info(f"Sample job file created: {filename}")
        return filename