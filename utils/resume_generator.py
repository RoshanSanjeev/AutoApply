"""
Resume Generator using NVIDIA AI for job-specific customization and LaTeX output
"""
import os
import json
import requests
from typing import Dict, List, Any
from datetime import datetime

class ResumeGenerator:
    """Generate and customize resumes for specific job applications"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")  # This is actually the NVIDIA API key
        self.base_url = "https://integrate.api.nvidia.com/v1"
        
        if not self.api_key:
            raise ValueError("NVIDIA API key not found in environment variables")
        
    def customize_resume(self, base_resume: Dict[str, Any], job_description: str) -> Dict[str, Any]:
        """Customize resume content based on job description"""
        
        prompt = f"""
        Given this base resume data and job description, customize the resume to better match the job requirements.
        Focus on:
        1. Highlighting relevant skills and experience
        2. Reordering sections based on importance
        3. Tailoring bullet points to match job keywords
        4. Optimizing the summary/objective
        
        Base Resume:
        {json.dumps(base_resume, indent=2)}
        
        Job Description:
        {job_description}
        
        Return the customized resume in the same JSON format, ensuring all important keywords from the job description are naturally incorporated.
        Return only valid JSON, no additional text.
        """
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "nvidia/llama-3.1-nemotron-70b-instruct",
            "messages": [
                {"role": "system", "content": "You are an expert resume writer who specializes in ATS optimization and job matching. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"API request failed: {response.status_code}")
                return base_resume
            
            response_data = response.json()
            content = response_data['choices'][0]['message']['content'].strip()
            
            # Clean and parse JSON
            content = content.replace('```json', '').replace('```', '').strip()
            customized_resume = json.loads(content)
            return customized_resume
            
        except Exception as e:
            print(f"Resume customization failed: {e}")
            return base_resume
    
    def generate_latex(self, resume_data: Dict[str, Any], output_path: str) -> str:
        """Generate a LaTeX file from resume data"""
        
        latex_content = self._create_latex_template(resume_data)
        
        # Write LaTeX content to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        return output_path
    
    def _create_latex_template(self, resume_data: Dict[str, Any]) -> str:
        """Create a professional LaTeX resume template"""
        
        latex_template = r"""\documentclass[letterpaper,11pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\usepackage{fontawesome5}
\input{glyphtounicode}

%----------FONT OPTIONS----------
% sans-serif
% \usepackage[sfdefault]{FiraSans}
% \usepackage[sfdefault]{roboto}
% \usepackage[sfdefault]{noto-sans}
% \usepackage[default]{sourcesanspro}

% serif
% \usepackage{CormorantGaramond}
% \usepackage{charter}

\pagestyle{fancy}
\fancyhf{} % clear all header and footer fields
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

% Adjust margins
\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}

\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

% Sections formatting
\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

% Ensure that generate pdf is machine readable/ATS parsable
\pdfgentounicode=1

%-------------------------
% Custom commands
\newcommand{\resumeItem}[1]{
  \item\small{
    {#1 \vspace{-2pt}}
  }
}

\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubSubheading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \textit{\small#1} & \textit{\small #2} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeProjectHeading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \small#1 & #2 \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubItem}[1]{\resumeItem{#1}\vspace{-4pt}}

\renewcommand\labelitemii{$\vcenter{\hbox{\tiny$\bullet$}}$}

\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}

%-------------------------------------------
%%%%%%  RESUME STARTS HERE  %%%%%%%%%%%%%%%%%%%%%%%%%%%%

\begin{document}

%----------HEADING----------
\begin{center}
    \textbf{\Huge \scshape """ + self._escape_latex(resume_data.get('name', 'Your Name')) + r"""} \\ \vspace{1pt}
    \small """ + self._escape_latex(resume_data.get('phone', '')) + r""" $|$ \href{mailto:""" + resume_data.get('email', '') + r"""}{""" + self._escape_latex(resume_data.get('email', '')) + r"""} $|$ 
    \href{""" + resume_data.get('linkedin', '') + r"""}{""" + self._escape_latex(resume_data.get('linkedin', '')) + r"""}
\end{center}

"""

        # Professional Summary
        if resume_data.get('summary'):
            latex_template += r"""
%-----------PROFESSIONAL SUMMARY-----------
\section{Professional Summary}
\small{""" + self._escape_latex(resume_data['summary']) + r"""}

"""

        # Skills
        if resume_data.get('skills'):
            skills_str = ', '.join(resume_data['skills'])
            latex_template += r"""
%-----------TECHNICAL SKILLS-----------
\section{Technical Skills}
\begin{itemize}[leftmargin=0.15in, label={}]
    \small{\item{
     \textbf{Technologies}{: """ + self._escape_latex(skills_str) + r"""} \\
    }}
\end{itemize}

"""

        # Experience
        if resume_data.get('experience'):
            latex_template += r"""
%-----------EXPERIENCE-----------
\section{Experience}
\resumeSubHeadingListStart
"""
            for exp in resume_data['experience']:
                latex_template += r"""
    \resumeSubheading
      {""" + self._escape_latex(exp.get('position', '')) + r"""}{""" + self._escape_latex(exp.get('duration', '')) + r"""}
      {""" + self._escape_latex(exp.get('company', '')) + r"""}{""" + self._escape_latex(exp.get('location', '')) + r"""}
      \resumeItemListStart
"""
                for responsibility in exp.get('responsibilities', []):
                    latex_template += r"""        \resumeItem{""" + self._escape_latex(responsibility) + r"""}
"""
                latex_template += r"""      \resumeItemListEnd
"""
            
            latex_template += r"""\resumeSubHeadingListEnd

"""

        # Education
        if resume_data.get('education'):
            latex_template += r"""
%-----------EDUCATION-----------
\section{Education}
\resumeSubHeadingListStart
"""
            for edu in resume_data['education']:
                latex_template += r"""    \resumeSubheading
      {""" + self._escape_latex(edu.get('institution', '')) + r"""}{""" + self._escape_latex(edu.get('location', '')) + r"""}
      {""" + self._escape_latex(edu.get('degree', '')) + r"""}{""" + self._escape_latex(edu.get('year', '')) + r"""}
"""
            
            latex_template += r"""\resumeSubHeadingListEnd

"""

        # Projects (if available)
        if resume_data.get('projects'):
            latex_template += r"""
%-----------PROJECTS-----------
\section{Projects}
\resumeSubHeadingListStart
"""
            for project in resume_data['projects']:
                latex_template += r"""    \resumeProjectHeading
          {\textbf{""" + self._escape_latex(project.get('name', '')) + r"""} $|$ \emph{""" + self._escape_latex(project.get('technologies', '')) + r"""}}{""" + self._escape_latex(project.get('date', '')) + r"""}
          \resumeItemListStart
"""
                for detail in project.get('details', []):
                    latex_template += r"""            \resumeItem{""" + self._escape_latex(detail) + r"""}
"""
                latex_template += r"""          \resumeItemListEnd
"""
            
            latex_template += r"""\resumeSubHeadingListEnd

"""

        latex_template += r"""
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
    
    def load_base_resume(self, file_path: str) -> Dict[str, Any]:
        """Load base resume template from JSON file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return a default template if file doesn't exist
            return {
                "name": os.getenv("USER_NAME", "Your Name"),
                "email": os.getenv("USER_EMAIL", "your.email@example.com"),
                "phone": os.getenv("USER_PHONE", "+1234567890"),
                "linkedin": os.getenv("USER_LINKEDIN", "https://linkedin.com/in/yourprofile"),
                "summary": "Experienced professional with a strong background in technology and innovation.",
                "skills": ["Python", "Machine Learning", "Data Analysis", "Project Management"],
                "experience": [
                    {
                        "position": "Software Engineer",
                        "company": "Tech Company",
                        "duration": "2020-Present",
                        "responsibilities": [
                            "Developed and maintained software applications",
                            "Collaborated with cross-functional teams",
                            "Implemented best practices for code quality"
                        ]
                    }
                ],
                "education": [
                    {
                        "degree": "Bachelor of Science in Computer Science",
                        "institution": "University Name",
                        "year": "2020"
                    }
                ]
            }