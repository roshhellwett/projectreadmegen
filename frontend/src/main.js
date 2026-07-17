import './index.css';
import { registerRoute, initRouter, navigateTo } from './router.js';
import { syncPathInputs, getState } from './state.js';

// Page renderers
import { renderStudioPage } from './pages/studioPage.js';
import { renderAIPage } from './pages/aiPage.js';
import { renderProfilePage } from './pages/profilePage.js';
import { renderMindmapPage } from './pages/mindmapPage.js';
import { renderGitPage } from './pages/gitPage.js';
import { renderSkillsPage } from './pages/skillsPage.js';
import { renderSettingsPage } from './pages/settingsPage.js';

// Component initializers
import { initScannerStudio } from './components/scannerStudio.js';
import { initAIStudio } from './components/aiStudio.js';
import { initProfileStudio } from './components/profileStudio.js';
import { initMindMapStudio } from './components/mindmapStudio.js';
import { initGitTrack } from './components/gitTrack.js';
import { initDashboard, checkAPIStatus } from './components/dashboard.js';
import { initSkillsStudio } from './components/skillsStudio.js';

// Track which pages have been initialized (for one-time auto-triggers)
const pageInitState = {
  studio: false,
  mindmap: false,
  git: false,
  skills: false,
};

document.addEventListener('DOMContentLoaded', async () => {
  console.log('Project README Gen Studio 8.0 — Premium Architecture initialized');

  // ─── Sidebar hamburger toggle ──────────────────────────
  const hamburgerBtn = document.getElementById('hamburger-toggle');
  const sidebar = document.getElementById('app-sidebar');
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

  hamburgerBtn?.addEventListener('click', (e) => {
    e.stopPropagation();
    toggleSidebar();
  });
  overlay?.addEventListener('click', closeSidebar);
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeSidebar();
  });

  // ─── Register routes ──────────────────────────────────
  registerRoute('#/studio', {
    title: 'Project Studio',
    render: renderStudioPage,
    init: () => {
      syncPathInputs(getState().projectPath);
      initScannerStudio();
      if (!pageInitState.studio) {
        pageInitState.studio = true;
        // Auto-scan on first visit
        setTimeout(() => {
          document.getElementById('btn-scan')?.click();
        }, 100);
      }
    },
  });

  registerRoute('#/ai', {
    title: 'AI Architect',
    render: renderAIPage,
    init: () => {
      syncPathInputs(getState().projectPath);
      initAIStudio();
    },
  });

  registerRoute('#/profile', {
    title: 'GitHub Profile',
    render: renderProfilePage,
    init: () => {
      initProfileStudio();
    },
  });

  registerRoute('#/mindmap', {
    title: 'Mind Map Studio',
    render: renderMindmapPage,
    init: () => {
      syncPathInputs(getState().projectPath);
      initMindMapStudio();
      if (!pageInitState.mindmap) {
        pageInitState.mindmap = true;
        setTimeout(() => {
          const svg = document.getElementById('mindmap-svg');
          const btn = document.getElementById('btn-scan-mindmap');
          if (svg && svg.querySelector('.empty-mindmap') && btn) btn.click();
        }, 200);
      }
    },
  });

  registerRoute('#/git', {
    title: 'Git Track Studio',
    render: renderGitPage,
    init: () => {
      syncPathInputs(getState().projectPath);
      initGitTrack();
      if (!pageInitState.git) {
        pageInitState.git = true;
        setTimeout(() => {
          const svg = document.getElementById('git-svg');
          const btn = document.getElementById('btn-git-load');
          if (svg && svg.querySelector('.empty-mindmap') && btn) btn.click();
        }, 200);
      }
    },
  });

  registerRoute('#/skills', {
    title: 'Skills Studio',
    render: renderSkillsPage,
    init: () => {
      syncPathInputs(getState().projectPath);
      initSkillsStudio();
    },
  });

  registerRoute('#/settings', {
    title: 'Settings',
    render: renderSettingsPage,
    init: async () => {
      initDashboard();
      await checkAPIStatus();
    },
  });

  // ─── Sidebar navigation → route clicks ────────────────
  document.querySelectorAll('.nav-btn[data-route]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const route = btn.getAttribute('data-route');
      if (route) navigateTo(route);
      closeSidebar();
    });
  });

  // ─── Initialize Router ─────────────────────────────────
  initRouter();

  // ─── Initial API check ─────────────────────────────────
  await checkAPIStatus();
});

// ─── Global error boundary ─────────────────────────────
window.onerror = function (msg, source, line, col, error) {
  const code = 'UI-' + Math.random().toString(16).slice(2, 6).toUpperCase();
  showErrorDialog(code, msg || String(error), source ? source + ':' + line : '');
  return true;
};

window.addEventListener('unhandledrejection', function (e) {
  const code = 'UI-' + Math.random().toString(16).slice(2, 6).toUpperCase();
  const msg = e.reason?.message || String(e.reason);
  showErrorDialog(code, msg, '');
  e.preventDefault();
});

// ─── Toast Notification ────────────────────────────────
export function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  const prefix = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span class="toast-icon">${prefix}</span><span class="toast-msg">${message}</span>`;
  toast.setAttribute('role', 'alert');
  toast.setAttribute('aria-live', 'polite');

  container.appendChild(toast);

  requestAnimationFrame(() => {
    toast.classList.add('toast-visible');
  });

  setTimeout(() => {
    toast.classList.remove('toast-visible');
    toast.classList.add('toast-exit');
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ─── Error Dialog ──────────────────────────────────────
export function showErrorDialog(errorCode, message, detail) {
  const existing = document.getElementById('error-dialog-overlay');
  if (existing) existing.remove();

  const repoUrl = 'https://github.com/anomalyco/projectreadmegen/issues/new';
  const title = encodeURIComponent('Error ' + errorCode + ' - ' + (message ? message.slice(0, 60) : 'Unknown error'));
  const body = encodeURIComponent(
    '**Error Code:** ' + errorCode + '\n' +
    '**Message:** ' + (message || 'N/A') + '\n' +
    '**Detail:** ' + (detail || 'N/A') + '\n' +
    '**Page:** ' + window.location.href + '\n' +
    '**User Agent:** ' + navigator.userAgent + '\n' +
    '\n---\nPlease describe what you were doing when this error occurred.'
  );
  const issueUrl = repoUrl + '?title=' + title + '&body=' + body;

  const overlay = document.createElement('div');
  overlay.id = 'error-dialog-overlay';
  overlay.className = 'error-dialog-overlay';
  overlay.innerHTML =
    '<div class="error-dialog">' +
    '<div class="error-dialog-icon">&#x26A0;</div>' +
    '<h3 class="error-dialog-title">Something went wrong</h3>' +
    '<div class="error-dialog-code">Error Code: <strong>' + errorCode + '</strong></div>' +
    '<p class="error-dialog-msg">' + (message || 'An unexpected error occurred.') + '</p>' +
    (detail ? '<details class="error-detail"><summary>Technical Details</summary><pre>' + detail + '</pre></details>' : '') +
    '<div class="error-dialog-actions">' +
    '<button id="error-dialog-dismiss" class="btn btn-secondary">Dismiss</button>' +
    '<button id="error-dialog-report" class="btn btn-primary">Report on GitHub</button>' +
    '</div>' +
    '</div>';

  document.body.appendChild(overlay);

  document.getElementById('error-dialog-dismiss').addEventListener('click', function () {
    overlay.remove();
  });
  document.getElementById('error-dialog-report').addEventListener('click', function () {
    window.open(issueUrl, '_blank');
    overlay.remove();
  });
  overlay.addEventListener('click', function (e) {
    if (e.target === overlay) overlay.remove();
  });
}
