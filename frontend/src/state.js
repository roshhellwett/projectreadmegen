// src/state.js — Lightweight reactive shared state for cross-page data
// Provides a centralized store so all pages stay in sync without direct DOM coupling.

const listeners = new Map();

const state = {
  projectPath: '.',
  scanResult: null,
  detection: null,
  apiKeyConfigured: false,
  currentRoute: '#/studio',
};

export function getState() {
  return { ...state };
}

export function setState(key, value) {
  if (state[key] === value) return;
  state[key] = value;
  const fns = listeners.get(key) || [];
  fns.forEach(fn => {
    try { fn(value, key); } catch (e) { console.error('[State] listener error:', e); }
  });
}

export function onStateChange(key, fn) {
  if (!listeners.has(key)) listeners.set(key, []);
  listeners.get(key).push(fn);
  return () => {
    const arr = listeners.get(key);
    if (arr) listeners.set(key, arr.filter(f => f !== fn));
  };
}

// Convenience: sync all path inputs on the currently visible page
export function syncPathInputs(newPath) {
  setState('projectPath', newPath);
  const ids = ['scanner-path', 'ai-path', 'mindmap-path', 'git-path', 'skills-path'];
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el && el.value !== newPath) {
      el.value = newPath;
      el.title = newPath;
    }
  });
}
