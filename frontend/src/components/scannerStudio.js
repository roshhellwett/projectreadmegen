// src/components/scannerStudio.js — Interactive Project Scanner & Template Studio
import { marked } from 'marked';
import hljs from 'highlight.js';
import { showToast } from '../main.js';
import { setMindMapGraphFromScan } from './mindmapStudio.js';
import { syncPathInputs, setState } from '../state.js';

let currentScanResult = null;
let currentDetection = null;
let currentConfig = { template: 'standard' };

export function initScannerStudio() {
  const btnScan = document.getElementById('btn-scan');
  const inputPath = document.getElementById('scanner-path');
  const checkboxCache = document.getElementById('scanner-cache');
  const templatePills = document.querySelectorAll('#template-selector .pill-btn');
  const viewToggleBtns = document.querySelectorAll('#page-studio .view-mode-toggle .toggle-btn');
  const textareaCode = document.getElementById('readme-textarea');
  const btnCopyTree = document.getElementById('btn-copy-tree');
  const btnCopyReadme = document.getElementById('btn-copy-readme');
  const btnDownloadReadme = document.getElementById('btn-download-readme');

  // Scan button action
  btnScan?.addEventListener('click', async () => {
    const path = inputPath?.value || '.';
    const useCache = checkboxCache?.checked ?? true;

    btnScan.disabled = true;
    btnScan.innerHTML = `<span class="spinner-ring" style="width:16px;height:16px;border-width:2px;"></span><span>Scanning...</span>`;

    try {
      const response = await fetch('/api/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path, use_cache: useCache })
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Network error during scan' }));
        throw new Error(err.detail || 'Scan request failed');
      }

      const data = await response.json();
      currentScanResult = data.scan_result;
      currentDetection = data.detection;
      currentConfig = { ...data.config, template: currentConfig.template };

      // Update shared state
      setState('scanResult', currentScanResult);
      setState('detection', currentDetection);

      if (data.resolved_path) {
        syncPathInputs(data.resolved_path);
      }
      if (data.scan_result && data.scan_result.graph) {
        setMindMapGraphFromScan(data.scan_result.graph, data.resolved_path);
      }

      updateStatsOverview(data.scan_result, data.detection);
      updateTreeCode(data.scan_result.tree);
      updateDetectionChips(data.detection);
      
      showToast(`Successfully analyzed repository: ${data.scan_result.name}`, 'success');

      // Auto generate README with selected template
      await generateTemplateReadme();
    } catch (err) {
      console.error('Scan error:', err);
      showToast(err.message || 'Error executing scan', 'error');
    } finally {
      btnScan.disabled = false;
      btnScan.innerHTML = `<span>Scan Directory</span>`;
    }
  });

  // Path input sync via shared state
  inputPath?.addEventListener('input', () => {
    syncPathInputs(inputPath.value);
  });

  // Template selector pills
  templatePills.forEach(pill => {
    pill.addEventListener('click', async () => {
      templatePills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      currentConfig.template = pill.getAttribute('data-template') || 'standard';

      if (currentScanResult && currentDetection) {
        await generateTemplateReadme();
      }
    });
  });

  // View mode toggle (Live Preview vs Markdown Code)
  viewToggleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      viewToggleBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const viewMode = btn.getAttribute('data-view');
      const renderContainer = document.getElementById('readme-preview-render');
      const codeContainer = document.getElementById('readme-preview-code');

      if (viewMode === 'render') {
        renderContainer.classList.add('active');
        codeContainer.classList.remove('active');
        // Update live render from current textarea value
        renderMarkdownPreview(textareaCode.value, 'readme-preview-render');
      } else {
        renderContainer.classList.remove('active');
        codeContainer.classList.add('active');
      }
    });
  });

  // Real-time sync when typing in markdown textarea
  textareaCode?.addEventListener('input', () => {
    const renderContainer = document.getElementById('readme-preview-render');
    if (renderContainer.classList.contains('active')) {
      renderMarkdownPreview(textareaCode.value, 'readme-preview-render');
    }
  });

  // Copy buttons
  btnCopyTree?.addEventListener('click', () => {
    const treeCode = document.getElementById('scanner-tree-code')?.textContent || '';
    navigator.clipboard.writeText(treeCode);
    showToast('ASCII Tree copied to clipboard!', 'success');
  });

  btnCopyReadme?.addEventListener('click', () => {
    const readmeText = textareaCode?.value || '';
    navigator.clipboard.writeText(readmeText);
    showToast('README Markdown copied to clipboard!', 'success');
  });

  btnDownloadReadme?.addEventListener('click', () => {
    const readmeText = textareaCode?.value || '';
    if (!readmeText) {
      showToast('No README content to download', 'info');
      return;
    }
    const blob = new Blob([readmeText], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'README.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('README.md downloaded successfully!', 'success');
  });
}

function updateStatsOverview(scan, detection) {
  document.getElementById('stat-lang').textContent = detection.primary_lang || 'Unknown';
  document.getElementById('stat-type').textContent = detection.project_type || 'General';
  document.getElementById('stat-license').textContent = detection.license || 'None';
  const fileCount = scan.graph?.stats?.file_count ?? scan.files?.length ?? 0;
  const dirCount = scan.graph?.stats?.dir_count ?? scan.dirs?.length ?? 0;
  document.getElementById('stat-count').textContent = `${fileCount} Files / ${dirCount} Dirs`;
}

function updateTreeCode(tree) {
  const treeEl = document.getElementById('scanner-tree-code');
  if (treeEl) {
    treeEl.textContent = tree;
  }
}

function updateDetectionChips(detection) {
  const container = document.getElementById('detection-chips-container');
  if (!container) return;

  const chips = [
    { label: 'Languages', value: detection.languages?.slice(0, 4).join(', ') || 'None' },
    { label: 'Install Cmd', value: detection.install_cmd || 'N/A' },
    { label: 'Package Mgr', value: detection.package_manager || 'None' },
    { label: 'Tests', value: detection.has_tests ? 'Yes' : 'No' },
    { label: 'Docs', value: detection.has_docs ? 'Yes' : 'No' }
  ];

  container.innerHTML = chips.map(c => `
    <div class="chip" title="${c.label}: ${c.value}">
      <span>${c.label}:</span>
      <strong>${c.value}</strong>
    </div>
  `).join('');
}

async function generateTemplateReadme() {
  if (!currentScanResult || !currentDetection) return;

  try {
    const response = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        scan_result: currentScanResult,
        detection: currentDetection,
        config: currentConfig
      })
    });

    if (!response.ok) {
      throw new Error('Failed to generate template README');
    }

    const data = await response.json();
    const textareaCode = document.getElementById('readme-textarea');
    if (textareaCode) {
      textareaCode.value = data.readme;
    }
    renderMarkdownPreview(data.readme, 'readme-preview-render');
  } catch (err) {
    console.error('Template generation error:', err);
    showToast('Failed to generate README template', 'error');
  }
}

export function renderMarkdownPreview(markdownText, containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;

  if (!markdownText || markdownText.trim() === '') {
    container.innerHTML = `
      <div class="empty-state">
        <h4>Ready to Generate</h4>
        <p>Scan your directory or select a template to generate real-time documentation.</p>
      </div>
    `;
    return;
  }

  // Parse markdown
  const renderedHTML = marked.parse(markdownText);
  container.innerHTML = renderedHTML;

  // Apply syntax highlighting
  container.querySelectorAll('pre code').forEach((block) => {
    hljs.highlightElement(block);
  });
}
