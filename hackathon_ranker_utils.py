"""
Hackathon Ranking System Utilities
Helper functions for data loading, validation, and AI skill detection
"""

import json
from typing import Dict, List, Any, Tuple
from datetime import datetime

# Core AI/LLM Skills Library (precomputed, no API calls)
AI_CORE_SKILLS = {
    # LLM/Foundation Models
    "llm": ["llm", "large language model", "gpt", "bert", "transformer", "language model"],
    "gpt": ["gpt", "gpt-4", "gpt-3", "openai"],
    "claude": ["claude", "anthropic"],
    "prompt_engineering": ["prompt engineering", "prompt design", "prompting"],
    
    # ML/Deep Learning
    "tensorflow": ["tensorflow", "tf"],
    "pytorch": ["pytorch", "torch"],
    "keras": ["keras"],
    "neural_networks": ["neural network", "deep learning", "cnn", "rnn", "lstm", "transformer"],
    
    # ML Frameworks & Tools
    "scikit_learn": ["scikit-learn", "sklearn"],
    "xgboost": ["xgboost"],
    "huggingface": ["huggingface", "hugging face"],
    "ollama": ["ollama"],
    "llama": ["llama", "llama2"],
    "mistral": ["mistral"],
    
    # NLP
    "nlp": ["nlp", "natural language processing", "text processing"],
    "embedding": ["embedding", "embeddings", "vector embedding"],
    "rag": ["rag", "retrieval augmented generation"],
    
    # Data/ML Infrastructure
    "mlops": ["mlops", "ml ops"],
    "docker": ["docker", "containerization"],
    "kubernetes": ["kubernetes", "k8s"],
    "airflow": ["airflow"],
    "dbt": ["dbt"],
    
    # Data Science/Analytics
    "pandas": ["pandas", "dataframe"],
    "numpy": ["numpy"],
    "sql": ["sql", "database", "query"],
    "data_analysis": ["data analysis", "analytics", "statistical analysis"],
}

def flatten_skills_dict() -> Dict[str, str]:
    """Flatten AI_CORE_SKILLS into {skill_name: category} mapping"""
    flattened = {}
    for category, aliases in AI_CORE_SKILLS.items():
        for alias in aliases:
            flattened[alias.lower()] = category
    return flattened

def count_ai_skills(candidate: Dict[str, Any]) -> int:
    """Count number of AI core skills in candidate profile"""
    skills_dict = flatten_skills_dict()
    count = 0
    
    if "skills" in candidate:
        for skill in candidate.get("skills", []):
            skill_name = skill.get("name", "").lower()
            if any(ai_skill in skill_name for ai_skill in skills_dict.keys()):
                count += 1
    
    return count

def extract_current_title(candidate: Dict[str, Any]) -> str:
    """Extract and normalize current job title"""
    try:
        return candidate.get("profile", {}).get("current_title", "Unknown").lower()
    except:
        return "unknown"

def extract_experience_years(candidate: Dict[str, Any]) -> float:
    """Extract years of experience from candidate profile"""
    try:
        return float(candidate.get("profile", {}).get("years_of_experience", 0))
    except:
        return 0.0

def calculate_career_progression(candidate: Dict[str, Any]) -> float:
    """
    Detect career progression signal (0.0 to 1.0).
    Higher value = positive progression trajectory.
    """
    try:
        career_history = candidate.get("career_history", [])
        if len(career_history) < 2:
            return 0.5  # Neutral for candidates with little history
        
        # Check for increasing seniority or tenure in tech roles
        recent_roles = career_history[:3]
        tech_keywords = ["engineer", "scientist", "architect", "lead", "senior", "manager"]
        
        tech_count = sum(1 for role in recent_roles 
                        if any(kw in role.get("title", "").lower() for kw in tech_keywords))
        
        progression_score = min(tech_count / len(recent_roles), 1.0)
        return progression_score
    except:
        return 0.5

def calculate_engagement_score(candidate: Dict[str, Any]) -> float:
    """
    Calculate engagement/commitment signal (0.0 to 1.0).
    Based on: recruiter response rate, verified contacts, activity.
    """
    try:
        signals = candidate.get("redrob_signals", {})
        
        engagement = 0.0
        
        # Recruiter response rate (0-1) - 30% weight
        recruiter_response = signals.get("recruiter_response_rate", 0)
        engagement += recruiter_response * 0.3
        
        # Open to work flag - 10% weight
        if signals.get("open_to_work_flag"):
            engagement += 0.1
        
        # Profile completeness (0-100 to 0-1) - 20% weight
        profile_completeness = signals.get("profile_completeness_score", 0) / 100.0
        engagement += profile_completeness * 0.2
        
        # Verified email + phone - 15% weight
        verified = (signals.get("verified_email", False) + 
                   signals.get("verified_phone", False)) / 2.0
        engagement += verified * 0.15
        
        # Interview completion rate - 25% weight
        interview_rate = signals.get("interview_completion_rate", 0)
        engagement += interview_rate * 0.25
        
        return min(engagement, 1.0)
    except:
        return 0.5

def load_candidates_from_json(filepath: str) -> List[Dict[str, Any]]:
    """Load candidates from JSON file"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            # Handle both list and dict format
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'candidates' in data:
                return data['candidates']
            else:
                return []
    except Exception as e:
        print(f"Error loading candidates from {filepath}: {e}")
        return []

def generate_reasoning(candidate: Dict[str, Any], score: float) -> str:
    """Generate a one-line reasoning for the score"""
    try:
        profile = candidate.get("profile", {})
        title = profile.get("current_title", "Unknown")
        experience = profile.get("years_of_experience", 0)
        ai_skills = count_ai_skills(candidate)
        recruiter_response = candidate.get("redrob_signals", {}).get("recruiter_response_rate", 0)
        
        return f"{title} with {experience:.1f} yrs; {ai_skills} AI core skills; response rate {recruiter_response:.2f}."
    except:
        return "Candidate with strong profile match."

def validate_candidate_schema(candidate: Dict[str, Any]) -> bool:
    """Validate that a candidate has required fields"""
    required_fields = ["candidate_id", "profile", "career_history", "skills", "redrob_signals"]
    return all(field in candidate for field in required_fields)
