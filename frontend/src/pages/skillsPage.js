// src/pages/skillsPage.js — Skills Studio Page
import { getState } from '../state.js';

export function renderSkillsPage() {
  const path = getState().projectPath || '.';
  return `
    <section class="page-section" id="page-skills">
      <!-- Skills Controls -->
      <div class="control-banner panel-card">
        <div class="input-group path-input-group">
          <label for="skills-path">Target Project Path</label>
          <div class="input-with-actions">
            <input type="text" id="skills-path" placeholder="e.g., . or D:\\projects\\my-app" value="${path}" />
            <span class="input-hint" id="skills-path-hint"></span>
          </div>
        </div>
        <div class="skills-search-row mt-3">
          <div class="skills-search-wrap">
            <label for="skills-search">Search Skills</label>
            <input
              type="text"
              id="skills-search"
              placeholder="ui, ux, architect, testing, security..."
              autocomplete="off"
            />
            <button id="skills-clear-search">&times;</button>
          </div>
          <div class="skills-actions">
            <span class="badge badge-mono" id="skills-count">0 skills</span>
            <span class="badge badge-mono" id="skills-selected-count">0 selected</span>
            <button id="skills-install-all" class="btn btn-primary">Install Selected</button>
          </div>
        </div>
      </div>

      <!-- Skills Categories Container -->
      <div id="skills-categories-container" class="mt-4">
        <div class="empty-state">
          <h4>Loading Skills</h4>
          <p>Fetching available skill library...</p>
        </div>
      </div>
    </section>
  `;
}
