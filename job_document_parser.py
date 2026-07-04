"""
Job Document Parser
Extracts structured job information from PDF, DOCX, and TXT files
"""

import io
import re
from typing import Dict, Any, Optional, List

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None


class JobDocumentParser:
    """Parse job description documents and extract structured job data"""
    
    @staticmethod
    def parse_pdf(file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            if pdfplumber is not None:
                # Use pdfplumber if available
                with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() or ""
                    return text
            else:
                # Fallback: return a message if pdfplumber is not available
                raise ValueError("pdfplumber is not installed. Install with: pip install pdfplumber")
        except Exception as e:
            raise ValueError(f"Error parsing PDF: {str(e)}")
    
    @staticmethod
    def parse_docx(file_content: bytes) -> str:
        """Extract text from DOCX file"""
        try:
            if DocxDocument is not None:
                doc = DocxDocument(io.BytesIO(file_content))
                text = ""
                for para in doc.paragraphs:
                    text += para.text + "\n"
                return text
            else:
                raise ValueError("python-docx is not installed. Install with: pip install python-docx")
        except Exception as e:
            raise ValueError(f"Error parsing DOCX: {str(e)}")
    
    @staticmethod
    def parse_txt(file_content: bytes) -> str:
        """Extract text from TXT file"""
        try:
            return file_content.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Error parsing TXT: {str(e)}")
    
    @staticmethod
    def extract_text_from_document(file_content: bytes, file_type: str) -> str:
        """
        Extract text from document based on file type
        
        Args:
            file_content: Raw file bytes
            file_type: File extension (pdf, docx, txt)
        
        Returns:
            Extracted text content
        """
        file_type = file_type.lower()
        
        if file_type == 'pdf':
            return JobDocumentParser.parse_pdf(file_content)
        elif file_type in ['docx', 'doc']:
            return JobDocumentParser.parse_docx(file_content)
        elif file_type == 'txt':
            return JobDocumentParser.parse_txt(file_content)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    @staticmethod
    def extract_job_title(text: str) -> str:
        """Extract job title from document text"""
        # Look for common patterns like "Position:", "Role:", "Job Title:", etc.
        patterns = [
            r'(?:Position|Role|Job Title|Title)[\s]*:[\s]*([^\n]+)',
            r'^([A-Za-z\s]{5,50}(?:Developer|Engineer|Manager|Analyst|Specialist|Coordinator|Officer|Executive|Consultant|Lead|Senior|Junior))[\s]*$',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                title = match.group(1).strip() if '(' in str(match.groups()) else match.group(0).strip()
                if title and len(title) > 5 and len(title) < 100:
                    return title
        
        # Fallback: use first line if it looks like a title
        first_line = text.split('\n')[0].strip()
        if len(first_line) > 5 and len(first_line) < 100:
            return first_line
        
        return "Job Position"
    
    @staticmethod
    def extract_required_experience(text: str) -> int:
        """Extract required years of experience from document"""
        # Look for patterns like "5 years", "5+ years", "5-7 years"
        patterns = [
            r'(\d+)\+?\s*(?:to\s*)?(?:\d+)?\s*years?\s*(?:of\s*)?(?:experience|experience)',
            r'experience[\s]*:?[\s]*(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s*(?:in|of)',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    years = int(match.group(1))
                    if 0 <= years <= 50:
                        return years
                except ValueError:
                    continue
        
        return 3  # Default to 3 years if not found
    
    @staticmethod
    def extract_skills(text: str) -> List[str]:
        """Extract technical skills from document"""
        common_skills = [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'php', 'go', 'rust',
            'react', 'angular', 'vue', 'node', 'django', 'flask', 'spring', 'fastapi',
            'sql', 'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch',
            'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'jenkins', 'terraform',
            'git', 'agile', 'scrum', 'jira', 'linux', 'windows', 'macos',
            'machine learning', 'deep learning', 'nlp', 'computer vision', 'tensorflow', 'pytorch',
            'rest api', 'graphql', 'microservices', 'devops', 'ci/cd', 'etl',
            'html', 'css', 'sass', 'less', 'webpack', 'npm', 'yarn', 'maven', 'gradle',
            'excel', 'tableau', 'power bi', 'statistics', 'analytics', 'data analysis'
        ]
        
        text_lower = text.lower()
        found_skills = []
        
        for skill in common_skills:
            # Use word boundaries to match whole skills
            if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                found_skills.append(skill)
        
        return found_skills[:15]  # Return top 15 skills
    
    @staticmethod
    def extract_description(text: str, max_length: int = 500) -> str:
        """Extract job description from document"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Look for description sections
        description_patterns = [
            r'(?:About|Overview|Role|Description|Responsibilities)[:\s]+([^.]+\.[^.]+\.?)',
            r'Job Description[:\s]+([^.]+\.[^.]+\.?)',
        ]
        
        for pattern in description_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                desc = match.group(1).strip()
                if len(desc) > 50:
                    return desc[:max_length]
        
        # Fallback: use first substantial paragraph
        paragraphs = [p.strip() for p in text.split('\n') if len(p.strip()) > 50]
        if paragraphs:
            return paragraphs[0][:max_length]
        
        return "Seeking a talented professional to join our team."
    
    @staticmethod
    def extract_requirements(text: str, max_length: int = 500) -> str:
        """Extract job requirements from document"""
        text = re.sub(r'\s+', ' ', text)
        
        # Look for requirements sections
        requirements_patterns = [
            r'(?:Requirements|Qualifications|Must Haves)[:\s]+([^.]+\.[^.]+\.?)',
            r'Desired[:\s]+([^.]+\.[^.]+\.?)',
        ]
        
        for pattern in requirements_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                reqs = match.group(1).strip()
                if len(reqs) > 50:
                    return reqs[:max_length]
        
        # Fallback: extract bullet points if present
        lines = text.split('\n')
        bullet_points = [l.strip() for l in lines if l.strip().startswith(('-', '•', '*', '·')) and len(l.strip()) > 20]
        if bullet_points:
            return ' '.join(bullet_points[:5])[:max_length]
        
        return "Strong problem-solving skills and ability to work in a team environment."
    
    @staticmethod
    def parse_job_from_document(file_content: bytes, file_type: str, filename: str = "") -> Dict[str, Any]:
        """
        Parse a complete job document and return structured job data
        
        Args:
            file_content: Raw file bytes
            file_type: File extension (pdf, docx, txt)
            filename: Original filename for reference
        
        Returns:
            Job dict with: title, description, requirements, skills, experience_required, source
        """
        # Extract text from document
        text = JobDocumentParser.extract_text_from_document(file_content, file_type)
        
        # Extract structured job information
        job_data = {
            'title': JobDocumentParser.extract_job_title(text),
            'description': JobDocumentParser.extract_description(text),
            'requirements': JobDocumentParser.extract_requirements(text),
            'skills': JobDocumentParser.extract_skills(text),
            'experience_required': JobDocumentParser.extract_required_experience(text),
            'source': f'document: {filename}',
            'source_type': 'document'
        }
        
        return job_data


# Utility function for Streamlit integration
def parse_uploaded_job_document(uploaded_file) -> Dict[str, Any]:
    """
    Parse Streamlit uploaded file and extract job information
    
    Args:
        uploaded_file: Streamlit UploadedFile object
    
    Returns:
        Structured job data dictionary
    """
    try:
        file_content = uploaded_file.read()
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        job_data = JobDocumentParser.parse_job_from_document(
            file_content, 
            file_extension,
            uploaded_file.name
        )
        
        return job_data
    except Exception as e:
        raise ValueError(f"Failed to parse job document: {str(e)}")
