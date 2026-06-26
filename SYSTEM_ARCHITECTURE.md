# System Architecture - AI-Powered Candidate Ranking System

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER INTERFACE LAYER                       │
│                                                                 │
│  Streamlit Dashboard (app_ranking.py)                          │
│  ├── Upload Data Page                                          │
│  ├── Ranking Results Dashboard                                 │
│  ├── Candidate Details Viewer                                  │
│  └── Export & Download Module                                  │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ CSV Files (jobs, candidates)
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA PROCESSING LAYER                      │
│                                                                 │
│  DataParser (data_parser.py)                                   │
│  ├── CSV Loading & Validation                                  │
│  ├── Skill Extraction & Normalization                          │
│  ├── Experience Parsing                                        │
│  ├── Soft Skill Detection                                      │
│  └── Data Normalization                                        │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ Structured Data Objects
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      RANKING ENGINE LAYER                       │
│                                                                 │
│  RankingEngine (ranking_engine.py)                             │
│  ├── Multi-Factor Score Calculation                            │
│  │   ├── Semantic Similarity (20%) ──┐                        │
│  │   ├── Skill Match (40%)           │                        │
│  │   ├── Experience Level (20%)      ├─► Combined Score        │
│  │   ├── Career Growth (10%)         │                        │
│  │   └── Soft Skills (10%) ──────────┘                        │
│  ├── Tier Classification (Tier 1-4)                            │
│  └── Candidate Ranking                                         │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ Semantic Similarity Analysis
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EMBEDDINGS & AI LAYER                        │
│                                                                 │
│  EmbeddingsManager (embeddings.py)                             │
│  ├── OpenAI Embeddings API                                     │
│  ├── Vector Generation                                         │
│  ├── FAISS Index Building                                      │
│  ├── Cosine Similarity Search                                  │
│  └── Semantic Matching                                         │
│                                                                 │
│  LLMAnalyzer (llm_analyzer.py)                                 │
│  ├── GPT-4 Deep Analysis                                       │
│  ├── Strength Identification                                   │
│  ├── Gap Analysis                                              │
│  └── Recommendation Generation                                 │
└────────────┬────────────────────────────────────────────────────┘
             │
             │ Ranked Results with Analysis
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OUTPUT & EXPORT LAYER                      │
│                                                                 │
│  Export Formats:                                               │
│  ├── JSON (Full Ranking Report)                                │
│  ├── CSV (Tabular Format)                                      │
│  ├── Dashboard Display                                         │
│  └── API Response Objects                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Modules

### 1. Data Parser Module (`data_parser.py`)

**Purpose:** Extract structured information from unstructured CSV data

**Key Functions:**
```python
load_csv_data(file_path, data_type='jobs'/'candidates')
    ├── Reads CSV file
    ├── Validates required fields
    ├── Extracts and normalizes skills
    ├── Parses experience years
    ├── Detects soft skills
    └── Returns: List[Dict] with normalized data

_extract_skills(text)
    ├── Matches against skill database
    ├── Handles typos and variations
    └── Returns: List[str]

_extract_years(text)
    ├── Regex pattern matching
    ├── Handles various formats
    └── Returns: int (years)
```

**Data Structures:**
```python
Job = {
    'id': str,
    'title': str,
    'description': str,
    'required_skills': List[str],
    'experience_years': int,
    'department': str,
    'salary_range': str (optional)
}

Candidate = {
    'id': str,
    'name': str,
    'email': str,
    'resume': str,
    'skills': List[str],
    'experience_years': int,
    'education': str,
    'soft_skills': List[str]
}
```

---

### 2. Embeddings Manager (`embeddings.py`)

**Purpose:** Generate semantic embeddings and perform similarity search

**Key Functions:**
```python
embed_text(text)
    ├── Calls OpenAI embedding API
    ├── Returns 1536-dimensional vector
    └── Caches results for performance

build_index(candidate_embeddings)
    ├── Initializes FAISS index
    ├── Adds candidate embeddings
    └── Enables fast similarity search

find_similar_candidates(job_embedding, k=10)
    ├── Searches FAISS index
    ├── Returns top-k similar candidates
    └── Calculates cosine similarity scores

get_semantic_similarity(job_embedding, candidate_embedding)
    ├── Computes cosine similarity
    ├── Normalizes to 0-100 scale
    └── Returns: float (0-100)
```

**Technical Details:**
- Model: OpenAI text-embedding-3-small
- Embedding dimensions: 1536
- Index type: FAISS (L2 distance)
- Similarity metric: Cosine similarity
- Response time: ~50ms per embedding

---

### 3. Ranking Engine (`ranking_engine.py`)

**Purpose:** Calculate comprehensive candidate ranking scores

**Scoring Algorithm:**

```
Total Score = (Component Scores Weighted)

Components:
1. Semantic Similarity (20%)
   - Vector embedding cosine similarity
   - Job description vs. candidate resume
   - Range: 0-100

2. Skill Match (40%)
   - Count of matching skills
   - Weighting: required skills > nice-to-have
   - Calculation: (matched / required) * 100
   - Range: 0-100

3. Experience Level (20%)
   - Candidate years vs. job requirement
   - Scaling: capped at requirement + 5 years
   - Formula: (candidate_years / (requirement + buffer)) * 100
   - Range: 0-100

4. Career Growth (10%)
   - Skill progression analysis
   - Role advancement tracking
   - Range: 0-100

5. Soft Skills (10%)
   - Leadership, communication, teamwork signals
   - Text analysis from resume
   - Range: 0-100
```

**Tier Classification:**
```python
Tier 1 - Strong Match: 85-100
  ├── Excellent fit for the role
  ├── Has majority of required skills
  └── Experience level aligned

Tier 2 - Good Match: 70-84
  ├── Good fit with some gaps
  ├── Has core required skills
  └── May need brief onboarding

Tier 3 - Moderate Match: 55-69
  ├── Possible fit with training
  ├── Has some required skills
  └── Significant experience gap or skill gaps

Tier 4 - Weak Match: <55
  ├── Limited fit for the role
  ├── Missing key skills
  └── Requires substantial training
```

---

### 4. LLM Analyzer (`llm_analyzer.py`)

**Purpose:** Generate deep insights using GPT-4

**Analysis Components:**

```python
analyze_candidate(candidate, job)
    ├── Context Building
    │   ├── Job requirements summary
    │   ├── Candidate background
    │   └── Score components
    │
    ├── GPT-4 Analysis
    │   ├── Strength identification
    │   ├── Gap analysis
    │   └── Fit assessment
    │
    └── Returns: {
        'summary': str,
        'strengths': List[str],
        'gaps': List[str],
        'recommendation': str
    }

batch_analyze(ranked_results, job, top_n=10)
    ├── Analyzes top N candidates
    ├── Caches results
    └── Returns: enhanced results with 'analysis' field
```

**Prompt Template:**
```
Analyze this candidate's fit for the job:

JOB:
- Title: {job_title}
- Required Skills: {skills}
- Experience: {years} years
- Description: {description}

CANDIDATE:
- Name: {name}
- Resume: {resume}
- Skills: {skills}
- Experience: {years} years

Provide:
1. Summary of fit (2-3 sentences)
2. Top 3 strengths
3. Top 3 development areas
4. Hiring recommendation
```

---

### 5. Streamlit Dashboard (`app_ranking.py`)

**Architecture:**

```
App Pages:
│
├── Page 1: Upload Data
│   ├── File upload widgets
│   ├── Data preview
│   ├── Sample data loader
│   └── Ranking trigger
│
├── Page 2: Ranking Results
│   ├── Summary metrics (Tiers 1-4)
│   ├── Ranking table
│   ├── Tier distribution
│   └── CSV download
│
├── Page 3: Candidate Details
│   ├── Candidate selector
│   ├── Score breakdown chart
│   ├── Skills comparison
│   ├── LLM analysis (if available)
│   └── Recommendation
│
└── Page 4: Export Report
    ├── Report preview
    ├── JSON download
    └── CSV download
```

**Session State Management:**
```python
st.session_state:
├── ranking_results: List[Dict]  # Final rankings
├── job_data: Dict               # Current job
└── candidates_data: List[Dict]  # Loaded candidates
```

---

## Data Flow

### 1. Data Ingestion
```
CSV Files → DataParser → Normalized Data Objects
```

### 2. Embedding Generation
```
Job Description → EmbeddingsManager → Job Embedding (1536-dim vector)
├─ Candidate 1 Resume → Candidate 1 Embedding
├─ Candidate 2 Resume → Candidate 2 Embedding
└─ ...
```

### 3. Semantic Indexing
```
All Candidate Embeddings → FAISS Index
```

### 4. Ranking Calculation
```
For each Candidate:
├── Semantic Similarity Score
├── Skill Match Score
├── Experience Score
├── Career Growth Score
├── Soft Skills Score
└── Combined Score (Weighted) → Tier Classification
```

### 5. Optional Deep Analysis
```
Top N Candidates → LLMAnalyzer → Detailed Insights
```

### 6. Export & Display
```
Ranked Results → JSON/CSV/Dashboard
```

---

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Note |
|-----------|-----------|------|
| Load CSV | O(n) | n = candidates |
| Generate embedding | O(1) | API call ~50ms |
| Build FAISS index | O(n log n) | Performed once |
| Similarity search | O(log n) | Per candidate |
| Ranking calculation | O(n*m) | n=candidates, m=skills |
| Total for 100 candidates | ~15 seconds | Without LLM |
| With LLM analysis | ~60 seconds | Top 10 candidates |

### Space Complexity

| Component | Space | Note |
|-----------|-------|------|
| Job embedding | 6.1 KB | 1536 floats |
| Candidate embedding | 6.1 KB | Per candidate |
| FAISS index | 100*6.1 KB | For 100 candidates |
| Ranking results | Variable | ~1 KB per result |

---

## Integration Points

### External APIs
- **OpenAI Embeddings API**
  - Model: text-embedding-3-small
  - Rate limit: 3,500 RPM
  - Cost: $0.02 per 1M tokens

- **OpenAI Chat API (LLM Analysis)**
  - Model: gpt-4
  - Rate limit: 200 RPM
  - Cost: $0.03/1K input, $0.06/1K output

### File I/O
- CSV files for input
- JSON/CSV exports
- Session state caching

---

## Error Handling

### Data Validation
```python
├── CSV format validation
├── Required field checking
├── Data type validation
└── Skill database matching
```

### API Errors
```python
├── OpenAI API timeout handling
├── Rate limit retry logic
├── Graceful degradation
└── Error logging
```

### User Input Validation
```python
├── File upload checks
├── Data preview validation
├── Empty result handling
└── User feedback messages
```

---

## Future Extensibility

### Easy to Add
1. **New Scoring Factors** - Add to `RankingEngine.rank_candidates()`
2. **New Skill Extraction** - Extend skill database in `DataParser`
3. **New Export Formats** - Add export functions
4. **New LLM Models** - Update `LLMAnalyzer` provider
5. **New Data Sources** - Add loaders in `DataParser`

### Scalability Options
1. **Distributed Ranking** - Parallelize candidate processing
2. **Caching Layer** - Redis for embedding cache
3. **Batch Processing** - Async job queue
4. **Database Backend** - PostgreSQL for results storage
5. **API Wrapper** - FastAPI/Flask REST endpoints

---

## Testing Strategy

### Unit Tests (in `test_ranking_pipeline.py`)
- ✓ Data loading
- ✓ Skill extraction
- ✓ Experience parsing
- ✓ Ranking engine
- ✓ Export formats

### Integration Tests
- ✓ Full pipeline end-to-end
- ✓ Dashboard interaction
- ✓ File upload/download

### Performance Tests
- ✓ Benchmark with different dataset sizes
- ✓ API response time tracking
- ✓ Memory usage profiling

---

This architecture enables fast, accurate, and scalable candidate ranking with the flexibility to extend and customize the system for specific organizational needs.
