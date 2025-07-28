#!/usr/bin/env python3
"""
AutoApply Agent - NVIDIA Hackathon Entry
An AI agent that automates job applications with customized resumes and cover letters
"""

import os
import sys
from dotenv import load_dotenv
from agents.job_application_agent import JobApplicationAgent
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

def main():
    """Main entry point for the AutoApply agent"""
    logger = setup_logger("autoapply")
    
    try:
        # Initialize the job application agent
        agent = JobApplicationAgent()
        
        # Start the agent
        logger.info("Starting AutoApply Agent...")
        agent.run()
        
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
    except Exception as e:
        logger.error(f"Agent failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()