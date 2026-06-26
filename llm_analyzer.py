"""
LLM-Powered Candidate Analyzer
Uses Claude to generate detailed analysis and recommendations
"""

import os
import json
from typing import Dict, Any, List
from openai import OpenAI


class LLMAnalyzer:
    """Analyzes candidates using LLM for detailed insights"""
    
    def __init__(self, model: str = "gpt-4-turbo-preview"):
        """Initialize LLM analyzer"""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
    
    def generate_candidate_analysis(
        self,
        candidate: Dict[str, Any],
        job: Dict[str, Any],
        ranking_score: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate detailed analysis for a candidate"""
        
        prompt = self._build_analysis_prompt(candidate, job, ranking_score)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert HR analyst specializing in candidate evaluation. Provide concise, actionable insights."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            analysis_text = response.choices[0].message.content
            
            return {
                'summary': self._extract_summary(analysis_text),
                'strengths': self._extract_strengths(analysis_text),
                'gaps': self._extract_gaps(analysis_text),
                'recommendation': self._extract_recommendation(analysis_text),
                'full_analysis': analysis_text
            }
        except Exception as e:
            print(f"[llm_analyzer] Error generating analysis: {e}")
            return self._generate_fallback_analysis(candidate, job, ranking_score)
    
    def _build_analysis_prompt(
        self,
        candidate: Dict[str, Any],
        job: Dict[str, Any],
        ranking_score: Dict[str, Any]
    ) -> str:
        """Build prompt for LLM analysis"""
        
        return f"""
Analyze this candidate for the given job position.

JOB DESCRIPTION:
Title: {job['title']}
Description: {job['description'][:500]}...
Required Skills: {', '.join(job.get('required_skills', []))}
Experience Required: {job.get('experience_years', 0)} years

CANDIDATE PROFILE:
Name: {candidate['name']}
Resume: {candidate['resume'][:800]}...
Skills: {', '.join(candidate.get('skills', []))}
Years of Experience: {candidate.get('experience_years', 0)}

RANKING SCORES:
Total Score: {ranking_score['total']}/100
- Semantic Similarity: {ranking_score['components']['semantic_similarity']}/100
- Skill Match: {ranking_score['components']['skill_match']}/100
- Experience Level: {ranking_score['components']['experience_level']}/100
- Career Growth: {ranking_score['components']['career_growth']}/100
- Soft Skills: {ranking_score['components']['soft_skills']}/100

Please provide:
1. A brief summary (1-2 sentences) of overall fit
2. Top 3 strengths for this role
3. 2-3 potential gaps or areas for development
4. Hiring recommendation (Strong Hire / Good Fit / Consider / Pass)

Format your response as JSON with keys: summary, strengths, gaps, recommendation
"""
    
    def _extract_summary(self, text: str) -> str:
        """Extract summary from analysis"""
        try:
            data = json.loads(text)
            return data.get('summary', 'No summary available')
        except:
            lines = text.split('\n')
            for line in lines:
                if 'summary' in line.lower():
                    return line.replace('summary:', '').strip()
            return text.split('\n')[0]
    
    def _extract_strengths(self, text: str) -> List[str]:
        """Extract strengths from analysis"""
        try:
            data = json.loads(text)
            strengths = data.get('strengths', [])
            if isinstance(strengths, str):
                return [s.strip() for s in strengths.split(',')]
            return strengths
        except:
            return []
    
    def _extract_gaps(self, text: str) -> List[str]:
        """Extract gaps from analysis"""
        try:
            data = json.loads(text)
            gaps = data.get('gaps', [])
            if isinstance(gaps, str):
                return [g.strip() for g in gaps.split(',')]
            return gaps
        except:
            return []
    
    def _extract_recommendation(self, text: str) -> str:
        """Extract recommendation from analysis"""
        try:
            data = json.loads(text)
            return data.get('recommendation', 'Consider')
        except:
            if 'strong hire' in text.lower():
                return 'Strong Hire'
            elif 'good fit' in text.lower():
                return 'Good Fit'
            elif 'pass' in text.lower():
                return 'Pass'
            return 'Consider'
    
    def _generate_fallback_analysis(
        self,
        candidate: Dict[str, Any],
        job: Dict[str, Any],
        ranking_score: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate analysis using rule-based approach if LLM fails"""
        
        score = ranking_score['total']
        
        strengths = []
        gaps = []
        
        # Build strengths based on scores
        if ranking_score['components']['skill_match'] >= 80:
            strengths.append("Strong technical skill alignment")
        if ranking_score['components']['experience_level'] >= 90:
            strengths.append("Extensive relevant experience")
        if ranking_score['components']['career_growth'] >= 75:
            strengths.append("Clear career progression and growth")
        
        # Build gaps
        if ranking_score['components']['skill_match'] < 60:
            gaps.append("Missing some key technical skills")
        if ranking_score['components']['experience_level'] < 50:
            gaps.append("Limited years of relevant experience")
        if ranking_score['components']['soft_skills'] < 50:
            gaps.append("Soft skills not clearly demonstrated")
        
        if score >= 85:
            recommendation = "Strong Hire"
        elif score >= 70:
            recommendation = "Good Fit"
        elif score >= 55:
            recommendation = "Consider"
        else:
            recommendation = "Pass"
        
        return {
            'summary': f"Candidate scores {score}/100 for this position.",
            'strengths': strengths if strengths else ["Meets basic requirements"],
            'gaps': gaps if gaps else ["No major gaps identified"],
            'recommendation': recommendation,
            'full_analysis': f"Based on multi-factor analysis, this candidate receives a {recommendation}."
        }
    
    def batch_analyze(
        self,
        ranked_candidates: List[Dict[str, Any]],
        job: Dict[str, Any],
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """Analyze top N candidates"""
        
        results = []
        
        for i, item in enumerate(ranked_candidates[:top_n]):
            print(f"[llm_analyzer] Analyzing candidate {i+1}/{min(top_n, len(ranked_candidates))}...")
            
            analysis = self.generate_candidate_analysis(
                item['candidate'],
                job,
                item['score']
            )
            
            results.append({
                'candidate': item['candidate'],
                'ranking_score': item['score'],
                'analysis': analysis
            })
        
        return results
