"""
Multi-Factor Ranking Engine
Combines semantic search with multi-factor scoring for comprehensive candidate ranking
"""

from typing import List, Dict, Tuple, Any
import math
from embeddings import EmbeddingsManager
from data_parser import DataParser


class RankingEngine:
    """Ranks candidates based on multiple factors"""
    
    # Scoring weights
    WEIGHTS = {
        'semantic_similarity': 0.35,    # How well resume matches job description
        'skill_match': 0.25,            # Exact skill matches
        'experience_level': 0.15,       # Years of experience match
        'career_growth': 0.15,          # Growth signals and progression
        'soft_skills': 0.10              # Soft skills presence
    }
    
    def __init__(self):
        """Initialize ranking engine"""
        self.embeddings = EmbeddingsManager()
        self.candidates = []
        self.job_description = None
    
    def load_candidates(self, candidates: List[Dict[str, Any]]):
        """Load candidate data"""
        self.candidates = candidates
        print(f"[ranking] Loaded {len(candidates)} candidates")
    
    def load_job(self, job: Dict[str, Any]):
        """Load job description"""
        self.job_description = job
        print(f"[ranking] Loaded job: {job['title']}")
    
    def rank_candidates(self) -> List[Dict[str, Any]]:
        """Rank all candidates for the job"""
        if not self.job_description:
            raise ValueError("No job description loaded")
        if not self.candidates:
            raise ValueError("No candidates loaded")
        
        scores = []
        
        for candidate in self.candidates:
            score = self._calculate_candidate_score(candidate)
            scores.append({
                'candidate': candidate,
                'score': score,
                'components': score['components']
            })
        
        # Sort by total score
        scores.sort(key=lambda x: x['score']['total'], reverse=True)
        
        return scores
    
    def _calculate_candidate_score(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate composite score for a candidate"""
        components = {
            'semantic_similarity': self._score_semantic_similarity(candidate),
            'skill_match': self._score_skill_match(candidate),
            'experience_level': self._score_experience_level(candidate),
            'career_growth': self._score_career_growth(candidate),
            'soft_skills': self._score_soft_skills(candidate)
        }
        
        # Calculate weighted total
        total = sum(
            components[key] * self.WEIGHTS[key]
            for key in components
        )
        
        return {
            'total': round(total, 2),
            'components': {k: round(v, 2) for k, v in components.items()}
        }
    
    def _score_semantic_similarity(self, candidate: Dict[str, Any]) -> float:
        """Score how well candidate's resume semantically matches job (0-100)"""
        job_text = f"{self.job_description['title']} {self.job_description['description']}"
        candidate_text = f"{candidate['name']} {candidate['resume']}"
        
        # For MVP, use simple keyword overlap as proxy for semantic similarity
        job_words = set(job_text.lower().split())
        candidate_words = set(candidate_text.lower().split())
        
        if not job_words:
            return 50
        
        overlap = len(job_words & candidate_words)
        similarity = (overlap / len(job_words)) * 100
        
        return min(100, similarity)
    
    def _score_skill_match(self, candidate: Dict[str, Any]) -> float:
        """Score skill alignment (0-100)"""
        required_skills = set(self.job_description.get('required_skills', []))
        candidate_skills = set(candidate.get('skills', []))
        
        if not required_skills:
            return 50
        
        matched = len(required_skills & candidate_skills)
        score = (matched / len(required_skills)) * 100
        
        # Bonus for additional skills
        extra_skills = len(candidate_skills - required_skills)
        bonus = min(20, extra_skills * 2)
        
        return min(100, score + bonus)
    
    def _score_experience_level(self, candidate: Dict[str, Any]) -> float:
        """Score experience level match (0-100)"""
        required_years = self.job_description.get('experience_years', 0)
        candidate_years = candidate.get('experience_years', 0)
        
        if candidate_years == 0:
            return 30
        
        if required_years == 0:
            return 80
        
        # Calculate ratio
        ratio = candidate_years / required_years
        
        # Score logic: 
        # - Exact match or better = 100
        # - 50% of required = 60
        # - Less than 50% = lower score
        if ratio >= 1.0:
            return 100
        elif ratio >= 0.5:
            return 60 + (ratio - 0.5) * 80
        else:
            return ratio * 100
    
    def _score_career_growth(self, candidate: Dict[str, Any]) -> float:
        """Score career progression signals (0-100)"""
        progression = candidate.get('career_progression', {})
        
        score = 50  # Base score
        
        # Add points for growth indicators
        if progression.get('has_promotions'):
            score += 15
        if progression.get('has_skill_growth'):
            score += 10
        if progression.get('has_leadership'):
            score += 15
        if progression.get('has_certifications'):
            score += 5
        
        # Job stability bonus
        stability = progression.get('job_stability', 0.5)
        score += stability * 10
        
        return min(100, score)
    
    def _score_soft_skills(self, candidate: Dict[str, Any]) -> float:
        """Score soft skills presence (0-100)"""
        resume = candidate.get('resume', '').lower()
        
        soft_skills_keywords = {
            'communication': ['communication', 'articulate', 'presenter', 'speaking'],
            'leadership': ['led', 'leadership', 'mentored', 'managed'],
            'teamwork': ['team', 'collaborated', 'cooperation', 'cooperative'],
            'problem_solving': ['problem solving', 'analytical', 'analytical thinking'],
            'adaptability': ['adaptable', 'flexible', 'quickly learned', 'fast learner']
        }
        
        found_count = 0
        for category, keywords in soft_skills_keywords.items():
            for keyword in keywords:
                if keyword in resume:
                    found_count += 1
                    break
        
        return (found_count / len(soft_skills_keywords)) * 100
    
    def get_tier_classification(self, score: float) -> str:
        """Classify candidate into tier based on score"""
        if score >= 85:
            return "Tier 1 - Strong Match"
        elif score >= 70:
            return "Tier 2 - Good Match"
        elif score >= 55:
            return "Tier 3 - Moderate Match"
        else:
            return "Tier 4 - Weak Match"
