"""
Data Parsing and Utility Functions
Handles parsing of job descriptions and candidate resumes

Supports two candidate input shapes:
  1. "Simple" flat records (id/name/email/resume/...) - legacy CSV format.
  2. Full "Redrob Candidate Profile Schema" records (candidate_id/profile/
     career_history/education/skills/redrob_signals/...) - see
     candidate_schema.json.

Both shapes are normalized to the same internal record format so the rest
of the app (ranking_engine.py, llm_analyzer.py, app_ranking.py) does not
need to know which shape the data originally came from.
"""

import pandas as pd
import json
from typing import List, Dict, Any, Tuple, Iterable, Optional
import re
from datetime import datetime, date


class DataParser:
    """Parses and normalizes job and candidate data"""

    # ------------------------------------------------------------------
    # Job parsing (unchanged)
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Candidate parsing - entry point / dispatcher
    # ------------------------------------------------------------------
    @staticmethod
    def parse_candidate(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and normalize a candidate record.

        Auto-detects whether the record follows the full Redrob candidate
        schema (candidate_schema.json) or the legacy flat format, and
        routes to the appropriate parser. Either way the returned dict has
        the same set of keys so downstream code works unmodified.
        """
        if DataParser._is_schema_candidate(candidate_data):
            return DataParser._parse_schema_candidate(candidate_data)
        return DataParser._parse_simple_candidate(candidate_data)

    @staticmethod
    def _is_schema_candidate(candidate_data: Dict[str, Any]) -> bool:
        """Detect full Redrob schema records vs legacy flat records."""
        if not isinstance(candidate_data, dict):
            return False
        schema_markers = ('candidate_id', 'profile', 'career_history', 'redrob_signals')
        return any(marker in candidate_data for marker in schema_markers)

    # ------------------------------------------------------------------
    # Legacy flat candidate parsing (unchanged behavior)
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_simple_candidate(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'id': candidate_data.get('id', ''),
            'name': candidate_data.get('name', '').strip() if candidate_data.get('name') else '',
            'email': candidate_data.get('email', ''),
            'resume': (candidate_data.get('resume') or '').strip(),
            'skills': DataParser._extract_skills(candidate_data.get('resume', '') or ''),
            'experience_years': DataParser._extract_years(candidate_data.get('resume', '') or ''),
            'education': candidate_data.get('education', ''),
            'certifications': candidate_data.get('certifications', ''),
            'career_progression': DataParser._analyze_career_progression(candidate_data.get('resume', '') or ''),
            'summary': candidate_data.get('summary', ''),
            'raw_data': candidate_data
        }

    # ------------------------------------------------------------------
    # Full Redrob schema candidate parsing
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_schema_candidate(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        profile = candidate_data.get('profile', {}) or {}
        career_history = candidate_data.get('career_history', []) or []
        education_list = candidate_data.get('education', []) or []
        skills_list = candidate_data.get('skills', []) or []
        certifications_list = candidate_data.get('certifications', []) or []
        languages_list = candidate_data.get('languages', []) or []
        redrob_signals = candidate_data.get('redrob_signals', {}) or {}

        # Build a resume-like text blob so keyword-based extraction
        # (_extract_skills / _extract_years) still has something to work
        # with, in addition to the structured skills/years below.
        resume_text = DataParser._build_resume_text(
            profile, career_history, education_list, skills_list, certifications_list
        )

        # Skills: prefer the structured `skills` array (authoritative),
        # then fall back to / augment with keyword extraction from the
        # free-text resume blob so nothing is missed.
        structured_skills = sorted({
            str(s.get('name', '')).strip().lower()
            for s in skills_list
            if s.get('name')
        })
        keyword_skills = DataParser._extract_skills(resume_text)
        all_skills = sorted(set(structured_skills) | set(keyword_skills))

        # Experience years: prefer explicit profile field, fall back to
        # summing career_history durations, then keyword extraction.
        experience_years = profile.get('years_of_experience')
        if experience_years is None:
            total_months = sum(int(ch.get('duration_months', 0) or 0) for ch in career_history)
            experience_years = round(total_months / 12, 1) if total_months else DataParser._extract_years(resume_text)
        try:
            experience_years = int(round(float(experience_years)))
        except (TypeError, ValueError):
            experience_years = DataParser._extract_years(resume_text)

        # Education: flatten into a readable string
        education_str = DataParser._format_education(education_list)

        # Certifications: flatten into a readable string
        certifications_str = '; '.join(
            f"{c.get('name', '')} ({c.get('issuer', '')}, {c.get('year', '')})".strip()
            for c in certifications_list if c.get('name')
        )

        # Career progression: computed from structured career_history /
        # redrob_signals where possible (more reliable than regex on free
        # text), falling back to the original text-based heuristics.
        career_progression = DataParser._analyze_career_progression_structured(
            career_history, resume_text, redrob_signals
        )

        candidate_id = candidate_data.get('candidate_id', '')
        name = profile.get('anonymized_name', '') or ''
        summary = profile.get('summary', '') or profile.get('headline', '') or ''

        return {
            'id': candidate_id,
            'name': name.strip(),
            # The Redrob schema is anonymized and has no email field;
            # downstream code expects the key to exist.
            'email': candidate_data.get('email', ''),
            'resume': resume_text,
            'skills': all_skills,
            'experience_years': experience_years,
            'education': education_str,
            'certifications': certifications_str,
            'career_progression': career_progression,
            'summary': summary,
            'languages': languages_list,
            'redrob_signals': redrob_signals,
            'current_title': profile.get('current_title', ''),
            'current_company': profile.get('current_company', ''),
            'raw_data': candidate_data
        }

    # ------------------------------------------------------------------
    # Helpers for schema candidate parsing
    # ------------------------------------------------------------------
    @staticmethod
    def _build_resume_text(profile, career_history, education_list, skills_list, certifications_list) -> str:
        parts = []

        if profile.get('headline'):
            parts.append(profile['headline'])
        if profile.get('summary'):
            parts.append(profile['summary'])
        if profile.get('current_title') or profile.get('current_company'):
            parts.append(f"{profile.get('current_title', '')} at {profile.get('current_company', '')}")
        if profile.get('years_of_experience') is not None:
            parts.append(f"{profile.get('years_of_experience')} years of experience")

        for ch in career_history:
            start = ch.get('start_date', '') or ''
            end = ch.get('end_date') or 'present'
            line = f"{ch.get('title', '')} at {ch.get('company', '')} ({start} - {end}): {ch.get('description', '')}"
            parts.append(line)

        for ed in education_list:
            line = f"{ed.get('degree', '')} in {ed.get('field_of_study', '')} from {ed.get('institution', '')} ({ed.get('start_year', '')}-{ed.get('end_year', '')})"
            parts.append(line)

        if skills_list:
            skill_names = ', '.join(s.get('name', '') for s in skills_list if s.get('name'))
            parts.append(f"Skills: {skill_names}")

        if certifications_list:
            cert_names = ', '.join(c.get('name', '') for c in certifications_list if c.get('name'))
            parts.append(f"Certifications: {cert_names}")

        return '\n'.join(p for p in parts if p)

    @staticmethod
    def _format_education(education_list) -> str:
        entries = []
        for ed in education_list:
            degree = ed.get('degree', '')
            field = ed.get('field_of_study', '')
            institution = ed.get('institution', '')
            start_year = ed.get('start_year', '')
            end_year = ed.get('end_year', '')
            entry = f"{degree} in {field}, {institution} ({start_year}-{end_year})".strip()
            entries.append(entry)
        return '; '.join(e for e in entries if e.strip(' ,()-'))

    @staticmethod
    def _analyze_career_progression_structured(career_history, resume_text, redrob_signals) -> Dict[str, Any]:
        """Career progression analysis using structured career_history data
        when available, falling back to text heuristics."""
        text_progression = DataParser._analyze_career_progression(resume_text)

        if not career_history:
            return text_progression

        titles = ' '.join(str(ch.get('title', '')) for ch in career_history).lower()
        descriptions = ' '.join(str(ch.get('description', '')) for ch in career_history).lower()
        combined = f"{titles} {descriptions}"

        leadership_keywords = ['lead', 'manager', 'managed', 'director', 'directed', 'supervised', 'head of', 'principal']
        promotion_keywords = ['promoted', 'promotion', 'advanced to', 'senior', 'lead', 'principal', 'staff']
        growth_keywords = ['learned', 'mastered', 'developed expertise', 'expanded knowledge', 'trained', 'upskilled']

        has_leadership = any(k in combined for k in leadership_keywords)
        has_promotions = any(k in combined for k in promotion_keywords) or len(career_history) > 1
        has_skill_growth = any(k in combined for k in growth_keywords) or bool(career_history)
        has_certifications = text_progression.get('has_certifications', False)

        # Job stability from duration_months directly (more accurate than
        # regex over free text).
        durations = [int(ch.get('duration_months', 0) or 0) for ch in career_history if ch.get('duration_months')]
        if durations:
            avg_tenure_years = (sum(durations) / len(durations)) / 12.0
            job_stability = min(1.0, avg_tenure_years / 5.0)
        else:
            job_stability = text_progression.get('job_stability', 0.5)

        return {
            'has_promotions': has_promotions,
            'has_skill_growth': has_skill_growth,
            'has_leadership': has_leadership,
            'has_certifications': has_certifications,
            'job_stability': round(job_stability, 3),
        }

    # ------------------------------------------------------------------
    # Shared text-based extraction helpers (unchanged)
    # ------------------------------------------------------------------
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

        text_lower = (text or '').lower()
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
        matches = re.findall(r'(\d+)\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)?', (text or '').lower())
        if matches:
            return max(int(m) for m in matches)
        return 0

    @staticmethod
    def _analyze_career_progression(resume_text: str) -> Dict[str, Any]:
        """Analyze career progression and growth signals"""
        text_lower = (resume_text or '').lower()

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
        year_pattern = r'(\d{4})\s*-\s*(?:present|(\d{4}))'
        matches = re.findall(year_pattern, resume_text or '')

        if not matches:
            return 0.5

        tenures = []
        current_year = datetime.now().year
        for match in matches:
            start = int(match[0])
            end = int(match[1]) if match[1] else current_year
            tenure = end - start
            if 0 < tenure < 50:  # Sanity check
                tenures.append(tenure)

        if not tenures:
            return 0.5

        avg_tenure = sum(tenures) / len(tenures)
        # Normalize to 0-1 scale (5+ years is considered stable)
        return min(1.0, avg_tenure / 5.0)

    # ------------------------------------------------------------------
    # Loaders
    # ------------------------------------------------------------------
    @staticmethod
    def load_csv_data(source, data_type='candidates'):
        """Load CSV from file path or UploadedFile"""

        df = pd.read_csv(source)

        records = df.to_dict('records')

        if data_type == 'candidates':
            return [DataParser.parse_candidate(record) for record in records]

        elif data_type == 'jobs':
            return [DataParser.parse_job_description(record) for record in records]

        return records

    @staticmethod
    def _extract_records(data: Any) -> List[Dict[str, Any]]:
        """Given an arbitrary parsed JSON payload, find the list of
        candidate/job records, handling several common wrapper shapes."""
        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            for key in ("data", "candidates", "results", "parsed_candidates"):
                if key in data and isinstance(data[key], list):
                    return data[key]
            if "candidate" in data and isinstance(data["candidate"], dict):
                return [data["candidate"]]
            # Looks like a single record (e.g. has candidate_id or id)
            return [data]

        return []

    @staticmethod
    def load_json_data(file_obj, data_type='candidates'):
        """Load data from an uploaded JSON file (single JSON document,
        either a list of records or a wrapped object)."""

        data = json.load(file_obj)
        records = DataParser._extract_records(data)

        if data_type == 'candidates':
            return [DataParser.parse_candidate(record) for record in records]

        elif data_type == 'jobs':
            return [DataParser.parse_job_description(record) for record in records]

        return records

    @staticmethod
    def _iter_jsonl_lines(file_obj) -> Iterable[str]:
        """Yield non-empty lines from a file-like object, decoding bytes
        if necessary. Works with Streamlit's UploadedFile (bytes-based)
        as well as plain text file handles, without loading the whole
        file into memory at once."""
        for raw_line in file_obj:
            if isinstance(raw_line, bytes):
                line = raw_line.decode('utf-8', errors='replace')
            else:
                line = raw_line
            line = line.strip()
            if line:
                yield line

    @staticmethod
    def load_jsonl_data(
        file_obj,
        data_type: str = 'candidates',
        max_records: Optional[int] = None,
        on_error: str = 'skip',
    ) -> List[Dict[str, Any]]:
        """Stream-parse a JSON Lines (.jsonl) file, one record per line.

        Designed for large uploads (hundreds of MB) where loading the
        full file into a single json.load() call would be wasteful: each
        line is parsed and normalized independently, and the file is
        consumed as a stream rather than read fully into memory up
        front.

        Args:
            file_obj: file-like object (e.g. Streamlit UploadedFile) opened
                for reading, supporting line-by-line iteration.
            data_type: 'candidates' or 'jobs'.
            max_records: optional cap on number of records to parse.
            on_error: 'skip' to ignore malformed lines, 'raise' to stop on
                the first error.
        """
        parser_fn = (
            DataParser.parse_candidate if data_type == 'candidates'
            else DataParser.parse_job_description if data_type == 'jobs'
            else (lambda r: r)
        )

        results: List[Dict[str, Any]] = []
        # Ensure we read from the start of the stream.
        try:
            file_obj.seek(0)
        except (AttributeError, OSError):
            pass

        for line_num, line in enumerate(DataParser._iter_jsonl_lines(file_obj), start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                if on_error == 'raise':
                    raise ValueError(f"Invalid JSON on line {line_num}: {e}") from e
                continue

            try:
                results.append(parser_fn(record))
            except Exception as e:
                if on_error == 'raise':
                    raise ValueError(f"Failed to parse record on line {line_num}: {e}") from e
                continue

            if max_records is not None and len(results) >= max_records:
                break

        return results
