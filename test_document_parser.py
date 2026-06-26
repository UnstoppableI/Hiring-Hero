"""
Test script for Job Document Parser
Tests PDF, DOCX, and TXT document parsing
"""

import os
import sys
from io import BytesIO
from job_document_parser import JobDocumentParser
from data_parser import DataParser


def create_sample_text_document():
    """Create a sample text document for testing"""
    content = """
    SENIOR PYTHON DEVELOPER
    
    About the Role:
    We are seeking an experienced Senior Python Developer to join our team. 
    You will work on backend services, API development, and microservices architecture.
    
    Responsibilities:
    - Design and implement scalable Python applications
    - Build RESTful APIs and microservices
    - Collaborate with cross-functional teams
    - Mentor junior developers
    - Implement CI/CD pipelines
    
    Requirements:
    - 5+ years of professional Python experience
    - Strong knowledge of Django or FastAPI
    - Experience with PostgreSQL and Redis
    - Proficiency with Docker and Kubernetes
    - AWS or GCP experience preferred
    - Bachelor's degree in Computer Science or related field
    
    Required Skills:
    Python, Django, FastAPI, PostgreSQL, MySQL, Docker, Kubernetes, AWS, GCP, 
    REST API, Microservices, CI/CD, Git, Linux, Problem Solving
    
    Experience:
    8 years of software development experience
    
    Nice to have:
    - Open source contributions
    - Experience with Machine Learning
    - Published technical articles
    """
    return content.encode('utf-8')


def test_text_parser():
    """Test parsing a text document"""
    print("\n" + "="*60)
    print("TEST 1: Text Document Parser")
    print("="*60)
    
    try:
        content = create_sample_text_document()
        job_data = JobDocumentParser.parse_job_from_document(
            content, 
            'txt', 
            'sample_job.txt'
        )
        
        print("\nExtracted Job Data:")
        print(f"  Title: {job_data['title']}")
        print(f"  Experience Required: {job_data['experience_required']} years")
        print(f"  Skills: {', '.join(job_data['skills'][:10])}")
        print(f"  Description: {job_data['description'][:100]}...")
        print(f"  Requirements: {job_data['requirements'][:100]}...")
        print(f"  Source: {job_data['source']}")
        
        assert job_data['title'], "Title should be extracted"
        assert job_data['experience_required'] >= 5, "Experience should be at least 5 years"
        assert len(job_data['skills']) > 0, "Skills should be extracted"
        assert 'python' in [s.lower() for s in job_data['skills']], "Python should be in skills"
        
        print("\n✅ Text document parsing: PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Text document parsing: FAILED - {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_data_parser_integration():
    """Test DataParser integration with document parsing"""
    print("\n" + "="*60)
    print("TEST 2: DataParser Integration")
    print("="*60)
    
    try:
        content = create_sample_text_document()
        
        # Use DataParser to load job from document
        job_data = DataParser.load_job_from_document(
            content,
            'txt',
            'sample_job.txt'
        )
        
        print("\nParsed Job Data Structure:")
        print(f"  ID: {job_data['id']}")
        print(f"  Title: {job_data['title']}")
        print(f"  Level: {job_data['level']}")
        print(f"  Experience Years: {job_data['experience_years']}")
        print(f"  Required Skills: {job_data['required_skills'][:5]}")
        print(f"  Department: {job_data['department']}")
        
        assert 'title' in job_data, "Job should have title"
        assert 'description' in job_data, "Job should have description"
        assert 'required_skills' in job_data, "Job should have required_skills"
        assert isinstance(job_data['required_skills'], list), "Skills should be a list"
        
        print("\n✅ DataParser integration: PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ DataParser integration: FAILED - {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_skill_extraction():
    """Test skill extraction from various contexts"""
    print("\n" + "="*60)
    print("TEST 3: Skill Extraction")
    print("="*60)
    
    try:
        content = create_sample_text_document()
        job_data = JobDocumentParser.parse_job_from_document(
            content,
            'txt',
            'sample_job.txt'
        )
        
        skills = job_data['skills']
        print(f"\nExtracted skills: {skills}")
        
        expected_skills = ['python', 'django', 'fastapi', 'docker', 'kubernetes', 'aws']
        found_skills = [s.lower() for s in skills]
        
        found_count = sum(1 for skill in expected_skills if skill in found_skills)
        print(f"\nFound {found_count}/{len(expected_skills)} expected skills")
        
        assert found_count >= 4, f"Should find at least 4 of {len(expected_skills)} expected skills"
        
        print("\n✅ Skill extraction: PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Skill extraction: FAILED - {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_experience_extraction():
    """Test experience requirement extraction"""
    print("\n" + "="*60)
    print("TEST 4: Experience Extraction")
    print("="*60)
    
    try:
        content = create_sample_text_document()
        job_data = JobDocumentParser.parse_job_from_document(
            content,
            'txt',
            'sample_job.txt'
        )
        
        experience = job_data['experience_required']
        print(f"\nExtracted experience requirement: {experience} years")
        
        assert experience >= 5, "Should extract 5+ years requirement"
        assert experience <= 10, "Should not over-estimate experience requirement"
        
        print("\n✅ Experience extraction: PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Experience extraction: FAILED - {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("DOCUMENT PARSER TEST SUITE")
    print("="*70)
    
    tests = [
        test_text_parser,
        test_data_parser_integration,
        test_skill_extraction,
        test_experience_extraction,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test failed with exception: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
