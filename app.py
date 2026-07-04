# Resume Checker Pro - Career Lens AI
# Student Name: Khushi
# Class: MCA 2nd Year
# College: United Institute of Management
# Guidance: Scholar Sync
# Submission Date: September 2026

# Ye libraries use ki hain project me
import streamlit as st
import pandas as pd
import PyPDF2
import docx
import sqlite3
from streamlit_option_menu import option_menu
from fpdf import FPDF
import base64
import plotly.express as px

# 1. Website ka setup kar rahe hain
st.set_page_config(page_title="Career Lens AI - Resume Checker", page_icon="🎯", layout="wide")

# 2. CSS use kiya h attractive dikhne ke liye
st.markdown("""
<style>
.main-title {
        font-size: 2.8rem!important;
        color: #0068C9;
        text-align: center;
        font-weight: bold;
        padding: 5px;
    }
.sub-title {
        text-align: center;
        font-size: 1.2rem;
        color: #0068C9;
        font-weight: 600;
    }
.college-name {
        text-align: center;
        font-size: 1rem;
        color: grey;
    }
.stButton>button {
        background-color: #0068C9;
        color: white;
        font-weight: bold;
        border-radius: 10px;
        width: 100%;
    }
.footer {
        text-align: center;
        color: grey;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# 3. Functions banaye hain file padhne ke liye
def pdf_file_padho(upload_file):
    # PDF file ko read karne ka function
    pdf_ka_reader = PyPDF2.PdfReader(upload_file)
    sab_text = ""
    for page in pdf_ka_reader.pages:
        sab_text = sab_text + page.extract_text()
    return sab_text

def word_file_padho(upload_file):
    # Word file ko read karne ka function
    doc_file = docx.Document(upload_file)
    sab_text = ""
    for para in doc_file.paragraphs:
        sab_text = sab_text + para.text + " "
    return sab_text

def skills_nikalo(text):
    # Resume me se skills dhundne ka function
    skills = ['python', 'java', 'sql', 'excel', 'powerpoint', 'word', 'html', 'css',
              'javascript', 'c++', 'communication', 'teamwork', 'leadership',
              'data analysis', 'tableau', 'power bi', 'autocad', 'git', 'react',
              'machine learning', 'seo', 'content writing', 'photoshop', 'figma',
              'digital marketing', 'accounting', 'tally', 'docker', 'aws', 'linux',
              'problem solving', 'django', 'spring', 'node.js', 'mongodb', 'api',
              'statistics', 'deep learning', 'tensorflow', 'kubernetes', 'jenkins',
              'azure', 'networking', 'wordpress', 'creativity', 'english', 'illustrator',
              'canva', 'ui', 'ux', 'prototyping', 'google ads', 'facebook ads', 
              'analytics', 'google analytics', 'keyword research', 'negotiation',
              'finance', 'taxation', 'analysis', 'teaching', 'subject knowledge',
              'construction', 'planning', 'circuit design', 'strategy', 'android',
              'kotlin', 'firebase']
    
    mili_hui_skills = []
    text_ko_small = text.lower()
    
    for ek_skill in skills:
        if ek_skill in text_ko_small:
            mili_hui_skills.append(ek_skill)
    
    return mili_hui_skills

# 4. SQL Database ka setup
conn = sqlite3.connect('resume_jobs.db')
cursor = conn.cursor()

# Table banate hain agar pehle se nahi hai
cursor.execute('''
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_naam TEXT NOT NULL,
    jaruri_skills TEXT NOT NULL,
    salary_range TEXT NOT NULL
)
''')

# Data daalte hain - sirf pehli baar
cursor.execute("SELECT COUNT(*) FROM jobs")
if cursor.fetchone()[0] == 0:
    jobs_data = [
        ('Data Analyst', 'python, sql, excel, data analysis, tableau, power bi, communication', '6-12 LPA'),
        ('Web Developer', 'html, css, javascript, react, git, problem solving', '4-8 LPA'),
        ('Software Engineer', 'python, java, c++, sql, problem solving, git', '7-15 LPA'),
        ('Business Analyst', 'excel, sql, power bi, communication, problem solving', '6-12 LPA'),
        ('Data Scientist', 'python, machine learning, statistics, sql, tableau, power bi', '10-20 LPA'),
        ('Python Developer', 'python, django, sql, git, problem solving', '8-16 LPA'),
        ('Frontend Developer', 'html, css, javascript, react, figma, git', '5-10 LPA'),
        ('Backend Developer', 'python, node.js, sql, mongodb, api, git', '6-12 LPA'),
        ('Full Stack Developer', 'html, css, javascript, python, sql, git', '7-15 LPA'),
        ('AI Engineer', 'python, machine learning, deep learning, tensorflow, sql', '12-25 LPA'),
        ('Marketing Executive', 'communication, excel, powerpoint, leadership, teamwork, digital marketing', '3-6 LPA'),
        ('HR Executive', 'communication, leadership, excel, powerpoint, teamwork', '3-6 LPA')
    ]
    cursor.executemany("INSERT INTO jobs (job_naam, jaruri_skills, salary_range) VALUES (?,?,?)", jobs_data)
    conn.commit()

# Database se data nikal ke dataframe me daal diya
df = pd.read_sql_query("SELECT job_naam as Job, jaruri_skills as Skills, salary_range as Salary FROM jobs", conn)
conn.close()

# 5. Sidebar me Navigation Menu
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
    st.markdown("### **Khushi - Career Lens** 🎯")
    st.caption("MCA 2nd Year")

    selected = option_menu(
        menu_title=None,
        options=["Resume Checker", "Analytics", "About", "Login"],
        icons=["house", "bar-chart", "info-circle", "person"],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px"},
            "nav-link-selected": {"background-color": "#0068C9"},
        }
    )

    st.divider()
    st.success("💾 SQL Database Connected")
    st.info("📊 Ready to Analyze")
    st.write("---")
    st.markdown('<p class="footer">Made with ❤️ by<br><b>Khushi - Career Lens</b><br>United Institute of Management</p>', unsafe_allow_html=True)

# 6. Pages ka code
if selected == "Resume Checker":
    # Main Heading
    st.markdown('<p class="main-title">Career Lens AI</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Resume Checker Pro</p>', unsafe_allow_html=True)
    st.markdown('<p class="college-name">United Institute of Management | Guidance: Scholar Sync</p>', unsafe_allow_html=True)
    st.write("---")

    st.subheader("1️⃣ Resume Upload Karo")
    file = st.file_uploader("PDF ya Word file choose karo", type=['pdf', 'docx'])

    user_ki_skills = []
    resume_text = ""
    
    if file!= None:
        with st.spinner('Resume analyze ho raha hai...'):
            if file.name.endswith('.pdf'):
                resume_text = pdf_file_padho(file)
            else:
                resume_text = word_file_padho(file)
            user_ki_skills = skills_nikalo(resume_text)

        if len(user_ki_skills) > 0:
            st.success("**Mili Hui Skills:** " + ', '.join(user_ki_skills).title())
        else:
            st.error("Resume me koi skill nahi mili. Skills section add karo")

    # Feature 4: Best Job Auto Suggest
    if len(user_ki_skills) > 0:
        st.write("---")
        st.subheader("🎯 Best Job Match For Your Resume")

        job_scores = []
        for i in range(len(df)):
            jaruri_skills_list = [s.strip().lower() for s in df['Skills'][i].split(',')]
            match_count = len([s for s in jaruri_skills_list if s in user_ki_skills])
            percent = (match_count / len(jaruri_skills_list)) * 100
            job_scores.append((df['Job'][i], int(percent), df['Salary'][i]))

        job_scores.sort(key=lambda x: x[1], reverse=True)
        top_3_jobs = job_scores[:3]

        for job, score, salary in top_3_jobs:
            col1, col2, col3 = st.columns([2,1,1])
            col1.write(f"**{job}**")
            col2.progress(score, text=f"{score}%")
            col3.write(f"💰 {salary}")

        st.write("---")
        st.subheader("2️⃣ Job Select Karo")
        job_choice = st.selectbox("Ya fir manual job choose karo:", df['Job'])

        if st.button("🔍 Resume Check Karo", type="primary"):
            st.write("---")
            st.subheader("📊 Analysis Report:")

            job_ka_index = df[df['Job'] == job_choice].index[0]
            jaruri_skills_list = [s.strip().lower() for s in df['Skills'][job_ka_index].split(',')]

            match_hui = [s for s in jaruri_skills_list if s in user_ki_skills]
            match_nahi_hui = [s for s in jaruri_skills_list if s not in user_ki_skills]

            total_skills = len(jaruri_skills_list)
            matched_skills = len(match_hui)
            percentage = (matched_skills / total_skills) * 100

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("🎯 Target Job", job_choice)
            col2.metric("💰 Salary", df['Salary'][job_ka_index])
            col3.metric("📊 Skill Match", f"{matched_skills}/{total_skills}")
            col4.metric("🗄️ Source", "SQL DB")

            if percentage >= 80:
                st.success(f"## 🎉 Resume Score: {int(percentage)}% - JOB READY!")
                st.balloons()
            elif percentage >= 50:
                st.warning(f"## ⚠️ Resume Score: {int(percentage)}% - Thodi Mehnat Aur")
            else:
                st.error(f"## 📚 Resume Score: {int(percentage)}% - Skills Seekho")

            st.progress(int(percentage))

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("### ✅ Tumhari Strong Skills")
                for s in match_hui:
                    st.success(f"**{s.title()}** ✓")
            
            # Feature 2: YouTube Links
            with col2:
                st.markdown("### ❌ Missing Skills")
                skill_links = {
                    'python': 'https://youtube.com/playlist?list=PLu0W_9lII9agICnT8t4iYVSZ3eykIAOME',
                    'sql': 'https://youtube.com/playlist?list=PLxCzCOWd7aiFAN6I8CuViBuCdJgiOkT2Y',
                    'excel': 'https://youtube.com/playlist?list=PLWPirh4EWFpEpO6NjjWLbK0b-w0Z3xHnd',
                    'machine learning': 'https://youtube.com/playlist?list=PLxCzCOWd7aiEXg5BV10k9THtjnS48yI-T',
                    'power bi': 'https://youtube.com/playlist?list=PLWx5a9Tn2EvtP8D4yyC-Vlq22Zg5w9E8Y',
                    'javascript': 'https://youtube.com/playlist?list=PLu0W_9lII9ajyk081To1Cbt2eI5913Vg',
                    'react': 'https://youtube.com/playlist?list=PLu0W_9lII9agx66oZnT6IyhcMIbUMNMdt'
                }
                for s in match_nahi_hui:
                    st.error(f"**{s.title()}** ✗")
                    if s in skill_links:
                        st.markdown(f"[📺 Learn {s.title()} Free]({skill_links[s]})")

            # Feature 3: ATS Score
            st.write("---")
            st.subheader("🤖 ATS Compatibility Score")
            ats_score = 0
            if len(user_ki_skills) >= 5: ats_score += 30
            if 'email' in resume_text.lower() or 'phone' in resume_text.lower() or '@' in resume_text: ats_score += 20
            if 'education' in resume_text.lower() or 'bca' in resume_text.lower() or 'mca' in resume_text.lower(): ats_score += 20
            if 'experience' in resume_text.lower() or 'project' in resume_text.lower() or 'internship' in resume_text.lower(): ats_score += 30

            col1, col2 = st.columns([1,3])
            col1.metric("ATS Score", f"{ats_score}/100")
            if ats_score >= 80:
                col2.success("Your resume will pass ATS bots easily! ✅")
            elif ats_score >= 50:
                col2.warning("Add more sections like Education, Projects, Contact")
            else:
                col2.error("Resume me Education, Contact, Projects add karo")

            # Personal Skill Analysis Dashboard - Pie Chart
            st.write("---")
            st.subheader("📊 Personal Skill Analysis Dashboard")

            if len(match_hui) > 0 or len(match_nahi_hui) > 0:
                chart_data = pd.DataFrame({
                    'Category': ['Matched Skills ✅', 'Missing Skills ❌'],
                    'Count': [len(match_hui), len(match_nahi_hui)]
                })
                
                fig = px.pie(chart_data, values='Count', names='Category', 
                             title=f'Skill Match for {job_choice}',
                             color_discrete_map={'Matched Skills ✅':'#00CC96',
                                                 'Missing Skills ❌':'#EF553B'})
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
                
                st.caption(f"Total {total_skills} skills me se {matched_skills} skills tumhare paas hain")
            else:
                st.info("Resume upload karke check karo")

            # Feature 5: Interview Questions
            st.write("---")
            st.subheader("💬 Expected Interview Questions")
            if len(match_nahi_hui) > 0:
                st.info(f"Based on missing skill: **{match_nahi_hui[0].title()}**")
                questions = {
                    'python': ["1. Python me list vs tuple kya hai?", "2. Decorator kya hota hai?", "3. Lambda function kya hai?"],
                    'sql': ["1. Primary key vs Foreign key?", "2. JOIN types explain karo", "3. GROUP BY ka use kya hai?"],
                    'machine learning': ["1. Supervised vs Unsupervised learning?", "2. Overfitting kya hai?", "3. Train-Test split kyu karte hain?"],
                    'excel': ["1. VLOOKUP kaise use karte hain?", "2. Pivot table kya hai?", "3. Conditional formatting kya hai?"],
                    'javascript': ["1. var, let, const me difference?", "2. Closure kya hota hai?", "3. Promise kya hai?"]
                }
                if match_nahi_hui[0] in questions:
                    for q in questions[match_nahi_hui[0]]:
                        st.write(q)
                else:
                    st.write("1. Tell me about yourself")
                    st.write(f"2. Why do you want to learn {match_nahi_hui[0].title()}?")
                    st.write("3. Apne projects ke baare me batao")
            else:
                st.success("Wah! Saari skills hain. Interview me confidence se jao!")
                st.write("1. Tell me about yourself")
                st.write("2. Why should we hire you?")
                st.write("3. What are your strengths?")

            # Feature 1: PDF Download
            st.write("---")
            if st.button("📥 Download Report PDF"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, "Career Lens AI - Resume Report", ln=True, align='C')
                pdf.ln(10)
                pdf.set_font("Arial", '', 12)
                pdf.cell(0, 10, f"Student: Khushi - MCA 2nd Year", ln=True)
                pdf.cell(0, 10, f"College: United Institute of Management", ln=True)
                pdf.cell(0, 10, f"Guidance: Scholar Sync", ln=True)
                pdf.cell(0, 10, f"Job Role: {job_choice}", ln=True)
                pdf.cell(0, 10, f"Resume Score: {int(percentage)}%", ln=True)
                pdf.cell(0, 10, f"ATS Score: {ats_score}/100", ln=True)
                pdf.ln(5)
                pdf.cell(0, 10, "Matched Skills:", ln=True)
                for s in match_hui:
                    pdf.cell(0, 8, f"- {s.title()}", ln=True)
                pdf.ln(3)
                pdf.cell(0, 10, "Missing Skills:", ln=True)
                for s in match_nahi_hui:
                    pdf.cell(0, 8, f"- {s.title()}", ln=True)

                pdf.output("report.pdf")
                with open("report.pdf", "rb") as f:
                    base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                    href = f'<a href="data:application/pdf;base64,{base64_pdf}" download="Resume_Report_Khushi.pdf">Click Here to Download PDF</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    st.success("PDF Ready! Upar wale link pe click karo")

            st.success("✅ Analysis Complete - Career Lens AI")

elif selected == "Analytics":
    st.title("📊 Career Analytics Dashboard")
    st.info("Yaha Jobs vs Salary ka overall analysis hai - SQL Database se")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Jobs", len(df))
    col2.metric("Highest Package", "12-25 LPA")
    col3.metric("Skills Tracked", "50+")

    st.write("---")
    st.subheader("Jobs vs Average Salary")
    df['Avg_Salary'] = df['Salary'].str.extract('(\d+)').astype(int)
    st.bar_chart(df.set_index('Job')['Avg_Salary'])

    st.write("---")
    st.subheader("Job Data Table - SQL Se")
    st.dataframe(df, use_container_width=True)

elif selected == "About":
    st.title("ℹ️ About Career Lens AI")
    st.write("---")
    col1, col2 = st.columns([1,2])
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=150)
    with col2:
        st.subheader("Project: Resume Checker Pro")
        st.write("**Developer:** Khushi")
        st.write("**Class:** MCA 2nd Year")
        st.write("**College:** United Institute of Management")
        st.write("**Guidance:** Scholar Sync")
        st.write("**Purpose:** Students ko resume analyze karke career guidance dena")

    st.write("---")
    st.subheader("🛠️ Technologies Used:")
    c1, c2, c3, c4 = st.columns(4)
    c1.write("🐍 **Python**\n Backend Logic")
    c2.write("🎈 **Streamlit**\n Web Framework")
    c3.write("🗄️ **SQLite**\n Database")
    c4.write("📊 **Plotly**\n Visualization")

    st.write("---")
    st.subheader("✨ Key Features:")
    st.write("1. ✅ Resume se automatically skills extract karta hai")
    st.write("2. ✅ SQL database se 12+ jobs match karta hai")
    st.write("3. ✅ Score calculate karke personalized suggestions deta hai")
    st.write("4. ✅ ATS Compatibility check karta hai")
    st.write("5. ✅ Best Job auto-suggest karta hai")
    st.write("6. ✅ Missing skills ke liye YouTube links deta hai")
    st.write("7. ✅ Interview questions generate karta hai")
    st.write("8. ✅ PDF Report download kar sakte hain")

elif selected == "Login":
    st.title("🔐 Login Portal - Career Lens AI")
    st.info("Student & Admin Login System")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        with st.form("login_form"):
            st.subheader("Welcome Back!")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            if submit:
                if username == "khushi" and password == "1234":
                    st.success("Login Successful! Welcome Khushi 🎉")
                    st.balloons()
                elif username == "admin" and password == "admin":
                    st.success("Admin Login Successful!")
                else:
                    st.error("Galat username ya password. Demo: username=khushi, password=1234")

    with tab2:
        with st.form("signup_form"):
            st.subheader("Create New Account")
            new_user = st.text_input("New Username")
            new_email = st.text_input("Email ID")
            new_pass = st.text_input("New Password", type="password")
            signup = st.form_submit_button("Sign Up")
            if signup:
                st.success(f"Account ban gaya {new_user}! Abhi login karo")
                st.info("Note: Ye demo hai, actual database me save nahi hoga")