import { showToast, showErrorDialog } from '../main.js';

let allSkills = [];
let lastPath = '';
let searchCache = {};
let currentCategory = null;
let categoriesCache = {};

const CATEGORY_DESCRIPTIONS = {
  'Testing and QA': 'Automated testing, quality assurance, and validation tools for robust software delivery.',
  Backend: 'Server-side frameworks, APIs, databases, and backend infrastructure components.',
  Frontend: 'UI frameworks, component libraries, and client-side development tools.',
  'Artificial Intelligence': 'AI/ML integration, LLM tools, intelligent automation, and data pipelines.',
  DevOps: 'CI/CD, containerization, monitoring, infrastructure-as-code, and deployment tooling.',
  Security: 'Security scanning, authentication, encryption, and compliance tooling.',
  Mobile: 'Mobile app development frameworks, tools, and platform-specific utilities.',
  Data: 'Data processing, ETL pipelines, analytics, and data visualization tools.',
  Documentation: 'Documentation generators, API docs, wikis, and technical writing tools.',
  Productivity: 'Developer workflow tools, automation scripts, and utility libraries.',
  Design: 'Design systems, prototyping tools, and UI/UX development resources.',
};

function getCategoryDescription(cat) {
  if (CATEGORY_DESCRIPTIONS[cat]) return CATEGORY_DESCRIPTIONS[cat];
  const words = cat.split(/[\s-/]+/);
  return `${cat} — A collection of ${words.length > 1 ? words.join(', ') : cat.toLowerCase()} tools and utilities for your project.`;
}

function getCategoryIcon(cat) {
  const icons = {
    'Testing and QA': '&#x2699;',
    Backend: '&#x1F4E1;',
    Frontend: '&#x1F3A8;',
    'Artificial Intelligence': '&#x1F916;',
    DevOps: '&#x1F504;',
    Security: '&#x1F512;',
    Mobile: '&#x1F4F1;',
    Data: '&#x1F4CA;',
    Documentation: '&#x1F4C4;',
    Productivity: '&#x26A1;',
    Design: '&#x1F3A8;',
  };
  return icons[cat] || '&#x1F4E6;';
}

export function initSkillsStudio() {
  const container = document.getElementById('skills-categories-container');
  loadSkillsData(container);
}

function getInstalledState() {
  try {
    return JSON.parse(localStorage.getItem('skills_installed') || '{}');
  } catch { return {}; }
}

function saveInstalledState(skillId, tools) {
  const state = getInstalledState();
  state[skillId] = { tools: tools || [], timestamp: Date.now() };
  localStorage.setItem('skills_installed', JSON.stringify(state));
}

function removeInstalledState(skillId) {
  const state = getInstalledState();
  delete state[skillId];
  localStorage.setItem('skills_installed', JSON.stringify(state));
}

async function setDefaultPath(pathInput) {
  if (!pathInput) return;
  const hint = document.getElementById('skills-path-hint');

  let currentCwd = '.';
  try {
    const res = await fetch('/api/status');
    if (res.ok) {
      const data = await res.json();
      if (data.cwd) currentCwd = data.cwd;
    }
  } catch {}

  const saved = localStorage.getItem('skills_last_path');
  const workspace = localStorage.getItem('skills_path_workspace');

  if (saved && workspace === currentCwd) {
    pathInput.value = saved;
    lastPath = saved;
    if (hint) hint.textContent = saved;
    return;
  }

  pathInput.value = currentCwd;
  lastPath = currentCwd;
  if (hint) hint.textContent = currentCwd;
  localStorage.removeItem('skills_last_path');
  localStorage.removeItem('skills_path_workspace');
}

function setupEventListeners(container, searchInput, pathInput, installBtn) {
  searchInput.addEventListener('input', () => {
    clearTimeout(searchInput._debounce);
    searchInput._debounce = setTimeout(() => {
      const q = searchInput.value.trim();
      document.getElementById('skills-clear-search').classList.toggle('visible', !!q);
      if (currentCategory) {
        renderCategoryDetail(currentCategory, container, q);
      } else {
        const filtered = q ? fuzzySearch(q) : allSkills;
        renderBanners(filtered, container, q);
      }
    }, 150);
  });

  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      searchInput.value = '';
      searchInput.dispatchEvent(new Event('input'));
      searchInput.blur();
    }
  });

  document.getElementById('skills-clear-search')?.addEventListener('click', () => {
    searchInput.value = '';
    searchInput.dispatchEvent(new Event('input'));
    searchInput.focus();
  });

  pathInput.addEventListener('change', async () => {
    const val = pathInput.value.trim();
    if (val) {
      localStorage.setItem('skills_last_path', val);
      try {
        const res = await fetch('/api/status');
        if (res.ok) {
          const data = await res.json();
          if (data.cwd) localStorage.setItem('skills_path_workspace', data.cwd);
        }
      } catch {}
      lastPath = val;
      const hint = document.getElementById('skills-path-hint');
      if (hint) hint.textContent = val;
    }
  });

  installBtn.addEventListener('click', () => {
    const ids = Array.from(container.querySelectorAll('.skill-checkbox:checked')).map((cb) => cb.value);
    if (!ids.length) {
      showToast('Select at least one skill to install', 'info');
      return;
    }
    showToolPicker(ids, container);
  });

  container.addEventListener('change', (e) => {
    if (e.target.classList.contains('skill-checkbox')) {
      updateSelectedCount();
    }
  });

  container.addEventListener('click', (e) => {
    const banner = e.target.closest('.skills-banner-card');
    if (banner) {
      const cat = banner.dataset.category;
      if (cat) {
        currentCategory = cat;
        renderCategoryDetail(cat, container, document.getElementById('skills-search').value.trim());
      }
      return;
    }

    const backBtn = e.target.closest('.skills-back-btn');
    if (backBtn) {
      currentCategory = null;
      document.getElementById('skills-search').value = '';
      document.getElementById('skills-clear-search').classList.remove('visible');
      renderBanners(allSkills, container, '');
      return;
    }

    const catBtn = e.target.closest('.skills-install-cat');
    if (catBtn) {
      e.stopPropagation();
      const cat = catBtn.dataset.category;
      const ids = Array.from(container.querySelectorAll('.skill-checkbox')).map((cb) => cb.value);
      if (ids.length) showToolPicker(ids, container);
      return;
    }

    const installBtn = e.target.closest('.skill-install-btn');
    if (installBtn) {
      e.stopPropagation();
      showToolPicker([installBtn.dataset.id], container);
      return;
    }

    const uninstallBtn = e.target.closest('.skill-uninstall-btn');
    if (uninstallBtn) {
      e.stopPropagation();
      const skillId = uninstallBtn.dataset.id;
      uninstallSkill(skillId, container);
      return;
    }
  });
}

async function loadSkillsData(container) {
  const pathInput = document.getElementById('skills-path');
  const searchInput = document.getElementById('skills-search');
  const installBtn = document.getElementById('skills-install-all');

  setDefaultPath(pathInput);
  setupEventListeners(container, searchInput, pathInput, installBtn);

  container.innerHTML =
    '<div class="skills-loading"><div class="spinner-ring"></div><span>Loading skills...</span></div>';
  try {
    const res = await fetch('/api/skills/list');
    if (!res.ok) throw new Error('Failed to load skills');
    const data = await res.json();
    allSkills = data.skills || [];
    searchCache = {};
    groupByCategory();
    currentCategory = null;
    renderBanners(allSkills, container, '');
    updateCount(allSkills.length);
    // Restore persistent installed state
    setTimeout(() => loadInstalledState(container), 100);
  } catch (err) {
    container.innerHTML = `<div class="empty-state"><h4>Failed to Load Skills</h4><p>${err.message}</p></div>`;
  }
}

function groupByCategory() {
  categoriesCache = {};
  for (const s of allSkills) {
    (categoriesCache[s.category] ||= []).push(s);
  }
}

function fuzzySearch(query) {
  if (!query) return allSkills;
  if (searchCache[query]) return searchCache[query];
  const q = query.toLowerCase().trim();
  const scored = [];
  for (const s of allSkills) {
    const name = s.name.toLowerCase();
    const id = s.id.toLowerCase();
    const cat = s.category.toLowerCase();
    const desc = s.description.toLowerCase();

    let score = 0;
    if (q === name || q === id) score = 100;
    else if (name.startsWith(q) || id.startsWith(q)) score = 80;
    else if (name.includes(q) || id.includes(q)) score = 60;
    else if (cat.includes(q)) score = 40;
    else if (desc.includes(q)) score = 20;

    if (score > 0) scored.push({ score, s });
  }
  scored.sort((a, b) => b.score - a.score || a.s.name.localeCompare(b.s.name));
  const result = scored.map((x) => x.s);
  searchCache[query] = result;
  return result;
}

function renderBanners(skills, container, query) {
  const grouped = {};
  for (const s of skills) {
    (grouped[s.category] ||= []).push(s);
  }

  const cats = Object.keys(grouped).sort();
  updateCount(skills.length);

  if (!cats.length) {
    container.innerHTML = `<div class="empty-state"><h4>No Skills Found</h4><p>Try a different search term.</p></div>`;
    return;
  }

  const grid = document.createElement('div');
  grid.className = 'skills-banner-grid';

  for (const cat of cats) {
    const list = grouped[cat];
    const banner = document.createElement('div');
    banner.className = 'skills-banner-card';
    banner.dataset.category = cat;

    banner.innerHTML = `
      <div class="skills-banner-icon">${getCategoryIcon(cat)}</div>
      <h3 class="skills-banner-title">${cat}</h3>
      <span class="skills-banner-count">${list.length} skill${list.length !== 1 ? 's' : ''}</span>
      <p class="skills-banner-desc">${getCategoryDescription(cat)}</p>
    `;

    grid.appendChild(banner);
  }

  container.innerHTML = '';
  container.appendChild(grid);

  grid.querySelectorAll('.skills-banner-card').forEach((card, i) => {
    card.style.animation = `fadeSlideIn 0.25s ease-out ${i * 0.03}s both`;
  });

  updateSelectedCount();
}

function renderCategoryDetail(category, container, query) {
  let skills = categoriesCache[category] || allSkills.filter((s) => s.category === category);

  if (query) {
    const q = query.toLowerCase().trim();
    skills = skills.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        s.id.toLowerCase().includes(q) ||
        (s.description && s.description.toLowerCase().includes(q)),
    );
  }

  updateCount(skills.length);

  let html = `
    <div class="skills-detail-header">
      <button class="skills-back-btn" title="Back to categories">&larr; Back to Categories</button>
      <div class="skills-detail-title-row">
        <h3 class="skills-detail-title">${category}</h3>
        <span class="skills-category-count">${skills.length} skill${skills.length !== 1 ? 's' : ''}</span>
        <button class="btn btn-secondary btn-sm skills-install-cat" data-category="${category}">Install All</button>
      </div>
    </div>
    <div class="skills-detail-list">
  `;

  if (!skills.length) {
    html += `<div class="empty-state" style="padding:40px 0"><h4>No Skills Found</h4><p>Try a different search term.</p></div>`;
  } else {
    for (const s of skills) {
      const riskBadge =
        s.risk && s.risk !== 'unknown' && s.risk !== 'none'
          ? `<span class="skills-risk-badge skills-risk-${s.risk}">${s.risk}</span>`
          : '';
      html += `<div class="skill-item" data-id="${s.id}">
        <label class="skill-check-wrap">
          <input type="checkbox" class="skill-checkbox" value="${s.id}" />
          <div class="skill-info">
            <div class="skill-name-row">
              <span class="skill-name">${s.name}</span>
              ${riskBadge}
            </div>
            <p class="skill-desc">${s.description || 'No description available.'}</p>
          </div>
        </label>
        <button class="btn btn-primary btn-sm skill-install-btn" data-id="${s.id}">Install</button>
      </div>`;
    }
  }

  html += '</div>';
  container.innerHTML = html;

  container.querySelectorAll('.skill-item').forEach((item, i) => {
    item.style.animation = `fadeSlideIn 0.2s ease-out ${i * 0.02}s both`;
  });

  updateSelectedCount();
}

function updateCount(total) {
  const el = document.getElementById('skills-count');
  if (el) el.textContent = `${total} skills`;
}

function updateSelectedCount() {
  const el = document.getElementById('skills-selected-count');
  if (!el) return;
  const count = document.querySelectorAll('.skill-checkbox:checked').length;
  el.textContent = `${count} selected`;
}

async function showToolPicker(skillIds, container) {
  const existing = document.getElementById('tool-picker-overlay');
  if (existing) existing.remove();

  try {
    const res = await fetch('/api/skills/detect-tools');
    const data = await res.json();
    const allTools = data.tools || [];
    const detectedTools = allTools.filter((t) => t.detected);

    if (detectedTools.length === 0 && allTools.length === 0) {
      showProjectFallbackDialog(skillIds, container);
      return;
    }

    const overlay = document.createElement('div');
    overlay.id = 'tool-picker-overlay';
    overlay.className = 'tool-picker-overlay';

    const icons = {
      opencode: '&#x2699;', 'claude-code': '&#x1F9E0;', cursor: '&#x1F4BB;',
      'codex-cli': '&#x1F4DD;', 'gemini-cli': '&#x2B50;', windsurf: '&#x1F30A;',
      cline: '&#x1F527;', vscode: '&#x1F4BB;',
    };

    const detectedIds = new Set(allTools.filter((t) => t.detected).map((t) => t.id));

    let itemsHtml = allTools.map((t) => {
      const icon = icons[t.id] || '&#x1F4E6;';
      const checked = t.detected ? 'checked' : '';
      const label = t.detected ? t.name : `${t.name} (not detected)`;
      const extraClass = t.detected ? '' : ' tool-picker-item-dim';
      return `<label class="tool-picker-item${extraClass}">
        <input type="checkbox" class="tool-picker-cb" value="${t.id}" ${checked} />
        <span class="tool-picker-icon">${icon}</span>
        <span class="tool-picker-name">${label}</span>
      </label>`;
    }).join('');

    const selectedCount = allTools.filter((t) => t.detected).length;

    overlay.innerHTML = `
      <div class="tool-picker-dialog">
        <h3 class="tool-picker-title">Install skills for which AI tools?</h3>
        <p class="tool-picker-subtitle">${skillIds.length} skill${skillIds.length > 1 ? 's' : ''} selected &middot; detected tools pre-checked</p>
        <div class="tool-picker-list">${itemsHtml}</div>
        <div class="tool-picker-actions">
          <button id="tool-picker-cancel" class="btn btn-secondary">Cancel</button>
          <button id="tool-picker-install" class="btn btn-primary">Install</button>
        </div>
      </div>`;

    document.body.appendChild(overlay);

    function updateInstallBtn() {
      const btn = document.getElementById('tool-picker-install');
      const count = overlay.querySelectorAll('.tool-picker-cb:checked').length;
      if (btn) btn.textContent = count ? `Install for ${count} tool${count > 1 ? 's' : ''}` : 'Install (project only)';
    }

    overlay.querySelectorAll('.tool-picker-cb').forEach((cb) => {
      cb.addEventListener('change', updateInstallBtn);
    });
    updateInstallBtn();

    document.getElementById('tool-picker-cancel').addEventListener('click', () => overlay.remove());
    document.getElementById('tool-picker-install').addEventListener('click', () => {
      const selected = Array.from(overlay.querySelectorAll('.tool-picker-cb:checked')).map((cb) => cb.value);
      overlay.remove();
      installSelectedSkills(skillIds, container, selected);
    });
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) overlay.remove();
    });
  } catch (err) {
    showToast('Failed to detect AI tools. Install to project directory?', 'info');
    showProjectFallbackDialog(skillIds, container);
  }
}

function showProjectFallbackDialog(skillIds, container) {
  const overlay = document.createElement('div');
  overlay.className = 'tool-picker-overlay';

  overlay.innerHTML = `
    <div class="tool-picker-dialog">
      <h3 class="tool-picker-title">No AI coding tools detected</h3>
      <p class="tool-picker-subtitle">No globally installed AI tools were found on your system.</p>
      <p class="tool-picker-subtitle" style="margin-top:4px;">Install skills in the project directory instead? The skills will be registered via AGENTS.md for opencode/codex-cli compatibility.</p>
      <div class="tool-picker-actions">
        <button id="tool-picker-cancel" class="btn btn-secondary">Cancel</button>
        <button id="tool-picker-install" class="btn btn-primary">Install in Project</button>
      </div>
    </div>`;

  document.body.appendChild(overlay);

  document.getElementById('tool-picker-cancel').addEventListener('click', () => overlay.remove());
  document.getElementById('tool-picker-install').addEventListener('click', () => {
    overlay.remove();
    installSelectedSkills(skillIds, container, []);
  });
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) overlay.remove();
  });
}

async function installSelectedSkills(skillIds, container, tools) {
  const pathInput = document.getElementById('skills-path');
  const projectPath = (pathInput?.value || '.').trim();
  if (!projectPath) {
    showToast('Please enter a project path', 'error');
    return;
  }
  localStorage.setItem('skills_last_path', projectPath);

  const installBtn = document.getElementById('skills-install-all');
  if (installBtn) {
    installBtn.disabled = true;
    installBtn.innerHTML =
      '<span class="spinner-ring" style="width:14px;height:14px;border-width:2px;"></span><span> Installing...</span>';
  }

  try {
    const body = { project_path: projectPath, skills: skillIds };
    if (tools && tools.length) body.tools = tools;

    const res = await fetch('/api/skills/install', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const e = await res.json().catch(() => ({ detail: 'Install failed' }));
      throw new Error(e.detail);
    }
    const data = await res.json();
    const installed = data.installed || [];
    const errors = data.errors || [];
    const fresh = installed.filter((i) => i.status === 'installed');
    const existing = installed.filter((i) => i.status === 'already_installed');

    let msg = '';
    if (fresh.length) msg += `Installed ${fresh.length} skill${fresh.length > 1 ? 's' : ''}. `;
    if (existing.length) msg += `${existing.length} already present. `;
    if (errors.length) msg += `${errors.length} failed. `;

    if (fresh.length || existing.length) {
      const reg = data.registration;
      const regTools = reg?.detected_tools || [];
      let regMsg = msg.trim();
      if (reg) {
        const tools = reg.detected_tools;
        if (tools && tools.length) {
          regMsg += `\nRegistered for: ${tools.join(', ')}`;
        }
        const scopes = reg.registrations || [];
        const globalCount = scopes.filter((r) => r.scope === 'global').length;
        const projectCount = scopes.filter((r) => r.scope === 'project').length;
        const verifiedCount = scopes.filter((r) => r.verified).length;
        const totalRegs = scopes.filter((r) => r.status === 'registered' || r.status === 'already_registered').length;
        if (globalCount) regMsg += `\n${globalCount} global install(s)`;
        if (projectCount) regMsg += `\n${projectCount} project install(s)`;
        if (verifiedCount !== totalRegs) {
          regMsg += `\n${verifiedCount}/${totalRegs} verified`;
        } else if (totalRegs > 0) {
          regMsg += `\nAll ${totalRegs} verified \u2705`;
        }
        if (reg.errors && reg.errors.length) {
          regMsg += `\nRegistration errors: ${reg.errors.length}`;
          for (const err of reg.errors.slice(0, 3)) {
            const ec = err.error_code || 'N/A';
            regMsg += `\n  [${ec}] ${err.tool}/${err.skill_id}: ${err.error.slice(0, 80)}`;
          }
        }
      }
      showToast(regMsg || 'Done!', 'success');
      // Persist installed state
      for (const sid of skillIds) {
        saveInstalledState(sid, regTools);
      }
      container.querySelectorAll('.skill-checkbox:checked').forEach((cb) => (cb.checked = false));
      updateSelectedCount();
      markInstalled(
        container,
        installed.map((i) => i.id),
      );
    } else {
      showToast(errors.map((e) => e.id).join(', ') + ' failed', 'error');
    }
  } catch (err) {
    showErrorDialog('SKL-FR00', 'Install failed: ' + err.message, err.stack || '');
  } finally {
    if (installBtn) {
      installBtn.disabled = false;
      installBtn.innerHTML = 'Install Selected';
    }
  }
}

async function uninstallSkill(skillId, container) {
  const pathInput = document.getElementById('skills-path');
  const projectPath = (pathInput?.value || '.').trim();
  if (!projectPath) {
    showToast('Please enter a project path', 'error');
    return;
  }

  if (!confirm(`Remove "${skillId.replace(/-/g, ' ')}" from project and all AI tools?`)) return;

  try {
    const res = await fetch('/api/skills/uninstall', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_path: projectPath, skills: [skillId] }),
    });
    if (!res.ok) {
      const e = await res.json().catch(() => ({ detail: 'Uninstall failed' }));
      throw new Error(e.detail);
    }
    const data = await res.json();
    const removed = (data.uninstalled || []).length;
    const errs = (data.errors || []).length;

    let msg = `Removed from ${removed} location(s).`;
    if (errs) {
      msg += ` ${errs} error(s).`;
      for (const err of data.errors.slice(0, 3)) {
        const ec = err.error_code || 'N/A';
        showErrorDialog(ec, err.error, '');
      }
    }
    showToast(msg, errs ? 'info' : 'success');

    removeInstalledState(skillId);
    const item = container.querySelector(`.skill-item[data-id="${skillId}"]`);
    if (item) {
      item.classList.remove('is-installed');
      const btn = item.querySelector('.skill-install-btn');
      if (btn) {
        btn.disabled = false;
        btn.textContent = 'Install';
        btn.className = 'btn btn-primary btn-sm skill-install-btn';
      }
      const uBtn = item.querySelector('.skill-uninstall-btn');
      if (uBtn) uBtn.remove();
    }
  } catch (err) {
    showErrorDialog('SKL-FR01', 'Uninstall failed: ' + err.message, err.stack || '');
  }
}

function markInstalled(container, ids) {
  const set = new Set(ids);
  container.querySelectorAll('.skill-item').forEach((item) => {
    if (set.has(item.dataset.id)) {
      item.classList.add('is-installed');
      const btn = item.querySelector('.skill-install-btn');
      if (btn) {
        btn.disabled = true;
        btn.textContent = 'Installed';
        btn.className = 'btn btn-sm btn-installed';
      }
      // Add uninstall button if not already present
      if (!item.querySelector('.skill-uninstall-btn')) {
        const uBtn = document.createElement('button');
        uBtn.className = 'btn btn-sm btn-outline skill-uninstall-btn';
        uBtn.textContent = 'Remove';
        uBtn.dataset.id = item.dataset.id;
        btn?.parentNode?.appendChild(uBtn);
      }
    }
  });
}

// Load persistent installed state from localStorage after skills are rendered
function loadInstalledState(container) {
  const state = getInstalledState();
  const ids = Object.keys(state);
  if (ids.length) {
    markInstalled(container, ids);
  }
}
