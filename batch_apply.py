#!/usr/bin/env python3
"""
AutoApply Batch Processor - Comprehensive Job Application Automation
Generate custom resumes and cover letters for multiple jobs, export for Simplify, track in Google Sheets
"""
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

from utils.batch_processor import BatchJobProcessor
from utils.sheets_manager import SheetsManager
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

def show_banner():
    """Display the application banner"""
    print("\n" + "="*80)
    print("🚀 AUTOAPPLY BATCH PROCESSOR")
    print("="*80)
    print("Comprehensive Job Application Automation System")
    print("• Generate custom LaTeX resumes and cover letters")
    print("• Export for Simplify browser extension")
    print("• Track applications in Google Sheets")
    print("• Process multiple jobs from CSV, JSON, or text files")
    print("="*80)

def interactive_mode():
    """Run in interactive mode"""
    show_banner()
    
    processor = BatchJobProcessor()
    logger = setup_logger("batch_apply")
    
    while True:
        try:
            print("\n📋 MAIN MENU")
            print("-" * 40)
            print("1. Process jobs from file")
            print("2. Create sample job file")
            print("3. View application statistics")
            print("4. Setup verification")
            print("5. Exit")
            print("-" * 40)
            
            choice = input("Select an option (1-5): ").strip()
            
            if choice == "1":
                process_jobs_menu(processor)
            elif choice == "2":
                create_sample_file_menu(processor)
            elif choice == "3":
                view_statistics_menu()
            elif choice == "4":
                setup_verification_menu()
            elif choice == "5":
                print("👋 Thanks for using AutoApply!")
                break
            else:
                print("❌ Invalid choice. Please select 1-5.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error in main menu: {e}")
            print(f"❌ Error: {e}")

def process_jobs_menu(processor: BatchJobProcessor):
    """Handle job processing menu"""
    print("\n📁 PROCESS JOBS FROM FILE")
    print("-" * 40)
    
    file_path = input("Enter file path (or drag & drop file): ").strip().strip('"\'')
    
    if not file_path:
        print("❌ No file specified.")
        return
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    # Detect or ask for file format
    try:
        format_type = processor._detect_file_format(file_path)
        print(f"📄 Detected format: {format_type.upper()}")
    except:
        print("🔍 Could not auto-detect format.")
        format_type = input("Enter format (csv/json/txt): ").strip().lower()
        if format_type not in ['csv', 'json', 'txt']:
            print("❌ Invalid format. Must be csv, json, or txt.")
            return
    
    # Confirm processing
    print(f"\n🔄 Ready to process jobs from: {file_path}")
    confirm = input("Proceed? (y/n): ").lower().strip()
    
    if confirm != 'y':
        print("❌ Processing cancelled.")
        return
    
    # Process the jobs
    print("\n🚀 Starting batch processing...")
    print("This may take several minutes depending on the number of jobs.")
    
    results = processor.process_jobs_from_file(file_path, format_type)
    
    if "error" in results:
        print(f"❌ Processing failed: {results['error']}")
        return
    
    # Display results
    print("\n" + "="*60)
    print("📊 PROCESSING RESULTS")
    print("="*60)
    print(f"✅ Total Jobs: {results['total_jobs']}")
    print(f"✅ Successful: {results['successful']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"⏱️  Processing Time: {results['processing_time']:.2f} seconds")
    print(f"📈 Success Rate: {(results['successful']/results['total_jobs']*100):.1f}%")
    
    if results['successful'] > 0:
        print(f"\n📁 Generated Files:")
        print(f"  • Resumes: output/resumes/")
        print(f"  • Cover Letters: output/cover_letters/")
        print(f"  • Simplify Exports: output/simplify_export/")
    
    if results['errors']:
        print(f"\n⚠️  Errors encountered:")
        for error in results['errors'][:3]:  # Show first 3 errors
            print(f"  • {error}")
        if len(results['errors']) > 3:
            print(f"  • ... and {len(results['errors']) - 3} more errors")
    
    print("\n🎉 Batch processing complete!")
    print("📋 Upload .tex files to Overleaf, then use Simplify to apply")
    
    input("\nPress Enter to continue...")

def create_sample_file_menu(processor: BatchJobProcessor):
    """Handle sample file creation"""
    print("\n📄 CREATE SAMPLE JOB FILE")
    print("-" * 40)
    print("Available formats:")
    print("1. JSON (recommended)")
    print("2. CSV")  
    print("3. TXT")
    
    choice = input("Select format (1-3): ").strip()
    
    format_map = {'1': 'json', '2': 'csv', '3': 'txt'}
    
    if choice not in format_map:
        print("❌ Invalid choice.")
        return
    
    format_type = format_map[choice]
    
    try:
        filename = processor.create_sample_job_file(format_type)
        print(f"✅ Sample file created: {filename}")
        print(f"📝 Edit this file with your job data, then use option 1 to process it.")
    except Exception as e:
        print(f"❌ Failed to create sample file: {e}")
    
    input("\nPress Enter to continue...")

def view_statistics_menu():
    """Handle statistics viewing"""
    print("\n📊 APPLICATION STATISTICS")
    print("-" * 40)
    
    try:
        sheets_manager = SheetsManager()
        stats = sheets_manager.get_application_stats()
        
        if not stats:
            print("📝 No statistics available. Make sure Google Sheets is configured.")
            return
        
        print(f"📈 Total Applications: {stats.get('total_applications', 0)}")
        print(f"🎯 Response Rate: {stats.get('response_rate', 0)}%")
        print(f"📅 Recent Applications (7 days): {stats.get('recent_applications', 0)}")
        print(f"🗣️  Interviews Scheduled: {stats.get('interviews_scheduled', 0)}")
        print(f"🎉 Offers Received: {stats.get('offers_received', 0)}")
        
        status_breakdown = stats.get('status_breakdown', {})
        if status_breakdown:
            print(f"\n📋 Status Breakdown:")
            for status, count in status_breakdown.items():
                print(f"  • {status}: {count}")
        
    except Exception as e:
        print(f"❌ Failed to get statistics: {e}")
    
    input("\nPress Enter to continue...")

def setup_verification_menu():
    """Handle setup verification"""
    print("\n🔧 SETUP VERIFICATION")
    print("-" * 40)
    
    checks = [
        ("NVIDIA API Key", os.getenv("OPENAI_API_KEY")),
        ("User Name", os.getenv("USER_NAME")),
        ("User Email", os.getenv("USER_EMAIL")),
        ("User Phone", os.getenv("USER_PHONE")),
        ("Master Resume", os.path.exists("data/master_resume.json")),
        ("User Profile", os.path.exists("data/user_profile.json")),
        ("Google Sheets Credentials", os.path.exists(os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "credentials.json"))),
    ]
    
    print("Checking configuration...")
    all_good = True
    
    for check_name, check_value in checks:
        status = "✅" if check_value else "❌"
        print(f"{status} {check_name}")
        if not check_value:
            all_good = False
    
    if all_good:
        print("\n🎉 All checks passed! You're ready to process jobs.")
    else:
        print("\n⚠️  Some configuration issues found:")
        print("• Check your .env file for missing values")
        print("• Ensure data/ directory has master_resume.json and user_profile.json")
        print("• For Google Sheets: add credentials.json and set GOOGLE_SHEETS_CREDENTIALS_FILE")
    
    # Test NVIDIA API
    print("\n🧪 Testing NVIDIA API connection...")
    try:
        from utils.job_text_parser import JobTextParser
        parser = JobTextParser()
        print("✅ NVIDIA API connection ready")
    except Exception as e:
        print(f"❌ NVIDIA API connection failed: {e}")
    
    input("\nPress Enter to continue...")

def command_line_mode(args):
    """Handle command line processing"""
    processor = BatchJobProcessor()
    logger = setup_logger("batch_apply_cli")
    
    if not os.path.exists(args.file):
        print(f"❌ File not found: {args.file}")
        return 1
    
    logger.info(f"Processing jobs from: {args.file}")
    
    # Process the jobs
    results = processor.process_jobs_from_file(args.file, args.format)
    
    if "error" in results:
        print(f"❌ Processing failed: {results['error']}")
        return 1
    
    # Output results
    print(f"✅ Processed {results['total_jobs']} jobs")
    print(f"✅ Successful: {results['successful']}")
    print(f"❌ Failed: {results['failed']}")
    
    if args.quiet:
        return 0
    
    # Detailed output
    print(f"\n📁 Generated Files:")
    print(f"  • Resumes: output/resumes/")
    print(f"  • Cover Letters: output/cover_letters/")
    print(f"  • Simplify Exports: output/simplify_export/")
    
    return 0

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="AutoApply Batch Processor - Generate custom resumes and cover letters for multiple jobs"
    )
    
    parser.add_argument(
        "file",
        nargs="?",
        help="Job file to process (CSV, JSON, or TXT format)"
    )
    
    parser.add_argument(
        "--format",
        choices=["csv", "json", "txt", "auto"],
        default="auto",
        help="File format (auto-detected if not specified)"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal output"
    )
    
    args = parser.parse_args()
    
    if args.file:
        # Command line mode
        return command_line_mode(args)
    else:
        # Interactive mode
        interactive_mode()
        return 0

if __name__ == "__main__":
    sys.exit(main())