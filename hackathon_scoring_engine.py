"""
Hackathon Scoring Engine
CPU-only, precomputed multi-factor ranking algorithm
Scores: Experience (30%), AI Skills (35%), Title Signal (20%), Engagement (15%)
"""

import json
from typing import Dict, List, Tuple, Any
from datetime import datetime
from hackathon_ranker_utils import (
    count_ai_skills,
    extract_experience_years,
    extract_current_title,
    calculate_career_progression,
    calculate_engagement_score,
    generate_reasoning,
    validate_candidate_schema
)

class ScoringEngine:
    """
    Multi-factor scoring system for ranking candidates.
    All computations are CPU-based with no network access.
    """
    
    # Target job: Senior AI Engineer
    TARGET_JOB_TITLE_KEYWORDS = [
        "engineer", "ml", "ai", "machine learning", "data scientist",
        "ai engineer", "ml engineer", "senior", "lead", "staff"
    ]
    
    # Scoring weights
    WEIGHT_EXPERIENCE = 0.30      # Years of relevant experience
    WEIGHT_AI_SKILLS = 0.35        # Count of AI/LLM skills
    WEIGHT_TITLE_CAREER = 0.20     # Title match + career progression
    WEIGHT_ENGAGEMENT = 0.15       # Engagement signals
    
    # Experience scoring thresholds
    EXP_JUNIOR = 2                 # < 2 years
    EXP_MID = 5                    # 2-5 years
    EXP_SENIOR = 10                # 5-10 years
    
    # AI Skills benchmarks
    AI_SKILLS_LOW = 2
    AI_SKILLS_MID = 5
    AI_SKILLS_HIGH = 8
    
    def __init__(self):
        """Initialize the scoring engine"""
        self.scores = []
    
    def score_experience(self, candidate: Dict[str, Any]) -> float:
        """
        Score candidate experience (0.0 to 1.0)
        Target: Senior level (5+ years)
        """
        years = extract_experience_years(candidate)
        
        if years >= self.EXP_SENIOR:
            # Senior level: 1.0
            return min(years / 15, 1.0)
        elif years >= self.EXP_MID:
            # Mid level: 0.6 to 0.9
            return 0.6 + (years - self.EXP_MID) / (self.EXP_SENIOR - self.EXP_MID) * 0.3
        elif years >= self.EXP_JUNIOR:
            # Junior level: 0.3 to 0.6
            return 0.3 + (years - self.EXP_JUNIOR) / (self.EXP_MID - self.EXP_JUNIOR) * 0.3
        else:
            # Entry level: 0.1
            return 0.1 + years / self.EXP_JUNIOR * 0.2
    
    def score_ai_skills(self, candidate: Dict[str, Any]) -> float:
        """
        Score AI/LLM skills (0.0 to 1.0)
        Target: 8+ AI core skills for Senior AI Engineer
        """
        ai_skill_count = count_ai_skills(candidate)
        
        if ai_skill_count >= self.AI_SKILLS_HIGH:
            return min(ai_skill_count / 10, 1.0)
        elif ai_skill_count >= self.AI_SKILLS_MID:
            return 0.6 + (ai_skill_count - self.AI_SKILLS_MID) / (self.AI_SKILLS_HIGH - self.AI_SKILLS_MID) * 0.4
        elif ai_skill_count >= self.AI_SKILLS_LOW:
            return 0.2 + (ai_skill_count - self.AI_SKILLS_LOW) / (self.AI_SKILLS_MID - self.AI_SKILLS_LOW) * 0.4
        else:
            return 0.1 * min(ai_skill_count / self.AI_SKILLS_LOW, 1.0)
    
    def score_title_and_career(self, candidate: Dict[str, Any]) -> float:
        """
        Score job title match and career progression (0.0 to 1.0)
        Target: Tech-focused roles with upward trajectory
        """
        title = extract_current_title(candidate)
        progression = calculate_career_progression(candidate)
        
        # Check if title matches target keywords
        title_match_score = 0.0
        for keyword in self.TARGET_JOB_TITLE_KEYWORDS:
            if keyword in title:
                if keyword in ["senior", "lead", "staff"]:
                    title_match_score = max(title_match_score, 1.0)
                elif keyword in ["engineer", "ai", "ml", "scientist"]:
                    title_match_score = max(title_match_score, 0.8)
                else:
                    title_match_score = max(title_match_score, 0.5)
        
        # Combine title match and progression
        combined_score = title_match_score * 0.6 + progression * 0.4
        return min(combined_score, 1.0)
    
    def score_engagement(self, candidate: Dict[str, Any]) -> float:
        """
        Score engagement and commitment signals (0.0 to 1.0)
        Uses redrob_signals: recruiter response rate, profile completeness, etc.
        """
        return calculate_engagement_score(candidate)
    
    def compute_total_score(self, candidate: Dict[str, Any]) -> float:
        """
        Compute total score as weighted combination of all factors.
        Returns: float between 0.0 and 1.0
        """
        # Validate candidate
        if not validate_candidate_schema(candidate):
            return 0.0
        
        # Compute individual scores
        exp_score = self.score_experience(candidate)
        ai_score = self.score_ai_skills(candidate)
        title_score = self.score_title_and_career(candidate)
        engagement_score = self.score_engagement(candidate)
        
        # Weighted combination
        total = (
            exp_score * self.WEIGHT_EXPERIENCE +
            ai_score * self.WEIGHT_AI_SKILLS +
            title_score * self.WEIGHT_TITLE_CAREER +
            engagement_score * self.WEIGHT_ENGAGEMENT
        )
        
        return min(total, 1.0)
    
    def rank_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rank all candidates and return sorted list with scores.
        Returns: List of {candidate_id, score, reasoning}
        """
        scored_candidates = []
        
        for candidate in candidates:
            try:
                candidate_id = candidate.get("candidate_id")
                score = self.compute_total_score(candidate)
                reasoning = generate_reasoning(candidate, score)
                
                scored_candidates.append({
                    "candidate_id": candidate_id,
                    "score": score,
                    "reasoning": reasoning,
                    "raw_candidate": candidate  # Keep for potential later use
                })
            except Exception as e:
                print(f"Error scoring candidate: {e}")
                continue
        
        # Sort by score descending
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        
        return scored_candidates
    
    def generate_submission_csv(self, ranked_candidates: List[Dict[str, Any]]) -> str:
        """
        Generate CSV format submission from ranked candidates.
        Format: candidate_id, rank (1-100), score, reasoning
        """
        lines = ["candidate_id,rank,score,reasoning"]
        
        for rank, entry in enumerate(ranked_candidates[:100], 1):
            candidate_id = entry["candidate_id"]
            score = entry["score"]
            reasoning = entry["reasoning"].replace(",", ";")  # Escape commas in reasoning
            
            lines.append(f"{candidate_id},{rank},{score:.4f},{reasoning}")
        
        return "\n".join(lines)
