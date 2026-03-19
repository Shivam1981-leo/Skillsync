"""
SkillSync — Flask Backend (app.py)
Improved version: fixed weak_points, static paths, better scoring.
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import PyPDF2
import re
import os
import numpy as np
import json
from collections import Counter
import string

# ── Optional: sentence-transformers (comment out if not installed) ──────────
try:
    from sentence_transformers import SentenceTransformer
    bert_model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ BERT model loaded.")
    USE_BERT = True
except Exception as e:
    print(f"⚠️  sentence-transformers not available ({e}). Using keyword fallback.")
    USE_BERT = False

# ── Optional: MySQL (comment out if not using a DB) ─────────────────────────
try:
    import mysql.connector
    USE_DB = True
except ImportError:
    USE_DB = False
    print("⚠️  mysql-connector not installed. DB storage disabled.")

# ── App setup ────────────────────────────────────────────────────────────────
app = Flask(
    __name__,
    template_folder=".",          # dashboard.html is in root
    static_folder="static"
)
CORS(app)

# ── DB connection (optional) ─────────────────────────────────────────────────
def get_db_connection():
    if not USE_DB:
        return None
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="YOUR_MYSQL_PASSWORD",   # 🔑 Replace before running
        database="resumelens"
    )

# ── Stopwords ─────────────────────────────────────────────────────────────────
STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "have",
    "has", "was", "are", "will", "responsible", "worked", "experience",
    "project", "education", "company", "university", "also", "able",
    "using", "used", "work", "team", "our", "your", "etc"
}

# ── Target skill sets ──────────────────────────────────────────────────────────
TARGET_SKILLS = {
    "python", "java", "c++", "flask", "spring boot",
    "sql", "nosql", "git", "docker", "algorithms",
    "system design", "api", "machine learning",
    "android", "data structures", "kotlin", "rest",
    "kubernetes", "aws", "linux", "react", "node"
}

# ── Helper: extract text from PDF ─────────────────────────────────────────────
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + " "
    return text.lower()

# ── Helper: auto-extract skills from resume text ───────────────────────────────
def extract_skills_from_text(text):
    words = [
        w.strip(string.punctuation).lower()
        for w in text.split()
        if w.strip(string.punctuation)
    ]

    phrases = []
    for i in range(len(words)):
        phrases.append(words[i])
        if i < len(words) - 1:
            phrases.append(words[i] + " " + words[i + 1])
        if i < len(words) - 2:
            phrases.append(words[i] + " " + words[i + 1] + " " + words[i + 2])

    cleaned = [
        p for p in phrases
        if all(w not in STOPWORDS for w in p.split())
        and not any(c.isdigit() for c in p)
        and len(p) > 2
    ]

    freq = Counter(cleaned)
    skills = [s for s, c in freq.items() if c >= 2 and len(s.split()) <= 3]
    return skills[:25]

# ── Helper: find which TARGET_SKILLS are in the resume ────────────────────────
def find_matched_and_missing(resume_text):
    matched = []
    missing = []
    for skill in TARGET_SKILLS:
        if skill in resume_text:
            matched.append(skill.title())
        else:
            missing.append(skill.title())
    return matched, missing

# ── Helper: cosine similarity without BERT ────────────────────────────────────
def keyword_similarity(text_a, text_b):
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    if not words_a or not words_b:
        return 0.5
    intersection = words_a & words_b
    return len(intersection) / (len(words_a | words_b) ** 0.5 + 1e-9)

# ── Helper: store resume to DB ────────────────────────────────────────────────
def store_resume(filename, text, embedding=None):
    conn = get_db_connection()
    if conn is None:
        return
    try:
        cursor = conn.cursor()
        emb_json = json.dumps(embedding.tolist()) if embedding is not None else "[]"
        cursor.execute(
            "INSERT INTO resumes (filename, text, embedding) VALUES (%s, %s, %s)",
            (filename, text, emb_json)
        )
        conn.commit()
    except Exception as e:
        print(f"DB write error: {e}")
    finally:
        cursor.close()
        conn.close()

# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route('/')
def home():
    return render_template("dashboard.html")

@app.route('/dashboard.html')
def dashboard():
    return render_template("dashboard.html")

# Serve login/other HTML pages from root directory
@app.route('/<path:filename>')
def serve_root(filename):
    return send_from_directory('.', filename)


@app.route('/api/upload', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    job_description = request.form.get("job_description", "").strip()

    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    try:
        resume_text = extract_text_from_pdf(file)

        # ── 1. JD Match Score (40%) ──────────────────────────────────────────
        if job_description:
            if USE_BERT:
                jd_emb = bert_model.encode([job_description])[0]
                res_emb = bert_model.encode([resume_text])[0]
                similarity = float(np.dot(res_emb, jd_emb) / (
                    np.linalg.norm(res_emb) * np.linalg.norm(jd_emb) + 1e-9
                ))
                jd_score = min(similarity * 100, 100)
            else:
                sim = keyword_similarity(resume_text, job_description)
                jd_score = min(sim * 200, 100)   # scale up keyword ratio
        else:
            jd_score = 58  # neutral baseline

        # ── 2. Experience Score (20%) ────────────────────────────────────────
        exp_matches = re.findall(r'(\d+)\+?\s*(years|yrs)', resume_text)
        total_years = sum(int(m[0]) for m in exp_matches)

        if total_years >= 5:
            experience_score = 90
        elif total_years >= 3:
            experience_score = 75
        elif total_years >= 1:
            experience_score = 60
        else:
            experience_score = 40

        # ── 3. Skill Coverage (15%) ──────────────────────────────────────────
        matched_skills, missing_skills = find_matched_and_missing(resume_text)
        skill_score = min((len(matched_skills) / max(len(TARGET_SKILLS), 1)) * 100, 100)

        # Also pull auto-extracted skills for display
        auto_skills = extract_skills_from_text(resume_text)

        # ── 4. Project Detection (15%) ───────────────────────────────────────
        project_kw = ["project", "developed", "built", "implemented", "designed", "created"]
        project_count = sum(resume_text.count(w) for w in project_kw)

        if project_count >= 6:
            project_score = 90
        elif project_count >= 3:
            project_score = 72
        elif project_count >= 1:
            project_score = 55
        else:
            project_score = 35

        # ── 5. Quality Signals (10%) ─────────────────────────────────────────
        quality_score = 45
        if len(resume_text) > 1500:
            quality_score += 10
        if re.search(r'\b\d+%|\$\d+|₹\d+|\d+\+', resume_text):
            quality_score += 20
        if "education" in resume_text:
            quality_score += 10
        if "experience" in resume_text:
            quality_score += 15
        quality_score = min(quality_score, 100)

        # ── Final Score ──────────────────────────────────────────────────────
        final_score = int(
            0.40 * jd_score +
            0.20 * experience_score +
            0.15 * skill_score +
            0.15 * project_score +
            0.10 * quality_score
        )

        # ── Status ───────────────────────────────────────────────────────────
        if final_score >= 80:
            status = "Excellent Match"
        elif final_score >= 65:
            status = "Strong Candidate"
        elif final_score >= 50:
            status = "Good Foundation"
        else:
            status = "Needs Optimisation"

        # ── Recommendations ──────────────────────────────────────────────────
        recommendations = []
        if jd_score < 60:
            recommendations.append("Align resume keywords more closely with the job description.")
        if experience_score < 60:
            recommendations.append("Highlight relevant experience and internship durations clearly.")
        if project_score < 60:
            recommendations.append("Add 2–3 technical projects with measurable outcomes.")
        if quality_score < 65:
            recommendations.append("Include quantified achievements (e.g. 'improved performance by 30%').")
        if len(missing_skills) > 5:
            top_missing = missing_skills[:3]
            recommendations.append(f"Consider adding skills: {', '.join(top_missing)}.")
        if not recommendations:
            recommendations.append("Great resume! Tailor it specifically for each role you apply to.")

        # ── DB Store (optional) ──────────────────────────────────────────────
        if USE_BERT:
            emb = bert_model.encode([resume_text])[0]
            store_resume(file.filename, resume_text, emb)
        else:
            store_resume(file.filename, resume_text)

        return jsonify({
            "match_score":    final_score,
            "status":         status,
            "strengths":      [s.title() for s in (matched_skills or auto_skills)[:6]],
            "weak_points":    missing_skills[:6],          # ✅ Fixed — now always returns gaps
            "recommendations": recommendations[:4],
            "radar_scores":   [
                round(skill_score, 1),
                round(experience_score, 1),
                round(project_score, 1),
                round(jd_score, 1),
                round(quality_score, 1)
            ]
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, port=5000)
