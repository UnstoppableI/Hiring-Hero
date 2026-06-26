# Quick Start Guide - Candidate Ranking System

## 5-Minute Setup

### 1. Prerequisites
- Python 3.8+
- OpenAI API key
- CSV files with job and candidate data (optional - use sample data)

### 2. Installation

```bash
# Navigate to project directory
cd /vercel/share/v0-project

# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Set API Key

```bash
# Option 1: Set as environment variable
export OPENAI_API_KEY="sk-your-api-key-here"

# Option 2: Create .env file
echo "OPENAI_API_KEY=sk-your-api-key-here" > .env
```

### 4. Run Interactive Dashboard

```bash
streamlit run app_ranking.py
```

Then:
1. Open browser to `http://localhost:8501`
2. Click **"Load Demo Data"** button
3. Click **"Run Ranking Engine"**
4. Explore results across the 4 pages

### 5. Run Tests

```bash
python test_ranking_pipeline.py
```

Expected output:
- ✓ Data loading
- ✓ Ranking engine
- ✓ Hackathon export format
- ✓ Top candidate: Raj Kumar (Score: 89.5/100)

---

## Using Your Own Data

### 1. Prepare CSV Files

**jobs.csv:**
```csv
id,title,description,experience_years,department
job_001,Senior Python Developer,"Looking for 5+ years...",5,Engineering
```

**candidates.csv:**
```csv
id,name,email,resume,education,experience_years
cand_001,John Doe,john@email.com,"Python expert with 8 years...",B.S. CS,8
```

### 2. Upload via Dashboard

1. Run: `streamlit run app_ranking.py`
2. Go to "Upload Data" page
3. Upload your CSV files
4. Click "Run Ranking Engine"
5. View results and export

---

## Key Files

| File | Purpose |
|------|---------|
| `app_ranking.py` | Interactive Streamlit dashboard |
| `ranking_engine.py` | Core ranking algorithm |
| `embeddings.py` | Semantic embedding logic |
| `data_parser.py` | CSV parsing and data extraction |
| `test_ranking_pipeline.py` | Full system test |
| `sample_jobs.csv` | Sample job data |
| `sample_candidates.csv` | Sample candidate data |

---

## Output Formats

### Command Line
```bash
python test_ranking_pipeline.py
# Outputs: hackathon_ranking_YYYYMMDD_HHMMSS.json
#          hackathon_ranking_YYYYMMDD_HHMMSS.csv
```

### Dashboard
- View rankings with metrics
- Export JSON or CSV
- Download individual reports

---

## Scoring System

Candidates ranked on 100-point scale:

- **85+:** Tier 1 - Strong Match
- **70-84:** Tier 2 - Good Match
- **55-69:** Tier 3 - Moderate Match
- **<55:** Tier 4 - Weak Match

Score breakdown:
- Semantic Similarity: 20%
- Skill Match: 40%
- Experience: 20%
- Career Growth: 10%
- Soft Skills: 10%

---

## Common Issues

**"API Key not found"**
- Set `OPENAI_API_KEY` environment variable
- Check `.env` file is in project root

**"CSV format error"**
- Ensure required columns are present
- Check CSV isn't using unusual encoding
- Use sample CSVs as template

**"Streamlit not loading"**
- Kill existing processes: `pkill streamlit`
- Run again: `streamlit run app_ranking.py`
- Check port 8501 is available

---

## Next Steps

1. **Try demo data** - Click "Load Demo Data" in dashboard
2. **Explore rankings** - View top candidates with scores
3. **Check analysis** - See detailed breakdown per candidate
4. **Export results** - Download JSON/CSV for integration
5. **Customize** - Modify scoring weights in `ranking_engine.py`

---

## Performance

- **Sample data (8 candidates):** <5 seconds
- **100 candidates:** ~10-15 seconds
- **With LLM analysis:** Add 2-5 seconds per candidate analyzed

---

Need help? Check `HACKATHON_README.md` for detailed documentation.
