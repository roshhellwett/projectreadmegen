// src/components/aiStudio.js — AI README Architect Component
import { renderMarkdownPreview } from './scannerStudio.js';
import { showToast } from '../main.js';
import { syncPathInputs } from '../state.js';

export function initAIStudio() {
  const btnGenerateAI = document.getElementById('btn-generate-ai');
  const inputPath = document.getElementById('ai-path');
  const selectModel = document.getElementById('ai-model');
  const selectTone = document.getElementById('ai-tone');
  const textareaInstructions = document.getElementById('ai-instructions');
  const thinkingCard = document.getElementById('ai-thinking-state');
  const modelBadge = document.getElementById('ai-model-badge');
  const viewToggleBtns = document.querySelectorAll('#page-ai .view-mode-toggle .toggle-btn');
  const textareaAICode = document.getElementById('ai-textarea');
  const btnCopyAI = document.getElementById('btn-copy-ai');
  const btnDownloadAI = document.getElementById('btn-download-ai');

  // Path sync via shared state
  inputPath?.addEventListener('input', () => {
    syncPathInputs(inputPath.value);
  });

  textareaInstructions?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      btnGenerateAI?.click();
    }
  });

  btnGenerateAI?.addEventListener('click', async () => {
    const path = inputPath?.value || '.';
    const model = selectModel?.value || 'llama-3.3-70b-versatile';
    const tone = selectTone?.value || 'professional';
    const custom_instructions = textareaInstructions?.value || '';

    btnGenerateAI.disabled = true;
    btnGenerateAI.innerHTML = `<span class="spinner-ring" style="width:16px;height:16px;border-width:2px;"></span><span>Architecting AI README...</span>`;
    thinkingCard?.classList.remove('hidden');
    thinkingCard?.style.setProperty('animation', 'fadeSlideIn 0.2s ease-out');

    try {
      const response = await fetch('/api/generate-ai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          path,
          model,
          tone,
          custom_instructions
        })
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Groq API request failed' }));
        throw new Error(err.detail || 'AI generation failed');
      }

      const data = await response.json();
      if (modelBadge) {
        modelBadge.textContent = `Model: ${data.model_used}`;
      }

      textareaAICode.value = data.readme;
      renderMarkdownPreview(data.readme, 'ai-preview-render');

      showToast('AI README successfully architected by Groq LLM!', 'success');
    } catch (err) {
      console.error('AI generation error:', err);
      showToast(`AI Error: ${err.message}`, 'error');
    } finally {
      btnGenerateAI.disabled = false;
      btnGenerateAI.innerHTML = `<span>Architect AI README</span>`;
      thinkingCard?.classList.add('hidden');
      thinkingCard?.style.removeProperty('animation');
    }
  });

  // View mode toggle
  viewToggleBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      viewToggleBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const viewMode = btn.getAttribute('data-view');
      const renderContainer = document.getElementById('ai-preview-render');
      const codeContainer = document.getElementById('ai-preview-code');

      if (viewMode === 'ai-render') {
        renderContainer.classList.add('active');
        codeContainer.classList.remove('active');
        renderMarkdownPreview(textareaAICode.value, 'ai-preview-render');
      } else {
        renderContainer.classList.remove('active');
        codeContainer.classList.add('active');
      }
    });
  });

  textareaAICode?.addEventListener('input', () => {
    const renderContainer = document.getElementById('ai-preview-render');
    if (renderContainer.classList.contains('active')) {
      renderMarkdownPreview(textareaAICode.value, 'ai-preview-render');
    }
  });

  btnCopyAI?.addEventListener('click', () => {
    const aiText = textareaAICode?.value || '';
    navigator.clipboard.writeText(aiText);
    showToast('AI README copied to clipboard!', 'success');
  });

  btnDownloadAI?.addEventListener('click', () => {
    const aiText = textareaAICode?.value || '';
    if (!aiText) {
      showToast('No AI README content to download', 'info');
      return;
    }
    const blob = new Blob([aiText], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'AI-README.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('AI-README.md downloaded successfully!', 'success');
  });
}
