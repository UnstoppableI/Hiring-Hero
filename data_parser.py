"""
Data Parsing and Utility Functions
Handles parsing of job descriptions and candidate resumes
"""

import json
from typing import List, Dict, Any, Tuple
import re


class DataParser:
    """Parses and normalizes job and candidate data"""
    
    @staticmethod
    def parse_job_description(job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and normalize job description"""
        return {
            'id': job_data.get('id', ''),
            'title': job_data.get('title', '').strip(),
            'description': job_data.get('description', '').strip(),
            'required_skills': DataParser._extract_skills(job_data.get('description', '')),
            'level': job_data.get('level', 'mid').lower(),
            'salary_range': job_data.get('salary_range', ''),
            'department': job_data.get('department', ''),
            'experience_years': DataParser._extract_years(job_data.get('description', '')),
            'raw_data': job_data
        }
    
    @staticmethod
    def parse_candidate(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and normalize candidate profile"""
        return {
            'id': candidate_data.get('id', ''),
            'name': candidate_data.get('name', '').strip(),
            'email': candidate_data.get('email', ''),
            'resume': candidate_data.get('resume', '').strip(),
            'skills': DataParser._extract_skills(candidate_data.get('resume', '')),
            'experience_years': DataParser._extract_years(candidate_data.get('resume', '')),
            'education': candidate_data.get('education', ''),
            'certifications': candidate_data.get('certifications', ''),
            'career_progression': DataParser._analyze_career_progression(candidate_data.get('resume', '')),
            'summary': candidate_data.get('summary', ''),
            'raw_data': candidate_data
        }
    
    @staticmethod
    def _extract_skills(text: str) -> List[str]:
        """Extract skills from text using keyword matching"""
        common_skills = {
            'python': ['python', 'py'],
            'javascript': ['javascript', 'js', 'node.js', 'nodejs'],
            'typescript': ['typescript', 'ts'],
            'react': ['react', 'reactjs'],
            'vue': ['vue', 'vuejs'],
            'angular': ['angular', 'angularjs'],
            'java': ['java'],
            'csharp': ['c#', 'csharp', '.net'],
            'sql': ['sql', 'mysql', 'postgresql', 'oracle'],
            'aws': ['aws', 'amazon web services'],
            'azure': ['azure', 'microsoft azure'],
            'gcp': ['gcp', 'google cloud', 'bigquery'],
            'docker': ['docker', 'kubernetes', 'k8s'],
            'git': ['git', 'github', 'gitlab'],
            'ci/cd': ['ci/cd', 'cicd', 'jenkins', 'gitlab ci'],
            'machine learning': ['machine learning', 'ml', 'ai', 'artificial intelligence'],
            'data science': ['data science', 'data scientist'],
            'project management': ['project management', 'scrum', 'agile', 'kanban'],
            'communication': ['communication', 'leadership', 'teamwork'],
            'problem solving': ['problem solving', 'analytical'],
        }
        
        text_lower = text.lower()
        found_skills = set()
        
        for skill, keywords in common_skills.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_skills.add(skill)
                    break
        
        return sorted(list(found_skills))
    
    @staticmethod
    def _extract_years(text: str) -> int:
        """Extract years of experience from text"""
        import re
        matches = re.findall(r'(\d+)\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)?', text.lower())
        if matches:
            return max(int(m) for m in matches)
        return 0
    
    @staticmethod
    def _analyze_career_progression(resume_text: str) -> Dict[str, Any]:
        """Analyze career progression and growth signals"""
        text_lower = resume_text.lower()
        
        progression = {
            'has_promotions': any(word in text_lower for word in ['promoted', 'promotion', 'advanced to', 'lead', 'senior', 'principal']),
            'has_skill_growth': any(word in text_lower for word in ['learned', 'mastered', 'developed expertise', 'expanded knowledge']),
            'has_leadership': any(word in text_lower for word in ['led', 'managed', 'directed', 'supervised', 'team lead']),
            'has_certifications': any(word in text_lower for word in ['certified', 'certification', 'certificate', 'credential']),
            'job_stability': DataParser._calculate_job_stability(resume_text),
        }
        
        return progression
    
    @staticmethod
    def _calculate_job_stability(resume_text: str) -> float:
        """Calculate job stability score (0-1)"""
        # Look for patterns of long tenure
        year_pattern = r'(\d{4})\s*-\s*(?:present|(\d{4}))'
        matches = re.findall(year_pattern, resume_text)
        
        if not matches:
            return 0.5
        
        tenures = []
        for match in matches:
            start = int(match[0])
            end = int(match[1]) if match[1] else 2024
            tenure = end - start
            if 0 < tenure < 50:  # Sanity check
                tenures.append(tenure)
        
        if not tenures:
            return 0.5
        
        avg_tenure = sum(tenures) / len(tenures)
        # Normalize to 0-1 scale (5+ years is considered stable)
        return min(1.0, avg_tenure / 5.0)
    
    @staticmethod
    def load_csv_data(file_path: str, data_type: str = 'candidates') -> List[Dict[str, Any]]:
        """Load data from CSV file"""
        import pandas as pd
        df = pd.read_csv(file_path)
        records = df.to_dict('records')
        
        if data_type == 'candidates':
            return [DataParser.parse_candidate(record) for record in records]
        elif data_type == 'jobs':
            return [DataParser.parse_job_description(record) for record in records]
        
        return records
    
    @staticmethod
    def load_json_data(file_path: str, data_type: str = 'candidates') -> List[Dict[str, Any]]:
        """Load data from JSON file"""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        records = data if isinstance(data, list) else data.get('data', [])
        
        if data_type == 'candidates':
            return [DataParser.parse_candidate(record) for record in records]
        elif data_type == 'jobs':
            return [DataParser.parse_job_description(record) for record in records]
        
        return records
