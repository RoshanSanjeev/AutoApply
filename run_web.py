#!/usr/bin/env python3
"""
AutoApply Web Frontend Launcher
Simple script to start the web interface
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Launch the web frontend"""
    print("🚀 Starting AutoApply Web Frontend...")
    print("="*50)
    
    # Check if Flask is installed
    try:
        import flask
        print(f"✅ Flask {flask.__version__} found")
    except ImportError:
        print("❌ Flask not found. Please install requirements:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    
    # Check environment variables
    required_env = ["OPENAI_API_KEY", "USER_NAME", "USER_EMAIL"]
    missing_env = []
    
    for env_var in required_env:
        if not os.getenv(env_var):
            missing_env.append(env_var)
    
    if missing_env:
        print("⚠️  Missing environment variables:")
        for var in missing_env:
            print(f"   - {var}")
        print("   Please check your .env file")
        print()
    
    # Check data files
    data_files = ["data/master_resume.json", "data/user_profile.json"]
    missing_files = []
    
    for file_path in data_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("⚠️  Missing data files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        print("   Run quick_setup.py to create these files")
        print()
    
    # Start the web app
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    print(f"🌐 Starting web server on http://localhost:{port}")
    print("   Press Ctrl+C to stop")
    print("="*50)
    
    try:
        from app import app
        app.run(debug=debug, host='0.0.0.0', port=port)
    except KeyboardInterrupt:
        print("\n👋 Web server stopped")
    except Exception as e:
        print(f"\n❌ Error starting web server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()