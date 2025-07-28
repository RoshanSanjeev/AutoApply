"""
Cover Letter Generator using NVIDIA AI for job-specific customization and LaTeX output
"""
import os
import json
import requests
from typing import Dict, Any
from datetime import datetime

class CoverLetterGenerator:
    """Generate personalized cover letters for specific job applications"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")  # This is actually the NVIDIA API key
        self.base_url = "https://integrate.api.nvidia.com/v1"
        
        if not self.api_key:
            raise ValueError("NVIDIA API key not found in environment variables")
        
    def generate_cover_letter(self, job_info: Dict[str, Any], user_profile: Dict[str, Any]) -> str:
        """Generate a personalized cover letter based on job info and user profile"""
        
        prompt = f"""
        Write a professional, compelling cover letter for the following job application.
        
        Job Information:
        - Position: {job_info.get('position', 'N/A')}
        - Company: {job_info.get('company', 'N/A')}
        - Job Description: {job_info.get('description', 'N/A')}
        - Required Skills: {job_info.get('required_skills', [])}
        
        Applicant Profile:
        - Name: {user_profile.get('name', 'N/A')}
        - Current Role: {user_profile.get('current_role', 'N/A')}
        - Key Skills: {user_profile.get('skills', [])}
        - Notable Achievements: {user_profile.get('achievements', [])}
        - Years of Experience: {user_profile.get('experience_years', 'N/A')}
        
        Guidelines:
        1. Keep it concise (3-4 paragraphs)
        2. Show enthusiasm for the specific role and company
        3. Highlight relevant experience and skills
        4. Include specific examples that demonstrate value
        5. End with a strong call to action
        6. Use professional but personable tone
        7. Avoid generic phrases
        
        Format as a standard business letter with proper addressing.
        """
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "nvidia/llama-3.1-nemotron-70b-instruct",
            "messages": [
                {"role": "system", "content": "You are an expert career counselor and professional writer specializing in compelling cover letters that get interviews."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"API request failed: {response.status_code} - {response.text}")
            
            response_data = response.json()
            return response_data['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            raise Exception(f"Cover letter generation failed: {str(e)}")
    
    def generate_latex(self, cover_letter_text: str, job_info: Dict[str, Any], user_profile: Dict[str, Any], output_path: str) -> str:
        """Generate a LaTeX file from cover letter text"""
        
        latex_content = self._create_latex_template(cover_letter_text, job_info, user_profile)
        
        # Write LaTeX content to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        return output_path
    
    def _create_latex_template(self, cover_letter_text: str, job_info: Dict[str, Any], user_profile: Dict[str, Any]) -> str:
        """Create a professional LaTeX cover letter template"""
        
        # Clean and format the cover letter text
        paragraphs = [p.strip() for p in cover_letter_text.split('\n\n') if p.strip()]
        
        latex_template = r"""\documentclass[letterpaper,11pt]{article}

\usepackage[empty]{fullpage}
\usepackage{geometry}
\usepackage[hidelinks]{hyperref}
\usepackage{fontawesome5}
\usepackage{setspace}
\usepackage{parskip}

% Adjust margins
\geometry{
    top=1in,
    bottom=1in,
    left=1in,
    right=1in
}

% Remove page numbers
\pagestyle{empty}

% Set line spacing
\onehalfspacing

\begin{document}

% Header with personal information
\begin{flushleft}
\textbf{\large """ + self._escape_latex(user_profile.get('name', os.getenv('USER_NAME', 'Your Name'))) + r"""} \\
""" + self._escape_latex(user_profile.get('email', os.getenv('USER_EMAIL', 'your.email@example.com'))) + r""" \\
""" + self._escape_latex(user_profile.get('phone', os.getenv('USER_PHONE', '+1234567890'))) + r""" \\
""" + self._escape_latex(user_profile.get('linkedin', os.getenv('USER_LINKEDIN', ''))) + r"""
\end{flushleft}

\vspace{0.5in}

% Date
""" + datetime.now().strftime('%B %d, %Y') + r"""

\vspace{0.25in}

% Recipient information
"""
        
        if job_info.get('company'):
            latex_template += r"""Hiring Manager \\
""" + self._escape_latex(job_info['company']) + r""" \\
"""
            if job_info.get('company_address'):
                latex_template += self._escape_latex(job_info['company_address']) + r""" \\
"""
        
        latex_template += r"""
\vspace{0.25in}

% Salutation
Dear Hiring Manager,

\vspace{0.1in}

"""
        
        # Add cover letter paragraphs
        for paragraph in paragraphs:
            # Skip salutation and signature if they're already in the text
            if paragraph.lower().startswith('dear ') or paragraph.lower().startswith('sincerely'):
                continue
            latex_template += self._escape_latex(paragraph) + r"""

"""
        
        latex_template += r"""
\vspace{0.25in}

% Closing
Sincerely,

\vspace{0.5in}

""" + self._escape_latex(user_profile.get('name', os.getenv('USER_NAME', 'Your Name'))) + r"""

\end{document}
"""
        
        return latex_template
    
    def _escape_latex(self, text) -> str:
        """Escape special LaTeX characters"""
        if not text:
            return ""
        
        # Handle lists by joining them first
        if isinstance(text, list):
            text = ', '.join(str(item) for item in text)
        
        # Convert to string if not already
        text = str(text)
        
        # Define the replacements
        replacements = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '^': r'\textasciicircum{}',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '\\': r'\textbackslash{}',
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        return text
    
    def customize_for_company_culture(self, base_cover_letter: str, company_info: Dict[str, Any]) -> str:
        """Further customize cover letter based on company culture and values"""
        
        if not company_info.get('culture') and not company_info.get('values'):
            return base_cover_letter
        
        prompt = f"""
        Enhance this cover letter to better align with the company's culture and values:
        
        Original Cover Letter:
        {base_cover_letter}
        
        Company Culture/Values:
        {company_info.get('culture', '')}
        {company_info.get('values', '')}
        
        Adjust the tone and content to show alignment with their values while maintaining professionalism.
        Keep the same length and structure.
        """
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "nvidia/llama-3.1-nemotron-70b-instruct",
            "messages": [
                {"role": "system", "content": "You are an expert at adapting communication styles to match company cultures."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.6,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"Culture customization failed: {response.status_code}")
                return base_cover_letter
            
            response_data = response.json()
            return response_data['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            print(f"Culture customization failed: {e}")
            return base_cover_letter