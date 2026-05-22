// ==========================================================================
// CONFIGURATION & GLOBAL STATE SYSTEM
// ==========================================================================
const API_BASE_URL = `${window.location.origin}/api`;
let currentView = "section-home";
let activeDifficultyFilter = "all";

// Initialization routine when document loads
document.addEventListener("DOMContentLoaded", () => {
    initAppRouting();
    setupFormListeners();
    checkExistingAuth();
    setupFilterChips();
});

// ==========================================================================
// ROUTING & NAVIGATION FRAMEWORK
// ==========================================================================
function navigateTo(sectionId) {
    // Hide all view screens
    const sections = document.querySelectorAll("main.spa-content > section");
    sections.forEach(sec => sec.style.display = "none");

    // Enable visibility for targeted view
    const activeSection = document.getElementById(sectionId);
    if (activeSection) {
        activeSection.style.display = "block";
        currentView = sectionId;
    }

    // Trigger data fetch pipelines based on current views mapping
    if (sectionId === "section-dashboard") loadDashboardData();
    if (sectionId === "section-skills") loadSkillsManagerData();
    if (sectionId === "section-tasks") loadAvailableTasks();
    if (sectionId === "section-leaderboard") loadGlobalLeaderboard();
    if (sectionId === "section-admin") loadAdminConsoleData();
}

function initAppRouting() {
    window.addEventListener("hashchange", () => {
        const hash = window.location.hash.replace("#", "");
        if (hash) navigateTo(hash);
    });
}

// ==========================================================================
// UI GLOBAL NOTIFICATION SYSTEMS
// ==========================================================================
function toggleSpinner(show) {
    document.getElementById("loading-spinner").style.display = show ? "flex" : "none";
}

function showToast(message, type = "success") {
    const toast = document.getElementById("toast");
    const toastMsg = document.getElementById("toast-message");
    
    toast.className = type; 
    toastMsg.textContent = message;
    toast.style.display = "block";
    
    setTimeout(() => {
        toast.style.display = "none";
    }, 4000);
}

// ==========================================================================
// AUTHENTICATION AND ACCESS control
// ==========================================================================
function checkExistingAuth() {
    const token = localStorage.getItem("token");
    const role = localStorage.getItem("role");
    const name = localStorage.getItem("name");

    if (token && role) {
        document.getElementById("auth-logged-out").style.display = "none";
        document.getElementById("auth-logged-in").style.display = "flex";
        document.getElementById("user-display-name").textContent = `👤 ${name}`;
        
        if (role === "admin") {
            document.getElementById("nav-admin").style.display = "inline-block";
        } else {
            document.getElementById("nav-admin").style.display = "none";
        }
        navigateTo("section-dashboard");
    } else {
        performClientSignout();
    }
}

function performClientSignout() {
    localStorage.clear();
    document.getElementById("auth-logged-out").style.display = "flex";
    document.getElementById("auth-logged-in").style.display = "none";
    document.getElementById("nav-admin").style.display = "none";
    navigateTo("section-home");
}

document.getElementById("btn-logout").addEventListener("click", performClientSignout);

// ==========================================================================
// HTTP FORM HANDLERS (SUBMISSIONS & PAYLOADS)
// ==========================================================================
function setupFormListeners() {
    // User login process pipeline
    document.getElementById("form-login").addEventListener("submit", async (e) => {
        e.preventDefault();
        toggleSpinner(true);
        
        const payload = {
            email: document.getElementById("login-email").value,
            password: document.getElementById("login-password").value,
            role: document.getElementById("login-role").value
        };

        try {
            const res = await fetch(`${API_BASE_URL}/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            
            if (res.ok) {
                localStorage.setItem("token", data.access_token);
                localStorage.setItem("role", data.role);
                localStorage.setItem("name", data.name);
                localStorage.setItem("user_id", data.user_id);
                showToast("Authenticated successfully. Welcome!");
                checkExistingAuth();
            } else {
                showToast(data.detail || "Authentication mapping failure.", "error");
            }
        } catch (err) {
            showToast("Server configuration connection failure.", "error");
        } finally {
            toggleSpinner(false);
        }
    });

    // User system onboarding pipeline registration
    document.getElementById("form-register").addEventListener("submit", async (e) => {
        e.preventDefault();
        const pwd = document.getElementById("reg-password").value;
        const cpwd = document.getElementById("reg-confirm-password").value;

        if (pwd !== cpwd) {
            showToast("Password confirmation inputs mismatch.", "error");
            return;
        }

        toggleSpinner(true);
        const selectedRole = document.querySelector('input[name="reg-role"]:checked').value;
        const payload = {
            full_name: `${document.getElementById("reg-firstname").value} ${document.getElementById("reg-lastname").value}`,
            email: document.getElementById("reg-email").value,
            password: pwd,
            role: selectedRole,
            roll_number: `SE-${Math.floor(1000 + Math.random() * 9000)}`
        };

        try {
            const res = await fetch(`${API_BASE_URL}/auth/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();

            if (res.ok) {
                showToast("Account established completely. Proceed to login workspace.");
                navigateTo("section-login");
            } else {
                showToast(data.detail || "Registration processing denied.", "error");
            }
        } catch (err) {
            showToast("Network pipeline initialization failure.", "error");
        } finally {
            toggleSpinner(false);
        }
    });

    // Skill matrix logging injection form submission
    document.getElementById("form-add-skill").addEventListener("submit", async (e) => {
        e.preventDefault();
        toggleSpinner(true);

        const payload = {
            skill_id: parseInt(document.getElementById("new-skill-category").value),
            proficiency_level: document.getElementById("new-skill-level").value,
            proficiency_percent: document.getElementById("new-skill-level").value === "Beginner" ? 35 : document.getElementById("new-skill-level").value === "Intermediate" ? 65 : 95
        };

        try {
            const res = await fetch(`${API_BASE_URL}/skills/add`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${localStorage.getItem("token")}`
                },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                showToast("Skill added to profile matrix.");
                loadSkillsManagerData();
            } else {
                const errData = await res.json();
                showToast(errData.detail || "Error logging skill metadata.", "error");
            }
        } catch (err) {
            showToast("Failed syncing skill infrastructure.", "error");
        } finally {
            toggleSpinner(false);
        }
    });

    // SANDBOX COMPONENT INLINE DIRECT RAW CODE SUBMISSION FOR TESTING
    document.getElementById("form-testing-submission").addEventListener("submit", async (e) => {
        e.preventDefault();
        toggleSpinner(true);

        const payload = {
            app_id: parseInt(document.getElementById("submit-task-app-id").value),
            submission_text: document.getElementById("submit-raw-code").value
        };

        try {
            const res = await fetch(`${API_BASE_URL}/tasks/submit`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${localStorage.getItem("token")}`
                },
                body: JSON.stringify(payload)
            });
            
            if (res.ok) {
                showToast("Code logic dispatched successfully to Admin Evaluation Queue!");
                document.getElementById("testing-submission-workspace").style.display = "none";
                document.getElementById("submit-raw-code").value = "";
                loadAvailableTasks();
            } else {
                const data = await res.json();
                showToast(data.detail || "Submission tracking failure.", "error");
            }
        } catch (err) {
            showToast("Communication line with testing engine failed.", "error");
        } finally {
            toggleSpinner(false);
        }
    });

    // Copilot AI chatbot thread execution handling
    document.getElementById("form-chat-input").addEventListener("submit", async (e) => {
        e.preventDefault();
        const msgBox = document.getElementById("chat-user-textbox");
        const msg = msgBox.value.trim();
        if (!msg) return;

        appendChatBubble(msg, "user-msg");
        msgBox.value = "";
        
        const loader = document.getElementById("ai-typing-loader");
        loader.style.display = "flex";

        try {
            const res = await fetch(`${API_BASE_URL}/ai/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${localStorage.getItem("token")}`
                },
                body: JSON.stringify({ message: msg })
            });
            const data = await res.json();
            if (res.ok) {
                appendChatBubble(data.reply, "ai-msg");
            } else {
                appendChatBubble("Error communicating with AI runtime server instance.", "ai-msg");
            }
        } catch {
            appendChatBubble("AI compilation network failure channel.", "ai-msg");
        } finally {
            loader.style.display = "none";
        }
    });

    // Admin blueprint pipeline creator engine
    document.getElementById("form-admin-create-task").addEventListener("submit", async (e) => {
        e.preventDefault();
        toggleSpinner(true);

        const payload = {
            title: document.getElementById("admin-task-title").value,
            description: document.getElementById("admin-task-desc").value,
            difficulty: document.getElementById("admin-task-diff").value,
            reward_xp: parseInt(document.getElementById("admin-task-xp").value),
            required_skills: [parseInt(document.getElementById("admin-task-skill-select").value)]
        };

        try {
            const res = await fetch(`${API_BASE_URL}/admin/create-task`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${localStorage.getItem("token")}`
                },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                showToast("Task blueprint deployed to available student workspace matrix maps.");
                document.getElementById("admin-task-title").value = "";
                document.getElementById("admin-task-desc").value = "";
                loadAdminConsoleData();
            }
        } catch {
            showToast("Deployment pipeline fault block.", "error");
        } finally {
            toggleSpinner(false);
        }
    });
}

// ==========================================================================
// CORE DATA FETCH PIPELINES & RENDERING DYNAMICS
// ==========================================================================

async function loadDashboardData() {
    if (localStorage.getItem("role") === "admin") return;
    
    try {
        // Fetch applied apps metric state array to map counts completely
        const resApps = await fetch(`${API_BASE_URL}/tasks/my-applications`, {
            headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
        });
        const apps = resApps.ok ? await resApps.json() : [];
        const completedCount = apps.filter(a => a.status === 'completed').length;
        document.getElementById("stat-tasks-count").textContent = completedCount;

        // Fetch user active skills array details
        const resSk = await fetch(`${API_BASE_URL}/skills/my-skills`, {
            headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
        });
        const skills = resSk.ok ? await resSk.json() : [];
        document.getElementById("stat-skills-count").textContent = skills.length;

        // Dynamic XP Calculation based on completed application records profiles array list
        let calculatedXp = 0;
        apps.forEach(app => {
            if (app.status === "completed") {
                calculatedXp += app.reward_xp || 0;
            }
        });
        
        document.getElementById("user-current-xp").textContent = calculatedXp;

        // Manage Level progress bar computations dynamically
        let rankStr = "Level 1 Novice Engineer";
        let targetXp = 500;
        let fillPct = (calculatedXp / targetXp) * 100;

        if (calculatedXp >= 500 && calculatedXp < 1200) {
            rankStr = "Level 2 Competent System Engineer";
            targetXp = 1200;
            fillPct = (calculatedXp / targetXp) * 100;
        } else if (calculatedXp >= 1200) {
            rankStr = "Level 3 Senior Enterprise Architect Consultant";
            targetXp = calculatedXp + 500; 
            fillPct = 100;
        }

        document.getElementById("user-current-rank").textContent = rankStr;
        document.getElementById("user-needed-xp").textContent = targetXp;
        document.getElementById("user-xp-bar").style.width = `${Math.min(fillPct, 100)}%`;
        document.getElementById("user-next-rank").textContent = `XP Milestone Track: (${calculatedXp}/${targetXp} XP Completed)`;

        // Render dashboard linear metrics bars stack component UI rendering pipeline
        const dashboardSkContainer = document.getElementById("dashboard-skills-container");
        dashboardSkContainer.innerHTML = skills.length === 0 ? "<p style='color:var(--text-muted); font-size:0.9rem;'>No verified tracking metrics on profile.</p>" : "";
        
        skills.forEach(sk => {
            const color = sk.proficiency_level === "Advanced" ? "var(--teal)" : sk.proficiency_level === "Intermediate" ? "var(--purple)" : "var(--amber)";
            dashboardSkContainer.innerHTML += `
                <div class="skill-progress-item">
                   <div class="skill-meta"><span>${sk.skill_name}</span><strong style="color:${color}">${sk.proficiency_level}</strong></div>
                   <div class="bar-bg"><div class="bar-fill" style="width: ${sk.proficiency_percent}%; background-color: ${color}"></div></div>
                </div>`;
        });

        // Load automated system AI engine recommendations matching framework matrix list block
        const resRec = await fetch(`${API_BASE_URL}/match/recommend`, {
            headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
        });
        const recs = resRec.ok ? await resRec.json() : [];
        const recContainer = document.getElementById("dashboard-rec-container");
        recContainer.innerHTML = recs.length === 0 ? "<p style='color:var(--text-muted); font-size:0.9rem;'>Add skills to initialize AI recommendation models.</p>" : "";
        
        recs.forEach(task => {
            recContainer.innerHTML += `
                <div style="background:#0b0c13; padding:0.75rem; border-radius:6px; margin-bottom:0.75rem; border-left:3px solid var(--purple);">
                   <div style="display:flex; justify-content:space-between; font-size:0.85rem;"><span style="color:var(--text-muted)">Match Confidence: ${task.match_percent}%</span><span style="color:var(--teal)">+${task.reward_xp} XP</span></div>
                   <h4 style="margin:2px 0; color:#fff">${task.title}</h4>
                   <button class="btn btn-purple btn-sm" style="margin-top:5px; width:100%; padding:2px;" onclick="navigateTo('section-tasks')">View Blueprint</button>
                </div>`;
        });

    } catch (err) {
        console.error("Dashboard engine rendering failure:", err);
    }
}

async function loadSkillsManagerData() {
    try {
        // Dynamic fetch of master skills dropdown list records profiles array configuration matrix
        const resAll = await fetch(`${API_BASE_URL}/skills/all`);
        const allSkills = await resAll.json();
        
        const dropdown = document.getElementById("new-skill-category");
        dropdown.innerHTML = "";
        allSkills.forEach(s => {
            dropdown.innerHTML += `<option value="${s.skill_id}">${s.skill_name} [${s.category}]</option>`;
        });

        // Load dynamic verification user skills items matrix container cards grid row
        const resMy = await fetch(`${API_BASE_URL}/skills/my-skills`, {
            headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
        });
        const mySkills = await resMy.json();
        const container = document.getElementById("skills-matrix-container");
        container.innerHTML = mySkills.length === 0 ? "<p style='color:var(--text-muted)'>Workspace tracking register holds zero mapped skills.</p>" : "";

        mySkills.forEach(sk => {
            container.innerHTML += `
               <div class="matrix-card" style="background: var(--bg-card); padding:1rem; border-radius:8px; border:1px solid var(--border-color);">
                  <span class="badge badge-hot" style="margin-bottom:5px;">MAPPED INDEX</span>
                  <h3>${sk.skill_name}</h3>
                  <p style="color: var(--text-muted); font-size:0.9rem; margin: 5px 0;">Proficiency Track Level: <b style="color:var(--purple)">${sk.proficiency_level}</b></p>
                  <button class="btn btn-danger btn-sm" style="margin-top:10px; width:100%" onclick="deleteSkillMapping(${sk.user_skill_id})">Purge Skill</button>
               </div>`;
        });
    } catch (err) {
        showToast("Error processing skills setup infrastructure layout pipelines.", "error");
    }
}

async function deleteSkillMapping(id) {
    if (!confirm("Are you certain you want to purge this skill profile metrics trace reference?")) return;
    toggleSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/skills/delete`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem("token")}`
            },
            body: JSON.stringify({ user_skill_id: id })
        });
        if (res.ok) {
            showToast("Skill structure mapping removed safely.");
            loadSkillsManagerData();
        }
    } catch {
        showToast("System failed processing data transaction request delete workflow.", "error");
    } finally {
        toggleSpinner(false);
    }
}

async function loadAvailableTasks() {
    try {
        const resTasks = await fetch(`${API_BASE_URL}/tasks/all`, {
            headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
        });
        const tasks = await resTasks.json();

        const resApps = await fetch(`${API_BASE_URL}/tasks/my-applications`, {
            headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
        });
        const apps = await resApps.json();

        // Establish quick lookup database dictionaries mapping array values lists state flags object maps
        const appStateMap = {};
        const appTextMap = {};
        apps.forEach(a => {
            appStateMap[a.title] = a.status; // Mapping through structural entity title references safely
            appTextMap[a.title] = a.app_id;
        });

        const container = document.getElementById("tasks-cards-container");
        container.innerHTML = "";

        tasks.forEach(task => {
            // Apply filtering mechanics configurations rules blocks sequentially
            if (activeDifficultyFilter !== "all" && task.difficulty !== activeDifficultyFilter) return;

            const currentStatus = appStateMap[task.title] || "unapplied";
            
            let operationalActionButtonHTML = "";
            if (currentStatus === "unapplied") {
                operationalActionButtonHTML = `<button class="btn btn-purple" style="width:100%; margin-top:auto;" onclick="applyForTaskBlueprint(${task.task_id})">Accept Code Sprint Task</button>`;
            } else if (currentStatus === "pending") {
                operationalActionButtonHTML = `
                    <div style="margin-top:auto; display:flex; flex-direction:column; gap:5px;">
                       <span class="badge badge-hot" style="text-align:center; padding:5px;">IN REVIEW UNDER EVALUATION</span>
                       <button class="btn btn-success btn-sm" onclick="openTestingSandboxWorkspace(${appTextMap[task.title]})">Update/Resubmit Raw Code</button>
                    </div>`;
            } else if (currentStatus === "completed") {
                operationalActionButtonHTML = `<button class="btn btn-outline" style="width:100%; margin-top:auto; border-color:var(--teal); color:var(--teal); cursor:default;" disabled>✓ Task Approved & XP Awarded</button>`;
            } else if (currentStatus === "rejected") {
                operationalActionButtonHTML = `
                    <div style="margin-top:auto; display:flex; flex-direction:column; gap:5px;">
                       <span class="badge btn-danger" style="text-align:center; padding:5px;">REJECTED BY CODE AUDITOR</span>
                       <button class="btn btn-purple btn-sm" onclick="openTestingSandboxWorkspace(${appTextMap[task.title]})">Submit Corrected Code Script</button>
                    </div>`;
            }

            container.innerHTML += `
               <div class="task-card">
                  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                     <span class="badge ${task.difficulty==='Advanced'?'badge-hot':'badge-success'}">${task.difficulty}</span>
                     <strong style="color:var(--teal)">+${task.reward_xp} XP</strong>
                  </div>
                  <h3>${task.title}</h3>
                  <p style="color:var(--text-muted); font-size:0.9rem; margin:10px 0; line-height:1.4;">${task.description}</p>
                  ${operationalActionButtonHTML}
               </div>`;
        });

    } catch (err) {
        showToast("Error configuring tasks interface dashboard panels.", "error");
    }
}

function setupFilterChips() {
    const chips = document.querySelectorAll("#difficulty-chips .chip");
    chips.forEach(chip => {
        chip.addEventListener("click", () => {
            chips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            activeDifficultyFilter = chip.getAttribute("data-filter");
            loadAvailableTasks();
        });
    });

    // In-line instant search bar event tracking configuration metrics setup routines
    document.getElementById("task-search-input").addEventListener("input", (e) => {
        const query = e.target.value.toLowerCase().trim();
        const cards = document.querySelectorAll("#tasks-cards-container .task-card");
        cards.forEach(card => {
            const title = card.querySelector("h3").textContent.toLowerCase();
            card.style.display = title.includes(query) ? "flex" : "none";
        });
    });
}

async function applyForTaskBlueprint(taskId) {
    toggleSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/tasks/apply`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem("token")}`
            },
            body: JSON.stringify({ task_id: taskId })
        });
        if (res.ok) {
            showToast("Task assigned completely. Code Workspace Sandbox unlocked below!");
            loadAvailableTasks();
        } else {
            const d = await res.json();
            showToast(d.detail || "Error claiming blueprint entity mapping.", "error");
        }
    } catch {
        showToast("Claim system transactional processing error.", "error");
    } finally {
        toggleSpinner(false);
    }
}

// TOGGLE VISIBILITY INTERFACE FUNCTION FOR EMBEDDED CODE/TEXT AREA BOX
function openTestingSandboxWorkspace(applicationId) {
    document.getElementById("submit-task-app-id").value = applicationId;
    document.getElementById("testing-submission-workspace").style.display = "block";
    document.getElementById("submit-raw-code").focus();
    
    // Smooth scroll down layout focus logic view
    document.getElementById("testing-submission-workspace").scrollIntoView({ behavior: "smooth" });
}

async function loadGlobalLeaderboard() {
    try {
        const res = await fetch(`${API_BASE_URL}/leaderboard/global`, {
            headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
        });
        const data = await res.json();
        const tbody = document.getElementById("leaderboard-entries");
        tbody.innerHTML = "";

        if (!data.ranking || data.ranking.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" style="padding:15px; text-align:center; color:var(--text-muted)">Syncing ranking tracking indexes metrics databases complete...</td></tr>`;
            return;
        }

        data.ranking.forEach((user, index) => {
            const rank = index + 1;
            let rowStyle = "";
            let rankMedal = rank;
            
            if (rank === 1) { rowStyle = "background:rgba(255,179,0,0.05); font-weight:bold;"; rankMedal = "🥇 1"; }
            else if (rank === 2) { rowStyle = "background:rgba(255,255,255,0.02);"; rankMedal = "🥈 2"; }
            else if (rank === 3) { rankMedal = "🥉 3"; }

            tbody.innerHTML += `
               <tr style="border-bottom:1px solid var(--border-color); ${rowStyle}">
                  <td style="padding:12px; color:var(--amber)"><b>${rankMedal}</b></td>
                  <td style="padding:12px; color:#fff">${user.name}</td>
                  <td style="padding:12px;"><span class="chip" style="padding:2px 8px; cursor:default;">${user.role.toUpperCase()}</span></td>
                  <td style="padding:12px; color:var(--teal)"><b>${user.xp} XP</b></td>
               </tr>`;
        });
    } catch {
        showToast("Error processing data from leaderboard endpoint matrix pipeline.", "error");
    }
}

function appendChatBubble(text, className) {
    const box = document.getElementById("chat-stream-box");
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${className}`;
    
    // Formatting code chunks blocks within chat display modules safely
    if (className === "ai-msg") {
        bubble.innerHTML = `<div><b>Copilot AI:</b><p style="white-space:pre-wrap; margin-top:4px; font-size:0.95rem;">${text}</p></div>`;
    } else {
        bubble.innerHTML = `<div><b>You:</b><p style="margin-top:2px;">${text}</p></div>`;
    }
    
    box.appendChild(bubble);
    box.scrollTop = box.scrollHeight;
}

// ==========================================================================
// ADMIN CONSOLE INTERFACE CONTROLLERS MODULES
// ==========================================================================
async function loadAdminConsoleData() {
    if (localStorage.getItem("role") !== "admin") return;

    try {
        // Dropdown skill selection initialization inside system admin task creator panel container
        const resAllSk = await fetch(`${API_BASE_URL}/skills/all`);
        const allSk = await resAllSk.json();
        const adminDropdown = document.getElementById("admin-task-skill-select");
        adminDropdown.innerHTML = "";
        allSk.forEach(s => {
            adminDropdown.innerHTML += `<option value="${s.skill_id}">${s.skill_name} [${s.category}]</option>`;
        });

        // Load system state counters metrics panels rows values indices positions completely
        const resStats = await fetch(`${API_BASE_URL}/admin/stats`, {
            headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
        });
        const stats = await resStats.json();
        document.getElementById("admin-stat-students").textContent = stats.students || 0;
        document.getElementById("admin-stat-pending").textContent = stats.pending || 0;
        document.getElementById("admin-stat-tasks").textContent = stats.tasks || 0;

        // Fetch blueprints list layout rows setup tracking components
        const resTasks = await fetch(`${API_BASE_URL}/tasks/all`, {
            headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
        });
        const tasks = await resTasks.json();
        const tasksTbody = document.getElementById("admin-tasks-tbody");
        tasksTbody.innerHTML = "";
        tasks.forEach(t => {
            tasksTbody.innerHTML += `
               <tr style="border-bottom:1px solid var(--border-color)">
                  <td style="padding:10px; color:var(--text-muted)">#${t.task_id}</td>
                  <td style="padding:10px; font-weight:600; color:#fff">${t.title}</td>
                  <td style="padding:10px;"><span class="badge badge-success">${t.difficulty}</span></td>
                  <td style="padding:10px; color:var(--teal)">${t.reward_xp} XP</td>
                  <td style="padding:10px;"><button class="btn btn-danger btn-sm" onclick="purgeTaskBlueprintByAdmin(${t.task_id})">Delete Blueprint</button></td>
               </tr>`;
        });

        // FIXED: Display raw code block artifacts directly inside admin audit panel dashboard grids rows elements list view 
        const resSubs = await fetch(`${API_BASE_URL}/admin/submissions`, {
            headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
        });
        const subs = await resSubs.json();
        const subsTbody = document.getElementById("admin-submissions-tbody");
        subsTbody.innerHTML = "";

        if (subs.length === 0) {
            subsTbody.innerHTML = `<tr><td colspan="4" style="padding:15px; text-align:center; color:var(--text-muted)">Submission evaluation queue register is currently empty.</td></tr>`;
            return;
        }

        subs.forEach(sub => {
            // Escape code elements block structures text characters string elements strings arrays safely to block browser scripts parsing execution
            const safeCodeSnippet = (sub.submission_text || "/* Empty Code Element Body */")
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;");

            subsTbody.innerHTML += `
               <tr style="border-bottom:1px solid var(--border-color)">
                  <td style="padding:10px; color:var(--purple)"><b>${sub.student_email}</b><br><small style="color:var(--text-muted)">${sub.student_name || 'Student'}</small></td>
                  <td style="padding:10px; color:#fff">${sub.task_title}</td>
                  <td style="padding:10px;">
                     <div class="code-preview-box">${safeCodeSnippet}</div>
                  </td>
                  <td style="padding:10px;">
                     <div style="display:flex; gap:5px;">
                        <button class="btn btn-success btn-sm" onclick="reviewStudentSubmissionArtifact(${sub.app_id}, 'approve')">Approve Work</button>
                        <button class="btn btn-danger btn-sm" onclick="reviewStudentSubmissionArtifact(${sub.app_id}, 'reject')">Reject</button>
                     </div>
                  </td>
               </tr>`;
        });

    } catch (err) {
        console.error("Administrative management console initialization fault error tracking sequence exception:", err);
    }
}

async function reviewStudentSubmissionArtifact(applicationId, actionDecisionString) {
    toggleSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/admin/review`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem("token")}`
            },
            body: JSON.stringify({ app_id: applicationId, action: actionDecisionString })
        });
        if (res.ok) {
            showToast(`Submission successfully transitioned to: ${actionDecisionString.toUpperCase()}`);
            loadAdminConsoleData();
        }
    } catch {
        showToast("Error logging evaluation decision audit.", "error");
    } finally {
        toggleSpinner(false);
    }
}

async function purgeTaskBlueprintByAdmin(taskId) {
    if (!confirm("Are you certain you want to permanently delete this master task blueprint? This action is irreversible.")) return;
    toggleSpinner(true);
    try {
        const res = await fetch(`${API_BASE_URL}/admin/delete-task/${taskId}`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
        });
        if (res.ok) {
            showToast("Master task blueprint completely deleted.");
            loadAdminConsoleData();
        } else {
            const data = await res.json();
            showToast(data.detail || "Error wiping database blueprint.", "error");
        }
    } catch {
        showToast("Purge transmission routine failure.", "error");
    } finally {
        toggleSpinner(false);
    }
}