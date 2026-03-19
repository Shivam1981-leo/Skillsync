/* ============================================================
   SkillSync — Shared JavaScript
   ============================================================ */

// ── Card mouse-spotlight effect ─────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.card').forEach(card => {
        card.addEventListener('mousemove', e => {
            const r = card.getBoundingClientRect();
            card.style.setProperty('--mx', `${e.clientX - r.left}px`);
            card.style.setProperty('--my', `${e.clientY - r.top}px`);
        });
    });
});

// ── Load user session data from sessionStorage ───────────────
document.addEventListener('DOMContentLoaded', () => {
    const name     = sessionStorage.getItem('ss_name')     || 'Guest User';
    const role     = sessionStorage.getItem('ss_role')     || 'Software Engineer';
    const location = sessionStorage.getItem('ss_location') || '';

    const roleLabels = {
        backend:  'Backend Engineer',
        android:  'Android Developer',
        data:     'Data Analyst / ML',
        frontend: 'Frontend Developer',
        devops:   'DevOps Engineer'
    };

    // Update every element with data-user-name / data-user-role
    document.querySelectorAll('[data-user-name]').forEach(el => el.textContent = name);
    document.querySelectorAll('[data-user-role]').forEach(el => el.textContent = roleLabels[role] || role);
    document.querySelectorAll('[data-user-location]').forEach(el => el.textContent = location);

    // Profile avatar initials
    document.querySelectorAll('.profile-avatar').forEach(el => {
        const initials = name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
        el.textContent = initials;
    });
});

// ── Profile dropdown toggle ──────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.profile-avatar').forEach(btn => {
        const wrap     = btn.closest('.profile-wrap');
        const dropdown = wrap?.querySelector('.profile-dropdown');
        if (!dropdown) return;

        btn.addEventListener('click', e => {
            e.stopPropagation();
            dropdown.classList.toggle('open');
        });

        document.addEventListener('click', e => {
            if (!wrap.contains(e.target)) dropdown.classList.remove('open');
        });
    });
});

// ── Hackathon / job card filter ──────────────────────────────
function filterCards(selectId, containerSelector, attr) {
    const val  = document.getElementById(selectId)?.value;
    const cards = document.querySelectorAll(containerSelector);
    cards.forEach(c => {
        const match = !val || val === 'all' || c.dataset[attr] === val;
        c.style.display = match ? '' : 'none';
    });
}

// ── Animate score ring ───────────────────────────────────────
function animateRing(ringId, textId, score, colorClass) {
    const ring = document.getElementById(ringId);
    const text = document.getElementById(textId);
    if (!ring || !text) return;

    // Set color class
    ring.className = `ring-fill ${colorClass || 'green'}`;
    ring.setAttribute('stroke-dasharray', '0, 100');
    text.textContent = '0%';

    setTimeout(() => {
        ring.setAttribute('stroke-dasharray', `${score}, 100`);
    }, 100);

    let current = 0;
    const interval = setInterval(() => {
        if (current >= score) {
            clearInterval(interval);
            text.textContent = `${score}%`;
        } else {
            current++;
            text.textContent = `${current}%`;
        }
    }, 12);
}

// ── Chart.js radar (dashboard only) ─────────────────────────
let skillChart;
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('skillChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    skillChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Skills', 'Experience', 'Projects', 'JD Match', 'Quality'],
            datasets: [{
                label: 'Your Profile',
                data: [0, 0, 0, 0, 0],
                backgroundColor: 'rgba(99,179,237,0.15)',
                borderColor: '#63b3ed',
                pointBackgroundColor: '#63b3ed',
                pointBorderColor: '#fff',
                borderWidth: 2,
                pointRadius: 4,
            }, {
                label: 'Ideal Profile',
                data: [90, 85, 80, 88, 75],
                backgroundColor: 'rgba(167,139,250,0.05)',
                borderColor: 'rgba(167,139,250,0.4)',
                borderDash: [5, 5],
                borderWidth: 1.5,
                pointRadius: 3,
                pointBackgroundColor: 'rgba(167,139,250,0.5)',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                r: {
                    angleLines:  { color: 'rgba(255,255,255,0.06)' },
                    grid:        { color: 'rgba(255,255,255,0.06)' },
                    pointLabels: { color: '#6b7a99', font: { family: 'DM Sans', size: 11 } },
                    ticks:       { display: false, max: 100, min: 0 }
                }
            },
            plugins: {
                legend: {
                    labels: { color: '#f0f4ff', font: { family: 'DM Sans', size: 11 }, boxWidth: 12 }
                }
            }
        }
    });
});

// ── Upload resume → Flask API ────────────────────────────────
async function uploadResume() {
    const fileInput = document.getElementById('resume-upload');
    if (!fileInput || !fileInput.files[0]) {
        alert('Please select a PDF resume first.');
        return;
    }

    const file = fileInput.files[0];
    const label = document.getElementById('upload-label');
    if (label) { label.textContent = '⏳ Scanning...'; }

    const formData = new FormData();
    formData.append('file', file);

    // Optionally attach job description if present on the page
    const jdInput = document.getElementById('job-description');
    if (jdInput?.value?.trim()) {
        formData.append('job_description', jdInput.value.trim());
    }

    try {
        const res  = await fetch('http://127.0.0.1:5000/api/upload', { method: 'POST', body: formData });
        if (!res.ok) throw new Error('Server error');
        const data = await res.json();

        // Score ring
        const score = data.match_score;
        const color = score >= 75 ? 'green' : score >= 55 ? 'blue' : 'red';
        animateRing('score-ring', 'score-text', score, color);

        // Status
        const statusEl = document.getElementById('status-text');
        if (statusEl) {
            statusEl.innerHTML = `<strong>ATS Status:</strong> <span class="badge ${score >= 65 ? 'badge-green' : 'badge-red'}">${data.status}</span>`;
        }

        // Radar chart
        if (skillChart && data.radar_scores) {
            skillChart.data.datasets[0].data = data.radar_scores;
            skillChart.update();
        }

        // Strengths
        const str = document.getElementById('strengths-list');
        if (str) {
            str.innerHTML = data.strengths?.length
                ? data.strengths.map(s => `<span class="badge badge-green">✓ ${s}</span>`).join('')
                : `<span class="badge badge-blue">Keep scanning…</span>`;
        }

        // Weak points — build from TARGET_SKILLS not in strengths
        const weak = document.getElementById('weak-list');
        if (weak) {
            const gaps = data.weak_points || [];
            weak.innerHTML = gaps.length
                ? gaps.map(s => `<span class="badge badge-red">✗ ${s}</span>`).join('')
                : `<span class="badge badge-green">No major gaps found!</span>`;
        }

        // Recommendations / projects
        const proj = document.getElementById('recs-list');
        if (proj) {
            proj.innerHTML = data.recommendations?.length
                ? data.recommendations.map(r => `<li>🚀 ${r}</li>`).join('')
                : '<li>Looking great! Tailor resume per each role.</li>';
        }

    } catch (err) {
        console.error('Upload error:', err);
        const statusEl = document.getElementById('status-text');
        if (statusEl) statusEl.innerHTML = `<span class="badge badge-red">⚠ Could not reach server</span>`;
    } finally {
        fileInput.value = '';
        if (label) label.textContent = '📄 Upload Resume';
    }
}

// Auto-trigger upload when file is selected
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('resume-upload')?.addEventListener('change', uploadResume);
});
