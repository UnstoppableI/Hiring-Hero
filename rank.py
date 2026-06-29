"""
rank.py - Offline candidate ranking for reproducible submissions.

Single command:
    python rank.py --candidates ./candidates.jsonl --out ./submission.csv

Runs end-to-end on CPU, no network access required. Reads candidates from a
JSONL file (one JSON object per line), scores them with the multi-factor
RankingEngine, generates a rule-based analysis for each, and writes
submission.csv with columns: Rank, Candidate_ID, Total Score, LLM Analysis.
"""

import argparse
import csv
import json
import os
import sys
from typing import Any, Dict, List

from data_parser import DataParser
from ranking_engine import RankingEngine


# Default job target used when no --job file is supplied, so the single
# reproduce command works standalone and offline. Derived from the Redrob AI
# "Senior AI Engineer — Founding Team" job description. Override with
# --job <path-to-json>.
DEFAULT_JOB: Dict[str, Any] = {
    "id": "redrob-senior-ai-engineer",
    "title": "Senior AI Engineer - Founding Team",
    "description": (
        "Redrob AI, a Series A AI-native talent intelligence platform, is hiring a "
        "Senior AI Engineer to own the intelligence layer of the product: the ranking, "
        "retrieval, and matching systems that power candidate-JD matching at scale. "
        "5 to 9 years of experience. We need deep technical depth in modern ML systems "
        "combined with a scrappy product-engineering, ship-fast attitude. "
        "Must have: production experience with embeddings-based retrieval systems "
        "(sentence-transformers, OpenAI embeddings, BGE, E5) deployed to real users, "
        "handling embedding drift, index refresh, and retrieval-quality regression. "
        "Production experience with vector databases and hybrid search infrastructure "
        "(Pinecone, Weaviate, Qdrant, Milvus, OpenSearch, Elasticsearch, FAISS). "
        "Strong Python and high code quality. Hands-on experience designing evaluation "
        "frameworks for ranking systems: NDCG, MRR, MAP, offline-to-online correlation, "
        "and A/B test interpretation. "
        "Nice to have: LLM fine-tuning (LoRA, QLoRA, PEFT), learning-to-rank models "
        "(XGBoost-based or neural), HR-tech or recruiting tech or marketplace products, "
        "distributed systems, large-scale inference optimization, and open-source "
        "contributions in AI/ML. "
        "Strong communication, leadership, mentoring, and problem solving are valued, "
        "as the engineer will help grow the team and drive long-term architecture."
    ),
    "level": "senior",
}


def load_candidates_jsonl(path: str) -> List[Dict[str, Any]]:
    """Load and parse candidates from a JSONL file (one JSON object per line)."""
    records: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"[rank] Skipping malformed JSON on line {line_no}: {e}")
                continue
            records.append(DataParser.parse_candidate(raw))
    return records


def load_job(path: str) -> Dict[str, Any]:
    """Load and parse a job description from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        data = data[0]
    return DataParser.parse_job_description(data)


def build_analysis(candidate: Dict[str, Any], score: Dict[str, Any]) -> str:
    """Rule-based, fully offline candidate analysis (no LLM/network)."""
    components = score["components"]
    total = score["total"]

    strengths: List[str] = []
    if components["skill_match"] >= 80:
        strengths.append("strong technical skill alignment")
    if components["experience_level"] >= 90:
        strengths.append("extensive relevant experience")
    if components["career_growth"] >= 75:
        strengths.append("clear career progression")
    if components["semantic_similarity"] >= 70:
        strengths.append("resume closely matches the role")
    if components["soft_skills"] >= 60:
        strengths.append("demonstrated soft skills")
    if not strengths:
        strengths.append("meets baseline requirements")

    gaps: List[str] = []
    if components["skill_match"] < 60:
        gaps.append("missing some key technical skills")
    if components["experience_level"] < 50:
        gaps.append("limited years of relevant experience")
    if components["soft_skills"] < 50:
        gaps.append("soft skills not clearly demonstrated")
    if components["semantic_similarity"] < 50:
        gaps.append("resume weakly aligned with role")
    if not gaps:
        gaps.append("no major gaps identified")

    if total >= 85:
        recommendation = "Strong Hire"
    elif total >= 70:
        recommendation = "Good Fit"
    elif total >= 55:
        recommendation = "Consider"
    else:
        recommendation = "Pass"

    return (
        f"{recommendation} ({total}/100). "
        f"Strengths: {', '.join(strengths)}. "
        f"Gaps: {', '.join(gaps)}."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Offline candidate ranking -> submission.csv"
    )
    parser.add_argument(
        "--candidates",
        required=True,
        help="Path to candidates.jsonl (one JSON object per line)",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Path to write submission.csv",
    )
    parser.add_argument(
        "--job",
        default=None,
        help="Optional path to a job description JSON file (defaults to built-in role)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.candidates):
        print(f"[rank] Candidates file not found: {args.candidates}")
        return 1

    candidates = load_candidates_jsonl(args.candidates)
    if not candidates:
        print("[rank] No valid candidates found; writing empty submission.")

    job = load_job(args.job) if args.job else DataParser.parse_job_description(DEFAULT_JOB)

    engine = RankingEngine()
    engine.load_candidates(candidates)
    engine.load_job(job)

    ranked = engine.rank_candidates() if candidates else []

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Rank", "Candidate_ID", "Total Score", "LLM Analysis"])
        for rank, item in enumerate(ranked, start=1):
            candidate = item["candidate"]
            score = item["score"]
            candidate_id = candidate.get("id") or candidate.get("name", f"candidate_{rank}")
            analysis = build_analysis(candidate, score)
            writer.writerow([rank, candidate_id, score["total"], analysis])

    print(f"[rank] Wrote {len(ranked)} ranked candidates to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
