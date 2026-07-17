// src/pages/studioPage.js — Project Scanner & README Template Studio Page
import { getState } from '../state.js';

export function renderStudioPage() {
  const path = getState().projectPath || '.';
  return `
    <section class="page-section" id="page-studio">
      <!-- Scanner Controls -->
      <div class="control-banner panel-card">
        <div class="input-group path-input-group">
          <label for="scanner-path">Project Root Path</label>
          <div class="input-with-actions">
            <input
              type="text"
              id="scanner-path"
              placeholder="e.g., . or D:\\projects\\my-app or C:\\workspace\\project"
              value="${path}"
            />
            <button id="btn-scan" class="btn btn-primary">
              <span>Scan Directory</span>
            </button>
          </div>
        </div>
        <div class="banner-actions mt-2">
          <label class="toggle-checkbox">
            <input type="checkbox" id="scanner-cache" checked />
            <span class="checkmark"></span>
            <span class="toggle-label">Smart Scan Cache (Zero-latency atomic cache)</span>
          </label>
        </div>
      </div>

      <!-- Stats Overview -->
      <div class="stats-overview" id="scanner-stats-bar">
        <div class="stat-card stat-card-dark">
          <span class="stat-label">Primary Language</span>
          <span class="stat-value" id="stat-lang">—</span>
        </div>
        <div class="stat-card panel-card">
          <span class="stat-label">Project Type</span>
          <span class="stat-value" id="stat-type">—</span>
        </div>
        <div class="stat-card panel-card">
          <span class="stat-label">Detected License</span>
          <span class="stat-value" id="stat-license">—</span>
        </div>
        <div class="stat-card panel-card">
          <span class="stat-label">Total Files & Dirs</span>
          <span class="stat-value" id="stat-count">—</span>
        </div>
      </div>

      <!-- Split Grid: Tree + Preview -->
      <div class="studio-split-grid">
        <!-- Left: Folder Structure -->
        <div class="split-pane panel-card">
          <div class="pane-header">
            <div class="header-left">
              <h3>Folder Structure & Detection</h3>
              <span class="badge badge-mono" id="tree-depth-badge">Depth: Auto</span>
            </div>
            <button class="btn btn-secondary btn-sm" id="btn-copy-tree" title="Copy ASCII Tree">Copy</button>
          </div>
          <div class="tree-container">
            <pre><code class="language-plaintext" id="scanner-tree-code">Click "Scan Directory" above to analyze your repository structure and build our ASCII visualizer.</code></pre>
          </div>
          <div class="detection-chips" id="detection-chips-container"></div>
        </div>

        <!-- Right: README Preview -->
        <div class="split-pane panel-card">
          <div class="pane-header">
            <div class="header-left">
              <h3>README Studio</h3>
              <div class="template-selector-pills" id="template-selector">
                <button class="pill-btn active" data-template="standard">Standard</button>
                <button class="pill-btn" data-template="minimal">Minimal</button>
                <button class="pill-btn" data-template="full">Full</button>
                <button class="pill-btn" data-template="academic">Academic</button>
              </div>
            </div>
            <div class="header-right">
              <div class="view-mode-toggle">
                <button class="toggle-btn active" data-view="render">Live Preview</button>
                <button class="toggle-btn" data-view="code">Markdown Code</button>
              </div>
              <button class="btn btn-secondary btn-sm" id="btn-copy-readme">Copy</button>
              <button class="btn btn-primary btn-sm" id="btn-download-readme">Download</button>
            </div>
          </div>

          <div class="preview-area">
            <div id="readme-preview-render" class="markdown-body active">
              <div class="empty-state">
                <h4>Ready to Generate</h4>
                <p>Scan your directory or select a template to generate documentation.</p>
              </div>
            </div>
            <div id="readme-preview-code" class="code-view">
              <textarea
                id="readme-textarea"
                spellcheck="false"
                placeholder="# Generated README markdown will appear here..."
              ></textarea>
            </div>
          </div>
        </div>
      </div>
    </section>
  `;
}
