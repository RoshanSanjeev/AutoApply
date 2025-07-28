"""
Job Text Parser using NVIDIA API for extracting information from job postings
"""
import os
import json
import re
from typing import Dict, List, Any
import requests
from datetime import datetime

class JobTextParser:
    """Parse job posting text to extract structured information"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")  # This is actually the NVIDIA API key
        self.base_url = "https://integrate.api.nvidia.com/v1"
        
        if not self.api_key:
            raise ValueError("NVIDIA API key not found in environment variables")
    
    def parse_job_text(self, job_text: str) -> Dict[str, Any]:
        """Parse job posting text and extract structured information"""
        
        try:
            # Clean the text
            cleaned_text = self._clean_text(job_text)
            
            # Use NVIDIA API to extract information
            extracted_info = self._extract_with_ai(cleaned_text)
            
            # Post-process and validate
            processed_info = self._post_process(extracted_info, cleaned_text)
            
            return processed_info
            
        except Exception as e:
            return {"error": f"Failed to parse job text: {str(e)}"}
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize the job posting text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might interfere
        text = re.sub(r'[^\w\s\.\,\;\:\-\(\)\$\+\&\@\#\%\/]', '', text)
        return text.strip()
    
    def _extract_with_ai(self, job_text: str) -> Dict[str, Any]:
        """Use NVIDIA AI to extract structured information from job text"""
        
        prompt = f"""
        Extract the following information from this job posting text and return it as valid JSON:

        {{
            "position": "exact job title",
            "company": "company name",
            "location": "location (city, state/country)",
            "remote_ok": true/false,
            "salary_range": "salary range if mentioned, or null",
            "required_skills": ["list", "of", "required", "skills"],
            "preferred_skills": ["list", "of", "preferred", "skills"],
            "experience_years": "number of years required or null",
            "education_requirements": "education requirements or null",
            "description": "brief summary of the role",
            "responsibilities": ["list", "of", "key", "responsibilities"],
            "benefits": ["list", "of", "benefits", "if", "mentioned"],
            "application_deadline": "deadline if mentioned or null",
            "employment_type": "full-time/part-time/contract/internship"
        }}

        Job Posting Text:
        {job_text}

        Return only the JSON object, no additional text.
        """
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "nvidia/llama-3.1-nemotron-70b-instruct",
            "messages": [
                {
                    "role": "system", 
                    "content": "You are an expert at extracting structured information from job postings. Always return valid JSON."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 1500
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
            content = response_data['choices'][0]['message']['content'].strip()
            
            # Try to extract JSON from the response
            try:
                # Remove any markdown formatting
                content = re.sub(r'```json\n?', '', content)
                content = re.sub(r'\n?```', '', content)
                
                extracted_info = json.loads(content)
                return extracted_info
                
            except json.JSONDecodeError:
                # Fallback: try to extract JSON with regex
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    extracted_info = json.loads(json_match.group())
                    return extracted_info
                else:
                    raise Exception("Could not parse JSON from AI response")
                    
        except Exception as e:
            raise Exception(f"AI extraction failed: {str(e)}")
    
    def _post_process(self, extracted_info: Dict[str, Any], original_text: str) -> Dict[str, Any]:
        """Post-process and validate extracted information"""
        
        # Ensure required fields exist
        if not extracted_info.get('position'):
            # Fallback: try to extract position from text
            position_match = re.search(r'(?:position|role|job title|title):\s*([^\n\r]+)', original_text, re.IGNORECASE)
            if position_match:
                extracted_info['position'] = position_match.group(1).strip()
        
        if not extracted_info.get('company'):
            # Fallback: try to extract company from text
            company_patterns = [
                r'(?:company|organization|employer):\s*([^\n\r]+)',
                r'(?:join|work at|employment with)\s+([A-Z][^\n\r,]+?)(?:\s|,|\.)',
                r'^([A-Z][A-Za-z\s&]+?)(?:\s+is|,|\n)'
            ]
            for pattern in company_patterns:
                company_match = re.search(pattern, original_text, re.IGNORECASE)
                if company_match:
                    extracted_info['company'] = company_match.group(1).strip()
                    break
        
        # Clean and validate fields
        extracted_info['position'] = extracted_info.get('position', '').strip()
        extracted_info['company'] = extracted_info.get('company', '').strip()
        extracted_info['location'] = extracted_info.get('location', '').strip()
        
        # Ensure lists are actually lists
        for field in ['required_skills', 'preferred_skills', 'responsibilities', 'benefits']:
            if not isinstance(extracted_info.get(field), list):
                extracted_info[field] = []
        
        # Add metadata
        extracted_info['parsed_at'] = datetime.now().isoformat()
        extracted_info['source'] = 'text_input'
        
        return extracted_info
    
    def validate_extraction(self, extracted_info: Dict[str, Any]) -> bool:
        """Validate that essential information was extracted"""
        required_fields = ['position', 'company']
        
        for field in required_fields:
            if not extracted_info.get(field) or not extracted_info[field].strip():
                return False
        
        return True