// --- DYNAMIC CARD LIGHTING (Mouse Tracking) ---
document.addEventListener("DOMContentLoaded", () => {
    const cards = document.querySelectorAll(".card");
    cards.forEach(card => {
        card.onmousemove = e => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            card.style.setProperty("--mouse-x", `${x}px`);
            card.style.setProperty("--mouse-y", `${y}px`);
        };
    });
});

// --- CHART.JS SETUP (The Radar Graph) ---
let skillChart;
document.addEventListener("DOMContentLoaded", () => {
    const ctx = document.getElementById('skillChart').getContext('2d');
    skillChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Databases', 'Backend/Java', 'System Design', 'Algorithms', 'Cloud'],
            datasets: [{
                label: 'Your Profile',
                data: [0, 0, 0, 0, 0], // Starts at Zero, updates on upload
                backgroundColor: 'rgba(59, 130, 246, 0.3)',
                borderColor: '#3b82f6',
                pointBackgroundColor: '#3b82f6',
                pointBorderColor: '#fff',
                borderWidth: 2,
            }, {
                label: 'Ideal Backend Role',
                data: [90, 85, 80, 95, 75], // The baseline to compare against
                backgroundColor: 'rgba(148, 163, 184, 0.05)',
                borderColor: '#64748b',
                borderDash: [5, 5],
                borderWidth: 1,
            }]
        },
        options: {
            scales: {
                r: {
                    angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    pointLabels: { color: '#94a3b8', font: { family: 'Inter', size: 10 } },
                    ticks: { display: false, max: 100, min: 0 }
                }
            },
            plugins: { legend: { labels: { color: '#f8fafc', font: { family: 'Inter' } } } }
        }
    });
});

// --- PROFILE DROPDOWN LOGIC ---
document.addEventListener("DOMContentLoaded", () => {
    const profileBtn = document.getElementById('profile-btn');
    const dropdown = document.getElementById('profile-dropdown');

    // Toggle menu when clicking the icon
    if(profileBtn && dropdown) {
        profileBtn.addEventListener('click', (e) => {
            e.stopPropagation(); 
            dropdown.classList.toggle('active');
        });

        // Close menu if user clicks anywhere else on the page
        window.addEventListener('click', (e) => {
            if (!dropdown.contains(e.target) && e.target !== profileBtn) {
                dropdown.classList.remove('active');
            }
        });
    }
});

// --- THE MAIN UPLOAD FUNCTION ---
async function uploadToPython() {
    const fileInput = document.getElementById('resume-upload');
    if (!fileInput) return;
    
    const file = fileInput.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    const uploadLabel = document.getElementById('upload-btn-label');
    uploadLabel.innerText = "⏳ Scanning PDF...";
    document.getElementById('score-text').innerText = "...";

    try {
        const response = await fetch("http://127.0.0.1:5000/api/upload", {
            method: "POST",
            body: formData
        });

        if (!response.ok) throw new Error("Server Error");

        const data = await response.json();

        // 1. Animate the Circular Score
        const score = data.match_score;

        // Animate circular stroke
    const circle = document.getElementById("score-circle");
const scoreText = document.getElementById("score-text");

// Reset first
circle.setAttribute("stroke-dasharray", `0, 100`);
scoreText.textContent = "0%";

// Animate ring
setTimeout(() => {
    circle.setAttribute("stroke-dasharray", `${score}, 100`);
}, 100);

// Animate number smoothly
let current = 0;
const speed = 15; // lower = faster

const counter = setInterval(() => {
    if (current >= score) {
        clearInterval(counter);
        scoreText.textContent = `${score}%`;
    } else {
        current++;
        scoreText.textContent = `${current}%`;
    }
}, speed);

    // Update status
    document.getElementById("status-text").innerHTML =
    `<strong>ATS Status:</strong> 
     <span style="color: var(--accent-green);">${data.status}</span>`;

        // 2. Animate the Radar Chart (Using REAL data from Python)
        skillChart.data.datasets[0].data = data.radar_scores; 
        skillChart.update(); 

        // 3. Update Status
        document.getElementById('status-text').innerHTML = `<strong>ATS Status:</strong> <span style="color: var(--accent-green);">${data.status}</span>`;

        // 4. Populate Neon Badges
        const strengthsList = document.getElementById('strengths-list');
        const weakPointsList = document.getElementById('weak-points-list');
        
        if(data.strengths.length > 0) {
            strengthsList.innerHTML = data.strengths.map(skill => `<span class="badge badge-green">✓ ${skill}</span>`).join('');
        } else {
            strengthsList.innerHTML = `<span class="badge" style="color: gray;">None detected</span>`;
        }
            
        if(data.weak_points.length > 0) {
            weakPointsList.innerHTML = data.weak_points.map(skill => `<span class="badge badge-red">✗ ${skill}</span>`).join('');
        } else {
            weakPointsList.innerHTML = `<span class="badge badge-green">No major gaps!</span>`;
        }
            
        // 5. Populate Projects List
        const projectsList = document.getElementById('projects-list');
        projectsList.innerHTML = data.recommendations.map(proj => `<li>🚀 ${proj}</li>`).join('');

    } catch (error) {
    console.error("REAL ERROR:", error);
    } finally {
        fileInput.value = ""; 
        uploadLabel.innerText = "🚀 Upload New Resume";
    }
}

// --- HACKATHON FILTER FUNCTION ---
function filterEvents() {
    const selectedCompany = document.getElementById('company-filter').value;
    const cards = document.querySelectorAll('.hack-card');
    cards.forEach(card => {
        const cardCompany = card.getAttribute('data-company');
        if (selectedCompany === 'all' || selectedCompany === cardCompany) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}