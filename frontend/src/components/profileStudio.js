// src/components/profileStudio.js — GitHub Profile Studio Component
import { renderMarkdownPreview } from './scannerStudio.js';
import { showToast } from '../main.js';

export function initProfileStudio() {
  const btnGenerateProfile = document.getElementById('btn-generate-profile');
  const inputUsername = document.getElementById('profile-username');
  const selectStyle = document.getElementById('profile-style');
  const inputTagline = document.getElementById('profile-tagline');
  const inputToken = document.getElementById('profile-token');
  const statsContent = document.getElementById('profile-stats-content');
  const styleBadge = document.getElementById('profile-style-badge');
  const viewToggleBtns = document.querySelectorAll('#tab-profile .view-mode-toggle .toggle-btn');
  const textareaProfileCode = document.getElementById('profile-textarea');
  const btnCopyProfile = document.getElementById('btn-copy-profile');
  const btnDownloadProfile = document.getElementById('btn-download-profile');

  btnGenerateProfile?.addEventListener('click', async () => {
    const username = inputUsername?.value?.trim();
    if (!username) {
      showToast('Please enter a valid GitHub username', 'error');
      return;
    }

    const style = selectStyle?.value || 'professional';
    const custom_tagline = inputTagline?.value || '';
    const token = inputToken?.value?.trim() || null;

    btnGenerateProfile.disabled = true;
    btnGenerateProfile.innerHTML = `<span class="spinner-ring" style="width:16px;height:16px;border-width:2px;"></span><span>Fetching Profile & Generating...</span>`;

    try {
      const response = await fetch('/api/github-profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username,
          style,
          token,
          custom_tagline
        })
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Failed to generate profile README' }));
        throw new Error(err.detail || 'GitHub Profile API error');
      }

      const data = await response.json();
      if (styleBadge) {
        styleBadge.textContent = `Style: ${data.style_used.charAt(0).toUpperCase() + data.style_used.slice(1)}`;
      }

      textareaProfileCode.value = data.readme;
      renderMarkdownPreview(data.readme, 'profile-preview-render');
      updateLiveStatsCard(data.user_data, data.languages, username);

      showToast(`GitHub Profile created for @${username}!`, 'success');
    } catch (err) {
      console.error('Profile generation error:', err);
      showToast(`Profile Error: ${err.message}`, 'error');
    } finally {
      btnGenerateProfile.disabled = false;
      btnGenerateProfile.innerHTML = `<span>Generate Profile README</span>`;
    }
  });

  viewToggleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      viewToggleBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const viewMode = btn.getAttribute('data-view');
      const renderContainer = document.getElementById('profile-preview-render');
      const codeContainer = document.getElementById('profile-preview-code');

      if (viewMode === 'profile-render') {
        renderContainer.classList.add('active');
        codeContainer.classList.remove('active');
        renderMarkdownPreview(textareaProfileCode.value, 'profile-preview-render');
      } else {
        renderContainer.classList.remove('active');
        codeContainer.classList.add('active');
      }
    });
  });

  textareaProfileCode?.addEventListener('input', () => {
    const renderContainer = document.getElementById('profile-preview-render');
    if (renderContainer.classList.contains('active')) {
      renderMarkdownPreview(textareaProfileCode.value, 'profile-preview-render');
    }
  });

  btnCopyProfile?.addEventListener('click', () => {
    const profileText = textareaProfileCode?.value || '';
    navigator.clipboard.writeText(profileText);
    showToast('GitHub Profile Markdown copied to clipboard!', 'success');
  });

  btnDownloadProfile?.addEventListener('click', () => {
    const profileText = textareaProfileCode?.value || '';
    if (!profileText) {
      showToast('No Profile README content to download', 'info');
      return;
    }
    const blob = new Blob([profileText], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const username = inputUsername?.value?.trim() || 'github-profile';
    a.download = `${username}-README.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Profile README.md downloaded successfully!', 'success');
  });
}

function updateLiveStatsCard(userData, languages, username) {
  const statsContent = document.getElementById('profile-stats-content');
  if (!statsContent) return;

  if (!userData) {
    statsContent.innerHTML = `
      <div class="empty-state">
        <h4>User: @${username}</h4>
        <p>Profile metrics fetched from GitHub API.</p>
      </div>
    `;
    return;
  }

  const langList = Object.entries(languages || {})
    .slice(0, 5)
    .map(([lang, pct]) => `<span class="badge badge-mono">${lang}: ${pct}%</span>`)
    .join(' ');

  statsContent.style.animation = 'none';
  statsContent.offsetHeight;
  statsContent.innerHTML = `
    <div style="display: flex; flex-direction: column; gap: 14px; animation: fadeSlideIn 0.3s ease-out;">
      <div style="display: flex; align-items: center; gap: 14px;">
        ${userData.avatar_url ? `<img src="${userData.avatar_url}" alt="${username}" style="width: 56px; height: 56px; border-radius: 50%; border: 1px solid var(--border-color);" />` : ''}
        <div>
          <h4 style="font-size: 1.15rem; color: var(--text-primary);">${userData.name || username}</h4>
          <p style="font-size: 0.88rem; color: var(--text-secondary);">@${username}</p>
        </div>
      </div>
      ${userData.bio ? `<p style="font-size: 0.9rem; color: var(--text-secondary); font-style: italic;">"${userData.bio}"</p>` : ''}
      <div style="display: flex; flex-wrap: wrap; gap: 16px; font-size: 0.85rem; color: var(--text-secondary);">
        <span><strong>${userData.public_repos || 0}</strong> Repos</span>
        <span><strong>${userData.followers || 0}</strong> Followers</span>
        ${userData.company ? `<span>Company: ${userData.company}</span>` : ''}
        ${userData.location ? `<span>Location: ${userData.location}</span>` : ''}
      </div>
      ${langList ? `<div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 6px;">${langList}</div>` : ''}
    </div>
  `;
}
