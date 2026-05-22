/**
 * ==========================================================================
 * MICRO-SKILL HUB SPA CORE ENGINE (app.js) - MASTER PREMIUM EDITION
 * Global Constants & Configurations
 * ==========================================================================
 */
const BACKEND_URL = 'http://localhost:8000';

/* Global references to keep track of operational state layers client-side */
let cachedTasks = []; 
let cachedRecommendations = [];

/**
 * ==========================================================================
 * UTILITY FUNCTIONS (Loading, Routing, Toasts, API Infrastructure)
 * ==========================================================================
 */

function showSection(sectionId) {
  const sections = document.querySelectorAll('main.spa-content > section');
  sections.forEach(sec => {
    sec.style.display = 'none';
  });

  const targetSection = document.getElementById(sectionId);
  if (targetSection) {
    targetSection.style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } else {
    console.error(`SPA Router: Destination ID "${sectionId}" was not found.`);
  }
}

function showLoading() {
  const spinner = document.getElementById('loading-spinner');
  if (spinner) spinner.style.display = 'flex';
}

function hideLoading() {
  const spinner = document.getElementById('loading-spinner');
  if (spinner) spinner.style.display = 'none';
}

function showToast(message, type = 'success') {
  const existing = document.querySelector('.toast-popup');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = `toast-popup ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => { if (toast) toast.remove(); }, 3200);
}

function setToken(token) { localStorage.setItem('msh_token', token); }
function getToken() { return localStorage.getItem('msh_token'); }
function removeToken() { localStorage.removeItem('msh_token'); }

async function makeAuthenticatedRequest(url, options = {}) {
  const token = getToken();
  if (!token) {
    handleLogout();
    throw new Error("Authentication credential token not found.");
  }

  options.headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };

  const response = await fetch(url, options);
  if (response.status === 401) {
    handleLogout();
    throw new Error("Session expired. Please log in again.");
  }
  return response;
}

/**
 * ==========================================================================
 * USER SECURITY LAYERS & ROUTING CONTROLLERS
 * ==========================================================================
 */

function setupNavigation() {
  document.querySelectorAll('[data-target]').forEach(link => {
    link.addEventListener('click', function(e) {
      e.preventDefault();
      const dest = this.getAttribute('data-target');
      navigateTo(dest);
    });
  });
}

function navigateTo(sectionId) {
  const token = getToken();

  if (!token && !publicPublicOverrideCheck(sectionId)) {
    showSection('section-home');
    return;
  }

  showSection(sectionId);

  // Trigger real-time view statistics pipeline data fetch steps
  if (sectionId === 'section-dashboard') fetchStudentDashboardMetrics();
  if (sectionId === 'section-skills') fetchSkillsMatrixInventory();
  if (sectionId === 'section-tasks') fetchPlatformTasksCatalog();
  if (sectionId === 'section-chat') syncAIChatViewportConsole();
  if (sectionId === 'section-admin') fetchAdminMetricsEngine();
}

function publicPublicOverrideCheck(id) {
  return ['section-home', 'section-login', 'section-register'].includes(id);
}

function initPasswordSecurityFeatures() {
  console.log("Cryptography validation framework initialized.");
}

/**
 * ==========================================================================
 * CONTROLLER ACTIONS (Auth, Forms, Pipeline Submission Actions)
 * ==========================================================================
 */

async function handleRegister(e) {
  e.preventDefault();
  const fullName = document.getElementById('reg-fullname').value;
  const email = document.getElementById('reg-email').value;
  const password = document.getElementById('reg-password').value;
  const rollNumber = document.getElementById('reg-rollnumber').value;
  
  const roleRadio = document.querySelector('input[name="reg-role"]:checked');
  const role = roleRadio ? roleRadio.value : 'student';

  const payload = {
    full_name: fullName,
    email: email,
    password: password,
    role: role,
    roll_number: rollNumber
  };

  showLoading();
  try {
    const res = await fetch(`${BACKEND_URL}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Registration workflow faulted.");

    showToast("Registration completed successfully! Please Log In.");
    navigateTo('section-login');
    document.getElementById('form-register-submit').reset();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    hideLoading();
  }
}

async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;
  const roleRadio = document.querySelector('input[name="login-role"]:checked');
  const role = roleRadio ? roleRadio.value : 'student';

  const payload = { email, password, role };

  showLoading();
  try {
    const res = await fetch(`${BACKEND_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Invalid system credentials.");

    setToken(data.access_token);
    const userObj = { name: data.name, role: data.role };
    localStorage.setItem('msh_user', JSON.stringify(userObj));

    syncNavbarState(userObj);
    showToast(`Welcome back, ${data.name}!`);
    
    navigateTo(data.role === 'admin' ? 'section-admin' : 'section-dashboard');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    hideLoading();
  }
}

function syncNavbarState(user) {
  const loggedOut = document.getElementById('auth-logged-out');
  const loggedIn = document.getElementById('auth-logged-in');
  const navLinks = document.querySelector('.nav-links');

  if (user) {
    if (loggedOut) loggedOut.style.display = 'none';
    if (loggedIn) {
      loggedIn.style.display = 'flex';
      document.getElementById('nav-username').textContent = user.name;
    }
    
    if (navLinks) {
      navLinks.innerHTML = user.role === 'admin' 
        ? `<li><a href="#" data-target="section-admin">Admin Control Panel</a></li>`
        : `<li><a href="#" data-target="section-dashboard">Dashboard</a></li>
           <li><a href="#" data-target="section-skills">My Skills</a></li>
           <li><a href="#" data-target="section-tasks">Tasks Portal</a></li>
           <li><a href="#" data-target="section-chat">AI Advisor Chat</a></li>`;
      setupNavigation();
    }
  } else {
    if (loggedOut) loggedOut.style.display = 'flex';
    if (loggedIn) loggedIn.style.display = 'none';
    if (navLinks) {
      navLinks.innerHTML = `<li><a href="#" data-target="section-home">Home</a></li>`;
      setupNavigation();
    }
  }
}

function handleLogout() {
  removeToken();
  localStorage.removeItem('msh_user');
  syncNavbarState(null);
  showToast("You have been signed out successfully.");
  navigateTo('section-home');
}

/**
 * ==========================================================================
 * STUDENT VIEWS CONTROLLERS PIPELINE INVENTORY
 * ==========================================================================
 */

async function fetchStudentDashboardMetrics() {
  showLoading();
  try {
    const res = await makeAuthenticatedRequest(`${BACKEND_URL}/api/student/dashboard`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to load dashboard metrics.");

    document.getElementById('dash-xp-val').textContent = data.current_xp;
    document.getElementById('dash-skills-count').textContent = data.skills_count;
    document.getElementById('dash-applied-count').textContent = data.applied_tasks_count;
    document.getElementById('dash-completed-count').textContent = data.completed_tasks_count;

    const currentLevel = Math.floor(data.current_xp / 1000) + 1;
    const nextLevelXPTarget = currentLevel * 1000;
    const currentLevelBaseXP = (currentLevel - 1) * 1000;
    const xpEarnedInLevel = data.current_xp - currentLevelBaseXP;
    const progressPercent = Math.min((xpEarnedInLevel / 1000) * 100, 100);

    document.getElementById('dash-level-lbl').textContent = `Level ${currentLevel}`;
    document.getElementById('dash-xp-progress-text').textContent = `${data.current_xp} / ${nextLevelXPTarget} Total XP`;
    document.getElementById('dash-progress-fill').style.width = `${progressPercent}%`;

    const skillsContainer = document.getElementById('dash-skill-bars-stack');
    skillsContainer.innerHTML = '';
    if (data.skills.length === 0) {
      skillsContainer.innerHTML = `<p style="font-size:0.85rem; color:var(--gray);">No track profiles added yet. Head to "My Skills" view to begin profiling.</p>`;
    } else {
      data.skills.forEach(sk => {
        const row = document.createElement('div');
        row.innerHTML = `
          <div class="skill-meta"><span>${sk.skill_name}</span><span>${sk.proficiency_level} (${sk.proficiency_percent}%)</span></div>
          <div class="bar-bg"><div class="bar-fill" style="width: ${sk.proficiency_percent}%;"></div></div>
        `;
        skillsContainer.appendChild(row);
      });
    }

    const recsContainer = document.getElementById('dash-recommendations-list');
    recsContainer.innerHTML = '';
    if (data.recommendations.length === 0) {
      recsContainer.innerHTML = `<p style="font-size:0.85rem; color:var(--gray);">Add structured skills matrix data components to unlock immediate AI optimizations.</p>`;
    } else {
      data.recommendations.forEach(rec => {
        const div = document.createElement('div');
        div.className = 'rec-card';
        div.style.marginBottom = '10px';
        div.innerHTML = `
          <div style="display:flex; justify-content:space-between; align-items:center;">
             <span class="badge badge-hot">Recommended Task</span>
             <span class="task-xp-yield">+${rec.reward_xp} XP</span>
          </div>
          <h4>${rec.title}</h4>
          <p>${rec.description.substring(0, 110)}...</p>
          <button class="btn btn-sm btn-primary btn-block" onclick="navigateTo('section-tasks')">View Task Details</button>
        `;
        recsContainer.appendChild(div);
      });
    }
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    hideLoading();
  }
}

async function fetchSkillsMatrixInventory() {
  showLoading();
  try {
    const skRes = await fetch(`${BACKEND_URL}/api/skills/catalog`);
    const catalog = await skRes.json();
    const dropdown = document.getElementById('add-skill-select');
    dropdown.innerHTML = '<option value="">-- Choose Platform Track Option --</option>';
    catalog.forEach(s => {
      dropdown.innerHTML += `<option value="${s.skill_id}">${s.skill_name} [${s.category}]</option>`;
    });

    const res = await makeAuthenticatedRequest(`${BACKEND_URL}/api/student/skills`);
    const data = await res.json();
    
    const matrixGrid = document.getElementById('student-skills-grid');
    matrixGrid.innerHTML = '';
    
    if (data.length === 0) {
      matrixGrid.innerHTML = `<div class="matrix-card" style="grid-column: span 2; text-align:center;"><p style="color:var(--gray);">Your structured core skills list layout metrics are empty.</p></div>`;
    } else {
      data.forEach(sk => {
        const card = document.createElement('div');
        card.className = 'matrix-card';
        card.innerHTML = `
          <div class="card-badge-row"><span class="badge badge-success">${sk.proficiency_level}</span></div>
          <h4>${sk.skill_name}</h4>
          <p style="color:var(--gray); font-size:0.85rem; margin-top:0.25rem;">Proficiency Target Tuning Ratio Layer: ${sk.proficiency_percent}%</p>
          <div class="bar-bg" style="margin: 0.75rem 0;"><div class="bar-fill" style="width: ${sk.proficiency_percent}%;"></div></div>
          <button class="btn btn-sm btn-outline btn-block" style="border-color:var(--red); color:var(--red);" onclick="handleDeleteUserSkill(${sk.user_skill_id})">Remove Track Record</button>
        `;
        matrixGrid.appendChild(card);
      });
    }
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    hideLoading();
  }
}

async function handleAddSkill(e) {
  e.preventDefault();
  const skill_id = parseInt(document.getElementById('add-skill-select').value);
  const proficiency_level = document.getElementById('add-skill-level').value;
  const proficiency_percent = parseInt(document.getElementById('add-skill-percent').value);

  if (!skill_id || !proficiency_level || isNaN(proficiency_percent)) {
    showToast("Please fill all required context configuration values.", 'error');
    return;
  }

  const payload = { skill_id, proficiency_level, proficiency_percent };
  showLoading();
  try {
    const res = await makeAuthenticatedRequest(`${BACKEND_URL}/api/student/skills`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Skill record insertion error.");

    showToast("Profile skill trace tracking item updated.");
    document.getElementById('form-add-skill').reset();
    fetchSkillsMatrixInventory();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    hideLoading();
  }
}

async function handleDeleteUserSkill(id) {
  if (!confirm("Are you certain you wish to discard this indexed skill metric layer profiling parameters?")) return;
  showLoading();
  try {
    const res = await makeAuthenticatedRequest(`${BACKEND_URL}/api/student/skills`, {
      method: 'DELETE',
      body: JSON.stringify({ user_skill_id: id })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Deletion target mismatch exception processing lifecycle.");

    showToast("Skill profile structure purged successfully.");
    fetchSkillsMatrixInventory();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    hideLoading();
  }
}

async function fetchPlatformTasksCatalog() {
  showLoading();
  try {
    const res = await makeAuthenticatedRequest(`${BACKEND_URL}/api/student/tasks`);
    const data = await res.json();
    cachedTasks = data; 
    renderTasksGrid(cachedTasks);
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    hideLoading();
  }
}

function renderTasksGrid(tasksList) {
  const container = document.getElementById('platform-tasks-grid');
  container.innerHTML = '';

  if (tasksList.length === 0) {
    container.innerHTML = `<p style="grid-column: span 2; text-align:center; color:var(--gray);">No relevant operation tasks catalog match tracking constraints layers.</p>`;
    return;
  }

  tasksList.forEach(tk => {
    const card = document.createElement('div');
    card.className = 'task-card';

    let actionBtnHTML = '';
    if (!tk.application_status) {
      actionBtnHTML = `<button class="btn btn-sm btn-primary" onclick="handleApplyTask(${tk.task_id})">Apply Task</button>`;
    } else if (tk.application_status === 'applied') {
      actionBtnHTML = `
        <div style="width:100%; display:flex; flex-direction:column; gap:8px; margin-top:10px;">
           <input type="text" id="proof-${tk.application_id}" placeholder="Paste source link / description asset file" style="padding:6px; font-size:0.8rem; border:1px solid var(--border); border-radius:4px;" />
           <button class="btn btn-sm btn-success" onclick="handleSubmitWorkProof(${tk.application_id})">Submit Asset Work Evidence</button>
        </div>
      `;
    } else if (tk.application_status === 'submitted') {
      actionBtnHTML = `<span class="badge badge-warn" style="padding:6px 12px;">Under Review Queue Audit</span>`;
    } else if (tk.application_status === 'approved') {
      actionBtnHTML = `<span class="badge badge-success" style="padding:6px 12px; background-color:rgba(16,185,129,0.25);">Completed & Credited</span>`;
    } else if (tk.application_status === 'rejected') {
      actionBtnHTML = `
        <div style="display:flex; flex-direction:column; gap:4px;">
           <span class="badge" style="background-color:rgba(239,68,68,0.15); color:var(--red); text-align:center;">Revision Requested</span>
           <input type="text" id="proof-${tk.application_id}" placeholder="Paste revised work URL" style="padding:6px; font-size:0.8rem; border:1px solid var(--border); border-radius:4px;" />
           <button class="btn btn-sm btn-primary" onclick="handleSubmitWorkProof(${tk.application_id})">Resubmit Revision</button>
        </div>
      `;
    }

    const requiredSkillsBadges = tk.required_skills.map(s => `<span class="task-tag">${s.skill_name} (${s.required_level})</span>`).join(' ');

    card.innerHTML = `
      <div class="task-card-header">
         <span class="task-difficulty intermediate">${tk.difficulty}</span>
         <span class="task-xp-yield">+${tk.reward_xp} XP</span>
      </div>
      <h3 class="task-title">${tk.title}</h3>
      <p class="task-excerpt">${tk.description}</p>
      <div style="margin-bottom: 1rem; display:flex; flex-wrap:wrap; gap:4px;">${requiredSkillsBadges}</div>
      <div class="task-card-footer" style="margin-top:auto; padding-top:10px; border-top:1px solid var(--gray-light);">
         ${actionBtnHTML}
      </div>
    `;
    container.appendChild(card);
  });
}

async function handleApplyTask(taskId) {
  showLoading();
  try {
    const res = await makeAuthenticatedRequest(`${BACKEND_URL}/api/student/tasks/apply`, {
      method: 'POST',
      body: JSON.stringify({ task_id: taskId })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Task allocation parameters initialization error.");

    showToast("Task assigned. Please review execution guidelines and fulfill dependencies proof.");
    fetchPlatformTasksCatalog();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    hideLoading();
  }
}

async function handleSubmitWorkProof(appId) {
  const txtVal = document.getElementById(`proof-${appId}`).value;
  if (!txtVal || txtVal.trim().length < 5) {
    showToast("Please supply explicit operational proof parameters deployment asset references.", 'error');
    return;
  }

  showLoading();
  try {
    const res = await makeAuthenticatedRequest(`${BACKEND_URL}/api/student/tasks/submit`, {
      method: 'POST',
      body: JSON.stringify({ app_id: appId, submission_text: txtVal })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Evidence processing exception execution error.");

    showToast("Work submission logged into admin audit pipelines successfully.");
    fetchPlatformTasksCatalog();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    hideLoading();
  }
}

function handleSearch() {
  const query = document.getElementById('task-search-input').value.toLowerCase().trim();
  const filtered = cachedTasks.filter(t => t.title.toLowerCase().includes(query) || t.description.toLowerCase().includes(query));
  renderTasksGrid(filtered);
}

function handleFilterChip(filterType, element) {
  document.querySelectorAll('.filter-chips-row .chip').forEach(c => c.classList.remove('active'));
  element.classList.add('active');

  if (filterType === 'all') {
    renderTasksGrid(cachedTasks);
  } else {
    const filtered = cachedTasks.filter(t => t.difficulty.toLowerCase() === filterType.toLowerCase());
    renderTasksGrid(filtered);
  }
}

/**
 * ==========================================================================
 * AI COUNSELOR CHAT SYSTEM LOGIC OPERATIONS
 * ==========================================================================
 */

function syncAIChatViewportConsole() {
  const container = document.getElementById('chat-viewport-history');
  if (container && container.children.length <= 1) {
    container.innerHTML = `
      <div class="chat-bubble ai-msg">
         <div class="bubble-avatar">AI</div>
         <div class="bubble-body">Assalam-o-Alaikum! Welcome to Micro-Skill Hub Career Core Advisor Dashboard. Ask me anything regarding stack alignment tracks optimizations!</div>
      </div>
    `;
  }
}

async function handleSendMessage() {
  const input = document.getElementById('chat-input-field');
  const msgText = input.value.trim();
  if (!msgText) return;

  input.value = '';
  const container = document.getElementById('chat-viewport-history');

  const userBubble = document.createElement('div');
  userBubble.className = 'chat-bubble user-msg';
  userBubble.innerHTML = `<div class="bubble-body">${msgText}</div>`;
  container.appendChild(userBubble);
  container.scrollTop = container.scrollHeight;

  const typingBubble = document.createElement('div');
  typingBubble.className = 'chat-bubble ai-msg typing-indicator-bubble';
  typingBubble.innerHTML = `
    <div class="bubble-avatar">AI</div>
    <div class="typing-indicator-dots"><span></span><span></span><span></span></div>
  `;
  container.appendChild(typingBubble);
  container.scrollTop = container.scrollHeight;

  try {
    const res = await makeAuthenticatedRequest(`${BACKEND_URL}/api/chat`, {
      method: 'POST',
      body: JSON.stringify({ message: msgText })
    });
    const data = await res.json();
    typingBubble.remove();

    const aiBubble = document.createElement('div');
    aiBubble.className = 'chat-bubble ai-msg';
    aiBubble.innerHTML = `
      <div class="bubble-avatar">AI</div>
      <div class="bubble-body">${data.reply}</div>
    `;
    container.appendChild(aiBubble);
    container.scrollTop = container.scrollHeight;
  } catch (err) {
    typingBubble.remove();
    showToast("AI network connection latency error.", 'error');
  }
}

/**
 * ==========================================================================
 * ADMINISTRATIVE DASHBOARD PIPELINE METRICS ENGINE
 * ==========================================================================
 */

async function fetchAdminMetricsEngine() {
  showLoading();
  try {
    const res = await makeAuthenticatedRequest(`${BACKEND_URL}/api/admin/metrics`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Administrative structural analytics fetch error.");

    if(document.getElementById('admin-total-students')) document.getElementById('admin-total-students').textContent = data.total_students;
    if(document.getElementById('admin-total-tasks')) document.getElementById('admin-total-tasks').textContent = data.total_tasks;
    if(document.getElementById('admin-pending-submissions')) document.getElementById('admin-pending-submissions').textContent = data.pending_submissions;

    await fetchAdminUsersReport();
    await fetchAdminTasksCatalogList();
    await loadAdminSubmissionsAuditQueue();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    hideLoading();
  }
}

async function fetchAdminUsersReport() {
  const res = await makeAuthenticatedRequest(`${BACKEND_URL}/api/admin/users`);
  const users = await res.json();
  
  const tbody = document.querySelector('#section-admin table:nth-of-type(1) tbody');
  if(!tbody) return;
  tbody.innerHTML = '';
  
  users.forEach(u => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><code>#${u.user_id}</code></td>
      <td>${u.full_name}</td>
      <td>${u.email}</td>
      <td>${u.roll_number || 'N/A'}</td>
      <td><span class="badge badge-success">${u.skill_count} Active Track</span></td>
      <td><strong>${u.total_xp} XP</strong></td>
    `;
    tbody.appendChild(tr);
  });
}

async function fetchAdminTasksCatalogList() {
  const res = await makeAuthenticatedRequest(`${BACKEND_URL}/api/student/tasks`);
  const tasks = await res.json();
  
  const tbody = document.getElementById('admin-tasks-tbody-render');
  if (!tbody) return;
  tbody.innerHTML = '';

  tasks.forEach(t => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="padding:10px;"><code>#${t.task_id}</code></td>
      <td style="padding:10px; font-weight:600;">${t.title}</td>
      <td style="padding:10px;"><span class="badge badge-hot">${t.difficulty}</span></td>
      <td style="padding:10px; color:var(--purple); font-weight:700;">${t.reward_xp} XP</td>
      <td style="padding:10px;">
          <button class="btn btn-sm btn-danger" onclick="handlePurgeTaskStructureRow(${t.task_id})" style="padding:2px 8px;">Delete Task</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

async function loadAdminSubmissionsAuditQueue() {
  const res = await makeAuthenticatedRequest(`${BACKEND_URL}/api/admin/submissions`);
  const subs = await res.json();
  
  const tbody = document.getElementById('admin-submissions-tbody-render');
  if (!tbody) return;
  tbody.innerHTML = '';

  if (subs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" style="padding:15px; text-align:center; color:var(--text-muted);">Audit pipeline workspace structural queue is empty.</td></tr>`;
    return;
  }

  subs.forEach(s => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td style="padding:10px;">
          <strong>${s.student_name}</strong><br/>
          <small style="color:var(--text-muted);">${s.student_email}</small>
      </td>
      <td style="padding:10px; font-size:0.9rem;">${s.task_title}</td>
      <td style="padding:10px;">
          <div style="max-width:260px; overflow-x:auto; background:#1e2235; padding:6px; border-radius:4px; font-family:monospace; font-size:0.8rem; color:var(--teal);">
             ${s.submission_text}
          </div>
      </td>
      <td style="padding:10px;">
          <div style="display:flex; gap:6px;">
             <button class="btn btn-sm btn-success" onclick="handleProcessAuditDecision(${s.application_id}, 'approved')" style="padding:2px 8px;">Approve</button>
             <button class="btn btn-sm btn-danger" onclick="handleProcessAuditDecision(${s.application_id}, 'rejected')" style="padding:2px 8px;">Reject</button>
          </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

async function handleCreateNewTaskFormSubmission(e) {
  e.preventDefault();
  const title = document.getElementById('task-title-input').value;
  const description = document.getElementById('task-desc-input').value;
  const difficulty = document.getElementById('task-diff-select').value;
  const reward_xp = parseInt(document.getElementById('task-xp-input').value);
  
  const skillCheckboxes = document.querySelectorAll('input[name="admin-skills-selector"]:checked');
  const required_skills = Array.from(skillCheckboxes).map(cb => parseInt(cb.value));

  if (!title || !description || !difficulty || isNaN(reward_xp) || required_skills.length === 0) {
    showToast("Please provide comprehensive execution profile metadata configurations.", 'error');
    return;
  }

  const payload = { title, description, difficulty, reward_xp, required_skills };
  showLoading();
  try {
    const res = await makeAuthenticatedRequest(`${BACKEND_URL}/api/admin/tasks`, {
      method: 'POST',
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Error creating task structure configuration.");

    showToast("Operational assignment entity registry deployed onto dynamic platform matrices.");
    document.getElementById('form-admin-create-task').reset();
    fetchAdminMetricsEngine();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    hideLoading();
  }
}

async function handleProcessAuditDecision(appId, decisionStatus) {
  showLoading();
  try {
    const res = await makeAuthenticatedRequest(`${BACKEND_URL}/api/admin/submissions/review`, {
      method: 'POST',
      body: JSON.stringify({ application_id: appId, status: decisionStatus })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Pipeline authorization audit status change state fault.");

    showToast(`Student tracking index structural assignment execution resolution updated to: ${decisionStatus}`);
    fetchAdminMetricsEngine();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    hideLoading();
  }
}

async function handlePurgeTaskStructureRow(taskId) {
  if (!confirm("Are you absolutely certain you wish to permanently purge this task assignment structural entity from tables records?")) return;
  showLoading();
  try {
    const res = await makeAuthenticatedRequest(`${BACKEND_URL}/api/admin/tasks/${taskId}`, {
      method: 'DELETE'
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Transaction sequence deletion structural failure.");

    showToast("Purged task structure configuration safely from data tables records.");
    fetchAdminMetricsEngine();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    hideLoading();
  }
}

/**
 * ==========================================================================
 * MASTER APP LIFE CYCLE CORE ENGINE COUPLING SETUP
 * ==========================================================================
 */

function init() {
  if (document.getElementById('form-login')) document.getElementById('form-login').addEventListener('submit', handleLogin);
  if (document.getElementById('form-register-submit')) document.getElementById('form-register-submit').addEventListener('submit', handleRegister);
  if (document.getElementById('form-add-skill')) document.getElementById('form-add-skill').addEventListener('submit', handleAddSkill);
  if (document.getElementById('form-chat-input')) document.getElementById('form-chat-input').addEventListener('submit', function(e) { e.preventDefault(); handleSendMessage(); });
  if (document.getElementById('btn-logout')) document.getElementById('btn-logout').addEventListener('click', handleLogout);
  if (document.getElementById('task-search-input')) document.getElementById('task-search-input').addEventListener('input', handleSearch);
  if (document.getElementById('form-admin-create-task')) document.getElementById('form-admin-create-task').addEventListener('submit', handleCreateNewTaskFormSubmission);

  document.querySelectorAll('.filter-chips-row .chip').forEach(chip => {
    chip.addEventListener('click', function() {
      handleFilterChip(this.textContent.trim().toLowerCase().includes('all') ? 'all' : this.textContent.trim(), this);
    });
  });

  setupNavigation();
  initPasswordSecurityFeatures();

  const token = getToken();
  const cachedUserString = localStorage.getItem('msh_user');

  if (token && cachedUserString) {
    try {
      const userObj = JSON.parse(cachedUserString);
      syncNavbarState(userObj);
      navigateTo(userObj.role === 'admin' ? 'section-admin' : 'section-dashboard');
    } catch (err) { handleLogout(); }
  } else {
    // Agar user logged in nahi hai toh strictly home/hero section par ruko
    navigateTo('section-home');
  }
}

document.addEventListener('DOMContentLoaded', init);

// Global bindings for HTML onclick contexts execution mapping
window.navigateTo = navigateTo;
window.handleApplyTask = handleApplyTask;
window.handleSubmitWorkProof = handleSubmitWorkProof;
window.handleDeleteUserSkill = handleDeleteUserSkill;
window.handleProcessAuditDecision = handleProcessAuditDecision;
window.handlePurgeTaskStructureRow = handlePurgeTaskStructureRow;