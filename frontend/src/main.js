import './index.css';
import { initScannerStudio } from './components/scannerStudio.js';
import { initAIStudio } from './components/aiStudio.js';
import { initProfileStudio } from './components/profileStudio.js';
import { initMindMapStudio } from './components/mindmapStudio.js';
import { initGitTrack } from './components/gitTrack.js';
import { initDashboard, checkAPIStatus } from './components/dashboard.js';
import { initSkillsStudio } from './components/skillsStudio.js';

document.addEventListener('DOMContentLoaded', async () => {
  console.log('Project README Gen Studio 7.0.0 initialized');

  // Sidebar hamburger toggle
  const hamburgerBtn = document.getElementById('hamburger-toggle');
  const sidebar = document.querySelector('.app-sidebar');
  const overlay = document.createElement('div');
  overlay.className = 'sidebar-overlay';
  overlay.id = 'sidebar-overlay';
  document.body.appendChild(overlay);

  function closeSidebar() {
    sidebar?.classList.remove('open');
    overlay?.classList.remove('open');
  }
  function toggleSidebar() {
    sidebar?.classList.toggle('open');
    overlay?.classList.toggle('open');
  }

  hamburgerBtn?.addEventListener('click', (e) => { e.stopPropagation(); toggleSidebar(); });
  overlay?.addEventListener('click', closeSidebar);

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeSidebar();
  });

  // Navigation Tab Switching
  const navBtns = document.querySelectorAll('.nav-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  let currentTabId = 'tab-scanner';

  navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTabId = btn.getAttribute('data-tab');
      if (targetTabId === currentTabId) { closeSidebar(); return; }

      navBtns.forEach(b => b.classList.remove('active'));
      tabPanes.forEach(p => p.classList.remove('active'));

      btn.classList.add('active');
      const targetPane = document.getElementById(targetTabId);
      if (targetPane) {
        targetPane.classList.add('active');
        targetPane.style.animation = 'none';
        requestAnimationFrame(() => {
          targetPane.style.animation = '';
        });
      }
      currentTabId = targetTabId;

      if (targetTabId === 'tab-mindmap') {
        const mPath = document.getElementById('mindmap-path');
        const sPath = document.getElementById('scanner-path');
        if (mPath && sPath && (!mPath.value || mPath.value === '.')) {
          if (sPath.value && sPath.value !== '.') mPath.value = sPath.value;
        }
        const svg = document.getElementById('mindmap-svg');
        const btnScanMindMap = document.getElementById('btn-scan-mindmap');
        if (svg && svg.querySelector('.empty-mindmap') && btnScanMindMap) {
          btnScanMindMap.click();
        }
      } else if (targetTabId === 'tab-git') {
        const gPath = document.getElementById('git-path');
        const sPath = document.getElementById('scanner-path');
        if (gPath && sPath && (!gPath.value || gPath.value === '.')) {
          if (sPath.value && sPath.value !== '.') gPath.value = sPath.value;
        }
        const svg = document.getElementById('git-svg');
        const btnGitLoad = document.getElementById('btn-git-load');
        if (svg && svg.querySelector('.empty-mindmap') && btnGitLoad) {
          btnGitLoad.click();
        }
      }

      const topbarTitle = document.getElementById('current-section-title');
      if (topbarTitle) {
        topbarTitle.textContent = btn.textContent.trim();
      }

      closeSidebar();
    });
  });

  // Initialize Studios
  initScannerStudio();
  initAIStudio();
  initProfileStudio();
  initMindMapStudio();
  initGitTrack();
  initDashboard();
  initSkillsStudio();

  // Initial API check
  await checkAPIStatus();
});

export function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  const prefix = type === 'success' ? 'Success:' : type === 'error' ? 'Error:' : 'Info:';
  toast.className = `toast ${type}`;
  toast.innerHTML = `<strong>${prefix}</strong><span>${message}</span>`;
  toast.setAttribute('role', 'alert');
  toast.setAttribute('aria-live', 'polite');

  container.appendChild(toast);

  requestAnimationFrame(() => {
    toast.style.transition = 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)';
  });

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}
