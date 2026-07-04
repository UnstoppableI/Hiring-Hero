"""
AI-Powered Candidate Ranking System
Hackathon Solution for Intelligent Candidate Screening
"""

import streamlit as st
import pandas as pd
import os
from typing import List, Dict, Any
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/vercel/share/.env.project')

from data_parser import DataParser
from ranking_engine import RankingEngine
from llm_analyzer import LLMAnalyzer

# Page Configuration
st.set_page_config(
    page_title="Candidate Ranking System",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styling
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #0068C9;
    text-align: center;
    font-weight: bold;
    margin-bottom: 10px;
}
.sub-header {
    font-size: 1.3rem;
    color: #555;
    text-align: center;
    margin-bottom: 20px;
}
.metric-card {
    background-color: #f0f7ff;
    padding: 15px;
    border-radius: 10px;
    border-left: 4px solid #0068C9;
    margin: 10px 0;
}
.tier1 {
    background-color: #e8f5e9;
    padding: 10px;
    border-left: 4px solid #4caf50;
    border-radius: 5px;
    margin: 5px 0;
}
.tier2 {
    background-color: #fff3e0;
    padding: 10px;
    border-left: 4px solid #ff9800;
    border-radius: 5px;
    margin: 5px 0;
}
.tier3 {
    background-color: #fff8e1;
    padding: 10px;
    border-left: 4px solid #fbc02d;
    border-radius: 5px;
    margin: 5px 0;
}
.tier4 {
    background-color: #ffebee;
    padding: 10px;
    border-left: 4px solid #f44336;
    border-radius: 5px;
    margin: 5px 0;
}
</style>
""", unsafe_allow_html=True)

# Session State Management
if 'ranking_results' not in st.session_state:
    st.session_state.ranking_results = None
if 'job_data' not in st.session_state:
    st.session_state.job_data = None
if 'candidates_data' not in st.session_state:
    st.session_state.candidates_data = None

# Header
st.markdown('<p class="main-header">AI-Powered Candidate Ranking System</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Intelligent Screening & Semantic Matching</p>', unsafe_allow_html=True)
st.divider()

# Auto-load sample data if available
@st.cache_data
def load_sample_data():
    try:
        jobs = DataParser.load_csv_data('sample_jobs.csv', data_type='jobs')
        candidates = DataParser.load_csv_data('sample_candidates.csv', data_type='candidates')
        return jobs, candidates
    except:
        return None, None

# Sidebar Navigation
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
    st.title("Navigation")
    
    page = st.radio(
        "Select Page:",
        ["Upload Data", "Ranking Results", "Candidate Details", "Export Report"],
        key="page_select"
    )

# PAGE 1: UPLOAD DATA
if page == "Upload Data":
    st.header("Upload Job & Candidate Data")
    st.write("Upload CSV files containing job descriptions and candidate profiles")
    
    # Demo Data Button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Load Demo Data", type="secondary", use_container_width=True):
            sample_jobs, sample_candidates = load_sample_data()
            if sample_jobs and sample_candidates:
                st.session_state.job_data = sample_jobs[0]
                st.session_state.candidates_data = sample_candidates
                st.success(f"Loaded demo data: {sample_jobs[0]['title']}")
                st.rerun()
    with col2:
        st.markdown("*Click the button above to load sample job and candidate data for quick testing*")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Job Description")
        st.info("""
        **CSV Format required:**
        - id: Unique job ID
        - title: Job title
        - description: Full job description
        - level: Experience level (junior/mid/senior)
        - department: Department name
        - salary_range: Salary range (optional)
        """)
        
        job_file = st.file_uploader("Upload Job CSV", type=['csv'], key="job_upload")
        
        if job_file:
            try:
                jobs = DataParser.load_csv_data(job_file, data_type='jobs')
                if jobs:
                    st.session_state.job_data = jobs[0]  # For MVP, use first job
                    st.success(f"✅ Loaded job: {jobs[0]['title']}")
                    st.json({
                        'Title': jobs[0]['title'],
                        'Required Skills': jobs[0]['required_skills'][:5],
                        'Experience': f"{jobs[0]['experience_years']} years"
                    })
            except Exception as e:
                st.error(f"Error loading job: {e}")
    
    with col2:
        st.subheader("👥 Candidate Profiles")
        st.info("""
        **CSV Format required:**
        - id: Unique candidate ID
        - name: Full name
        - email: Email address
        - resume: Resume text/content
        - education: Education details
        - summary: Professional summary (optional)
        """)
        
        candidates_file = st.file_uploader("Upload Candidates CSV", type=['csv'], key="candidates_upload")
        
        if candidates_file:
            try:
                candidates = DataParser.load_csv_data(candidates_file, data_type='candidates')
                if candidates:
                    st.session_state.candidates_data = candidates
                    st.success(f"✅ Loaded {len(candidates)} candidates")
                    
                    st.write("**Sample Candidates:**")
                    sample_df = pd.DataFrame([
                        {
                            'Name': c['name'],
                            'Skills': len(c['skills']),
                            'Experience': f"{c['experience_years']}y"
                        }
                        for c in candidates[:3]
                    ])
                    st.dataframe(sample_df, use_container_width=True)
            except Exception as e:
                st.error(f"Error loading candidates: {e}")
    
    st.divider()
    
    # Ranking Button
    if st.session_state.job_data and st.session_state.candidates_data:
        st.subheader("🚀 Start Ranking")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            analyze_details = st.checkbox("Include LLM Analysis (slower but detailed)")
        with col2:
            top_k = st.number_input("Top K candidates to analyze", 5, 20, 10)
        with col3:
            st.write("")
        
        if st.button("🎯 Run Ranking Engine", type="primary", use_container_width=True):
            with st.spinner("⏳ Analyzing candidates..."):
                try:
                    # Initialize ranking engine
                    ranking_engine = RankingEngine()
                    ranking_engine.load_job(st.session_state.job_data)
                    ranking_engine.load_candidates(st.session_state.candidates_data)
                    
                    # Get rankings
                    ranked = ranking_engine.rank_candidates()
                    
                    # Optional: Add LLM analysis
                    if analyze_details:
                        st.info("🤖 Running LLM analysis on top candidates...")
                        llm_analyzer = LLMAnalyzer()
                        ranked = llm_analyzer.batch_analyze(
                            ranked,
                            st.session_state.job_data,
                            top_n=min(top_k, len(ranked))
                        )
                    
                    st.session_state.ranking_results = ranked
                    st.success("✅ Ranking complete!")
                    st.balloons()
                    
                except Exception as e:
                    st.error(f"❌ Error during ranking: {str(e)}")
                    import traceback
                    st.write(traceback.format_exc())

# PAGE 2: RANKING RESULTS
elif page == "Ranking Results":
    st.header("2️⃣ Ranking Results")
    
    if not st.session_state.ranking_results:
        st.warning("⚠️ Please upload data and run ranking first")
    else:
        results = st.session_state.ranking_results
        job = st.session_state.job_data
        
        st.write(f"**Job:** {job['title']}")
        st.write(f"**Total Candidates Ranked:** {len(results)}")
        st.divider()
        
        # Summary Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            tier1_count = sum(1 for r in results if r['score']['total'] >= 85)
            col1.metric("🥇 Tier 1 (Strong Match)", tier1_count)
        with col2:
            tier2_count = sum(1 for r in results if 70 <= r['score']['total'] < 85)
            col2.metric("🥈 Tier 2 (Good Match)", tier2_count)
        with col3:
            tier3_count = sum(1 for r in results if 55 <= r['score']['total'] < 70)
            col3.metric("🥉 Tier 3 (Moderate)", tier3_count)
        with col4:
            avg_score = sum(r['score']['total'] for r in results) / len(results)
            col4.metric("📊 Average Score", f"{avg_score:.1f}")
        
        st.divider()
        
        # Ranking Table
        st.subheader("📊 Full Rankings")
        
        ranking_data = []
        for idx, result in enumerate(results, 1):
            candidate = result['candidate']
            score = result['score']
            
            ranking_data.append({
                'Rank': idx,
                'Name': candidate['name'],
                'Total Score': score['total'],
                'Skill Match': score['components']['skill_match'],
                'Experience': score['components']['experience_level'],
                'Career Growth': score['components']['career_growth'],
                'Tier': "🥇 Tier 1" if score['total'] >= 85 else
                        "🥈 Tier 2" if score['total'] >= 70 else
                        "🥉 Tier 3" if score['total'] >= 55 else "Tier 4"
            })
        
        df_results = pd.DataFrame(ranking_data)
        
        # Add styling
        def style_score(val):
            if val >= 85:
                return 'background-color: #e8f5e9'
            elif val >= 70:
                return 'background-color: #fff3e0'
            elif val >= 55:
                return 'background-color: #fff8e1'
            else:
                return 'background-color: #ffebee'
        
        styled_df = df_results.style.applymap(style_score, subset=['Total Score'])
        st.dataframe(styled_df, use_container_width=True)
        
        # Download Results
        st.divider()
        csv = df_results.to_csv(index=False)
        st.download_button(
            label="📥 Download Rankings CSV",
            data=csv,
            file_name=f"rankings_{job['title'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# PAGE 3: CANDIDATE DETAILS
elif page == "Candidate Details":
    st.header("3️⃣ Candidate Detailed Analysis")
    
    if not st.session_state.ranking_results:
        st.warning("⚠️ Please upload data and run ranking first")
    else:
        results = st.session_state.ranking_results
        
        # Candidate Selection
        candidate_options = [f"{r['candidate']['name']} (Score: {r['score']['total']})" 
                           for r in results]
        selected_idx = st.selectbox("Select Candidate:", 
                                   range(len(results)), 
                                   format_func=lambda i: candidate_options[i])
        
        result = results[selected_idx]
        candidate = result['candidate']
        score = result['score']
        
        st.divider()
        
        # Candidate Info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Total Score", f"{score['total']}/100")
        with col2:
            st.metric("💼 Experience", f"{candidate['experience_years']} years")
        with col3:
            st.metric("🎯 Tier", result.get('analysis', {}).get('recommendation', 'Analyzing...'))
        
        st.divider()
        
        # Score Components
        st.subheader("📈 Score Breakdown")
        components_data = {
            'Component': list(score['components'].keys()),
            'Score': list(score['components'].values())
        }
        df_components = pd.DataFrame(components_data)
        
        col1, col2 = st.columns([1, 2])
        with col1:
            st.dataframe(df_components, use_container_width=True)
        
        with col2:
            import plotly.express as px
            fig = px.bar(
                df_components,
                x='Component',
                y='Score',
                title='Score Components',
                color='Score',
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Skills Analysis
        st.subheader("💡 Skills Analysis")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Candidate Skills:**")
            for skill in candidate['skills'][:10]:
                st.success(f"✓ {skill}")
        
        with col2:
            st.markdown("**Required Skills:**")
            job = st.session_state.job_data
            required = job.get('required_skills', [])
            for skill in required[:10]:
                if skill in candidate['skills']:
                    st.success(f"✓ {skill}")
                else:
                    st.error(f"✗ {skill}")
        
        # LLM Analysis (if available)
        if 'analysis' in result:
            st.divider()
            st.subheader("🤖 AI Analysis")
            analysis = result['analysis']
            
            st.write(f"**Summary:** {analysis['summary']}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Strengths:**")
                for strength in analysis.get('strengths', []):
                    st.success(f"• {strength}")
            
            with col2:
                st.write("**Development Areas:**")
                for gap in analysis.get('gaps', []):
                    st.info(f"• {gap}")

# PAGE 4: EXPORT REPORT
elif page == "Export Report":
    st.header("4️⃣ Export Hackathon Report")
    
    if not st.session_state.ranking_results:
        st.warning("⚠️ Please upload data and run ranking first")
    else:
        results = st.session_state.ranking_results
        job = st.session_state.job_data
        
        st.subheader("📋 Hackathon Submission Format")
        
        # Generate Report
        report = {
            'timestamp': datetime.now().isoformat(),
            'job': {
                'id': job['id'],
                'title': job['title'],
                'description': job['description'][:200],
                'required_skills': job['required_skills'],
                'experience_years': job['experience_years']
            },
            'rankings': []
        }
        
        for idx, result in enumerate(results, 1):
            candidate = result['candidate']
            score = result['score']
            ranking_engine = RankingEngine()
            tier = ranking_engine.get_tier_classification(score['total'])
            
            report['rankings'].append({
                'rank': idx,
                'candidate_id': candidate['id'],
                'candidate_name': candidate['name'],
                'email': candidate['email'],
                'total_score': score['total'],
                'score_components': score['components'],
                'tier': tier,
                'skills': candidate['skills'][:5],
                'experience_years': candidate['experience_years']
            })
        
        # Display Report
        st.json(report)
        
        # Download Options
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            # JSON Export
            json_str = json.dumps(report, indent=2)
            st.download_button(
                label="📥 Download as JSON",
                data=json_str,
                file_name=f"hackathon_rankings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col2:
            # CSV Export
            csv_data = []
            for item in report['rankings']:
                csv_data.append({
                    'Rank': item['rank'],
                    'Candidate Name': item['candidate_name'],
                    'Email': item['email'],
                    'Total Score': item['total_score'],
                    'Skill Match': item['score_components']['skill_match'],
                    'Experience Match': item['score_components']['experience_level'],
                    'Career Growth': item['score_components']['career_growth'],
                    'Tier': item['tier'],
                    'Top Skills': '; '.join(item['skills'])
                })
            
            df_export = pd.DataFrame(csv_data)
            csv_str = df_export.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv_str,
                file_name=f"hackathon_rankings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #888; font-size: 12px; margin-top: 30px;">
    <p>🎯 AI-Powered Candidate Ranking System | Hackathon Submission</p>
    <p>Built with Streamlit, OpenAI Embeddings, and FAISS Vector Search</p>
</div>
""", unsafe_allow_html=True)
