#!/usr/bin/env python3
"""
Quick Apply Script - Paste a job posting text and automatically generate LaTeX resume and cover letter
Usage: python apply_to_job.py or run interactively
"""
import os
from dotenv import load_dotenv
from agents.job_application_agent import JobApplicationAgent
from utils.job_text_parser import JobTextParser
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

def apply_to_job_text(job_text: str) -> bool:
    """Apply to a job from pasted text"""
    logger = setup_logger("apply_to_job")
    
    try:
        logger.info("Starting application process for pasted job text")
        
        # Step 1: Parse job information from text
        logger.info("Extracting job information from text...")
        parser = JobTextParser()
        job_info = parser.parse_job_text(job_text)
        
        if 'error' in job_info:
            logger.error(f"Failed to parse job info: {job_info['error']}")
            return False
        
        if not job_info.get('position') or not job_info.get('company'):
            logger.error("Could not extract essential job information (position/company)")
            return False
        
        # Display extracted information
        print("\n" + "="*60)
        print("🔍 EXTRACTED JOB INFORMATION")
        print("="*60)
        print(f"Position: {job_info.get('position', 'N/A')}")
        print(f"Company: {job_info.get('company', 'N/A')}")
        print(f"Location: {job_info.get('location', 'N/A')}")
        print(f"Remote: {job_info.get('remote_ok', 'N/A')}")
        print(f"Salary: {job_info.get('salary_range', 'N/A')}")
        print(f"Skills: {', '.join(job_info.get('required_skills', []))}")
        print(f"Description: {job_info.get('description', 'N/A')[:200]}...")
        print("="*60)
        
        # Ask for confirmation
        confirm = input("\n🤖 Proceed with generating LaTeX documents? (y/n): ").lower().strip()
        if confirm != 'y':
            print("❌ Document generation cancelled.")
            return False
        
        # Step 2: Process application
        logger.info("Generating customized LaTeX documents...")
        agent = JobApplicationAgent()
        result = agent.process_job_application(job_info)
        
        # Display results
        print("\n" + "="*60)
        print("📋 DOCUMENT GENERATION RESULTS")
        print("="*60)
        
        if result.get('status') == 'success':
            print("✅ LaTeX documents generated successfully!")
            print(f"📄 Resume LaTeX: {result.get('resume_path', 'N/A')}")
            print(f"📝 Cover Letter LaTeX: {result.get('cover_letter_path', 'N/A')}")
            print(f"📊 Tracked in Sheets: {'Yes' if result.get('sheets_recorded') else 'No'}")
            print(f"⏱️ Processing Time: {result.get('processing_time', 0):.2f}s")
            
            print("\n🎉 LaTeX files ready for Overleaf!")
            print("📋 Upload the .tex files to Overleaf to generate PDFs")
        else:
            print("❌ Document generation failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
            return False
        
        print("="*60)
        return True
        
    except KeyboardInterrupt:
        print("\n❌ Application cancelled by user.")
        return False
    except Exception as e:
        logger.error(f"Application failed: {e}")
        print(f"\n❌ Application failed: {e}")
        return False

def interactive_mode():
    """Run in interactive mode to get job text from user"""
    print("\n" + "="*60)
    print("🚀 AUTOAPPLY - LaTeX Resume & Cover Letter Generator")
    print("="*60)
    print("Paste a job posting below and I'll automatically:")
    print("• Extract job information")
    print("• Generate customized LaTeX resume")
    print("• Create personalized LaTeX cover letter")
    print("• Prepare files for Overleaf PDF generation")
    print("• Track in Google Sheets")
    print("="*60)
    
    while True:
        try:
            print("\n📝 Paste the job posting text below (press Enter twice when done):")
            job_text_lines = []
            empty_lines = 0
            
            while True:
                line = input()
                if line.strip() == "":
                    empty_lines += 1
                    if empty_lines >= 2:
                        break
                else:
                    empty_lines = 0
                    
                job_text_lines.append(line)
            
            job_text = "\n".join(job_text_lines).strip()
            
            if job_text.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not job_text:
                print("❌ Please paste some job posting text")
                continue
            
            # Process the job application
            success = apply_to_job_text(job_text)
            
            if success:
                another = input("\n🔄 Generate documents for another job? (y/n): ").lower().strip()
                if another != 'y':
                    print("👋 Thanks for using AutoApply!")
                    break
            else:
                retry = input("\n🔄 Try with another job posting? (y/n): ").lower().strip()
                if retry != 'y':
                    break
                    
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            continue

def main():
    """Main entry point"""
    # Always run in interactive mode for job text input
    interactive_mode()

if __name__ == "__main__":
    main()