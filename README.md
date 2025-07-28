# AutoApply - Comprehensive Job Application Automation

**NVIDIA API Integration** 🚀

An intelligent system that automates job applications with AI-powered customized resumes and cover letters, designed to work seamlessly with Simplify and other job application tools.

## 🎯 Features

### Core Automation
- **NVIDIA AI-Powered Customization**: Uses NVIDIA's Llama models to tailor resumes and cover letters for each job
- **LaTeX Document Generation**: Creates professional LaTeX files ready for Overleaf compilation
- **Batch Processing**: Process multiple jobs at once from CSV, JSON, or text files
- **Simplify Integration**: Exports data and documents in format ready for Simplify browser extension

### Tracking & Management  
- **Google Sheets Integration**: Comprehensive application tracking with custom fields
- **Application Analytics**: Success rates, response tracking, interview scheduling
- **Document Management**: Organized file structure for resumes, cover letters, and exports
- **Status Monitoring**: Real-time updates on application progress

### Input Flexibility
- **Multiple Input Methods**: Job URLs, pasted text, or bulk file processing
- **Format Support**: CSV, JSON, and plain text job listings
- **Manual Override**: Single job processing with interactive interface

## 🏗️ Architecture

```
AutoApply/
├── agents/
│   ├── job_application_agent.py    # Main agent orchestrator
│   └── __init__.py
├── utils/
│   ├── batch_processor.py          # Batch job processing engine
│   ├── job_text_parser.py          # NVIDIA AI job text extraction  
│   ├── resume_generator.py         # LaTeX resume generation
│   ├── cover_letter_generator.py   # LaTeX cover letter generation
│   ├── sheets_manager.py           # Enhanced Google Sheets tracking
│   ├── form_filler.py              # Web form automation (legacy)
│   ├── logger.py                   # Logging utilities
│   └── __init__.py
├── data/
│   ├── master_resume.json          # Complete resume template
│   ├── user_profile.json           # User profile for cover letters
│   ├── base_resume.json            # Legacy resume template
│   └── jobs_to_apply.json          # Legacy jobs queue
├── output/                         # Generated files
│   ├── resumes/                    # LaTeX resume files
│   ├── cover_letters/              # LaTeX cover letter files
│   ├── simplify_export/            # Simplify-ready data exports
│   └── batch_reports/              # Processing reports
├── apply_to_job.py                 # Single job processor (interactive)
├── batch_apply.py                  # Batch processor (main interface)
├── main.py                         # Legacy entry point
├── requirements_batch.txt          # Updated dependencies
├── .env.example                    # Environment variables template
└── README.md                       # This file
```

## 🛠️ Setup

### 1. Install Dependencies

```bash
pip install -r requirements_batch.txt
```

For Google Sheets integration (optional):
```bash
pip install gspread google-auth
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
# NVIDIA API Key (required)
OPENAI_API_KEY=nvapi-your_nvidia_api_key_here

# Google Sheets API Credentials (optional)
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
GOOGLE_SHEETS_ID=your_google_sheets_id_here

# Browser automation settings (legacy)
HEADLESS_BROWSER=false

# User profile settings
USER_NAME=Your Full Name
USER_EMAIL=your.email@example.com
USER_PHONE=+1234567890
USER_LINKEDIN=https://linkedin.com/in/yourprofile
```

### 3. Google Sheets Setup

1. Create a Google Cloud Project
2. Enable Google Sheets API
3. Create a service account and download credentials JSON
4. Create a new Google Sheet and share it with the service account email
5. Copy the sheet ID from the URL

### 4. Customize Your Profile

Edit `data/master_resume.json` and `data/user_profile.json` with your information.

## 🚀 Usage

### Batch Processing (Recommended)

Process multiple jobs at once:

```bash
# Interactive mode with menu
python batch_apply.py

# Process from file directly  
python batch_apply.py jobs.csv
python batch_apply.py jobs.json
python batch_apply.py jobs.txt
```

#### Sample Job File Formats

**CSV Format** (`jobs.csv`):
```csv
company,position,location,salary_range,remote_ok,description,required_skills
NVIDIA,AI Engineer,Santa Clara CA,$150k-200k,true,We are seeking...,Python PyTorch CUDA
Google,ML Engineer,Mountain View CA,$140k-180k,true,Join our team...,Python TensorFlow GCP
```

**JSON Format** (`jobs.json`):
```json
{
  "jobs": [
    {
      "company": "NVIDIA",
      "position": "AI Software Engineer", 
      "location": "Santa Clara, CA",
      "salary_range": "$150k-200k",
      "remote_ok": true,
      "description": "We are looking for an AI Software Engineer...",
      "required_skills": ["Python", "PyTorch", "CUDA"],
      "job_url": "https://nvidia.wd5.myworkdayjobs.com/..."
    }
  ]
}
```

**Text Format** (`jobs.txt`):
```
Position: AI Software Engineer
Company: NVIDIA
Location: Santa Clara, CA
Salary: $150k-200k
Remote: Yes

Description:
We are looking for an AI Software Engineer to join our team...

Required Skills: Python, PyTorch, CUDA, Machine Learning
Experience Required: 3+ years

---

Position: ML Engineer  
Company: Google
...
```

### Single Job Processing

For individual job postings:

```bash
# Interactive text input
python apply_to_job.py
```

## 📋 Complete Workflow

### 1. Prepare Job Data
- Create a CSV, JSON, or TXT file with job listings
- Or use single job mode for individual applications

### 2. Run Batch Processing
```bash
python batch_apply.py
```

### 3. Generated Output
The system creates:
- `output/resumes/resume_Company_N.tex` - Custom LaTeX resumes
- `output/cover_letters/cover_letter_Company_N.tex` - Custom LaTeX cover letters  
- `output/simplify_export/simplify_export_Company_N.json` - Simplify integration data
- Google Sheets tracking with all job details

### 4. Use with Overleaf
1. Upload `.tex` files to Overleaf
2. Compile to generate professional PDFs
3. Download PDFs for applications

### 5. Apply with Simplify
1. Install Simplify browser extension
2. Use generated PDFs in applications
3. Reference export JSON for job details

### 6. Track Progress
- Monitor applications in Google Sheets
- Update status as you receive responses
- Use analytics to optimize approach

### Programmatic Usage

```python
from utils.batch_processor import BatchJobProcessor

processor = BatchJobProcessor()

# Process jobs from file
results = processor.process_jobs_from_file("jobs.csv")

# Generate sample file
sample_file = processor.create_sample_job_file("json")
```

## 🔧 Key Components

### Resume Generator (`utils/resume_generator.py`)
- Uses GPT-4 to analyze job descriptions
- Customizes resume content to match requirements
- Generates professional DOCX files
- Optimizes for ATS systems

### Cover Letter Generator (`utils/cover_letter_generator.py`)
- Creates personalized cover letters
- Adapts tone to company culture
- Includes specific achievements and skills
- Professional formatting

### Form Filler (`utils/form_filler.py`)
- Selenium-based web automation
- Handles various form types and fields
- Smart field detection and filling
- Error handling and retries

### Sheets Manager (`utils/sheets_manager.py`)
- Google Sheets API integration
- Application tracking and analytics
- Follow-up management
- Data export capabilities

## 📊 Tracking & Analytics

The agent automatically tracks:
- Application dates and statuses
- Response rates and timelines
- Interview scheduling
- Salary ranges and locations
- Follow-up reminders

Access your data through:
- Google Sheets dashboard
- Built-in analytics functions
- CSV exports

## 🎮 NVIDIA Integration

This project leverages the NVIDIA NeMo Agent Toolkit for:
- Performance monitoring and optimization
- Agent workflow orchestration
- GPU acceleration where applicable
- Integration with NVIDIA's AI ecosystem

## ⚙️ Configuration

### Daily Limits
- Default: 10 applications per day
- Configurable in `JobApplicationAgent.__init__()`

### Delays
- 30+ seconds between applications
- Randomized delays to appear human-like

### Browser Settings
- Headless mode by default
- Human-like user agent
- Anti-detection measures

## 🔒 Privacy & Ethics

- No credentials stored in plain text
- Respects website terms of service
- Implements reasonable rate limits
- User review before final submission
- Transparent application tracking

## 🐛 Troubleshooting

### Common Issues

1. **WebDriver Issues**: Ensure ChromeDriver is installed and in PATH
2. **API Limits**: Check OpenAI API quota and billing
3. **Google Sheets Access**: Verify service account permissions
4. **Form Filling Failures**: Website changes may require selector updates

### Debug Mode

Set `HEADLESS_BROWSER=false` to see browser automation in action.

### Logs

Check console output for detailed logs of all operations.

## 🚀 Deployment on NVIDIA GPU Instance

### Docker Deployment

```dockerfile
FROM nvidia/cuda:11.8-runtime-ubuntu20.04

RUN apt-get update && apt-get install -y python3 python3-pip chromium-browser

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . /app
WORKDIR /app

CMD ["python3", "main.py"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: autoapply-agent
spec:
  replicas: 1
  selector:
    matchLabels:
      app: autoapply-agent
  template:
    metadata:
      labels:
        app: autoapply-agent
    spec:
      containers:
      - name: autoapply
        image: autoapply:latest
        resources:
          limits:
            nvidia.com/gpu: 1
```

## 🏆 Hackathon Highlights

- **NVIDIA NeMo Agent Toolkit Integration**: Leverages cutting-edge agent optimization
- **End-to-End Automation**: Complete job application pipeline
- **AI-Powered Customization**: Smart resume and cover letter generation
- **Production Ready**: Robust error handling and monitoring
- **Scalable Architecture**: Modular design for easy extension

## 📝 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Create a GitHub issue
- Check the troubleshooting section
- Review logs for error details

---

**Built for the NVIDIA Agent Toolkit Hackathon 2025** 🏆