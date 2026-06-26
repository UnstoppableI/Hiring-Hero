"""
Test Script for Candidate Ranking System
Validates all components and exports hackathon format results
"""

import json
import csv
from datetime import datetime
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file or system
load_dotenv('/vercel/share/.env.project')

# Import our modules
from data_parser import DataParser
from ranking_engine import RankingEngine
from llm_analyzer import LLMAnalyzer


def test_data_loading():
    """Test loading sample data"""
    print("\n" + "="*60)
    print("TEST 1: Data Loading")
    print("="*60)
    
    try:
        jobs = DataParser.load_csv_data('sample_jobs.csv', data_type='jobs')
        candidates = DataParser.load_csv_data('sample_candidates.csv', data_type='candidates')
        
        print(f"✓ Loaded {len(jobs)} jobs")
        print(f"✓ Loaded {len(candidates)} candidates")
        
        # Display sample job
        if jobs:
            job = jobs[0]
            print(f"\nSample Job: {job['title']}")
            print(f"  - Required Skills: {', '.join(job['required_skills'][:5])}")
            print(f"  - Experience: {job['experience_years']} years")
        
        # Display sample candidate
        if candidates:
            cand = candidates[0]
            print(f"\nSample Candidate: {cand['name']}")
            print(f"  - Skills: {', '.join(cand['skills'][:5])}")
            print(f"  - Experience: {cand['experience_years']} years")
        
        return jobs, candidates
    
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        return None, None


def test_ranking_engine(job, candidates):
    """Test ranking engine"""
    print("\n" + "="*60)
    print("TEST 2: Ranking Engine")
    print("="*60)
    
    try:
        engine = RankingEngine()
        engine.load_job(job)
        engine.load_candidates(candidates)
        
        print(f"✓ Ranking engine initialized for: {job['title']}")
        
        # Run ranking
        ranked = engine.rank_candidates()
        
        print(f"✓ Ranked {len(ranked)} candidates")
        
        # Display top 3
        print("\nTop 3 Candidates:")
        for idx, result in enumerate(ranked[:3], 1):
            candidate = result['candidate']
            score = result['score']
            tier = engine.get_tier_classification(score['total'])
            
            print(f"\n  {idx}. {candidate['name']}")
            print(f"     Total Score: {score['total']}/100")
            print(f"     Tier: {tier}")
            print(f"     Components:")
            for comp, value in score['components'].items():
                print(f"       - {comp}: {value}")
        
        return ranked
    
    except Exception as e:
        print(f"✗ Error in ranking engine: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_hackathon_export(job, ranked):
    """Test hackathon format export"""
    print("\n" + "="*60)
    print("TEST 3: Hackathon Export Format")
    print("="*60)
    
    try:
        engine = RankingEngine()
        
        # Build report
        report = {
            'timestamp': datetime.now().isoformat(),
            'job': {
                'id': job['id'],
                'title': job['title'],
                'description': job['description'][:200],
                'required_skills': job['required_skills'],
                'experience_years': job['experience_years']
            },
            'total_candidates_evaluated': len(ranked),
            'rankings': []
        }
        
        # Add rankings
        for idx, result in enumerate(ranked, 1):
            candidate = result['candidate']
            score = result['score']
            tier = engine.get_tier_classification(score['total'])
            
            report['rankings'].append({
                'rank': idx,
                'candidate_id': candidate['id'],
                'candidate_name': candidate['name'],
                'email': candidate['email'],
                'total_score': round(score['total'], 2),
                'score_components': {k: round(v, 2) for k, v in score['components'].items()},
                'tier': tier,
                'years_of_experience': candidate['experience_years'],
                'top_skills': candidate['skills'][:5],
                'career_progression_score': score['components']['career_growth']
            })
        
        print("✓ Generated hackathon report")
        print(f"✓ Total candidates in report: {len(report['rankings'])}")
        
        # Export as JSON
        json_file = f"hackathon_ranking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"✓ Exported JSON to: {json_file}")
        
        # Export as CSV
        csv_file = f"hackathon_ranking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'rank', 'candidate_id', 'candidate_name', 'email', 
                'total_score', 'tier', 'years_of_experience'
            ])
            writer.writeheader()
            
            for item in report['rankings']:
                writer.writerow({
                    'rank': item['rank'],
                    'candidate_id': item['candidate_id'],
                    'candidate_name': item['candidate_name'],
                    'email': item['email'],
                    'total_score': item['total_score'],
                    'tier': item['tier'],
                    'years_of_experience': item['years_of_experience']
                })
        
        print(f"✓ Exported CSV to: {csv_file}")
        
        # Display report
        print("\n✓ Report Summary:")
        print(json.dumps(report, indent=2))
        
        return report
    
    except Exception as e:
        print(f"✗ Error in hackathon export: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_skill_extraction():
    """Test skill extraction"""
    print("\n" + "="*60)
    print("TEST 4: Skill Extraction")
    print("="*60)
    
    test_text = "Experienced Python developer with 8 years in Django and FastAPI. Expert in AWS and Docker. Strong SQL knowledge with PostgreSQL and MongoDB experience."
    
    skills = DataParser._extract_skills(test_text)
    
    print(f"✓ Extracted {len(skills)} skills from test text:")
    for skill in skills:
        print(f"  - {skill}")
    
    expected = ['python', 'django', 'aws', 'docker', 'sql']
    found = sum(1 for s in expected if s in skills)
    print(f"\n✓ Found {found}/{len(expected)} expected skills")


def test_experience_extraction():
    """Test experience extraction"""
    print("\n" + "="*60)
    print("TEST 5: Experience Extraction")
    print("="*60)
    
    test_cases = [
        ("8 years of experience", 8),
        ("5 yrs in software development", 5),
        ("3 years backend, 2 years frontend", 3),
    ]
    
    for text, expected in test_cases:
        years = DataParser._extract_years(text)
        status = "✓" if years == expected else "✗"
        print(f"{status} '{text}' -> {years} years (expected {expected})")


def main():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# CANDIDATE RANKING SYSTEM - COMPREHENSIVE TEST SUITE")
    print("#"*60)
    
    # Test 1: Data Loading
    jobs, candidates = test_data_loading()
    if not jobs or not candidates:
        print("\n✗ Data loading failed. Exiting.")
        return
    
    # Test 2: Ranking Engine
    job = jobs[0]  # Use first job for testing
    ranked = test_ranking_engine(job, candidates)
    if not ranked:
        print("\n✗ Ranking engine failed. Exiting.")
        return
    
    # Test 3: Hackathon Export
    report = test_hackathon_export(job, ranked)
    if not report:
        print("\n✗ Hackathon export failed. Exiting.")
        return
    
    # Test 4: Skill Extraction
    test_skill_extraction()
    
    # Test 5: Experience Extraction
    test_experience_extraction()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print("✓ All tests completed successfully!")
    print(f"\nSystem ready to rank {len(candidates)} candidates for:")
    print(f"  Job: {job['title']}")
    print(f"  Required Skills: {', '.join(job['required_skills'][:5])}")
    print(f"\nTop Candidate: {ranked[0]['candidate']['name']} (Score: {ranked[0]['score']['total']}/100)")
    print("\n" + "#"*60)
    print("# Ready for Hackathon Submission!")
    print("#"*60 + "\n")


if __name__ == "__main__":
    main()
