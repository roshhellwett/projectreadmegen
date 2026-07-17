// src/pages/settingsPage.js — API Dashboard & Settings Page

export function renderSettingsPage() {
  return `
    <section class="page-section" id="page-settings">
      <div class="dashboard-grid">
        <!-- API Key Card -->
        <div class="panel-card dashboard-card">
          <div class="card-title-icon">
            <div>
              <h3>Groq API Key Configuration</h3>
              <p>Required for AI README Generation and Groq integration.</p>
            </div>
          </div>
          <div class="api-key-box mt-4">
            <div class="input-group">
              <label for="dashboard-api-key">Your Groq API Key</label>
              <div class="password-input-wrapper">
                <input type="password" id="dashboard-api-key" placeholder="gsk_xxxxxxxxxxxxxxxxxxxxxxxx" />
                <button class="btn-toggle-visibility" id="btn-toggle-key">Show</button>
              </div>
            </div>
            <div class="dashboard-actions mt-3">
              <button id="btn-save-key" class="btn btn-primary">Save & Verify Key</button>
              <a
                href="https://console.groq.com/keys"
                target="_blank"
                rel="noopener noreferrer"
                class="btn btn-secondary"
              >
                <span>Get Free API Key</span>
              </a>
            </div>
          </div>
          <div class="api-status-banner mt-4" id="dashboard-key-banner"></div>
        </div>

        <!-- Usage Metrics Card -->
        <div class="panel-card dashboard-card">
          <div class="card-title-icon">
            <div>
              <h3>Usage Quotas & System Status</h3>
              <p>Real-time metrics monitored via local state.</p>
            </div>
          </div>
          <div class="usage-metrics-grid mt-4" id="dashboard-usage-grid">
            <div class="metric-box">
              <span class="metric-title">Groq Free Tier Rate Limit</span>
              <span class="metric-number">30 RPM / 14,400 RPD</span>
              <span class="metric-note">Ample quota for rapid documentation iteration</span>
            </div>
            <div class="metric-box">
              <span class="metric-title">Inference Speed</span>
              <span class="metric-number">~300+ Tokens/Sec</span>
              <span class="metric-note">Powered by Groq LPU™ Engine</span>
            </div>
            <div class="metric-box">
              <span class="metric-title">Local Cache Status</span>
              <span class="metric-number">Active & Atomic</span>
              <span class="metric-note">Zero redundant disk scans on unchanged folders</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  `;
}
