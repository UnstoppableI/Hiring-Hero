"""
LLM-Powered Candidate Analyzer
Uses Claude to generate detailed analysis and recommendations
"""

import os
import json
from typing import Dict, Any, List
# from openai import OpenAI
import google.generativeai as genai

class LLMAnalyzer:
    """Analyzes candidates using LLM for detailed insights"""
    
    def _clean_json(self, text: str) -> str:
        text = text.strip()

        if text.startswith("```json"):
            text = text[7:]

        if text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]

        return text.strip()

    def __init__(self, model="gemini-2.5-flash"):
        """Initialize LLM analyzer"""
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel(model)
    
    def generate_candidate_analysis(
        self,
        candidate: Dict[str, Any],
        job: Dict[str, Any],
        score: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate detailed analysis for a candidate"""
        
        prompt = self._build_analysis_prompt(candidate, job, score)
        
        try:
            system_prompt = """
            You are an expert HR analyst.

            Always return only valid JSON.

            Never use markdown.

            Never explain.
            """

            response = self.model.generate_content(
                system_prompt + "\n\n" + prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=500
                )
            )

            analysis_text = response.text

            return {
                'summary': self._extract_summary(analysis_text),
                'strengths': self._extract_strengths(analysis_text),
                'gaps': self._extract_gaps(analysis_text),
                'recommendation': self._extract_recommendation(analysis_text),
                'full_analysis': analysis_text
            }
        except Exception as e:
            print(f"[llm_analyzer] Error generating analysis: {e}")
            return self._generate_fallback_analysis(candidate, job, score)
    
    def _build_analysis_prompt(
        self,
        candidate: Dict[str, Any],
        job: Dict[str, Any],
        score: Dict[str, Any]
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
Total Score: {score['total']}/100
- Semantic Similarity: {score['components']['semantic_similarity']}/100
- Skill Match: {score['components']['skill_match']}/100
- Experience Level: {score['components']['experience_level']}/100
- Career Growth: {score['components']['career_growth']}/100
- Soft Skills: {score['components']['soft_skills']}/100

Please provide:
1. A brief summary (1-2 sentences) of overall fit
2. Top 3 strengths for this role
3. 2-3 potential gaps or areas for development
4. Hiring recommendation (Strong Hire / Good Fit / Consider / Pass)

Return ONLY valid JSON.

Do not use markdown.

Do not wrap the JSON inside ```json.

Output exactly in this format:

{{
  "summary": "...",
  "strengths": [
    "...",
    "...",
    "..."
  ],
  "gaps": [
    "...",
    "..."
  ],
  "recommendation": "Strong Hire"
}}
"""
    
    def _extract_summary(self, text: str) -> str:
        """Extract summary from analysis"""
        try:
            data = json.loads(self._clean_json(text))
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
            data = json.loads(self._clean_json(text))
            strengths = data.get('strengths', [])
            if isinstance(strengths, str):
                return [s.strip() for s in strengths.split(',')]
            return strengths
        except:
            return []
    
    def _extract_gaps(self, text: str) -> List[str]:
        """Extract gaps from analysis"""
        try:
            data = json.loads(self._clean_json(text))
            gaps = data.get('gaps', [])
            if isinstance(gaps, str):
                return [g.strip() for g in gaps.split(',')]
            return gaps
        except:
            return []
    
    def _extract_recommendation(self, text: str) -> str:
        """Extract recommendation from analysis"""
        try:
            data = json.loads(self._clean_json(text))
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
        score: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate analysis using rule-based approach if LLM fails"""
        
        total_score = score['total']
        
        strengths = []
        gaps = []
        
        # Build strengths based on scores
        if score['components']['skill_match'] >= 80:
            strengths.append("Strong technical skill alignment")
        if score['components']['experience_level'] >= 90:
            strengths.append("Extensive relevant experience")
        if score['components']['career_growth'] >= 75:
            strengths.append("Clear career progression and growth")
        
        # Build gaps
        if score['components']['skill_match'] < 60:
            gaps.append("Missing some key technical skills")
        if score['components']['experience_level'] < 50:
            gaps.append("Limited years of relevant experience")
        if score['components']['soft_skills'] < 50:
            gaps.append("Soft skills not clearly demonstrated")
        
        if total_score >= 85:
            recommendation = "Strong Hire"
        elif total_score >= 70:
            recommendation = "Good Fit"
        elif total_score >= 55:
            recommendation = "Consider"
        else:
            recommendation = "Pass"
        
        return {
            'summary': f"Candidate scores {total_score}/100 for this position.",
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
                'score': item['score'],
                'analysis': analysis
            })
        
        return results
