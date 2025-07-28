#!/usr/bin/env python3
"""
AutoApply Web Frontend
Flask web server that provides a web interface for the AutoApply job application system
"""

import os
import json
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from agents.job_application_agent import JobApplicationAgent
from utils.job_text_parser import JobTextParser
from utils.batch_processor import BatchJobProcessor
from utils.sheets_manager import SheetsManager
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize logger
logger = setup_logger("web_frontend")

@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/config')
def get_config():
    """Get configuration status"""
    checks = {
        "nvidia_api": bool(os.getenv("OPENAI_API_KEY")),
        "user_name": bool(os.getenv("USER_NAME")),
        "user_email": bool(os.getenv("USER_EMAIL")),
        "master_resume": os.path.exists("data/master_resume.json"),
        "user_profile": os.path.exists("data/user_profile.json"),
        "google_sheets": os.path.exists(os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "credentials.json"))
    }
    
    return jsonify({
        "checks": checks,
        "all_configured": all(checks.values())
    })

@app.route('/api/job/parse', methods=['POST'])
def parse_job_text():
    """Parse job text and extract information"""
    try:
        data = request.get_json()
        job_text = data.get('job_text', '').strip()
        
        if not job_text:
            return jsonify({"error": "No job text provided"}), 400
        
        parser = JobTextParser()
        job_info = parser.parse_job_text(job_text)
        
        if 'error' in job_info:
            return jsonify({"error": job_info['error']}), 400
        
        return jsonify({"job_info": job_info})
        
    except Exception as e:
        logger.error(f"Error parsing job text: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/job/apply', methods=['POST'])
def apply_to_job():
    """Apply to a single job"""
    try:
        data = request.get_json()
        job_info = data.get('job_info')
        
        if not job_info:
            return jsonify({"error": "No job information provided"}), 400
        
        agent = JobApplicationAgent()
        result = agent.process_job_application(job_info)
        
        return jsonify({"result": result})
        
    except Exception as e:
        logger.error(f"Error applying to job: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/batch/upload', methods=['POST'])
def upload_batch_file():
    """Upload and process batch job file"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Secure the filename and save
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Detect file format
        processor = BatchJobProcessor()
        try:
            format_type = processor._detect_file_format(file_path)
        except:
            # Try to detect from extension
            ext = filename.lower().split('.')[-1]
            format_type = ext if ext in ['csv', 'json', 'txt'] else 'json'
        
        return jsonify({
            "message": "File uploaded successfully",
            "file_path": file_path,
            "format": format_type,
            "filename": filename
        })
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/batch/process', methods=['POST'])
def process_batch_jobs():
    """Process jobs from uploaded file"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        format_type = data.get('format', 'json')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 400
        
        processor = BatchJobProcessor()
        results = processor.process_jobs_from_file(file_path, format_type)
        
        # Clean up uploaded file
        try:
            os.remove(file_path)
        except:
            pass
        
        return jsonify({"results": results})
        
    except Exception as e:
        logger.error(f"Error processing batch jobs: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get application statistics"""
    try:
        sheets_manager = SheetsManager()
        stats = sheets_manager.get_application_stats()
        return jsonify({"stats": stats})
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/applications')
def get_applications():
    """Get recent applications"""
    try:
        sheets_manager = SheetsManager()
        applications = sheets_manager.get_applications()
        
        # Limit to recent applications
        recent_apps = applications[:20] if applications else []
        
        return jsonify({"applications": recent_apps})
        
    except Exception as e:
        logger.error(f"Error getting applications: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/profile', methods=['GET'])
def get_profile():
    """Get user profile information"""
    try:
        # Try to load from file first
        profile_file = "data/user_profile.json"
        if os.path.exists(profile_file):
            with open(profile_file, 'r') as f:
                profile = json.load(f)
        else:
            # Return default profile structure
            profile = {
                "name": os.getenv("USER_NAME", ""),
                "email": os.getenv("USER_EMAIL", ""),
                "phone": os.getenv("USER_PHONE", ""),
                "linkedin": os.getenv("USER_LINKEDIN", ""),
                "current_role": "",
                "experience_years": 0,
                "skills": [],
                "achievements": [],
                "preferred_locations": [],
                "salary_range": ""
            }
        
        return jsonify({"profile": profile})
        
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/profile', methods=['POST'])
def save_profile():
    """Save user profile information"""
    try:
        data = request.get_json()
        profile = data.get('profile')
        
        if not profile:
            return jsonify({"error": "No profile data provided"}), 400
        
        # Save to file
        os.makedirs("data", exist_ok=True)
        profile_file = "data/user_profile.json"
        
        with open(profile_file, 'w') as f:
            json.dump(profile, f, indent=2)
        
        return jsonify({"message": "Profile saved successfully"})
        
    except Exception as e:
        logger.error(f"Error saving profile: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/resume', methods=['GET'])
def get_resume():
    """Get base resume information"""
    try:
        resume_file = "data/base_resume.json"
        if os.path.exists(resume_file):
            with open(resume_file, 'r') as f:
                resume = json.load(f)
        else:
            # Return default resume structure
            resume = {
                "name": os.getenv("USER_NAME", ""),
                "email": os.getenv("USER_EMAIL", ""),
                "phone": os.getenv("USER_PHONE", ""),
                "linkedin": os.getenv("USER_LINKEDIN", ""),
                "summary": "",
                "skills": [],
                "experience": [],
                "education": [],
                "projects": [],
                "certifications": [],
                "awards": []
            }
        
        return jsonify({"resume": resume})
        
    except Exception as e:
        logger.error(f"Error getting resume: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/resume', methods=['POST'])
def save_resume():
    """Save base resume information"""
    try:
        data = request.get_json()
        resume = data.get('resume')
        
        if not resume:
            return jsonify({"error": "No resume data provided"}), 400
        
        # Save to file
        os.makedirs("data", exist_ok=True)
        resume_file = "data/base_resume.json"
        
        with open(resume_file, 'w') as f:
            json.dump(resume, f, indent=2)
        
        return jsonify({"message": "Resume saved successfully"})
        
    except Exception as e:
        logger.error(f"Error saving resume: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/sample/<format_type>')
def download_sample_file(format_type):
    """Download sample job file"""
    try:
        if format_type not in ['json', 'csv', 'txt']:
            return jsonify({"error": "Invalid format"}), 400
        
        processor = BatchJobProcessor()
        filename = processor.create_sample_job_file(format_type)
        
        # Make sure the file exists
        if not os.path.exists(filename):
            return jsonify({"error": "Sample file could not be created"}), 500
        
        # Get just the filename for the download
        base_filename = os.path.basename(filename)
        
        return send_file(
            filename, 
            as_attachment=True,
            download_name=f"sample_jobs.{format_type}",
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"Error creating sample file: {e}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    
    logger.info(f"Starting AutoApply Web Frontend on port {port}")
    app.run(debug=debug_mode, host='0.0.0.0', port=port)