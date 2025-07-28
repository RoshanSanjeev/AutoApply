#!/usr/bin/env python3
"""
Quick Setup Script for AutoApply Agent
"""
import os
import json
import subprocess
import sys

def create_env_file():
    """Create .env file from template"""
    if os.path.exists('.env'):
        print("✅ .env file already exists")
        return
    
    print("📝 Creating .env file...")
    
    # Get user input for essential settings
    openai_key = input("🔑 Enter your OpenAI API key: ").strip()
    user_name = input("👤 Enter your full name: ").strip()
    user_email = input("📧 Enter your email: ").strip()
    user_phone = input("📱 Enter your phone number: ").strip()
    user_linkedin = input("🔗 Enter your LinkedIn profile URL: ").strip()
    
    env_content = f"""# OpenAI API Key
OPENAI_API_KEY={openai_key}

# Google Sheets API Credentials (optional - set up later)
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
GOOGLE_SHEETS_ID=

# Browser automation settings
HEADLESS_BROWSER=true

# User profile settings
USER_NAME={user_name}
USER_EMAIL={user_email}
USER_PHONE={user_phone}
USER_LINKEDIN={user_linkedin}
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ .env file created successfully!")

def create_user_profile():
    """Create user profile JSON"""
    profile_file = "data/user_profile.json"
    
    if os.path.exists(profile_file):
        print("✅ User profile already exists")
        return
    
    print("📝 Creating user profile...")
    
    os.makedirs("data", exist_ok=True)
    
    # Load from .env if it exists
    from dotenv import load_dotenv
    load_dotenv()
    
    name = os.getenv("USER_NAME", input("👤 Enter your full name: "))
    email = os.getenv("USER_EMAIL", input("📧 Enter your email: "))
    phone = os.getenv("USER_PHONE", input("📱 Enter your phone: "))
    linkedin = os.getenv("USER_LINKEDIN", input("🔗 Enter LinkedIn URL: "))
    
    current_role = input("💼 Current job title: ").strip()
    experience_years = input("📅 Years of experience: ").strip()
    
    skills_input = input("🛠️ Key skills (comma-separated): ").strip()
    skills = [skill.strip() for skill in skills_input.split(',') if skill.strip()]
    
    profile = {
        "name": name,
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "current_role": current_role,
        "experience_years": int(experience_years) if experience_years.isdigit() else 5,
        "skills": skills,
        "achievements": [
            "Add your key achievements here",
            "Quantify your impact when possible",
            "Use action verbs and specific numbers"
        ],
        "preferred_locations": ["Remote"],
        "salary_range": "$100k-150k",
        "job_preferences": {
            "remote_ok": True,
            "full_time": True,
            "contract": False,
            "min_salary": 100000
        }
    }
    
    with open(profile_file, 'w') as f:
        json.dump(profile, f, indent=2)
    
    print("✅ User profile created successfully!")
    print(f"📁 Edit {profile_file} to customize further")

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False
    return True

def setup_chrome_driver():
    """Setup Chrome driver for Selenium"""
    print("🌐 Setting up Chrome WebDriver...")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service
        
        # Test Chrome driver setup
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://www.google.com")
        driver.quit()
        
        print("✅ Chrome WebDriver setup successfully!")
        return True
    except Exception as e:
        print(f"❌ Chrome WebDriver setup failed: {e}")
        print("💡 Make sure Chrome browser is installed")
        return False

def main():
    """Main setup function"""
    print("\n" + "="*60)
    print("🚀 AUTOAPPLY SETUP")
    print("="*60)
    print("Setting up your AI job application agent...")
    print("="*60)
    
    steps = [
        ("Installing dependencies", install_dependencies),
        ("Creating environment file", create_env_file),
        ("Creating user profile", create_user_profile),
        ("Setting up Chrome WebDriver", setup_chrome_driver)
    ]
    
    for step_name, step_func in steps:
        print(f"\n📋 {step_name}...")
        try:
            if not step_func():
                print(f"❌ {step_name} failed")
                return False
        except Exception as e:
            print(f"❌ {step_name} failed: {e}")
            return False
    
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETE!")
    print("="*60)
    print("Your AutoApply agent is ready to use!")
    print()
    print("📋 Quick Start:")
    print("1. Run: python apply_to_job.py")
    print("2. Paste any job URL")
    print("3. Let the AI do the rest!")
    print()
    print("⚙️ Optional Setup:")
    print("• Google Sheets: Set up API credentials for application tracking")
    print("• Resume: Edit data/base_resume.json with your details")
    print("• Profile: Customize data/user_profile.json")
    print("="*60)
    
    return True

if __name__ == "__main__":
    main()