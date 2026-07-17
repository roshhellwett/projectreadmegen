// src/pages/aiPage.js — AI README Architect Page
import { getState } from '../state.js';

export function renderAIPage() {
  const path = getState().projectPath || '.';
  return `
    <section class="page-section" id="page-ai">
      <!-- AI Controls Banner -->
      <div class="ai-banner panel-card">
        <div class="ai-controls-grid">
          <div class="input-group">
            <label for="ai-path">Project Directory</label>
            <input type="text" id="ai-path" value="${path}" placeholder="e.g., . or D:\\projects\\my-app" />
          </div>
          <div class="input-group">
            <label for="ai-model">Groq AI Model</label>
            <select id="ai-model">
              <option value="llama-3.3-70b-versatile">llama-3.3-70b-versatile (Recommended)</option>
              <option value="llama-3.1-8b-instant">llama-3.1-8b-instant (Fast)</option>
              <option value="mixtral-8x7b-32768">mixtral-8x7b-32768 (High Context)</option>
            </select>
          </div>
          <div class="input-group">
            <label for="ai-tone">Architectural Tone</label>
            <select id="ai-tone">
              <option value="professional">Professional Corporate</option>
              <option value="technical">Deeply Technical & Architectural</option>
              <option value="enthusiastic">Vibrant & Community Focused</option>
              <option value="concise">Ultra-Concise Bullet Points</option>
            </select>
          </div>
        </div>
        <div class="input-group mt-3">
          <label for="ai-instructions">Custom Architectural Instructions (Optional)</label>
          <textarea
            id="ai-instructions"
            rows="3"
            placeholder="e.g., Emphasize zero-latency rendering, include deployment instructions for Docker, highlight security benchmarks..."
          ></textarea>
        </div>
        <div class="ai-action-bar mt-4 pt-3">
          <button id="btn-generate-ai" class="btn btn-primary">
            <span>Architect AI README</span>
          </button>
        </div>
      </div>

      <!-- Thinking State -->
      <div id="ai-thinking-state" class="thinking-card panel-card hidden">
        <div class="spinner-ring"></div>
        <div class="thinking-content">
          <h4 id="thinking-title">AI Architect is synthesizing codebase...</h4>
          <p id="thinking-subtitle">Analyzing folder tree, checking dependencies, and crafting documentation.</p>
        </div>
      </div>

      <!-- AI Preview -->
      <div class="panel-card preview-card mt-4">
        <div class="pane-header">
          <div class="header-left">
            <h3>AI Generated Documentation</h3>
            <span class="badge badge-mono" id="ai-model-badge">Model: llama-3.3-70b</span>
          </div>
          <div class="header-right">
            <div class="view-mode-toggle">
              <button class="toggle-btn active" data-view="ai-render">Live Preview</button>
              <button class="toggle-btn" data-view="ai-code">Markdown Code</button>
            </div>
            <button class="btn btn-secondary btn-sm" id="btn-copy-ai">Copy</button>
            <button class="btn btn-primary btn-sm" id="btn-download-ai">Download</button>
          </div>
        </div>
        <div class="preview-area">
          <div id="ai-preview-render" class="markdown-body active">
            <div class="empty-state">
              <h4>Configure & Architect</h4>
              <p>Select your tone and instructions above to generate a custom, project-aware README via Groq LLM.</p>
            </div>
          </div>
          <div id="ai-preview-code" class="code-view">
            <textarea
              id="ai-textarea"
              spellcheck="false"
              placeholder="# AI Generated Markdown will appear here..."
            ></textarea>
          </div>
        </div>
      </div>
    </section>
  `;
}
