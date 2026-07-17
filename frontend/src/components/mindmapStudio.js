import { showToast } from '../main.js';
import { syncPathInputs } from '../state.js';
import { marked } from 'marked';
import hljs from 'highlight.js';
import { computeTreePositions } from '../mindmap/treeLayout.js';

let currentGraph = null;
let collapsedFolders = new Set();
let currentLayout = 'tree';
let currentFilter = 'all';
let selectedNodeId = 'root';
let lastInspectedNodeId = null;
let scale = 1.0;
let panX = 0;
let panY = 0;
let isCanvasDragging = false;
let startDragCanvasX = 0;
let startDragCanvasY = 0;
let dragAccumulatedDistance = 0;
const DRAG_THRESHOLD = 5;
let draggingNodeId = null;
let dragNodeStartX = 0;
let dragNodeStartY = 0;
let customPositions = {};
let activeNodePositions = {};

export function initMindMapStudio() {
  const btnScanMindMap = document.getElementById('btn-scan-mindmap');
  const inputPath = document.getElementById('mindmap-path');
  const layoutBtns = document.querySelectorAll('#mindmap-layout-pills .pill-btn');
  const filterBtns = document.querySelectorAll('#mindmap-filter-pills .pill-btn');
  const btnZoomIn = document.getElementById('btn-mm-zoomin');
  const btnZoomOut = document.getElementById('btn-mm-zoomout');
  const btnResetZoom = document.getElementById('btn-mm-reset');
  const btnFitView = document.getElementById('btn-mm-fit');
  const canvasContainer = document.getElementById('mindmap-canvas-container');

  if (canvasContainer) {
    ensureMindMapToolbar(canvasContainer);
    ensureGraphTooltip(canvasContainer);
  }

  btnScanMindMap?.addEventListener('click', async () => {
    const path = inputPath?.value || '.';
    btnScanMindMap.disabled = true;
    btnScanMindMap.innerHTML = `<span class="spinner-ring" style="width:16px;height:16px;border-width:2px;"></span><span>Analyzing Graph...</span>`;

    try {
      const response = await fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path, use_cache: true })
      });

      if (!response.ok) throw new Error('Failed to analyze directory for mind map');

      const data = await response.json();
      const scan = data.scan_result;
      if (!scan || !scan.graph || !scan.graph.stats) {
        throw new Error('Graph analysis data missing from server response. Try disabling Smart Scan Cache.');
      }
      currentGraph = scan.graph;
      customPositions = {};
      collapsedFolders = new Set();

      if (data.resolved_path && inputPath) {
        inputPath.value = data.resolved_path;
        inputPath.dispatchEvent(new Event('input', { bubbles: true }));
      }

      renderMindMapCanvas(currentGraph);
      updateGraphStatsBar(currentGraph.stats);
      fitGraphToScreen();
      showToast(`Graph loaded: ${currentGraph.stats.total_nodes || 0} nodes & ${currentGraph.stats.total_edges || 0} edges`, 'success');
    } catch (err) {
      console.error('Mind Map load error:', err);
      showToast(err.message || 'Error generating graph', 'error');
    } finally {
      btnScanMindMap.disabled = false;
      btnScanMindMap.innerHTML = `<span>Refresh Mind Map</span>`;
    }
  });

  inputPath?.addEventListener('input', () => {
    syncPathInputs(inputPath.value);
  });

  layoutBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      layoutBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentLayout = btn.getAttribute('data-layout') || 'tree';
      lastInspectedNodeId = null;
      if (currentGraph && currentGraph.nodes) {
        renderMindMapCanvas(currentGraph);
        fitGraphToScreen();
      }
    });
  });

  filterBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      filterBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.getAttribute('data-filter') || 'all';
      if (currentGraph && currentGraph.nodes) renderMindMapCanvas(currentGraph);
    });
  });

  btnZoomIn?.addEventListener('click', () => { scale = Math.min(scale * 1.25, 3.5); applyTransform(); });
  btnZoomOut?.addEventListener('click', () => { scale = Math.max(scale / 1.25, 0.2); applyTransform(); });
  btnResetZoom?.addEventListener('click', () => { scale = 1.0; panX = 0; panY = 0; applyTransform(); });
  btnFitView?.addEventListener('click', () => { fitGraphToScreen(); });

  if (canvasContainer) {
    canvasContainer.addEventListener('mousedown', (e) => {
      if (e.target.closest('.node-vertex') || e.target.closest('.graph-floating-toolbar') || e.target.closest('.graph-tooltip')) return;
      isCanvasDragging = true;
      startDragCanvasX = e.clientX - panX;
      startDragCanvasY = e.clientY - panY;
      canvasContainer.style.cursor = 'grabbing';
    });

    canvasContainer.addEventListener('wheel', (e) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.12 : 0.89;
      scale = Math.min(Math.max(scale * zoomFactor, 0.2), 3.5);
      applyTransform();
    }, { passive: false });
  }

  if (!window._isMindMapEventsAttached) {
    window._isMindMapEventsAttached = true;
    window.addEventListener('mousemove', (e) => {
      if (currentLayout === 'tree' && draggingNodeId) { draggingNodeId = null; }

      if (draggingNodeId && activeNodePositions[draggingNodeId]) {
        const dx = (e.clientX - dragNodeStartX) / scale;
        const dy = (e.clientY - dragNodeStartY) / scale;
        dragAccumulatedDistance += Math.abs(e.clientX - dragNodeStartX) + Math.abs(e.clientY - dragNodeStartY);
        dragNodeStartX = e.clientX;
        dragNodeStartY = e.clientY;

        if (!customPositions[currentLayout]) customPositions[currentLayout] = {};
        const cur = activeNodePositions[draggingNodeId];
        const newX = cur.x + dx;
        const newY = cur.y + dy;
        cur.x = newX;
        cur.y = newY;
        customPositions[currentLayout][draggingNodeId] = { x: newX, y: newY };

        const svg = document.getElementById('mindmap-svg');
        const nodeGroup = svg?.querySelector(`.node-vertex[data-id="${draggingNodeId}"]`);
        if (nodeGroup) {
          const nodeObj = currentGraph?.nodes.find(n => n.id === draggingNodeId);
          const nodeWidth = nodeObj?.type === 'root' ? 190 : (nodeObj?.type === 'dir' ? 170 : 150);
          const nodeHeight = 40;
          nodeGroup.setAttribute('transform', `translate(${newX - nodeWidth / 2}, ${newY - nodeHeight / 2})`);
        }
        updateConnectedEdgesDOM(draggingNodeId);
        return;
      }

      if (isCanvasDragging) {
        const maxPan = 5000;
        panX = Math.max(-maxPan, Math.min(maxPan, e.clientX - startDragCanvasX));
        panY = Math.max(-maxPan, Math.min(maxPan, e.clientY - startDragCanvasY));
        applyTransform();
      }
    });

    window.addEventListener('mouseup', () => {
      draggingNodeId = null;
      if (isCanvasDragging) {
        isCanvasDragging = false;
        if (canvasContainer) canvasContainer.style.cursor = 'grab';
      }
    });
  }

  const btnTabDetails = document.getElementById('btn-tab-inspector-details');
  const btnTabCopilot = document.getElementById('btn-tab-inspector-copilot');
  const detailsContent = document.getElementById('mindmap-inspector-content');
  const copilotContent = document.getElementById('mindmap-copilot-content');

  btnTabDetails?.addEventListener('click', () => {
    btnTabDetails.classList.add('active');
    btnTabCopilot?.classList.remove('active');
    if (detailsContent) detailsContent.style.display = 'flex';
    if (copilotContent) copilotContent.style.display = 'none';
  });

  btnTabCopilot?.addEventListener('click', () => {
    btnTabCopilot.classList.add('active');
    btnTabDetails?.classList.remove('active');
    if (copilotContent) copilotContent.style.display = 'flex';
    if (detailsContent) detailsContent.style.display = 'none';
  });
}

export function setMindMapGraphFromScan(graph, resolvedPath) {
  const inputPath = document.getElementById('mindmap-path');
  if (resolvedPath && inputPath) {
    inputPath.value = resolvedPath;
  }
  if (!graph || !graph.stats) return;
  currentGraph = graph;
  customPositions = {};
  collapsedFolders = new Set();
  renderMindMapCanvas(currentGraph);
  updateGraphStatsBar(currentGraph.stats);
  fitGraphToScreen();
}

function ensureMindMapToolbar(container) {
  let toolbar = container.querySelector('#mindmap-toolbar');
  if (!toolbar) {
    toolbar = document.createElement('div');
    toolbar.className = 'graph-floating-toolbar';
    toolbar.id = 'mindmap-toolbar';
    toolbar.innerHTML = `
      <input type="text" id="mindmap-search-input" class="graph-search-input" placeholder="Search nodes..." />
      <div class="graph-toolbar-divider"></div>
      <button class="graph-toolbar-btn" id="btn-mm-expand-all" title="Expand All Folders">↗</button>
      <button class="graph-toolbar-btn" id="btn-mm-collapse-all" title="Collapse All Folders">↙</button>
      <div class="graph-toolbar-divider"></div>
      <span class="graph-zoom-label" id="mindmap-zoom-display">100%</span>
    `;
    container.appendChild(toolbar);

    const searchInput = toolbar.querySelector('#mindmap-search-input');
    searchInput?.addEventListener('input', (e) => {
      const q = e.target.value.trim().toLowerCase();
      const svg = document.getElementById('mindmap-svg');
      if (!svg) return;
      svg.querySelectorAll('.node-vertex').forEach(v => {
        const label = (v.getAttribute('data-label') || '').toLowerCase();
        if (!q || label.includes(q)) {
          v.style.opacity = '1';
        } else {
          v.style.opacity = '0.15';
        }
      });
      if (q && currentGraph && currentGraph.nodes) {
        const match = currentGraph.nodes.find(n => (n.label || '').toLowerCase().includes(q));
        if (match && activeNodePositions[match.id]) {
          const pos = activeNodePositions[match.id];
          const cW = svg.clientWidth || 1100;
          const cH = svg.clientHeight || 520;
          panX = (cW / 2) - (pos.x * scale);
          panY = (cH / 2) - (pos.y * scale);
          applyTransform();
        }
      }
    });

    toolbar.querySelector('#btn-mm-expand-all')?.addEventListener('click', () => {
      collapsedFolders = new Set();
      if (currentGraph && currentGraph.nodes) {
        renderMindMapCanvas(currentGraph);
        fitGraphToScreen();
      }
    });

    toolbar.querySelector('#btn-mm-collapse-all')?.addEventListener('click', () => {
      if (currentGraph && currentGraph.nodes) {
        currentGraph.nodes.forEach(n => { if (n.type === 'dir' && n.id !== 'root') collapsedFolders.add(n.id); });
        renderMindMapCanvas(currentGraph);
        fitGraphToScreen();
      }
    });
  }
}

function ensureGraphTooltip(container) {
  let tooltip = container.querySelector('.graph-tooltip');
  if (!tooltip) {
    tooltip = document.createElement('div');
    tooltip.className = 'graph-tooltip';
    container.appendChild(tooltip);
  }
}

function showTooltipAt(node, e, container) {
  const tooltip = container.querySelector('.graph-tooltip');
  if (!tooltip || !node) return;
  tooltip.innerHTML = `
    <div class="graph-tooltip-title"><span class="graph-tooltip-badge">${(node.type || 'NODE').toUpperCase()}</span><span>${node.label || ''}</span></div>
    <div style="color:#d4d4d8;margin-top:2px;font-size:0.75rem;">${node.summary || 'Workspace structure item'}</div>
    <div class="graph-tooltip-meta">
      <span>Path: ${node.path || node.label || ''}</span>
    </div>
  `;
  tooltip.classList.add('show');
  moveTooltip(e, container);
}

function moveTooltip(e, container) {
  const tooltip = container.querySelector('.graph-tooltip');
  if (!tooltip || !tooltip.classList.contains('show')) return;
  const rect = container.getBoundingClientRect();
  const x = Math.min(e.clientX - rect.left + 14, rect.width - 330);
  const y = Math.min(e.clientY - rect.top + 14, rect.height - 110);
  tooltip.style.left = `${Math.max(10, x)}px`;
  tooltip.style.top = `${Math.max(10, y)}px`;
}

function hideTooltip(container) {
  const tooltip = container?.querySelector('.graph-tooltip');
  if (tooltip) tooltip.classList.remove('show');
}

function applyTransform() {
  const g = document.getElementById('mindmap-transform-group');
  if (g) g.style.transform = `translate(${panX}px, ${panY}px) scale(${scale})`;
  const zl = document.getElementById('mindmap-zoom-display');
  if (zl) zl.textContent = Math.round(scale * 100) + '%';
}

export function fitGraphToScreen() {
  if (!activeNodePositions || Object.keys(activeNodePositions).length === 0) {
    scale = 1.0; panX = 0; panY = 0; applyTransform();
    return;
  }
  const positions = Object.values(activeNodePositions);
  let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
  positions.forEach(pos => {
    if (pos.x < minX) minX = pos.x;
    if (pos.x > maxX) maxX = pos.x;
    if (pos.y < minY) minY = pos.y;
    if (pos.y > maxY) maxY = pos.y;
  });
  const graphWidth = Math.max(maxX - minX + 300, 400);
  const graphHeight = Math.max(maxY - minY + 300, 400);
  const svg = document.getElementById('mindmap-svg');
  const containerWidth = svg?.clientWidth || 1100;
  const containerHeight = svg?.clientHeight || 520;
  const scaleX = containerWidth / graphWidth;
  const scaleY = containerHeight / graphHeight;
  scale = Math.min(Math.max(Math.min(scaleX, scaleY) * 0.9, 0.25), 1.6);
  const centerX = (minX + maxX) / 2;
  const centerY = (minY + maxY) / 2;
  panX = (containerWidth / 2) - (centerX * scale);
  panY = (containerHeight / 2) - (centerY * scale);
  applyTransform();
}

export function renderMindMapCanvas(graph) {
  if (!graph || !graph.nodes || !Array.isArray(graph.nodes)) return;
  const svg = document.getElementById('mindmap-svg');
  const container = document.getElementById('mindmap-canvas-container');
  if (!svg || !container) return;

  ensureMindMapToolbar(container);
  ensureGraphTooltip(container);

  const filteredEdges = graph.edges.filter(e => {
    if (currentFilter === 'structural') return e.relation === 'contains';
    if (currentFilter === 'imports') return e.relation === 'imports';
    return true;
  });

  let nodesToRender;
  let visibleEdgeIds;

  if (currentLayout === 'tree') {
    const result = computeTreePositions(graph, collapsedFolders);
    activeNodePositions = result.positions;
    visibleEdgeIds = result.visibleEdgeIds;
    nodesToRender = graph.nodes
      .filter(n => result.visibleNodeIds.has(n.id))
      .sort((a, b) => {
        const pa = activeNodePositions[a.id];
        const pb = activeNodePositions[b.id];
        return (pa?.y || 0) - (pb?.y || 0);
      });
    if (selectedNodeId && !result.visibleNodeIds.has(selectedNodeId)) {
      selectedNodeId = 'root';
    }
  } else {
    visibleEdgeIds = new Set(filteredEdges.map(e => `${e.source}->${e.target}`));
    const layoutPositions = computeLayout(graph.nodes, filteredEdges, currentLayout);
    const savedOverrides = customPositions[currentLayout] || {};
    activeNodePositions = {};
    graph.nodes.forEach(n => {
      if (savedOverrides[n.id]) {
        activeNodePositions[n.id] = { ...savedOverrides[n.id] };
      } else {
        activeNodePositions[n.id] = layoutPositions[n.id] || { x: 600, y: 400 };
      }
    });
    nodesToRender = graph.nodes;
  }

  const isTreeMode = currentLayout === 'tree';
  let pathsHTML = '';
  let nodesHTML = '';

  filteredEdges.forEach(e => {
    if (!visibleEdgeIds.has(`${e.source}->${e.target}`)) return;
    const src = activeNodePositions[e.source];
    const tgt = activeNodePositions[e.target];
    if (!src || !tgt) return;
    const srcNode = graph.nodes.find(n => n.id === e.source);
    const tgtNode = graph.nodes.find(n => n.id === e.target);
    const pathD = computeEdgePath(src, tgt, e.relation, currentLayout, srcNode, tgtNode);
    const edgeClass = e.relation === 'imports' ? 'edge-import' : 'edge-structural';
    pathsHTML += `<path class="edge-path ${edgeClass}" d="${pathD}" data-source="${e.source}" data-target="${e.target}" data-relation="${e.relation}" />`;
  });

  nodesToRender.forEach(n => {
    const pos = activeNodePositions[n.id];
    if (!pos) return;
    const isSelected = n.id === selectedNodeId ? 'selected' : '';
    const isDir = n.type === 'dir';
    const isRoot = n.type === 'root';
    const isCollapsed = collapsedFolders.has(n.id);

    let icon = '📄';
    let accentColor = '#71717a';
    if (isRoot) { icon = '⚡'; accentColor = '#f59e0b'; }
    else if (isDir) { icon = '📁'; accentColor = '#3b82f6'; }
    else if (n.type === 'module') { icon = '🐍'; accentColor = '#10b981'; }
    else if (n.type === 'config') { icon = '⚙️'; accentColor = '#f97316'; }
    else if (n.type === 'ui') { icon = '🎨'; accentColor = '#8b5cf6'; }
    else if (n.type === 'test') { icon = '🧪'; accentColor = '#ec4899'; }
    else if (n.type === 'doc') { icon = '📝'; accentColor = '#06b6d4'; }

    const nodeWidth = isRoot ? 190 : (isDir ? 170 : 150);
    const nodeHeight = 40;
    const halfW = nodeWidth / 2;
    const halfH = nodeHeight / 2;
    const cursor = isTreeMode && isDir ? 'pointer' : (isTreeMode ? 'default' : 'move');
    const toggleIcon = isDir && isTreeMode ? (isCollapsed ? '+' : '−') : '';

    const childCount = graph.nodes.filter(child => child.parent === n.id).length;
    const importCount = graph.edges.filter(e => e.source === n.id && e.relation === 'imports').length;
    const badgeCount = childCount > 0 ? childCount : (importCount > 0 ? importCount : 0);
    const badgeLabel = badgeCount > 0 ? (childCount > 0 ? `${childCount}` : `↗${importCount}`) : '';
    const badgeX = toggleIcon ? nodeWidth - 44 : nodeWidth - 28;

    const maxChars = isTreeMode ? (isDir ? (badgeLabel ? 13 : 18) : (badgeLabel ? 12 : 16)) : 14;

    nodesHTML += `
      <g class="node-vertex ${n.type} ${isSelected}" transform="translate(${pos.x - halfW}, ${pos.y - halfH})" data-id="${n.id}" data-dir="${isDir}" data-label="${n.label || ''}" style="cursor: ${cursor};">
        <clipPath id="mindmap-clip-${n.id}">
          <rect width="${nodeWidth}" height="${nodeHeight}" rx="10" />
        </clipPath>
        <rect class="node-rect" width="${nodeWidth}" height="${nodeHeight}" rx="10" />
        <rect class="node-accent" x="0" y="0" width="6" height="${nodeHeight}" fill="${accentColor}" clip-path="url(#mindmap-clip-${n.id})" />
        <text class="node-icon" x="16" y="${halfH}">${icon}</text>
        <text class="node-label" x="38" y="${halfH}" text-anchor="start">${truncateString(n.label, maxChars)}</text>
        ${badgeLabel ? `
          <g class="node-badge" transform="translate(${badgeX - 12}, 10)">
            <rect class="node-badge-rect" width="24" height="20" rx="5" />
            <text class="node-badge-text" x="12" y="10">${badgeLabel}</text>
          </g>
        ` : ''}
        ${toggleIcon ? `<text class="node-toggle" x="${nodeWidth - 16}" y="${halfH}" text-anchor="middle">${toggleIcon}</text>` : ''}
      </g>
    `;
  });

  svg.innerHTML = `
    <g id="mindmap-transform-group" style="transform: translate(${panX}px, ${panY}px) scale(${scale});">
      <g class="edges-layer">${pathsHTML}</g>
      <g class="nodes-layer">${nodesHTML}</g>
    </g>
  `;

  svg.querySelectorAll('.node-vertex').forEach(el => {
    const id = el.getAttribute('data-id');
    const isDir = el.getAttribute('data-dir') === 'true';

    el.addEventListener('click', (e) => {
      if (dragAccumulatedDistance > DRAG_THRESHOLD) return;
      e.stopPropagation();

      if (isTreeMode && isDir) {
        if (collapsedFolders.has(id)) {
          collapsedFolders.delete(id);
        } else {
          collapsedFolders.add(id);
        }
        renderMindMapCanvas(graph);
        fitGraphToScreen();
        return;
      }

      selectedNodeId = id;
      lastInspectedNodeId = id;
      svg.querySelectorAll('.node-vertex').forEach(v => v.classList.remove('selected'));
      el.classList.add('selected');
      const nodeObj = graph.nodes.find(n => n.id === id);
      if (nodeObj) selectAndInspectNode(nodeObj, graph);
    });

    if (!isTreeMode) {
      el.addEventListener('mousedown', (e) => {
        e.stopPropagation();
        draggingNodeId = id;
        dragNodeStartX = e.clientX;
        dragNodeStartY = e.clientY;
        dragAccumulatedDistance = 0;
      });
    }

    el.addEventListener('mouseenter', (e) => {
      svg.querySelectorAll('.edge-path').forEach(pathEl => {
        const srcId = pathEl.getAttribute('data-source');
        const tgtId = pathEl.getAttribute('data-target');
        if (srcId === id || tgtId === id) {
          pathEl.classList.add('edge-highlighted');
          pathEl.classList.remove('edge-dimmed');
        } else {
          pathEl.classList.add('edge-dimmed');
          pathEl.classList.remove('edge-highlighted');
        }
      });
      const nodeObj = graph.nodes.find(n => n.id === id);
      if (nodeObj) showTooltipAt(nodeObj, e, container);
    });

    el.addEventListener('mousemove', (e) => {
      moveTooltip(e, container);
    });

    el.addEventListener('mouseleave', () => {
      svg.querySelectorAll('.edge-path').forEach(pathEl => {
        pathEl.classList.remove('edge-highlighted', 'edge-dimmed');
      });
      hideTooltip(container);
    });
  });

  const selNode = graph.nodes.find(n => n.id === selectedNodeId) || graph.nodes[0];
  if (selNode && selNode.id !== lastInspectedNodeId) {
    lastInspectedNodeId = selNode.id;
    selectAndInspectNode(selNode, graph);
  }
}

function computeEdgePath(src, tgt, relation, layoutMode, srcNode, tgtNode) {
  const srcW = srcNode ? (srcNode.type === 'root' ? 190 : (srcNode.type === 'dir' ? 170 : 150)) : 160;
  const tgtW = tgtNode ? (tgtNode.type === 'root' ? 190 : (tgtNode.type === 'dir' ? 170 : 150)) : 160;

  if (layoutMode === 'tree' && relation === 'contains') {
    const srcRight = src.x + srcW / 2;
    const tgtLeft = tgt.x - tgtW / 2;
    const dx = Math.max(Math.abs(tgtLeft - srcRight) * 0.5, 30);
    return `M ${srcRight} ${src.y} C ${srcRight + dx} ${src.y}, ${tgtLeft - dx} ${tgt.y}, ${tgtLeft} ${tgt.y}`;
  } else if (layoutMode === 'horizontal') {
    const srcRight = src.x + srcW / 2;
    const tgtLeft = tgt.x - tgtW / 2;
    const dx = Math.abs(tgtLeft - srcRight) * 0.5;
    return `M ${srcRight} ${src.y} C ${srcRight + dx} ${src.y}, ${tgtLeft - dx} ${tgt.y}, ${tgtLeft} ${tgt.y}`;
  } else {
    const midX = (src.x + tgt.x) / 2;
    const midY = (src.y + tgt.y) / 2;
    const offset = relation === 'imports' ? 45 : -20;
    return `M ${src.x} ${src.y} Q ${midX + offset} ${midY + offset} ${tgt.x} ${tgt.y}`;
  }
}

function updateConnectedEdgesDOM(nodeId) {
  const svg = document.getElementById('mindmap-svg');
  if (!svg || !activeNodePositions[nodeId]) return;
  svg.querySelectorAll(`.edge-path[data-source="${nodeId}"], .edge-path[data-target="${nodeId}"]`).forEach(pathEl => {
    const srcId = pathEl.getAttribute('data-source');
    const tgtId = pathEl.getAttribute('data-target');
    const relation = pathEl.getAttribute('data-relation');
    const src = activeNodePositions[srcId];
    const tgt = activeNodePositions[tgtId];
    const srcNode = currentGraph?.nodes.find(n => n.id === srcId);
    const tgtNode = currentGraph?.nodes.find(n => n.id === tgtId);
    if (src && tgt) pathEl.setAttribute('d', computeEdgePath(src, tgt, relation, currentLayout, srcNode, tgtNode));
  });
}

function computeLayout(nodes, edges, mode) {
  const positions = {};
  if (!nodes || !Array.isArray(nodes) || nodes.length === 0) return positions;
  const rootNode = nodes.find(n => n.type === 'root') || nodes[0];
  const centerX = 600;
  const centerY = 400;

  if (mode === 'radial') {
    positions[rootNode.id] = { x: centerX, y: centerY };
    const dirs = nodes.filter(n => n.type === 'dir');
    const files = nodes.filter(n => n.type !== 'root' && n.type !== 'dir');
    const dirRadius = Math.max(260, Math.min(800, dirs.length * 48));
    dirs.forEach((d, i) => {
      const angle = (i / Math.max(dirs.length, 1)) * 2 * Math.PI;
      positions[d.id] = { x: centerX + dirRadius * Math.cos(angle), y: centerY + dirRadius * Math.sin(angle) };
    });
    const parentCounts = {};
    files.forEach(f => { const pid = f.parent || rootNode.id; parentCounts[pid] = (parentCounts[pid] || 0) + 1; });
    const parentIndices = {};
    files.forEach(f => {
      const pid = f.parent || rootNode.id;
      const pPos = positions[pid] || { x: centerX, y: centerY };
      const idx = parentIndices[pid] || 0;
      parentIndices[pid] = idx + 1;
      const total = parentCounts[pid] || 1;
      const ringIdx = Math.floor(idx / 6);
      const fileRadius = (pid === rootNode.id ? 180 : 150) + ringIdx * 80;
      const baseAngle = Math.atan2(pPos.y - centerY, pPos.x - centerX);
      const spread = Math.min(Math.PI * 1.2, total * 0.25);
      const fAngle = baseAngle - spread / 2 + (idx / Math.max(total, 1)) * spread;
      positions[f.id] = { x: pPos.x + fileRadius * Math.cos(fAngle), y: pPos.y + fileRadius * Math.sin(fAngle) };
    });
  } else if (mode === 'horizontal') {
    const depthGroups = {};
    nodes.forEach(n => { const d = n.depth || 0; if (!depthGroups[d]) depthGroups[d] = []; depthGroups[d].push(n); });
    Object.keys(depthGroups).forEach(depth => {
      const grp = depthGroups[depth];
      const x = 140 + int(depth) * 280;
      grp.forEach((n, idx) => { const y = 80 + idx * 65; positions[n.id] = { x, y }; });
    });
  } else {
    const cols = Math.ceil(Math.sqrt(nodes.length));
    nodes.forEach((n, idx) => { const c = idx % cols; const r = Math.floor(idx / cols); positions[n.id] = { x: 150 + c * 210, y: 120 + r * 80 }; });
  }

  resolveOverlaps(positions, nodes);
  return positions;
}

function resolveOverlaps(positions, nodes) {
  const iterations = 60;
  const minPadX = 160;
  const minPadY = 48;
  for (let iter = 0; iter < iterations; iter++) {
    let moved = false;
    for (let i = 0; i < nodes.length; i++) {
      const n1 = nodes[i]; const p1 = positions[n1.id];
      if (!p1) continue;
      for (let j = i + 1; j < nodes.length; j++) {
        const n2 = nodes[j]; const p2 = positions[n2.id];
        if (!p2) continue;
        const dx = p1.x - p2.x; const dy = p1.y - p2.y;
        const absX = Math.abs(dx); const absY = Math.abs(dy);
        if (absX < minPadX && absY < minPadY) {
          moved = true;
          const pushX = (minPadX - absX) * 0.55 * (dx >= 0 ? 1 : -1);
          const pushY = (minPadY - absY) * 0.55 * (dy >= 0 ? 1 : -1);
          if (n1.type !== 'root') { p1.x += pushX + (Math.random() - 0.5) * 2; p1.y += pushY + (Math.random() - 0.5) * 2; }
          if (n2.type !== 'root') { p2.x -= pushX + (Math.random() - 0.5) * 2; p2.y -= pushY + (Math.random() - 0.5) * 2; }
        }
      }
    }
    if (!moved) break;
  }
}

function panToMindMapNode(nodeId) {
  if (!activeNodePositions[nodeId]) return;
  const pos = activeNodePositions[nodeId];
  const svg = document.getElementById('mindmap-svg');
  const cW = svg?.clientWidth || 1100;
  const cH = svg?.clientHeight || 520;
  panX = (cW / 2) - (pos.x * scale);
  panY = (cH / 2) - (pos.y * scale);
  applyTransform();
}

function selectAndInspectNode(node, graph) {
  const inspectorContent = document.getElementById('mindmap-inspector-content');
  if (!inspectorContent || !node || !graph || !Array.isArray(graph.nodes)) return;

  const parentNode = graph.nodes.find(n => n.id === node.parent);
  const childNodes = graph.nodes.filter(n => n.parent === node.id);
  const importsFrom = graph.edges.filter(e => e.source === node.id && e.relation === 'imports').map(e => graph.nodes.find(n => n.id === e.target)).filter(Boolean);
  const importedBy = graph.edges.filter(e => e.target === node.id && e.relation === 'imports').map(e => graph.nodes.find(n => n.id === e.source)).filter(Boolean);

  inspectorContent.innerHTML = `
    <div class="inspector-header">
      <div class="inspector-badge">${node.type.toUpperCase()}</div>
      <h4 class="inspector-title" title="${node.path || node.label}">${node.label}</h4>
      <p class="inspector-path">${node.path || 'Root Workspace'}</p>
    </div>
    <div class="inspector-section mt-3">
      <span class="section-label">Vertex Summary</span>
      <p class="inspector-summary">${node.summary}</p>
    </div>
    ${parentNode ? `
      <div class="inspector-section mt-3">
        <span class="section-label">Parent Directory</span>
        <div class="connected-pill" data-id="${parentNode.id}">Directory: ${parentNode.label}</div>
      </div>
    ` : ''}
    ${importsFrom.length > 0 ? `
      <div class="inspector-section mt-3">
        <span class="section-label">Imports / References (${importsFrom.length})</span>
        <div class="connected-list">${importsFrom.map(n => `<div class="connected-pill" data-id="${n.id}">Import: ${n.label}</div>`).join('')}</div>
      </div>
    ` : ''}
    ${importedBy.length > 0 ? `
      <div class="inspector-section mt-3">
        <span class="section-label">Imported By (${importedBy.length})</span>
        <div class="connected-list">${importedBy.map(n => `<div class="connected-pill" data-id="${n.id}">Imported by: ${n.label}</div>`).join('')}</div>
      </div>
    ` : ''}
    ${childNodes.length > 0 ? `
      <div class="inspector-section mt-3">
        <span class="section-label">Contains (${childNodes.length} items)</span>
        <div class="connected-list">
          ${childNodes.slice(0, 8).map(n => `<div class="connected-pill" data-id="${n.id}">${n.label}</div>`).join('')}
          ${childNodes.length > 8 ? `<span class="text-xs text-secondary">+${childNodes.length - 8} more</span>` : ''}
        </div>
      </div>
    ` : ''}
    <div class="inspector-actions mt-4">
      <button class="btn btn-secondary btn-sm w-full" id="btn-copy-node-path">Copy Path</button>
    </div>
  `;

  inspectorContent.querySelectorAll('.connected-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      const targetId = pill.getAttribute('data-id');
      selectedNodeId = targetId;
      lastInspectedNodeId = null;
      renderMindMapCanvas(graph);
      panToMindMapNode(targetId);
    });
  });

  const btnCopy = document.getElementById('btn-copy-node-path');
  btnCopy?.addEventListener('click', () => {
    navigator.clipboard.writeText(node.path || node.label);
    showToast('Node path copied to clipboard!', 'success');
  });

  renderCopilotSuite(node, graph);
}

function updateGraphStatsBar(stats) {
  if (!stats) return;
  const el = document.getElementById('mindmap-stats-bar');
  if (el) {
    el.innerHTML = `
      <span class="badge badge-mono">Nodes: ${stats.total_nodes}</span>
      <span class="badge badge-mono">Edges: ${stats.total_edges}</span>
      <span class="badge badge-mono">Imports/Links: ${stats.import_connections}</span>
    `;
  }
}

function truncateString(str, len) {
  if (str === null || str === undefined) return '';
  if (typeof str !== 'string') str = String(str);
  return str.length > len ? str.substring(0, len - 2) + '..' : str;
}

function int(val) { return parseInt(val, 10) || 0; }

// =========================================================================
// GROQ AI COPILOT — Premium Chat UI
// =========================================================================
let nodeChatHistories = {};
let activeCopilotModel = 'llama-3.3-70b-versatile';

function formatTime(ts) {
  const d = new Date(ts);
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function renderCopilotSuite(node, graph) {
  const copilotContent = document.getElementById('mindmap-copilot-content');
  if (!copilotContent || !node || !graph) return;

  const parentNode = graph.nodes.find(n => n.id === node.parent);
  const childNodes = graph.nodes.filter(n => n.parent === node.id);
  const importsFrom = graph.edges.filter(e => e.source === node.id && e.relation === 'imports').map(e => graph.nodes.find(n => n.id === e.target)).filter(Boolean);
  const importedBy = graph.edges.filter(e => e.target === node.id && e.relation === 'imports').map(e => graph.nodes.find(n => n.id === e.source)).filter(Boolean);

  const history = nodeChatHistories[node.id] || [];

  let historyHTML = '';
  if (history.length === 0) {
    historyHTML = `
      <div class="chat-welcome-box">
        <p style="line-height:1.6;color:var(--text-primary);font-size:0.82rem;">AI has context for <code style="font-family:'JetBrains Mono';background:rgba(0,0,0,0.06);padding:2px 6px;border-radius:4px;font-weight:600;">${node.label}</code> &mdash; ${parentNode ? 'parent: ' + parentNode.label : 'root node'}, ${importsFrom.length} imports, ${childNodes.length} sub-items.</p>
        <div class="quick-prompts-list mt-3">
          <button class="quick-prompt-btn" data-prompt="What does ${node.label} do and how does it fit in the project?">What does this file do?</button>
          <button class="quick-prompt-btn" data-prompt="Review the quality, dependencies, and potential issues in ${node.label}."">Code review this file</button>
          <button class="quick-prompt-btn" data-prompt="Suggest concrete improvements for ${node.label}.">Suggest improvements</button>
        </div>
      </div>
    `;
  } else {
    historyHTML = history.map(turn => {
      if (turn.role === 'user') {
        const timeStr = turn.time ? formatTime(turn.time) : '';
        return `<div class="chat-bubble user"><strong>You</strong><span style="margin-top:3px;">${turn.content}</span>${timeStr ? `<span class="bubble-user-time">${timeStr}</span>` : ''}</div>`;
      } else {
        let formatted = '';
        try {
          formatted = marked.parse(turn.content || '');
        } catch(e) {
          formatted = (turn.content || '').replace(/\n{2,}/g, '<br><br>').replace(/\n/g, '<br>');
        }
        const durationLabel = turn.duration ? `<span style="font-size:0.72rem;color:var(--text-tertiary);margin-left:auto;">${turn.duration}s</span>` : '';
        const timeStr = turn.time ? formatTime(turn.time) : '';
        return `<div class="chat-bubble ai">
          <div class="bubble-header">
            <span class="bubble-avatar">G</span>
            <span class="bubble-model">Groq AI</span>
            ${durationLabel}
            ${timeStr ? `<span class="bubble-time">${timeStr}</span>` : ''}
          </div>
          <div class="markdown-body">${formatted}</div>
        </div>`;
      }
    }).join('');
  }

  copilotContent.innerHTML = `
    <div class="copilot-active-container">
      <div class="copilot-header-card">
        <div class="copilot-vertex-badge">
          <span class="inspector-badge">${node.type.toUpperCase()}</span>
          <strong class="copilot-vertex-title" title="${node.path || node.label}">${node.label}</strong>
        </div>
        <button class="btn btn-primary btn-sm w-full mt-3" id="btn-run-vertex-audit">
          <span>Review this file</span>
        </button>
      </div>

      <div class="copilot-chat-history" id="copilot-chat-history" style="position:relative;">
        ${historyHTML}
        <button class="scroll-to-bottom-btn" id="scroll-to-bottom-btn" title="New messages">↓</button>
      </div>

      <div class="copilot-input-bar">
        <div class="copilot-input-row">
          <textarea id="copilot-chat-input" rows="1" placeholder="Ask about ${node.label}..."></textarea>
          <button id="btn-copilot-send" class="btn btn-primary" title="Send">Send</button>
        </div>
        <div class="copilot-input-options">
          <label class="web-search-toggle" title="Search the web for context (only when you need it)">
            <input type="checkbox" id="copilot-web-search" />
            <span>Web search</span>
          </label>
        </div>
      </div>
    </div>
  `;

  const historyEl = document.getElementById('copilot-chat-history');
  if (historyEl) {
    historyEl.scrollTop = historyEl.scrollHeight;
    attachScrollToBottomBtn(historyEl);
  }

  // Highlight syntax in rendered code blocks
  copilotContent.querySelectorAll('pre code').forEach((block) => {
    try { hljs.highlightElement(block); } catch(e){}
  });
  enhanceCodeBlocks(copilotContent);
  if (historyEl && graph) postProcessFilePills(historyEl, graph);

  // Quick Prompt buttons
  const inputElPass = document.getElementById('copilot-chat-input');
  copilotContent.querySelectorAll('.quick-prompt-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const prompt = btn.getAttribute('data-prompt');
      if (prompt) sendCopilotMessage(node, graph, prompt, inputElPass);
    });
  });

  // Audit button
  const btnAudit = document.getElementById('btn-run-vertex-audit');
  btnAudit?.addEventListener('click', () => {
    sendCopilotMessage(node, graph, "AUDIT", inputElPass);
  });

  // Send button & enter key
  const btnSend = document.getElementById('btn-copilot-send');
  const inputEl = document.getElementById('copilot-chat-input');

  btnSend?.addEventListener('click', () => {
    const text = inputEl?.value?.trim();
    if (text) sendCopilotMessage(node, graph, text, inputEl);
  });

  inputEl?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      const text = inputEl.value.trim();
      if (text) sendCopilotMessage(node, graph, text, inputEl);
    }
  });

  // Auto-resize textarea
  inputEl?.addEventListener('input', () => {
    inputEl.style.height = 'auto';
    inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + 'px';
  });
}

function attachScrollToBottomBtn(container) {
  const btn = document.getElementById('scroll-to-bottom-btn');
  if (!btn) return;
  container.addEventListener('scroll', () => {
    const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 80;
    btn.classList.toggle('show', !isNearBottom);
  });
  btn.addEventListener('click', () => {
    container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
    btn.classList.remove('show');
  });
}

async function sendCopilotMessage(node, graph, userMessage, inputEl) {
  const historyEl = document.getElementById('copilot-chat-history');
  if (!historyEl || !node || !graph) return;

  if (!nodeChatHistories[node.id]) nodeChatHistories[node.id] = [];

  const now = Date.now();

  // Append user message
  const userBubble = document.createElement('div');
  userBubble.className = 'chat-bubble user';
  userBubble.id = 'user-bubble-pending';
  userBubble.innerHTML = `<strong>You</strong><span style="margin-top:3px;">${userMessage === 'AUDIT' ? 'Reviewing this file...' : userMessage}</span><span class="bubble-user-time">${formatTime(now)}</span>`;
  historyEl.appendChild(userBubble);

  // Append thinking indicator
  const startTime = Date.now();
  const typingBubble = document.createElement('div');
  typingBubble.className = 'chat-bubble ai thinking-container';
  typingBubble.id = 'copilot-typing-indicator';
  typingBubble.innerHTML = `
    <div class="thinking-header">
      <div class="spinner-ring-clean"></div>
      <span>Thinking...</span>
    </div>
    <div class="thinking-details" id="thinking-step-text">Analyzing code...</div>
  `;
  historyEl.appendChild(typingBubble);
  historyEl.scrollTop = historyEl.scrollHeight;

  const thinkingSteps = ['Analyzing code structure...', 'Checking dependencies...', 'Evaluating patterns...', 'Formulating response...'];
  let stepIndex = 0;
  const thinkingInterval = setInterval(() => {
    stepIndex = (stepIndex + 1) % thinkingSteps.length;
    const stepTextEl = document.getElementById('thinking-step-text');
    if (stepTextEl) stepTextEl.textContent = thinkingSteps[stepIndex];
  }, 900);

  const parentNode = graph.nodes.find(n => n.id === node.parent);
  const childNodes = graph.nodes.filter(n => n.parent === node.id);
  const importsFrom = graph.edges.filter(e => e.source === node.id && e.relation === 'imports').map(e => graph.nodes.find(n => n.id === e.target)).filter(Boolean);
  const importedBy = graph.edges.filter(e => e.target === node.id && e.relation === 'imports').map(e => graph.nodes.find(n => n.id === e.source)).filter(Boolean);

  const previousTurns = nodeChatHistories[node.id].slice(0, -1);

  const webSearchCheck = document.getElementById('copilot-web-search');
  const webSearch = webSearchCheck ? webSearchCheck.checked : false;

  const controller = new AbortController();
  const TIMEOUT_MS = 60000;
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const response = await fetch('/api/ai/graph-chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: controller.signal,
      body: JSON.stringify({
        node_id: node.id,
        node_label: node.label,
        node_type: node.type,
        node_path: node.path || null,
        node_summary: node.summary || null,
        connected_imports: importsFrom.map(n => n.label),
        connected_imported_by: importedBy.map(n => n.label),
        connected_children: childNodes.map(n => n.label),
        parent_label: parentNode ? parentNode.label : null,
        message: userMessage,
        history: previousTurns,
        model: activeCopilotModel,
        web_search: webSearch
      })
    });
    clearTimeout(timeoutId);

    const data = await response.json();
    clearInterval(thinkingInterval);
    typingBubble.remove();

    if (!response.ok || data.status !== 'success') {
      const errorMsg = data.detail || data.message || 'Failed to communicate with Groq AI';
      const errBubble = document.createElement('div');
      errBubble.className = 'chat-bubble ai';
      errBubble.innerHTML = `<div class="bubble-header"><span class="bubble-avatar">G</span><span class="bubble-model">Groq AI</span></div><span style="color:#dc2626;font-size:0.84rem;">Error: ${errorMsg}</span>`;
      historyEl.appendChild(errBubble);
      showToast(errorMsg, 'error');
      return;
    }

    // Commit to history
    nodeChatHistories[node.id].push({ role: 'user', content: userMessage, time: now });
    const pendingBubble = document.getElementById('user-bubble-pending');
    if (pendingBubble) pendingBubble.removeAttribute('id');
    if (inputEl) inputEl.value = '';

    const aiText = data.reply || '';
    const duration = ((Date.now() - startTime) / 1000).toFixed(1);

    const aiBubble = document.createElement('div');
    aiBubble.className = 'chat-bubble ai';

    const contentHtml = aiText ? marked.parse(aiText) : '<em style="color:var(--text-tertiary);font-size:0.82rem;">(empty response — AI returned no content)</em>';

    aiBubble.innerHTML = `
      <div class="bubble-header">
        <span class="bubble-avatar">G</span>
        <span class="bubble-model">Groq AI</span>
        <span style="font-size:0.72rem;color:var(--text-tertiary);margin-left:auto;">${duration}s</span>
        <span class="bubble-time">${formatTime(Date.now())}</span>
      </div>
      <div class="markdown-body">${contentHtml}</div>
    `;
    historyEl.appendChild(aiBubble);
    historyEl.scrollTop = historyEl.scrollHeight;

    // Highlight and enhance code blocks
    aiBubble.querySelectorAll('pre code').forEach((block) => {
      try { hljs.highlightElement(block); } catch(e){}
    });
    enhanceCodeBlocks(aiBubble);
    postProcessFilePills(aiBubble, graph);

    nodeChatHistories[node.id].push({ role: 'assistant', content: aiText, duration: duration, time: Date.now() });

  } catch (err) {
    clearTimeout(timeoutId);
    clearInterval(thinkingInterval);
    typingBubble.remove();
    const pendingBubble = document.getElementById('user-bubble-pending');
    if (pendingBubble) pendingBubble.remove();
    let msg = err.message;
    if (err.name === 'AbortError') msg = 'Request timed out. Groq API took too long to respond — try a simpler question or check your API key.';
    const errBubble = document.createElement('div');
    errBubble.className = 'chat-bubble ai';
    errBubble.innerHTML = `<div class="bubble-header"><span class="bubble-avatar">G</span><span class="bubble-model">Groq AI</span></div><span style="color:#dc2626;font-size:0.84rem;">Error: ${msg}</span>`;
    historyEl.appendChild(errBubble);
    showToast(msg, 'error');
  }
}

function enhanceCodeBlocks(container) {
  container.querySelectorAll('pre').forEach(pre => {
    if (pre.querySelector('.code-block-header')) return;
    const code = pre.querySelector('code');
    if (!code) return;
    const langClass = Array.from(code.classList).find(c => c.startsWith('language-'));
    const lang = langClass ? langClass.replace('language-', '') : '';
    const header = document.createElement('div');
    header.className = 'code-block-header';
    header.innerHTML = `
      <span class="lang-label">${lang || 'code'}</span>
      <button class="code-copy-btn" data-code="${encodeURIComponent(code.textContent)}">Copy</button>
    `;
    pre.parentNode.insertBefore(header, pre);
    pre.style.borderRadius = '0 0 8px 8px';
    pre.style.marginTop = '0';
  });

  container.querySelectorAll('.code-copy-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const text = decodeURIComponent(btn.getAttribute('data-code') || '');
      navigator.clipboard.writeText(text).then(() => {
        btn.textContent = 'Copied!';
        setTimeout(() => { btn.textContent = 'Copy'; }, 2000);
      }).catch(() => {
        btn.textContent = 'Failed';
        setTimeout(() => { btn.textContent = 'Copy'; }, 2000);
      });
    });
  });
}

function postProcessFilePills(container, graph) {
  if (!container || !graph || !graph.nodes) return;
  const nodeLabelMap = {};
  graph.nodes.forEach(n => { nodeLabelMap[n.label] = n; });

  container.querySelectorAll('code').forEach(el => {
    const text = el.textContent.trim();
    const match = nodeLabelMap[text];
    if (match && match.type !== 'root') {
      const pill = document.createElement('span');
      pill.className = 'ai-file-pill';
      pill.textContent = text;
      pill.dataset.id = match.id;
      pill.title = match.path || match.label;
      pill.style.cursor = 'pointer';
      pill.addEventListener('click', (e) => {
        e.stopPropagation();
        selectedNodeId = match.id;
        lastInspectedNodeId = null;
        renderMindMapCanvas(graph);
        panToMindMapNode(match.id);
        const detailsBtn = document.getElementById('btn-tab-inspector-details');
        if (detailsBtn) detailsBtn.click();
      });
      el.parentNode.replaceChild(pill, el);
    }
  });
}
