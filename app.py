from flask import Flask, request, jsonify
from flask import render_template
from flask import send_from_directory
from flask_cors import CORS
import PyPDF2
import re
import os
import numpy as np
import mysql.connector
import json
from sentence_transformers import SentenceTransformer
import string
from collections import Counter

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------
# LOAD NLP MODEL
# ---------------------------------------------------------
print("🧠 Loading BERT model...")
bert_model = SentenceTransformer('all-MiniLM-L6-v2')
print("✅ NLP model loaded!")

# ---------------------------------------------------------
# MYSQL CONNECTION
# ---------------------------------------------------------
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="#Gamerforlife123",   # 🔥 Replace with your MySQL password
        database="resumelens"
    )
STOPWORDS = {
    "the", "and", "for", "with", "from", "that",
    "this", "have", "has", "was", "are", "will",
    "responsible", "worked", "experience", "project",
    "education", "company", "university"
}
def extract_skills_automatically(text):

    words = [
        w.strip(string.punctuation).lower()
        for w in text.split()
        if w.strip(string.punctuation)
    ]

    # Generate 1, 2, and 3 word phrases
    phrases = []

    for i in range(len(words)):
        phrases.append(words[i])

        if i < len(words) - 1:
            phrases.append(words[i] + " " + words[i+1])

        if i < len(words) - 2:
            phrases.append(words[i] + " " + words[i+1] + " " + words[i+2])

    # Filter phrases
    cleaned = [
        p for p in phrases
        if all(word not in STOPWORDS for word in p.split())
        and not any(char.isdigit() for char in p)
        and len(p) > 2
    ]

    # Count frequency
    freq = Counter(cleaned)

    # Keep only meaningful frequent phrases
    skills = [
        skill for skill, count in freq.items()
        if count >= 2 and len(skill.split()) <= 3
    ]

    return skills[:20]  # top 20 detected skills
# ---------------------------------------------------------
# TARGET SKILLS
# ---------------------------------------------------------
TARGET_SKILLS = {
    "python", "java", "c++", "flask", "spring boot",
    "sql", "nosql", "git", "docker", "algorithms",
    "system design", "api", "machine learning",
    "android", "data structures"
}

# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------
def extract_text_from_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + " "
    return text.lower()


def store_resume(filename, text, embedding):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "INSERT INTO resumes (filename, text, embedding) VALUES (%s, %s, %s)"
    values = (filename, text, json.dumps(embedding.tolist()))

    cursor.execute(query, values)
    conn.commit()
    cursor.close()
    conn.close()


# ---------------------------------------------------------
# MAIN ROUTE
# ---------------------------------------------------------
@app.route('/')
def home():
    return render_template("dashboard.html")
@app.route('/api/upload', methods=['POST'])
def upload_resume():

    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    job_description = request.form.get("job_description", "")

    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    try:
        resume_text = extract_text_from_pdf(file)

        # -------------------------------------------------
        # 1️⃣ JOB DESCRIPTION MATCH (40%)
        # -------------------------------------------------
        if job_description.strip() != "":
            jd_embedding = bert_model.encode([job_description])[0]
            resume_embedding = bert_model.encode([resume_text])[0]

            similarity = np.dot(resume_embedding, jd_embedding) / (
                np.linalg.norm(resume_embedding) *
                np.linalg.norm(jd_embedding)
            )

            jd_score = similarity * 100
        else:
            jd_score = 60  # baseline if no JD

        # -------------------------------------------------
        # 2️⃣ EXPERIENCE SCORE (20%)
        # -------------------------------------------------
        experience_matches = re.findall(r'(\d+)\+?\s*(years|yrs)', resume_text)
        total_years = sum(int(match[0]) for match in experience_matches)

        if total_years >= 5:
            experience_score = 90
        elif total_years >= 3:
            experience_score = 75
        elif total_years >= 1:
            experience_score = 60
        else:
            experience_score = 40

        # -------------------------------------------------
        # 3️⃣ SKILL COVERAGE (15%)
        # -------------------------------------------------
        found_skills = extract_skills_automatically(resume_text)

        skill_score = (len(found_skills) / len(TARGET_SKILLS)) * 100

        # -------------------------------------------------
        # 4️⃣ PROJECT DETECTION (15%)
        # -------------------------------------------------
        project_keywords = ["project", "developed", "built", "implemented"]
        project_mentions = sum(resume_text.count(word) for word in project_keywords)

        if project_mentions >= 5:
            project_score = 90
        elif project_mentions >= 3:
            project_score = 75
        elif project_mentions >= 1:
            project_score = 60
        else:
            project_score = 40

        # -------------------------------------------------
        # 5️⃣ QUALITY SIGNALS (10%)
        # -------------------------------------------------
        quality_score = 50

        if len(resume_text) > 1500:
            quality_score += 10

        if re.search(r'\b\d+%|\$\d+|\d+\+', resume_text):
            quality_score += 15  # quantified achievements

        if "education" in resume_text:
            quality_score += 10

        if "experience" in resume_text:
            quality_score += 15

        quality_score = min(quality_score, 100)

        # -------------------------------------------------
        # FINAL HYBRID SCORE
        # -------------------------------------------------
        final_score = (
            0.40 * jd_score +
            0.20 * experience_score +
            0.15 * skill_score +
            0.15 * project_score +
            0.10 * quality_score
        )

        final_score = int(final_score)

        # -------------------------------------------------
        # STATUS
        # -------------------------------------------------
        if final_score >= 85:
            status = "Excellent Match"
        elif final_score >= 65:
            status = "Strong Candidate"
        else:
            status = "Needs Optimization"

        # -------------------------------------------------
        # STORE RESUME
        # -------------------------------------------------
        resume_embedding = bert_model.encode([resume_text])[0]
        store_resume(file.filename, resume_text, resume_embedding)

        # -------------------------------------------------
        # RECOMMENDATIONS
        # -------------------------------------------------
        recommendations = []

        if jd_score < 60:
            recommendations.append("Align resume with job description keywords.")

        if experience_score < 60:
            recommendations.append("Highlight more relevant experience.")

        if project_score < 60:
            recommendations.append("Add detailed technical projects.")

        if quality_score < 70:
            recommendations.append("Include quantified achievements.")

        if not recommendations:
            recommendations.append("Strong resume. Tailor per job role.")

        return jsonify({
            "match_score": final_score,
            "status": status,
            "strengths": [s.title() for s in found_skills[:4]],
            "weak_points": [],
            "recommendations": recommendations[:3],
            "radar_scores": [
                skill_score,
                experience_score,
                project_score,
                jd_score,
                quality_score
            ]
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------
# RUN SERVER
# ---------------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True, port=5000)