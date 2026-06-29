"""
rank.py - Offline candidate ranking for reproducible submissions.

Single command:
    python rank.py --candidates ./candidates.jsonl --out ./submission.csv

Runs end-to-end on CPU, no network access required. Reads candidates from a
JSONL file (one JSON object per line), scores them with the JD-aware Redrob
scorer (which reasons about what the JD *means* rather than counting AI
keywords), and writes submission.csv with columns:
Rank, Candidate_ID, Total Score, LLM Analysis.
"""

import argparse
import csv
import json
import os
import sys
from typing import Any, Dict, List

from data_parser import DataParser
from redrob_scoring import score_candidate, build_analysis


# The target role for this challenge: Redrob AI "Senior AI Engineer - Founding
# Team". Baked in so the single reproduce command works standalone and offline.
# The scorer in redrob_scoring.py encodes the meaning of this JD; the text is
# kept here for reference and for any downstream semantic use.
DEFAULT_JOB: Dict[str, Any] = {
    "id": "redrob-senior-ai-engineer",
    "title": "Senior AI Engineer - Founding Team (Redrob AI)",
    "description": (
        "Own the intelligence layer of an AI-native talent platform: the "
        "ranking, retrieval and matching systems that decide what recruiters "
        "see. Must have production experience with embeddings-based retrieval "
        "(sentence-transformers, BGE, E5, OpenAI embeddings) deployed to real "
        "users, vector/hybrid search infrastructure (Pinecone, Weaviate, "
        "Qdrant, Milvus, OpenSearch, Elasticsearch, FAISS), strong Python, and "
        "hands-on ranking evaluation (NDCG, MRR, MAP, offline-to-online "
        "correlation, A/B testing). Nice to have: LLM fine-tuning (LoRA, "
        "QLoRA, PEFT), learning-to-rank (XGBoost or neural), HR-tech or "
        "marketplace experience, distributed systems, open-source work. "
        "Ideal: 6-8 years total, 4-5 in applied ML at product companies, "
        "having shipped an end-to-end ranking/search/recommendation system at "
        "scale. Not a fit: pure-research-without-production, consulting-only "
        "careers, computer-vision/speech/robotics without NLP/IR, AI "
        "experience limited to LangChain/OpenAI wrappers, title-chasers, and "
        "candidates who are inactive or unresponsive to recruiters."
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
    args = parser.parse_args()

    if not os.path.exists(args.candidates):
        print(f"[rank] Candidates file not found: {args.candidates}")
        return 1

    candidates = load_candidates_jsonl(args.candidates)
    if not candidates:
        print("[rank] No valid candidates found; writing empty submission.")

    # Score every candidate against the Redrob JD, then sort by total desc.
    scored: List[Dict[str, Any]] = []
    for candidate in candidates:
        score = score_candidate(candidate)
        scored.append({"candidate": candidate, "score": score})
    scored.sort(key=lambda x: x["score"]["total"], reverse=True)

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Rank", "Candidate_ID", "Total Score", "LLM Analysis"])
        for rank, item in enumerate(scored, start=1):
            candidate = item["candidate"]
            score = item["score"]
            candidate_id = candidate.get("id") or candidate.get("name", f"candidate_{rank}")
            analysis = build_analysis(candidate, score)
            writer.writerow([rank, candidate_id, score["total"], analysis])

    print(f"[rank] Wrote {len(scored)} ranked candidates to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
