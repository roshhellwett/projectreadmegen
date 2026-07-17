import { showToast } from '../main.js';

let allSkills = [];
let lastPath = '';
let searchCache = {};

export function initSkillsStudio() {
  const container = document.getElementById('skills-categories-container');
  loadSkillsData(container);
}

async function setDefaultPath(pathInput) {
  if (!pathInput) return;
  const hint = document.getElementById('skills-path-hint');
  const saved = localStorage.getItem('skills_last_path');
  if (saved) { pathInput.value = saved; lastPath = saved; if (hint) hint.textContent = saved; return; }
  try {
    const res = await fetch('/api/status');
    if (res.ok) {
      const data = await res.json();
      if (data.cwd) { pathInput.value = data.cwd; lastPath = data.cwd; if (hint) hint.textContent = data.cwd; }
    }
  } catch { }
}

function setupEventListeners(container, searchInput, pathInput, installBtn) {
  searchInput.addEventListener('input', () => {
    clearTimeout(searchInput._debounce);
    searchInput._debounce = setTimeout(() => {
      const q = searchInput.value.trim();
      if (!q && !container.querySelector('.skills-category-card')) return;
      const filtered = q ? fuzzySearch(q) : allSkills;
      renderCategories(filtered, container, q);
      document.getElementById('skills-clear-search').classList.toggle('visible', !!q);
    }, 150);
  });

  searchInput.addEventListener('keydown', e => {
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

  pathInput.addEventListener('change', () => {
    const val = pathInput.value.trim();
    if (val) {
      localStorage.setItem('skills_last_path', val); lastPath = val;
      const hint = document.getElementById('skills-path-hint');
      if (hint) hint.textContent = val;
    }
  });

  installBtn.addEventListener('click', () => {
    const ids = Array.from(container.querySelectorAll('.skill-checkbox:checked')).map(cb => cb.value);
    if (!ids.length) { showToast('Select at least one skill to install', 'info'); return; }
    installSelectedSkills(ids, container);
  });

  container.addEventListener('change', e => {
    if (e.target.classList.contains('skill-checkbox')) {
      updateSelectedCount();
    }
  });

  container.addEventListener('click', e => {
    const header = e.target.closest('.skills-category-header');
    if (header && !e.target.closest('button')) {
      const card = header.closest('.skills-category-card');
      card.classList.toggle('collapsed');
    }

    const installBtn = e.target.closest('.skill-install-btn');
    if (installBtn) {
      e.stopPropagation();
      installBtn.disabled = true;
      installBtn.innerHTML = '<span class="spinner-ring" style="width:12px;height:12px;border-width:2px;"></span>';
      installSelectedSkills([installBtn.dataset.id], container)
        .finally(() => {
          if (!installBtn.closest('.is-installed')) {
            installBtn.disabled = false;
            installBtn.textContent = 'Install';
          }
        });
    }

    const catBtn = e.target.closest('.skills-install-cat');
    if (catBtn) {
      e.stopPropagation();
      const cat = catBtn.dataset.category;
      const ids = Array.from(container.querySelectorAll('.skill-checkbox'))
        .filter(cb => cb.closest('.skills-category-card').querySelector('.skills-category-header').dataset.category === cat)
        .map(cb => cb.value);
      if (ids.length) installSelectedSkills(ids, container);
    }
  });
}

async function loadSkillsData(container) {
  const pathInput = document.getElementById('skills-path');
  const searchInput = document.getElementById('skills-search');
  const installBtn = document.getElementById('skills-install-all');

  setDefaultPath(pathInput);
  setupEventListeners(container, searchInput, pathInput, installBtn);

  container.innerHTML = '<div class="skills-loading"><div class="spinner-ring"></div><span>Loading skills...</span></div>';
  try {
    const res = await fetch('/api/skills/list');
    if (!res.ok) throw new Error('Failed to load skills');
    const data = await res.json();
    allSkills = data.skills || [];
    searchCache = {};
    renderCategories(allSkills, container, '');
    updateCount(allSkills.length);
  } catch (err) {
    container.innerHTML = `<div class="empty-state"><h4>Failed to Load Skills</h4><p>${err.message}</p></div>`;
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
  const result = scored.map(x => x.s);
  searchCache[query] = result;
  return result;
}

function renderCategories(skills, container, query) {
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

  const frag = document.createDocumentFragment();
  for (const cat of cats) {
    const list = grouped[cat];
    const card = document.createElement('div');
    card.className = 'skills-category-card';

    card.innerHTML = `
      <div class="skills-category-header" data-category="${cat}">
        <span class="skills-category-toggle">&#9660;</span>
        <h3 class="skills-category-title">${cat}</h3>
        <span class="skills-category-count">${list.length}</span>
        <button class="btn btn-secondary btn-sm skills-install-cat" data-category="${cat}">Install All</button>
      </div>
      <div class="skills-category-body">
        ${list.map(s => {
          const riskBadge = s.risk && s.risk !== 'unknown' && s.risk !== 'none'
            ? `<span class="skills-risk-badge skills-risk-${s.risk}">${s.risk}</span>` : '';
          return `<div class="skill-item" data-id="${s.id}">
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
        }).join('')}
      </div>`;

    frag.appendChild(card);
  }

  container.innerHTML = '';
  container.appendChild(frag);

  container.querySelectorAll('.skills-category-card').forEach((card, i) => {
    card.style.animation = `fadeSlideIn 0.25s ease-out ${i * 0.03}s both`;
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

async function installSelectedSkills(skillIds, container) {
  const pathInput = document.getElementById('skills-path');
  const projectPath = (pathInput?.value || '.').trim();
  if (!projectPath) { showToast('Please enter a project path', 'error'); return; }
  localStorage.setItem('skills_last_path', projectPath);

  const installBtn = document.getElementById('skills-install-all');
  if (installBtn) { installBtn.disabled = true; installBtn.innerHTML = '<span class="spinner-ring" style="width:14px;height:14px;border-width:2px;"></span><span> Installing...</span>'; }

  try {
    const res = await fetch('/api/skills/install', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_path: projectPath, skills: skillIds })
    });
    if (!res.ok) { const e = await res.json().catch(() => ({ detail: 'Install failed' })); throw new Error(e.detail); }
    const data = await res.json();
    const installed = data.installed || [];
    const errors = data.errors || [];
    const fresh = installed.filter(i => i.status === 'installed');
    const existing = installed.filter(i => i.status === 'already_installed');

    let msg = '';
    if (fresh.length) msg += `Installed ${fresh.length} skill${fresh.length > 1 ? 's' : ''}. `;
    if (existing.length) msg += `${existing.length} already present. `;
    if (errors.length) msg += `${errors.length} failed. `;

    if (fresh.length || existing.length) {
      showToast(msg.trim() || 'Done!', 'success');
      container.querySelectorAll('.skill-checkbox:checked').forEach(cb => cb.checked = false);
      updateSelectedCount();
      markInstalled(container, installed.map(i => i.id));
    } else {
      showToast(errors.map(e => e.id).join(', ') + ' failed', 'error');
    }
  } catch (err) {
    showToast(`Install failed: ${err.message}`, 'error');
  } finally {
    if (installBtn) { installBtn.disabled = false; installBtn.innerHTML = 'Install Selected'; }
  }
}

function markInstalled(container, ids) {
  const set = new Set(ids);
  container.querySelectorAll('.skill-item').forEach(item => {
    if (set.has(item.dataset.id)) {
      item.classList.add('is-installed');
      const btn = item.querySelector('.skill-install-btn');
      if (btn) { btn.disabled = true; btn.textContent = 'Installed'; btn.className = 'btn btn-sm btn-installed'; }
    }
  });
}
