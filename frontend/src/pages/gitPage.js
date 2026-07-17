// src/pages/gitPage.js — Git Track Studio Page
import { getState } from '../state.js';

export function renderGitPage() {
  const path = getState().projectPath || '.';
  return `
    <section class="page-section" id="page-git">
      <!-- Git Controls -->
      <div class="control-banner panel-card">
        <div class="input-group path-input-group">
          <label for="git-path">Repository Path</label>
          <div class="input-with-actions">
            <input type="text" id="git-path" placeholder="e.g. . or D:\\project" value="${path}" />
            <button id="btn-git-load" class="btn btn-primary">Load Git Graph</button>
            <button id="btn-git-refresh" class="btn btn-secondary btn-sm" title="Refresh">Refresh</button>
          </div>
        </div>

        <div class="options-row">
          <div class="options-group">
            <span class="group-title">Layout Style</span>
            <div class="template-selector-pills" id="git-layout-pills">
              <button class="pill-btn active" data-git-layout="all">All Branches</button>
              <button class="pill-btn" data-git-layout="current">Current Branch Only</button>
              <button class="pill-btn" data-git-layout="compact">Compact Timeline</button>
            </div>
          </div>

          <div class="options-group">
            <span class="group-title">Working Tree Status</span>
            <div class="git-status-bar" id="git-status-bar" style="margin-top: 0">
              <span class="git-status-chip git-modified">Modified: 0</span>
              <span class="git-status-chip git-staged">Staged: 0</span>
              <span class="git-status-chip git-untracked">Untracked: 0</span>
              <span class="git-branch-label" id="git-current-branch">branch: main</span>
            </div>
          </div>

          <div class="options-group">
            <span class="group-title">Zoom & Pan</span>
            <div class="template-selector-pills">
              <button class="pill-btn" id="btn-git-zoomin" title="Zoom In">+</button>
              <button class="pill-btn" id="btn-git-zoomout" title="Zoom Out">-</button>
              <button class="pill-btn" id="btn-git-reset" title="Reset View">Reset</button>
              <button class="pill-btn" id="btn-git-fit" title="Fit View to Window">Fit</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Canvas + Inspector Split -->
      <div class="mindmap-split-grid mt-4">
        <div class="mindmap-canvas-card panel-card">
          <div class="pane-header">
            <div class="header-left">
              <h3>Interactive Git Commit Graph</h3>
              <div id="git-stats-bar" class="mindmap-stats-bar">
                <span class="badge badge-mono" id="git-commit-count">Commits: 0</span>
              </div>
            </div>
            <div class="header-right">
              <span class="text-xs text-secondary">Drag canvas to pan | Scroll to zoom | Click commits for details</span>
            </div>
          </div>
          <div id="git-canvas-container" class="mindmap-canvas-container">
            <svg id="git-svg" viewBox="0 0 1200 800" class="mindmap-svg">
              <g class="empty-mindmap">
                <text x="600" y="400" text-anchor="middle" class="empty-text">
                  Click "Load Git Graph" above to generate your repository graph
                </text>
              </g>
            </svg>
          </div>
        </div>

        <div class="mindmap-inspector-card panel-card">
          <div class="pane-header inspector-pane-header">
            <div class="inspector-tab-selector">
              <button class="inspector-tab-btn active" style="cursor: default">Commit Inspector</button>
            </div>
          </div>

          <div id="git-inspector-content" class="mindmap-inspector-content inspector-pane active">
            <div class="empty-state" style="padding: 40px 16px">
              <h4>Select a Commit</h4>
              <p>Click on any commit node on the graph to inspect its changes, files, and diff.</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  `;
}
