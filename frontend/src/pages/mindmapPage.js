// src/pages/mindmapPage.js — Codebase Mind Map & Graph Studio Page
import { getState } from '../state.js';

export function renderMindmapPage() {
  const path = getState().projectPath || '.';
  return `
    <section class="page-section" id="page-mindmap">
      <!-- Mind Map Controls -->
      <div class="control-banner panel-card">
        <div class="input-group path-input-group">
          <label for="mindmap-path">Workspace Root Path</label>
          <div class="input-with-actions">
            <input type="text" id="mindmap-path" placeholder="e.g. D:\\project or ." value="${path}" />
            <button id="btn-scan-mindmap" class="btn btn-primary">Analyze Graph</button>
          </div>
        </div>

        <div class="options-row">
          <div class="options-group">
            <span class="group-title">Layout Style</span>
            <div class="template-selector-pills" id="mindmap-layout-pills">
              <button class="pill-btn active" data-layout="tree">Collapsible Tree</button>
              <button class="pill-btn" data-layout="radial">Radial Mind Map</button>
              <button class="pill-btn" data-layout="horizontal">Horizontal Tree</button>
              <button class="pill-btn" data-layout="grid">Grid Cluster</button>
            </div>
          </div>

          <div class="options-group">
            <span class="group-title">Connection Filter</span>
            <div class="template-selector-pills" id="mindmap-filter-pills">
              <button class="pill-btn active" data-filter="all">All Edges (Hierarchy + Imports)</button>
              <button class="pill-btn" data-filter="structural">Folder Structure Only</button>
              <button class="pill-btn" data-filter="imports">Module Imports Only</button>
            </div>
          </div>

          <div class="options-group">
            <span class="group-title">Zoom & Pan</span>
            <div class="template-selector-pills">
              <button class="pill-btn" id="btn-mm-zoomin" title="Zoom In">+</button>
              <button class="pill-btn" id="btn-mm-zoomout" title="Zoom Out">-</button>
              <button class="pill-btn" id="btn-mm-reset" title="Reset View">Reset</button>
              <button class="pill-btn" id="btn-mm-fit" title="Fit View to Window">Fit</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Canvas + Inspector Split -->
      <div class="mindmap-split-grid mt-4">
        <div class="mindmap-canvas-card panel-card">
          <div class="pane-header">
            <div class="header-left">
              <h3>Interactive Codebase Mind Map</h3>
              <div id="mindmap-stats-bar" class="mindmap-stats-bar">
                <span class="badge badge-mono">Nodes: 0</span>
                <span class="badge badge-mono">Edges: 0</span>
              </div>
            </div>
            <div class="header-right">
              <span class="text-xs text-secondary">Drag canvas to pan | Scroll to zoom | Click vertices for details</span>
            </div>
          </div>
          <div id="mindmap-canvas-container" class="mindmap-canvas-container">
            <svg id="mindmap-svg" viewBox="0 0 1200 800" class="mindmap-svg">
              <g class="empty-mindmap">
                <text x="600" y="400" text-anchor="middle" class="empty-text">
                  Click "Analyze Graph" above to generate your architectural mind map
                </text>
              </g>
            </svg>
          </div>
        </div>

        <div class="mindmap-inspector-card panel-card">
          <div class="pane-header inspector-pane-header">
            <div class="inspector-tab-selector">
              <button class="inspector-tab-btn active" id="btn-tab-inspector-details" data-tab="details">
                Vertex Inspector
              </button>
              <button class="inspector-tab-btn" id="btn-tab-inspector-copilot" data-tab="copilot">
                Groq AI Copilot
              </button>
            </div>
          </div>

          <div id="mindmap-inspector-content" class="mindmap-inspector-content inspector-pane active">
            <div class="empty-state" style="padding: 40px 16px">
              <h4>Select a Vertex</h4>
              <p>Click on any directory, module, or configuration node on the mind map to inspect its parent folder and connection edges.</p>
            </div>
          </div>

          <div id="mindmap-copilot-content" class="mindmap-copilot-content inspector-pane" style="display: none">
            <div class="empty-state" style="padding: 40px 16px">
              <h4>No Vertex Selected</h4>
              <p>Select any node in the interactive mind map to launch a grounded Groq AI architectural audit and multi-turn codebase chat.</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  `;
}
