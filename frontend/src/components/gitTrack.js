import { showToast } from '../main.js';
import { marked } from 'marked';
import hljs from 'highlight.js';
import { computeGitPositions } from '../gittrack/treeLayout.js';

let currentCommits = [];
let currentBranches = [];
let nodePositions = {};
let laneMap = {};
let selectedCommitId = null;
let customPositions = {};  // hash -> {x, y} user-dragged overrides
let scale = 1.0;
let panX = 0;
let panY = 0;

// Canvas drag state
let isCanvasDragging = false;
let canvasDragStartX = 0;
let canvasDragStartY = 0;

// Node drag state
let draggingNodeId = null;
let dragNodeStartX = 0;
let dragNodeStartY = 0;
let dragAccum = 0;
const DRAG_THRESHOLD = 4;

const NODE_RADIUS = 14;
const LANE_WIDTH = 46;
const NODE_Y_START = 50;
const NODE_Y_STEP = 54;
const CROSSHAIR_R = 20;

export function initGitTrack() {
  const btnLoad = document.getElementById('btn-git-load');
  const btnRefresh = document.getElementById('btn-git-refresh');
  const inputPath = document.getElementById('git-path');
  const svg = document.getElementById('git-svg');
  const container = document.getElementById('git-canvas-container');

  const btnZoomIn = document.getElementById('btn-git-zoomin');
  const btnZoomOut = document.getElementById('btn-git-zoomout');
  const btnResetZoom = document.getElementById('btn-git-reset');
  const btnFitView = document.getElementById('btn-git-fit');
  const layoutBtns = document.querySelectorAll('#git-layout-pills .pill-btn');

  if (container) {
    ensureGitToolbar(container);
    ensureGitTooltip(container);
  }

  btnLoad?.addEventListener('click', () => loadGitGraph(inputPath?.value || '.'));
  btnRefresh?.addEventListener('click', () => loadGitGraph(inputPath?.value || '.'));

  inputPath?.addEventListener('input', () => {
    const sPath = document.getElementById('scanner-path');
    const aPath = document.getElementById('ai-path');
    const mPath = document.getElementById('mindmap-path');
    if (sPath) sPath.value = inputPath.value;
    if (aPath) aPath.value = inputPath.value;
    if (mPath) mPath.value = inputPath.value;
  });

  inputPath?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') loadGitGraph(inputPath.value || '.');
  });

  btnZoomIn?.addEventListener('click', () => { scale = Math.min(scale * 1.25, 3.5); applyGitTransform(); });
  btnZoomOut?.addEventListener('click', () => { scale = Math.max(scale / 1.25, 0.2); applyGitTransform(); });
  btnResetZoom?.addEventListener('click', () => { scale = 1.0; panX = 0; panY = 0; applyGitTransform(); });
  btnFitView?.addEventListener('click', () => { fitGitToScreen(); });

  layoutBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      layoutBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      computeLayout();
      if (svg) { renderGitGraph(svg); fitGitToScreen(); }
    });
  });

  if (container) {
    container.addEventListener('mousedown', (e) => {
      if (e.target.closest('.git-commit-group') || e.target.closest('.graph-floating-toolbar') || e.target.closest('.graph-tooltip')) return;
      isCanvasDragging = true;
      canvasDragStartX = e.clientX - panX;
      canvasDragStartY = e.clientY - panY;
      container.style.cursor = 'grabbing';
    });

    container.addEventListener('wheel', (e) => {
      e.preventDefault();
      const zf = e.deltaY < 0 ? 1.12 : 0.89;
      scale = Math.min(Math.max(scale * zf, 0.2), 3.0);
      applyGitTransform();
    }, { passive: false });
  }

  if (!window._isGitTrackEventsAttached) {
    window._isGitTrackEventsAttached = true;
    window.addEventListener('mousemove', (e) => {
      if (draggingNodeId && nodePositions[draggingNodeId]) {
        const dx = (e.clientX - dragNodeStartX) / scale;
        const dy = (e.clientY - dragNodeStartY) / scale;
        dragAccum += Math.abs(e.clientX - dragNodeStartX) + Math.abs(e.clientY - dragNodeStartY);
        dragNodeStartX = e.clientX;
        dragNodeStartY = e.clientY;

        const cur = nodePositions[draggingNodeId];
        cur.x += dx;
        cur.y += dy;
        customPositions[draggingNodeId] = { x: cur.x, y: cur.y };

        const svg = document.getElementById('git-svg');
        const nodeEl = svg?.querySelector(`.git-commit-group[data-id="${draggingNodeId}"]`);
        if (nodeEl) nodeEl.setAttribute('transform', `translate(${cur.x}, ${cur.y})`);

        updateGitEdgesDOM(draggingNodeId, svg);
        return;
      }

      if (isCanvasDragging) {
        panX = e.clientX - canvasDragStartX;
        panY = e.clientY - canvasDragStartY;
        applyGitTransform();
      }
    });

    window.addEventListener('mouseup', () => {
      if (draggingNodeId) draggingNodeId = null;
      if (isCanvasDragging) {
        isCanvasDragging = false;
        const c = document.getElementById('git-canvas-container');
        if (c) c.style.cursor = 'grab';
      }
    });
  }

  svg?.addEventListener('click', (e) => {
    if (e.target === svg || e.target.classList.contains('empty-mindmap') || e.target.tagName === 'text') {
      selectedCommitId = null;
      renderInspector(null);
    }
  });
}

function ensureGitToolbar(container) {
  let toolbar = container.querySelector('#git-toolbar');
  if (!toolbar) {
    toolbar = document.createElement('div');
    toolbar.className = 'graph-floating-toolbar';
    toolbar.id = 'git-toolbar';
    toolbar.innerHTML = `
      <input type="text" id="git-search-input" class="graph-search-input" placeholder="Search commits & branches..." />
      <div class="graph-toolbar-divider"></div>
      <button class="graph-toolbar-btn" id="btn-git-reset" title="Reset Zoom">Reset</button>
      <button class="graph-toolbar-btn" id="btn-git-fit" title="Fit to Screen">Fit</button>
      <div class="graph-toolbar-divider"></div>
      <span class="graph-zoom-label" id="git-zoom-display">100%</span>
    `;
    container.appendChild(toolbar);

    const searchInput = toolbar.querySelector('#git-search-input');
    searchInput?.addEventListener('input', (e) => {
      const q = e.target.value.trim().toLowerCase();
      const svg = document.getElementById('git-svg');
      if (!svg) return;
      svg.querySelectorAll('.git-commit-group').forEach(group => {
        const hash = (group.getAttribute('data-id') || '').toLowerCase();
        const msg = (group.getAttribute('data-msg') || '').toLowerCase();
        const author = (group.getAttribute('data-author') || '').toLowerCase();
        if (!q || hash.includes(q) || msg.includes(q) || author.includes(q)) {
          group.style.opacity = '1';
        } else {
          group.style.opacity = '0.15';
        }
      });
      if (q && currentCommits.length > 0) {
        const match = currentCommits.find(c => (c.message || '').toLowerCase().includes(q) || (c.hash_short || '').toLowerCase().includes(q) || (c.hash || '').toLowerCase().includes(q) || (c.author || '').toLowerCase().includes(q));
        if (match && (nodePositions[match.hash_short] || nodePositions[match.hash])) {
          const pos = nodePositions[match.hash_short] || nodePositions[match.hash];
          const cW = svg.clientWidth || 1100;
          const cH = svg.clientHeight || 520;
          panX = (cW / 2) - (pos.x * scale);
          panY = (cH / 2) - (pos.y * scale);
          applyGitTransform();
        }
      }
    });

    toolbar.querySelector('#btn-git-reset')?.addEventListener('click', () => { scale = 1.0; panX = 0; panY = 0; applyGitTransform(); });
    toolbar.querySelector('#btn-git-fit')?.addEventListener('click', () => { fitGitToScreen(); });
  }
}

function ensureGitTooltip(container) {
  let tooltip = container.querySelector('.graph-tooltip');
  if (!tooltip) {
    tooltip = document.createElement('div');
    tooltip.className = 'graph-tooltip';
    container.appendChild(tooltip);
  }
}

function showGitTooltipAt(commit, e, container) {
  const tooltip = container.querySelector('.graph-tooltip');
  if (!tooltip || !commit) return;
  tooltip.innerHTML = `
    <div class="graph-tooltip-title"><span class="graph-tooltip-badge">${commit.hash_short}</span><span>${commit.author || 'Unknown Author'}</span></div>
    <div style="color:#ffffff;margin-top:4px;font-size:0.78rem;font-weight:600;">${commit.message || 'No message'}</div>
    <div class="graph-tooltip-meta">
      <span>Committed: ${commit.date_rel || 'N/A'}</span>
      <span>Changed files: ${(commit.files || []).length}</span>
    </div>
  `;
  tooltip.classList.add('show');
  moveGitTooltip(e, container);
}

function moveGitTooltip(e, container) {
  const tooltip = container.querySelector('.graph-tooltip');
  if (!tooltip || !tooltip.classList.contains('show')) return;
  const rect = container.getBoundingClientRect();
  const x = Math.min(e.clientX - rect.left + 14, rect.width - 330);
  const y = Math.min(e.clientY - rect.top + 14, rect.height - 120);
  tooltip.style.left = `${Math.max(10, x)}px`;
  tooltip.style.top = `${Math.max(10, y)}px`;
}

function hideGitTooltip(container) {
  const tooltip = container?.querySelector('.graph-tooltip');
  if (tooltip) tooltip.classList.remove('show');
}

function applyGitTransform() {
  const g = document.getElementById('git-transform-group');
  if (g) g.style.transform = `translate(${panX}px, ${panY}px) scale(${scale})`;
  const zl = document.getElementById('git-zoom-display');
  if (zl) zl.textContent = Math.round(scale * 100) + '%';
}

async function loadGitGraph(dir) {
  const btnLoad = document.getElementById('btn-git-load');
  const svg = document.getElementById('git-svg');
  if (!svg) return;

  btnLoad.disabled = true;
  btnLoad.innerHTML = '<span class="spinner-ring" style="width:16px;height:16px;border-width:2px;"></span><span>Loading graph...</span>';
  selectedCommitId = null;
  customPositions = {};

  try {
    const resp = await fetch(`/api/git/graph?dir=${encodeURIComponent(dir)}&count=80`);
    const data = await resp.json();

    if (!resp.ok || data.status !== 'success') {
      throw new Error(data.detail || 'Failed to load git graph');
    }

    currentCommits = data.commits || [];
    currentBranches = data.branches || [];
    nodePositions = {};
    laneMap = {};

    updateStatusBar(data.git_status || {}, data.head_branch || '');

    const commitCount = document.getElementById('git-commit-count');
    if (commitCount) commitCount.textContent = `Commits: ${currentCommits.length}`;

    if (currentCommits.length === 0) {
      svg.innerHTML = `<g class="empty-mindmap"><text x="600" y="300" text-anchor="middle" class="empty-text">No commits found in this repository</text></g>`;
      btnLoad.disabled = false;
      btnLoad.innerHTML = '<span>Load Git Graph</span>';
      return;
    }

    computeLayout();
    renderGitGraph(svg);
    fitGitToScreen();

    showToast(`Loaded ${currentCommits.length} commits`, 'success');
  } catch (err) {
    console.error('Git graph error:', err);
    svg.innerHTML = `<g class="empty-mindmap"><text x="600" y="300" text-anchor="middle" class="empty-text">${err.message || 'Error loading git graph'}</text></g>`;
    showToast(err.message || 'Error loading git graph', 'error');
  } finally {
    btnLoad.disabled = false;
    btnLoad.innerHTML = '<span>Load Git Graph</span>';
  }
}

function updateStatusBar(gitStatus, headBranch) {
  const bar = document.getElementById('git-status-bar');
  if (!bar) return;
  const modified = (gitStatus.modified || []).length;
  const staged = (gitStatus.staged || []).length;
  const untracked = (gitStatus.untracked || []).length;
  bar.innerHTML = `
    <span class="git-status-chip git-modified">Modified: ${modified}</span>
    <span class="git-status-chip git-staged">Staged: ${staged}</span>
    <span class="git-status-chip git-untracked">Untracked: ${untracked}</span>
    <span class="git-branch-label" id="git-current-branch">${headBranch}</span>
  `;
}

function computeLayout() {
  if (currentCommits.length === 0) return;
  const result = computeGitPositions(currentCommits, customPositions);
  laneMap = result.laneMap || {};
  nodePositions = result.nodePositions || {};
}

function truncateString(str, len) {
  if (str === null || str === undefined) return '';
  if (typeof str !== 'string') str = String(str);
  return str.length > len ? str.substring(0, len - 2) + '..' : str;
}

function renderGitGraph(svg) {
  const container = document.getElementById('git-canvas-container');
  if (container) {
    ensureGitToolbar(container);
    ensureGitTooltip(container);
  }

  let pathsHTML = '';
  let nodesHTML = '';

  const allHashes = new Set(currentCommits.map(c => c.hash_short));
  const branchColorMap = {};
  const branchHeadMap = {};
  currentBranches.forEach(b => {
    branchColorMap[b.head] = b.color;
    if (!branchHeadMap[b.head]) branchHeadMap[b.head] = [];
    branchHeadMap[b.head].push(b);
  });
  const defaultColor = '#52525b';

  const nodeWidth = 400;
  const nodeHeight = 40;
  const halfW = nodeWidth / 2;
  const halfH = nodeHeight / 2;
  const cardStartX = 260;
  const dotRadius = 6;

  const edgeDrawn = new Set();
  currentCommits.forEach(commit => {
    const hash = commit.hash_short;
    const parents = commit.parents_short || [];
    const pos = nodePositions[hash];
    if (!pos) return;

    parents.forEach(parent => {
      if (!allHashes.has(parent)) return;
      const key = `${hash}->${parent}`;
      if (edgeDrawn.has(key)) return;
      edgeDrawn.add(key);

      const pPos = nodePositions[parent];
      if (!pPos) return;

      const srcBottom = pos.y + dotRadius;
      const tgtTop = pPos.y - dotRadius;
      let d;
      if (pos.x === pPos.x) {
        d = `M ${pos.x} ${srcBottom} L ${pPos.x} ${tgtTop}`;
      } else {
        const midY = (srcBottom + tgtTop) / 2;
        d = `M ${pos.x} ${srcBottom} C ${pos.x} ${midY}, ${pPos.x} ${midY}, ${pPos.x} ${tgtTop}`;
      }
      const color = branchColorMap[hash] || branchColorMap[parent] || defaultColor;
      pathsHTML += `<path class="git-edge" d="${d}" stroke="${color}" opacity="0.65" data-source="${hash}" data-target="${parent}" />`;
    });
  });

  currentCommits.forEach(commit => {
    const hash = commit.hash_short;
    const pos = nodePositions[hash];
    if (!pos) return;

    const isSelected = selectedCommitId === hash ? ' selected' : '';
    const color = branchColorMap[hash] || defaultColor;
    const hashShort = hash.substring(0, 5);

    const msg = (commit.message || 'No commit message').trim();
    const authorRel = `${commit.author || 'Anon'} • ${commit.date_rel || ''}`;

    const branchesAtHead = branchHeadMap[hash] || [];
    let branchLabelsHTML = '';
    if (branchesAtHead.length > 0) {
      let bOffset = nodeWidth + 14;
      branchesAtHead.forEach(b => {
        const lw = Math.max(b.name.length * 7 + 16, 36);
        branchLabelsHTML += `
          <g class="git-branch-label-group" transform="translate(${bOffset}, ${halfH - 11})">
            <rect class="git-branch-tag-bg" width="${lw}" height="22" rx="6" fill="${b.color}" />
            <text class="git-branch-tag" x="${lw / 2}" y="11" text-anchor="middle">${b.name}</text>
          </g>
        `;
        bOffset += lw + 8;
      });
    }

    const laneConnectorHTML = `<line class="git-lane-connector" x1="${pos.x + dotRadius + 2}" y1="${pos.y}" x2="${cardStartX}" y2="${pos.y}" stroke="${color}" stroke-width="1.5" stroke-dasharray="3,3" opacity="0.45" />`;
    const laneDotHTML = `<circle class="git-node-dot" cx="${pos.x}" cy="${pos.y}" r="${dotRadius}" fill="${color}" stroke="#18181b" stroke-width="2" style="filter: drop-shadow(0 1px 3px rgba(0,0,0,0.3));" />`;

    nodesHTML += `
      ${laneConnectorHTML}
      ${laneDotHTML}
      <g class="git-commit-group${isSelected}" data-id="${hash}" data-msg="${commit.message || ''}" data-author="${commit.author || ''}" transform="translate(${cardStartX}, ${pos.y - halfH})" style="cursor: pointer;">
        <clipPath id="card-clip-${hash}">
          <rect width="${nodeWidth}" height="${nodeHeight}" rx="10" />
        </clipPath>
        <rect class="node-rect git-commit-card-bg" width="${nodeWidth}" height="${nodeHeight}" rx="10" />
        <rect class="node-accent" x="0" y="0" width="6" height="${nodeHeight}" fill="${color}" clip-path="url(#card-clip-${hash})" />
        <text class="git-commit-hash" x="22" y="${halfH}" text-anchor="start" style="font-size:11px; font-weight:700; font-family:var(--font-mono, monospace);">${hashShort}</text>
        <text class="git-commit-msg" x="76" y="${halfH}" text-anchor="start" style="font-size:12px;">${truncateString(msg, 36)}</text>
        <text class="git-commit-meta-text" x="${nodeWidth - 14}" y="${halfH}" text-anchor="end" style="font-size:11px;">${authorRel}</text>
        ${branchLabelsHTML}
      </g>`;
  });

  svg.innerHTML = `
    <g id="git-transform-group" style="transform: translate(${panX}px, ${panY}px) scale(${scale});">
      <g class="git-edges-layer">${pathsHTML}</g>
      <g class="git-nodes-layer">${nodesHTML}</g>
    </g>
  `;

  svg.querySelectorAll('.git-commit-group').forEach(el => {
    const id = el.getAttribute('data-id');

    el.addEventListener('click', (e) => {
      e.stopPropagation();
      selectCommit(id);
    });

    el.addEventListener('mousedown', (e) => {
      e.stopPropagation();
    });

    el.addEventListener('mouseenter', (e) => {
      svg.querySelectorAll('.git-edge').forEach(path => {
        const src = path.getAttribute('data-source');
        const tgt = path.getAttribute('data-target');
        if (src === id || tgt === id) {
          path.classList.add('edge-highlighted');
          path.classList.remove('edge-dimmed');
        } else {
          path.classList.add('edge-dimmed');
          path.classList.remove('edge-highlighted');
        }
      });
      const commitObj = currentCommits.find(c => c.hash_short === id);
      if (commitObj && container) showGitTooltipAt(commitObj, e, container);
    });

    el.addEventListener('mousemove', (e) => {
      if (container) moveGitTooltip(e, container);
    });

    el.addEventListener('mouseleave', () => {
      svg.querySelectorAll('.git-edge').forEach(path => {
        path.classList.remove('edge-highlighted', 'edge-dimmed');
      });
      if (container) hideGitTooltip(container);
    });
  });
}

function selectCommit(hash) {
  selectedCommitId = hash;
  const svg = document.getElementById('git-svg');
  if (svg) {
    svg.querySelectorAll('.git-commit-group').forEach(g => g.classList.remove('selected'));
    const el = svg.querySelector(`.git-commit-group[data-id="${hash}"]`);
    if (el) el.classList.add('selected');
  }
  const commit = currentCommits ? currentCommits.find(c => c.hash_short === hash || c.hash === hash) : null;
  renderInspector(commit);
}

function updateGitEdgesDOM(nodeId, svg) {
  if (!svg || !nodePositions[nodeId]) return;
  const dotRadius = 6;
  svg.querySelectorAll(`.git-edge[data-source="${nodeId}"], .git-edge[data-target="${nodeId}"]`).forEach(path => {
    const src = path.getAttribute('data-source');
    const tgt = path.getAttribute('data-target');
    const sPos = nodePositions[src];
    const tPos = nodePositions[tgt];
    if (!sPos || !tPos) return;
    const srcBottom = sPos.y + dotRadius;
    const tgtTop = tPos.y - dotRadius;
    let d;
    if (sPos.x === tPos.x) {
      d = `M ${sPos.x} ${srcBottom} L ${tPos.x} ${tgtTop}`;
    } else {
      const midY = (srcBottom + tgtTop) / 2;
      d = `M ${sPos.x} ${srcBottom} C ${sPos.x} ${midY}, ${tPos.x} ${midY}, ${tPos.x} ${tgtTop}`;
    }
    path.setAttribute('d', d);
  });
}

function renderInspector(commit) {
  const container = document.getElementById('git-inspector-content');
  if (!container) return;

  if (!commit) {
    container.innerHTML = `
      <div class="empty-state" style="padding: 40px 16px;">
        <h4>Select a Commit</h4>
        <p>Click on any commit node on the graph to inspect its changes, files, and diff.</p>
      </div>`;
    return;
  }

  const files = commit.files || [];
  const filesHTML = files.length > 0
    ? files.map(f => {
        const fullHash = commit.hash || commit.hash_short || '';
        return `<div class="git-file-row" data-hash="${fullHash}" data-file="${f}" title="Click to inspect diff for ${f}">
          <span class="git-file-path" style="word-break: break-all; font-family: var(--font-mono); font-size: 0.76rem;">${f}</span>
          <span class="git-file-action badge badge-mono" style="margin-left: 8px; flex-shrink: 0; font-size: 0.68rem; background: var(--bg-subtle); border: 1px solid var(--border-color);">view diff ↗</span>
        </div>`;
      }).join('')
    : '<span class="text-xs text-secondary" style="display:block;padding:8px 0;">No file changes (merge or empty commit).</span>';

  container.innerHTML = `
    <div class="inspector-header">
      <div class="inspector-badge" style="background: #6366f1;">COMMIT</div>
      <h4 class="inspector-title" style="margin-top: 6px; font-weight: 700; color: var(--text-primary); line-height: 1.4;">${commit.message || 'No commit message'}</h4>
      <p class="inspector-path" style="margin-top: 4px; font-family: var(--font-mono);">
        <strong style="color: var(--text-primary);">${commit.hash_short}</strong> • ${commit.author || 'Unknown'} • ${commit.date_rel || ''}
      </p>
      ${commit.refs ? `<div class="mt-2"><span class="badge badge-mono" style="background: rgba(99, 102, 241, 0.15); color: #6366f1; border: 1px solid rgba(99, 102, 241, 0.3); font-size: 0.72rem;">Refs: ${commit.refs}</span></div>` : ''}
    </div>

    <div class="inspector-section mt-3">
      <span class="section-label">Changed Files (${files.length})</span>
      <div class="git-files-list" style="display: flex; flex-direction: column; gap: 6px; max-height: 260px; overflow-y: auto; padding-right: 4px; margin-top: 2px;">
        ${filesHTML}
      </div>
    </div>
    <div id="git-diff-container" class="mt-3"></div>
  `;

  container.querySelectorAll('.git-file-row').forEach(row => {
    row.addEventListener('click', async () => {
      const file = row.getAttribute('data-file');
      const hash = row.getAttribute('data-hash');
      if (!file) return;

      const diffContainer = document.getElementById('git-diff-container');
      if (!diffContainer) return;

      const existing = document.querySelector(`.git-diff-view[data-file="${file}"]`);
      if (existing) { 
        existing.classList.toggle('open'); 
        row.classList.toggle('active');
        return; 
      }

      row.classList.add('active');
      const loadEl = document.createElement('div');
      loadEl.className = 'git-diff-view open';
      loadEl.setAttribute('data-file', file);
      loadEl.innerHTML = `<div class="git-diff-header"><span>Diff: ${file}</span><span class="diff-header-hash">Loading...</span></div><div style="display:flex;align-items:center;gap:10px;padding:8px 0;color:#a1a1aa;font-family:var(--font-mono);font-size:0.75rem;"><span class="spinner-ring" style="width:14px;height:14px;border-width:2px;"></span> Loading diff...</div>`;
      diffContainer.appendChild(loadEl);

      try {
        const dir = document.getElementById('git-path')?.value || '.';
        const resp = await fetch(`/api/git/diff?file=${encodeURIComponent(file)}&hash=${hash}&dir=${encodeURIComponent(dir)}`);
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.detail || 'Failed to load diff');

        loadEl.innerHTML = `<div class="git-diff-header"><span>Diff: ${file}</span><span class="diff-header-hash">${hash}</span></div>`;
        const pre = document.createElement('pre');
        pre.className = 'git-diff-code-wrapper';
        const code = document.createElement('code');
        code.className = 'language-diff';
        code.textContent = data.diff || '(empty diff)';
        pre.appendChild(code);
        loadEl.appendChild(pre);
        try { hljs.highlightElement(code); } catch (e) {}

        if (code.innerHTML && !code.querySelector('.diff-line-add, .diff-line-del')) {
          const lines = code.innerHTML.split('\n');
          code.innerHTML = lines.map(l => {
            const stripped = l.replace(/<[^>]*>/g, '');
            if (stripped.startsWith('+') && !stripped.startsWith('+++')) {
              return `<span class="diff-line-add">${l}</span>`;
            } else if (stripped.startsWith('-') && !stripped.startsWith('---')) {
              return `<span class="diff-line-del">${l}</span>`;
            } else if (stripped.startsWith('@@')) {
              return `<span class="diff-line-chunk">${l}</span>`;
            } else if (stripped.startsWith('diff ') || stripped.startsWith('index ')) {
              return `<span class="diff-line-meta">${l}</span>`;
            }
            return l;
          }).join('\n');
        }
      } catch (err) {
        loadEl.innerHTML = `<div class="git-diff-header" style="border-color: rgba(239, 68, 68, 0.4);"><span style="color: #ef4444 !important;">Diff: ${file}</span><span class="diff-header-hash">Error</span></div><div style="color: #f87171; font-family: var(--font-mono); font-size: 0.75rem;">${err.message}</div>`;
      }
    });
  });
}

function fitGitToScreen() {
  const ids = Object.keys(nodePositions);
  if (ids.length === 0) return;

  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  ids.forEach(id => {
    const p = nodePositions[id];
    if (p.x < minX) minX = p.x;
    if (p.x > maxX) maxX = p.x;
    if (p.y < minY) minY = p.y;
    if (p.y > maxY) maxY = p.y;
  });

  const svg = document.getElementById('git-svg');
  const cW = svg?.clientWidth || 1100;
  const cH = svg?.clientHeight || 520;
  const cardRight = 260 + 460;
  const gW = Math.max(cardRight - minX + 120, 600);
  const gH = Math.max(maxY - minY + 200, 400);
  scale = Math.min(Math.max(Math.min(cW / gW, cH / gH) * 0.88, 0.25), 1.6);
  const cx = (minX + cardRight) / 2;
  const cy = (minY + maxY) / 2;
  panX = (cW / 2) - (cx * scale);
  panY = (cH / 2) - (cy * scale);
  applyGitTransform();
}
