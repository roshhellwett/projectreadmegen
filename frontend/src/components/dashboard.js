// src/components/dashboard.js — API Key Dashboard & Status Controller
import { showToast } from '../main.js';

export function initDashboard() {
  const btnSaveKey = document.getElementById('btn-save-key');
  const inputApiKey = document.getElementById('dashboard-api-key');
  const btnToggleKey = document.getElementById('btn-toggle-key');

  btnToggleKey?.addEventListener('click', () => {
    if (!inputApiKey) return;
    if (inputApiKey.type === 'password') {
      inputApiKey.type = 'text';
      btnToggleKey.textContent = 'Hide';
    } else {
      inputApiKey.type = 'password';
      btnToggleKey.textContent = 'Show';
    }
  });

  btnSaveKey?.addEventListener('click', async () => {
    const api_key = inputApiKey?.value?.trim();
    if (!api_key) {
      showToast('Please enter your Groq API key', 'error');
      return;
    }

    btnSaveKey.disabled = true;
    btnSaveKey.textContent = 'Saving & Verifying...';

    try {
      const response = await fetch('/api/key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key })
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Failed to update API key' }));
        throw new Error(err.detail || 'API key update failed');
      }

      const data = await response.json();
      inputApiKey.value = '';
      await checkAPIStatus();
      showToast(data.message || 'API key configured successfully!', 'success');
    } catch (err) {
      console.error('API key save error:', err);
      showToast(`Key Error: ${err.message}`, 'error');
    } finally {
      btnSaveKey.disabled = false;
      btnSaveKey.textContent = 'Save & Verify Key';
    }
  });

  document.querySelectorAll('.studio-feature-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTabId = btn.getAttribute('data-target-tab');
      if (targetTabId) {
        const navBtn = document.querySelector(`.nav-btn[data-tab="${targetTabId}"]`);
        if (navBtn) navBtn.click();
      }
    });
  });
}

export async function checkAPIStatus() {
  const statusPill = document.getElementById('api-status-pill');
  const statusText = document.getElementById('api-status-text');
  const keyBanner = document.getElementById('dashboard-key-banner');

  try {
    const response = await fetch('/api/status');
    if (!response.ok) throw new Error('Status endpoint unresponsive');

    const data = await response.json();

    if (data.api_key_configured) {
      statusPill?.classList.add('connected');
      statusPill?.classList.remove('error');
      if (statusText) statusText.textContent = 'Groq API: Connected';

      if (keyBanner) {
        const masked = data.api_key_masked ? `<code style="background:rgba(0,0,0,0.06);padding:2px 8px;border-radius:4px;font-family:'JetBrains Mono';font-size:12px;">${data.api_key_masked}</code>` : '';
        keyBanner.innerHTML = `
          <div class="status-banner banner-connected">
            <div class="banner-text">
              <strong>Groq API Key Configured</strong>
              <p>${masked ? 'Active key: ' + masked : 'Your custom API key is active.'} All AI README generation features are unlocked.</p>
            </div>
          </div>
        `;
      }
    } else {
      statusPill?.classList.remove('connected');
      statusPill?.classList.add('error');
      if (statusText) statusText.textContent = 'Groq API: Missing Key';

      if (keyBanner) {
        keyBanner.innerHTML = `
          <div class="status-banner banner-required">
            <div class="banner-text">
              <strong>API Key Required</strong>
              <p>Template-based README generation works locally. To unlock AI Architect features, enter your free Groq API key above.</p>
            </div>
          </div>
        `;
      }
    }
  } catch (err) {
    console.error('API Status Check Error:', err);
    if (statusText) statusText.textContent = 'Backend Offline';
    statusPill?.classList.remove('connected');
    statusPill?.classList.add('error');
  }
}
