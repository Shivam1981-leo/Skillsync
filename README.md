# ⚡ SkillSync — AI Resume Intelligence Platform

A complete, redesigned and integrated version of the SkillSync web application.

---

## 📁 Project Structure

```
skillsync/
├── app.py               ← Flask backend (start here)
├── login.html           ← Landing / login page
├── dashboard.html       ← AI resume analysis (main page)
├── hackathons.html      ← Hackathon listings with filters
├── jobs.html            ← Job/internship listings with search
├── courses.html         ← Curated learning roadmap & courses
├── static/
│   ├── style.css        ← Shared design system (all pages)
│   └── script.js        ← Shared JS (upload, radar, dropdown)
└── README.md
```

---

## 🚀 Getting Started

### 1. Install Python Dependencies

```bash
pip install flask flask-cors PyPDF2 numpy sentence-transformers
# Optional (for DB):
pip install mysql-connector-python
```

### 2. Configure MySQL (optional)

Open `app.py` and update:
```python
password="YOUR_MYSQL_PASSWORD"
```

Create the database:
```sql
CREATE DATABASE resumelens;
USE resumelens;
CREATE TABLE resumes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255),
    text LONGTEXT,
    embedding LONGTEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

If you don't want MySQL, the app works fine without it — storage is just skipped.

### 3. Run the Server

```bash
python app.py
```

### 4. Open in Browser

Visit: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## ✅ Improvements in This Version

| Area | What Changed |
|------|-------------|
| **Pages connected** | All pages share one `style.css` and `script.js`; navigation works across all pages |
| **User session** | Login saves name/role to `sessionStorage`; dashboard/navbar shows real user name |
| **`weak_points` bug fixed** | Backend now returns actual missing skills (was always empty `[]`) |
| **`uploadResume()` fix** | `index.html` called undefined function; now unified as `uploadResume()` in `script.js` |
| **Static paths fixed** | `dashboard.html` had mixed Flask `url_for()` + plain paths; all unified |
| **JD textarea added** | Users can paste job description directly on dashboard for more accurate scoring |
| **Better scoring** | Keyword fallback when BERT unavailable; `weak_points` now derived from `TARGET_SKILLS` diff |
| **UI/UX redesign** | New typography (Syne + DM Sans), grid layout, animated score ring, spotlight cards |
| **Hackathon filters** | Dual-filter (organiser + type) with live count |
| **Jobs search** | Live text search + type filter on jobs page |
| **Courses roadmap** | Visual step-by-step roadmap + tab + select filtering |
| **MySQL optional** | App no longer crashes if `mysql-connector` is not installed |

---

## 🌐 Pages Overview

- **`/` or `/dashboard.html`** → AI analysis (upload resume, see score + radar)
- **`/login.html`** → Enter name & role, saved to session
- **`/hackathons.html`** → Filter hackathons by organiser & format
- **`/jobs.html`** → Search jobs by keyword & type
- **`/courses.html`** → Learning roadmap + categorised course cards
