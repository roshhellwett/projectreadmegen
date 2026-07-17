// src/router.js — Lightweight hash-based SPA router with animated page transitions

const routes = new Map();
let currentPageId = null;
let currentCleanup = null;
let isTransitioning = false;

export function registerRoute(hash, { title, render, init, cleanup }) {
  routes.set(hash, { title, render, init, cleanup });
}

export function navigateTo(hash) {
  if (hash === currentPageId && document.getElementById('app-page-container')?.children.length) return;
  window.location.hash = hash;
}

export function getCurrentRoute() {
  return currentPageId;
}

export async function mountRoute(hash) {
  if (isTransitioning) return;
  const route = routes.get(hash);
  if (!route) {
    // Fallback to first registered route
    const fallback = routes.keys().next().value;
    if (fallback && fallback !== hash) {
      window.location.hash = fallback;
    }
    return;
  }

  const container = document.getElementById('app-page-container');
  if (!container) return;

  isTransitioning = true;

  // Run cleanup for previous page
  if (currentCleanup) {
    try { currentCleanup(); } catch (e) { console.error('[Router] cleanup error:', e); }
    currentCleanup = null;
  }

  // Animate out current content
  if (container.children.length > 0) {
    container.classList.add('page-exit');
    await waitForAnimation(container, 180);
    container.classList.remove('page-exit');
  }

  // Clear and render new page
  container.innerHTML = '';
  const html = route.render();
  container.innerHTML = html;

  // Animate in new content
  container.classList.add('page-enter');
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      container.classList.remove('page-enter');
    });
  });

  // Update sidebar active state
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-route') === hash);
  });

  // Update topbar title
  const titleEl = document.getElementById('current-section-title');
  if (titleEl) {
    titleEl.style.opacity = '0';
    titleEl.style.transform = 'translateY(-4px)';
    setTimeout(() => {
      titleEl.textContent = route.title;
      titleEl.style.opacity = '1';
      titleEl.style.transform = 'translateY(0)';
    }, 100);
  }

  currentPageId = hash;

  // Initialize page logic
  if (route.init) {
    try {
      const cleanup = await route.init();
      if (typeof cleanup === 'function') currentCleanup = cleanup;
    } catch (e) {
      console.error('[Router] init error:', e);
    }
  }

  isTransitioning = false;
}

function waitForAnimation(el, ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export function initRouter() {
  const handleHash = () => {
    const hash = window.location.hash || '#/studio';
    mountRoute(hash);
  };

  window.addEventListener('hashchange', handleHash);

  // Mount initial route
  handleHash();
}
