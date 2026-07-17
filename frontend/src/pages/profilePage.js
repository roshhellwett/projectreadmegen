// src/pages/profilePage.js — GitHub Profile Studio Page

export function renderProfilePage() {
  return `
    <section class="page-section" id="page-profile">
      <!-- Profile Controls Grid -->
      <div class="profile-controls-grid">
        <div class="panel-card profile-form-card">
          <h3>Profile Setup & Configuration</h3>
          <div class="form-grid">
            <div class="input-group">
              <label for="profile-username">GitHub Username <span class="required">*</span></label>
              <input type="text" id="profile-username" placeholder="e.g., roshhellwett" />
            </div>
            <div class="input-group">
              <label for="profile-style">Visual Style Preset</label>
              <select id="profile-style">
                <option value="professional">Professional & Career Focused</option>
                <option value="stylish">Stylish & Dynamic Cards</option>
                <option value="unique">Creative & Unique Bento</option>
                <option value="basic">Clean Minimalist</option>
              </select>
            </div>
            <div class="input-group">
              <label for="profile-tagline">Animated Typing Tagline</label>
              <input
                type="text"
                id="profile-tagline"
                placeholder="e.g., Building state-of-the-art applications"
              />
            </div>
            <div class="input-group">
              <label for="profile-token">GitHub Token (Optional for higher rate limits)</label>
              <input type="password" id="profile-token" placeholder="ghp_xxxxxxxxxxxx" />
            </div>
          </div>
          <div class="mt-4 pt-3" style="border-top: 1px solid var(--border-color)">
            <button id="btn-generate-profile" class="btn btn-primary w-full">
              <span>Generate Profile README</span>
            </button>
          </div>
        </div>

        <div class="panel-card profile-stats-preview">
          <h3>Live Profile Metrics Preview</h3>
          <div class="profile-stats-content" id="profile-stats-content">
            <div class="empty-state">
              <h4>Enter Username</h4>
              <p>We'll fetch public repositories, language distribution, and GitHub stats to populate your custom profile.</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Profile Preview -->
      <div class="panel-card preview-card mt-4">
        <div class="pane-header">
          <div class="header-left">
            <h3>Profile README Studio</h3>
            <span class="badge badge-mono" id="profile-style-badge">Style: Professional</span>
          </div>
          <div class="header-right">
            <div class="view-mode-toggle">
              <button class="toggle-btn active" data-view="profile-render">Live Preview</button>
              <button class="toggle-btn" data-view="profile-code">Markdown Code</button>
            </div>
            <button class="btn btn-secondary btn-sm" id="btn-copy-profile">Copy</button>
            <button class="btn btn-primary btn-sm" id="btn-download-profile">Download</button>
          </div>
        </div>
        <div class="preview-area">
          <div id="profile-preview-render" class="markdown-body active">
            <div class="empty-state">
              <h4>Your Profile Masterpiece</h4>
              <p>Click "Generate Profile README" to create a clean GitHub profile with live shields and dynamic stats.</p>
            </div>
          </div>
          <div id="profile-preview-code" class="code-view">
            <textarea
              id="profile-textarea"
              spellcheck="false"
              placeholder="# GitHub Profile Markdown will appear here..."
            ></textarea>
          </div>
        </div>
      </div>
    </section>
  `;
}
