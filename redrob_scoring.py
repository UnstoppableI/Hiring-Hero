"""
redrob_scoring.py - JD-aware, fully offline scorer for the Redrob
"Senior AI Engineer - Founding Team" hackathon challenge.

This intentionally does NOT reward raw AI-keyword density. The JD explicitly
warns that "find candidates whose skills section contains the most AI keywords"
is a trap. Instead we reason about what the JD *means*:

  * Reward production experience in retrieval / ranking / search /
    recommendation / embeddings, especially shipped to real users at a
    product company.
  * Reward rigorous evaluation experience (NDCG, MRR, MAP, A/B testing).
  * Treat 5-9 years as a soft sweet spot, not a hard gate.
  * Down-weight the red flags the JD names: pure-research-without-production,
    consulting-only careers, computer-vision/speech/robotics without NLP/IR,
    "LangChain-to-call-OpenAI"-only depth, and non-engineering titles
    (e.g. Marketing Manager) that are merely keyword-stuffed.
  * Apply behavioral availability signals when present (login recency,
    recruiter response rate, active profile) - a perfect-on-paper candidate
    who is unreachable is, for hiring purposes, not available.

Everything here is pure Python (no network, no heavy deps) so it runs inside
the 5-minute / 16GB / CPU / offline reproduce budget.
"""

from typing import Any, Dict, List, Tuple


# --- Signal vocabularies -------------------------------------------------

CORE_IR_ML = [
    "retrieval", "ranking", "learning to rank", "learning-to-rank", "ranker",
    "search", "recommendation", "recommender", "recsys", "embedding",
    "semantic search", "vector search", "hybrid search", "bm25",
    "information retrieval", "nlp", "natural language processing",
    "candidate matching", "matching system",
]

VECTOR_INFRA = [
    "pinecone", "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch",
    "elastic search", "faiss", "vector database", "vector db", "hnsw", "annoy",
    "scann", "vespa",
]

EVALUATION = [
    "ndcg", "mrr", "mean reciprocal", "map@", "precision@", "recall@",
    "a/b test", "ab test", "a/b testing", "offline eval", "online eval",
    "evaluation framework", "eval framework", "offline-to-online",
    "relevance metric", "ranking metric",
]

PRODUCTION = [
    "production", "real users", "deployed", "in production", "at scale",
    "scaled", "shipped", "serving", "latency", "throughput", "live traffic",
    "millions of", "high traffic", "low latency",
]

LLM_DEPTH = [
    "fine-tun", "fine tun", "lora", "qlora", "peft", "sentence-transformers",
    "sentence transformers", "bge", " e5 ", "re-rank", "rerank", "re rank",
    "distillation", "transformer", "cross-encoder", "bi-encoder",
]

NICE_TO_HAVE = [
    "xgboost", "gradient boosting", "distributed systems", "open source",
    "open-source", "hr-tech", "hrtech", "recruiting", "recruitment",
    "marketplace", "inference optimization",
]

PYTHON_SIGNAL = ["python", "pytorch", "tensorflow", "scikit-learn", "sklearn", "pandas", "numpy"]

# --- Red-flag vocabularies ----------------------------------------------

CONSULTING_FIRMS = [
    "tcs", "tata consultancy", "infosys", "wipro", "accenture", "cognizant",
    "capgemini", "hcl", "tech mahindra", "mindtree", "ltimindtree",
    "deloitte", "igate",
]

RESEARCH_ONLY = [
    "research scientist", "research-only", "research only", "academic",
    "postdoc", "post-doc", "research lab", "research fellow", "phd student",
]

NON_ENG_TITLES = [
    "marketing manager", "sales manager", "account manager", "hr manager",
    "human resources", "business development", "operations manager",
    "product marketing", "growth manager", "talent acquisition",
    "recruiter", "content writer", "customer success",
]

CV_SPEECH_ROBOTICS = [
    "computer vision", "image classification", "object detection",
    "segmentation", "speech recognition", "speech-to-text", "robotics",
    "slam", "lidar", "autonomous driving", "ocr",
]

LANGCHAIN_SHALLOW = [
    "langchain", "llamaindex", "called openai", "openai api", "prompt engineering",
    "chatgpt wrapper", "gpt wrapper",
]

ENG_TITLE_HINTS = [
    "engineer", "developer", "scientist", "architect", "ml ", "machine learning",
    "data scien", "software", "backend", "researcher", "programmer",
]


def _count_hits(text: str, vocab: List[str]) -> List[str]:
    """Return the distinct vocabulary terms that appear in text."""
    return [term for term in vocab if term in text]


def _density_score(hits: int, saturate_at: int) -> float:
    """Diminishing-returns score in 0-100 for a count of distinct signals."""
    if hits <= 0:
        return 0.0
    return min(100.0, (hits / saturate_at) * 100.0)


def _gather_text(candidate: Dict[str, Any]) -> str:
    """Combine every textual field we can find into one lowercase blob."""
    raw = candidate.get("raw_data", {}) or {}
    parts: List[str] = []
    for source in (candidate, raw):
        for key in ("name", "title", "current_title", "headline", "resume",
                    "summary", "education", "certifications", "experience",
                    "work_history", "current_company", "company", "companies",
                    "bio", "about", "skills_text"):
            val = source.get(key)
            if isinstance(val, str):
                parts.append(val)
            elif isinstance(val, list):
                parts.append(" ".join(str(v) for v in val))
            elif isinstance(val, dict):
                parts.append(" ".join(str(v) for v in val.values()))
    return " ".join(parts).lower()


def _behavioral_factor(candidate: Dict[str, Any]) -> Tuple[float, List[str]]:
    """
    Multiplier in [0.55, 1.0] from availability signals, if present.
    Returns (factor, notes). Absent signals are treated as neutral.
    """
    raw = candidate.get("raw_data", {}) or {}

    def first(*keys):
        for k in keys:
            for src in (candidate, raw):
                if k in src and src[k] is not None:
                    return src[k]
        return None

    factor = 1.0
    notes: List[str] = []

    login_days = first("last_login_days", "days_since_login", "last_active_days",
                       "days_since_active", "inactive_days")
    if isinstance(login_days, (int, float)):
        if login_days >= 180:
            factor *= 0.7
            notes.append(f"inactive for ~{int(login_days)} days")
        elif login_days >= 90:
            factor *= 0.85
            notes.append(f"low recent activity (~{int(login_days)} days)")

    rate = first("recruiter_response_rate", "response_rate")
    if isinstance(rate, (int, float)):
        r = rate / 100.0 if rate > 1 else rate  # accept 0-1 or 0-100
        if r < 0.1:
            factor *= 0.75
            notes.append(f"very low recruiter response rate ({int(r * 100)}%)")
        elif r < 0.3:
            factor *= 0.9
            notes.append(f"below-average recruiter response rate ({int(r * 100)}%)")

    active = first("profile_active", "is_active", "active")
    if active is False:
        factor *= 0.8
        notes.append("profile marked inactive")

    return max(0.55, factor), notes


def _experience_fit(years: int) -> float:
    """Soft sweet spot 5-9 yrs, peak 6-8; taper, never hard-zero."""
    if years <= 0:
        return 40.0
    if 6 <= years <= 8:
        return 100.0
    if 5 <= years <= 9:
        return 92.0
    if 4 <= years <= 10:
        return 80.0
    if 3 <= years <= 12:
        return 65.0
    if years < 3:
        return 45.0
    return 55.0  # very senior (12+): still possible, slight discount


def score_candidate(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """Return {'total': 0-100, 'components', 'strengths', 'flags', 'recommendation', 'tier'}."""
    text = _gather_text(candidate)
    years = int(candidate.get("experience_years", 0) or 0)

    core_hits = _count_hits(text, CORE_IR_ML)
    infra_hits = _count_hits(text, VECTOR_INFRA)
    eval_hits = _count_hits(text, EVALUATION)
    prod_hits = _count_hits(text, PRODUCTION)
    llm_hits = _count_hits(text, LLM_DEPTH)
    nice_hits = _count_hits(text, NICE_TO_HAVE)
    py_hits = _count_hits(text, PYTHON_SIGNAL)

    components = {
        "domain_relevance": _density_score(len(core_hits), 4),     # IR/ranking/recsys core
        "production_signal": _density_score(len(prod_hits), 3),
        "vector_infra": _density_score(len(infra_hits), 2),
        "evaluation_rigor": _density_score(len(eval_hits), 2),
        "llm_depth": _density_score(len(llm_hits), 3),
        "python_code": _density_score(len(py_hits), 2),
        "experience_fit": _experience_fit(years),
    }

    weights = {
        "domain_relevance": 0.30,
        "production_signal": 0.20,
        "vector_infra": 0.12,
        "evaluation_rigor": 0.13,
        "llm_depth": 0.10,
        "python_code": 0.05,
        "experience_fit": 0.10,
    }

    base = sum(components[k] * weights[k] for k in weights)

    # Nice-to-have bonus (small, capped).
    bonus = min(8.0, len(nice_hits) * 2.0)

    # --- "Read between the lines" gap reasoning -------------------------
    # A candidate who built a recommendation/search/ranking system at a
    # product company is a fit even without trendy buzzwords.
    strengths: List[str] = []
    if core_hits:
        strengths.append("relevant retrieval/ranking/recommendation work")
    if prod_hits:
        strengths.append("production deployment signals")
    if eval_hits:
        strengths.append("ranking-evaluation experience (NDCG/MRR/A-B)")
    if infra_hits:
        strengths.append("vector/search infrastructure experience")
    if llm_hits:
        strengths.append("modern LLM/embedding depth")
    built_system = any(t in text for t in ("recommendation system", "recommender system",
                                            "search engine", "ranking system",
                                            "matching system", "recsys"))
    if built_system and prod_hits:
        bonus += 6.0
        strengths.append("shipped an end-to-end ranking/recommendation system")

    # --- Red flags / penalties -----------------------------------------
    flags: List[str] = []
    penalty = 0.0

    consult_hits = _count_hits(text, CONSULTING_FIRMS)
    product_signal = built_system or len(prod_hits) >= 2
    if consult_hits and not product_signal:
        penalty += 22.0
        flags.append("services/consulting-only background with no product-company signal")

    research_hits = _count_hits(text, RESEARCH_ONLY)
    if research_hits and not prod_hits:
        penalty += 25.0
        flags.append("pure-research profile with no production deployment")

    # Non-engineering title that is merely keyword-stuffed.
    non_eng = _count_hits(text, NON_ENG_TITLES)
    is_engineer = any(h in text for h in ENG_TITLE_HINTS)
    if non_eng and not is_engineer:
        penalty += 35.0
        flags.append("non-engineering role (keyword-stuffed, not an IC engineer)")

    cv_hits = _count_hits(text, CV_SPEECH_ROBOTICS)
    if cv_hits and not core_hits:
        penalty += 18.0
        flags.append("CV/speech/robotics focus without NLP/IR exposure")

    lc_hits = _count_hits(text, LANGCHAIN_SHALLOW)
    shallow_llm = lc_hits and not (eval_hits or infra_hits or built_system) and len(prod_hits) < 2
    if shallow_llm:
        penalty += 15.0
        flags.append("AI experience appears limited to LangChain/OpenAI wrappers")

    # --- Combine, then apply behavioral availability --------------------
    pre_behavior = max(0.0, min(100.0, base + bonus - penalty))
    behavior_factor, behavior_notes = _behavioral_factor(candidate)
    flags.extend(behavior_notes)
    total = round(pre_behavior * behavior_factor, 2)

    if total >= 78:
        recommendation, tier = "Strong Match", "Tier 1"
    elif total >= 60:
        recommendation, tier = "Good Match", "Tier 2"
    elif total >= 42:
        recommendation, tier = "Worth a Look", "Tier 3"
    else:
        recommendation, tier = "Likely Pass", "Tier 4"

    if not strengths:
        strengths.append("general software background, limited role-specific signal")
    if not flags:
        flags.append("no major red flags detected")

    return {
        "total": total,
        "components": {k: round(v, 2) for k, v in components.items()},
        "strengths": strengths,
        "flags": flags,
        "recommendation": recommendation,
        "tier": tier,
    }


def build_analysis(candidate: Dict[str, Any], score: Dict[str, Any]) -> str:
    """Human-readable, fully offline reasoning string for the submission."""
    years = int(candidate.get("experience_years", 0) or 0)
    exp = f"{years} yrs exp" if years else "exp unknown"
    return (
        f"{score['recommendation']} ({score['tier']}, {score['total']}/100, {exp}). "
        f"Strengths: {'; '.join(score['strengths'])}. "
        f"Watch-outs: {'; '.join(score['flags'])}."
    )
