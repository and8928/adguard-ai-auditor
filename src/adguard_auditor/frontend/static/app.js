/* ===================================================
   AdGuard AI Auditor -- Dashboard Application
   Single-page app with SSE streaming and CRUD prompts
   =================================================== */

const API = '/api/v1';

/* == State == */
const state = {
    results: null,        // AnalysisResponse
    selectedBlock: {},    // { domain: true }
    selectedUnblock: {},
    rules: [],
    isRunning: false,
    editingRuleId: null,
    currentRules: null,   // OptimizedRulesSet from /get_actual_filter
};

/* ===============================
   INITIALIZATION
   =============================== */

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    loadPromptRules();
    loadCacheStatus();
    setupEventListeners();
});


function setupEventListeners() {
    // Audit buttons
    document.getElementById('btn-run-audit').addEventListener('click', () => startAudit('full'));
    document.getElementById('btn-fetch-data').addEventListener('click', () => startAudit('fetch'));
    document.getElementById('btn-run-analysis').addEventListener('click', () => startAudit('analyze'));

    // Apply changes button
    document.getElementById('btn-apply-changes').addEventListener('click', applyChanges);

    // Add rule button
    document.getElementById('btn-add-rule').addEventListener('click', () => toggleModal(true));

    // Modal
    document.getElementById('modal-close').addEventListener('click', () => toggleModal(false));
    document.getElementById('modal-overlay').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) toggleModal(false);
    });
    document.getElementById('modal-form').addEventListener('submit', (e) => {
        e.preventDefault();
        saveNewRule();
    });

    // Select all checkboxes
    document.getElementById('select-all-block').addEventListener('change', (e) => {
        toggleSelectAll('block', e.target.checked);
    });
    document.getElementById('select-all-unblock').addEventListener('change', (e) => {
        toggleSelectAll('unblock', e.target.checked);
    });

    // Current Rules card
    document.getElementById('cr-refresh').addEventListener('click', (e) => {
        e.stopPropagation();
        loadCurrentFilters();
    });
    document.getElementById('cr-header').addEventListener('click', toggleCurrentRules);
    document.getElementById('cr-search').addEventListener('input', renderCurrentRules);
    document.getElementById('cr-filter-type').addEventListener('change', renderCurrentRules);
}


/* ===============================
   TABS
   =============================== */

function initTabs() {
    const buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            buttons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
            document.getElementById(`tab-${tabId}`).classList.add('active');
        });
    });
}


/* ===============================
   CACHE STATUS
   =============================== */

async function loadCacheStatus() {
    try {
        const resp = await fetch(`${API}/audit/cache`);
        const data = await resp.json();
        updateCacheUI(data);
    } catch (e) {
        console.error('Failed to load cache status:', e);
    }
}

function updateCacheUI(cacheData) {
    const infoEl = document.getElementById('cache-info');
    const badgeEl = document.getElementById('cache-badge');
    const analysisBtn = document.getElementById('btn-run-analysis');

    if (cacheData && cacheData.has_data) {
        const dt = new Date(cacheData.fetch_time);
        const timeStr = dt.toLocaleString();
        const totalRecords = (cacheData.allowed_count || 0) + (cacheData.blocked_count || 0);
        badgeEl.textContent = t('cache.status', timeStr, totalRecords);
        infoEl.classList.remove('hidden');
        analysisBtn.disabled = false;
    } else {
        infoEl.classList.add('hidden');
        analysisBtn.disabled = true;
    }
}

async function clearCache() {
    try {
        await fetch(`${API}/audit/cache/clear`, {method: 'POST'});
        updateCacheUI({has_data: false});
        showToast(t('cache.cleared'), 'info');
    } catch (e) {
        showToast(t('toast.network_error'), 'error');
    }
}


/* ===============================
   AUDIT -- SSE STREAMING
   =============================== */

function startAudit(action = 'full') {
    if (state.isRunning) return;
    state.isRunning = true;
    state.results = null;
    state.selectedBlock = {};
    state.selectedUnblock = {};

    const limit = document.getElementById('sel-limit').value;
    const model = document.getElementById('sel-model').value;
    const userPrompt = document.getElementById('input-user-prompt').value.trim();

    // Reset UI
    setAllButtonsState(true, action);
    clearResults();

    if (action === 'analyze') {
        // For analyze-only, skip fetch/clean steps visually
        resetStepper();
        updateStep('fetch', 'done', '');
        updateStep('clean', 'done', t('step.from_cache'));
        updateStep('llm', 'active', t('step.llm_start', model));
    } else {
        resetStepper();
        updateStep('fetch', 'active', t('step.connecting'));
    }

    const params = new URLSearchParams({limit, model_services: model, action});
    if (userPrompt) params.set('user_prompt', userPrompt);

    const eventSource = new EventSource(`${API}/audit/stream?${params.toString()}`);

    eventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleStreamEvent(data, action);
        } catch (e) {
            console.error('SSE parse error:', e);
        }
    };

    eventSource.onerror = () => {
        eventSource.close();
        if (state.isRunning) {
            updateStep('fetch', 'error', t('step.err_conn'));
            showToast(t('toast.conn_lost'), 'error');
            finishAudit();
        }
    };

    state._eventSource = eventSource;
}

function handleStreamEvent(data, action) {
    switch (data.status) {
        case 'fetching':
            updateStep('fetch', 'active', t('step.fetching_count', data.count));
            break;

        case 'fetch_done':
            updateStep('fetch', 'done', t('step.fetching_count', data.count));
            updateStep('clean', 'active', t('step.cleaning'));
            break;

        case 'cleaning':
            updateStep('clean', 'active', t('step.cleaned_stats', data.allowed, data.blocked));
            break;

        case 'clean_done':
            if (data.from_cache) {
                updateStep('clean', 'done', t('step.from_cache'));
            } else {
                updateStep('clean', 'done', t('step.cleaned_stats', data.allowed, data.blocked));
            }
            // Update cache UI if cache info is present
            if (data.cache) {
                updateCacheUI(data.cache);
            }
            if (action !== 'fetch') {
                updateStep('llm', 'active', t('step.llm_start', data.model || 'AI'));
            }
            break;

        case 'fetch_complete':
            // Fetch-only mode finished
            updateStep('clean', 'done', t('step.done'));
            if (data.cache) {
                updateCacheUI(data.cache);
            }
            finishAudit();
            if (state._eventSource) {
                state._eventSource.close();
            }
            showToast(t('toast.fetch_success'), 'success');
            break;

        case 'llm_thinking':
            updateStep('llm', 'active', t('step.llm_thinking', data.model));
            break;

        case 'complete':
            updateStep('llm', 'done', t('step.llm_done'));
            updateStep('result', 'done', t('step.done'));
            state.results = data.result;
            renderResults(data.result);
            finishAudit();
            if (state._eventSource) {
                state._eventSource.close();
            }
            showToast(t('toast.audit_success'), 'success');
            break;

        case 'error':
            const errorStep = data.step || 'fetch';
            updateStep(errorStep, 'error', data.message || t('step.err_general'));
            finishAudit();
            if (state._eventSource) {
                state._eventSource.close();
            }
            showToast(data.message || t('toast.audit_error'), 'error');
            // Even on LLM error, cache might still be valid -- refresh it
            loadCacheStatus();
            break;
    }
}

function finishAudit() {
    state.isRunning = false;
    setAllButtonsState(false);
}


/* ===============================
   STEPPER UI
   =============================== */

function resetStepper() {
    ['fetch', 'clean', 'llm', 'result'].forEach(id => {
        const el = document.getElementById(`step-${id}`);
        el.className = 'step';
        el.querySelector('.step-detail').textContent = '';
    });
}

function updateStep(stepId, status, detail) {
    const el = document.getElementById(`step-${stepId}`);
    el.className = `step ${status}`;
    if (detail !== undefined) {
        el.querySelector('.step-detail').textContent = detail;
    }
}

function setAllButtonsState(loading, action) {
    const btnAudit = document.getElementById('btn-run-audit');
    const btnFetch = document.getElementById('btn-fetch-data');
    const btnAnalysis = document.getElementById('btn-run-analysis');

    if (loading) {
        btnAudit.disabled = true;
        btnFetch.disabled = true;
        btnAnalysis.disabled = true;

        // Animate only the button that triggered the current action; the
        // others are merely disabled (no pulsing glow).
        if (action === 'full') {
            btnAudit.classList.add('btn-loading');
            btnAudit.innerHTML = `<span>⏳</span> <span>${t('btn.run_audit.loading')}</span>`;
        } else if (action === 'fetch') {
            btnFetch.classList.add('btn-loading');
            btnFetch.innerHTML = `<span>⏳</span> <span>${t('btn.fetch_data.loading')}</span>`;
        } else if (action === 'analyze') {
            btnAnalysis.classList.add('btn-loading');
            btnAnalysis.innerHTML = `<span>⏳</span> <span>${t('btn.run_analysis.loading')}</span>`;
        }
    } else {
        btnAudit.classList.remove('btn-loading');
        btnFetch.classList.remove('btn-loading');
        btnAnalysis.classList.remove('btn-loading');

        btnAudit.disabled = false;
        btnFetch.disabled = false;

        btnAudit.innerHTML = `🚀 <span data-i18n="btn.run_audit">${t('btn.run_audit')}</span>`;
        btnFetch.innerHTML = `📡 <span data-i18n="btn.fetch_data">${t('btn.fetch_data')}</span>`;
        btnAnalysis.innerHTML = `🧠 <span data-i18n="btn.run_analysis">${t('btn.run_analysis')}</span>`;

        // Re-check cache to decide if analysis button should be enabled
        loadCacheStatus();
    }
}


/* ===============================
   RENDER RESULTS
   =============================== */

function clearResults() {
    document.getElementById('results-block-body').innerHTML = '';
    document.getElementById('results-unblock-body').innerHTML = '';
    document.getElementById('results-test-body').innerHTML = '';
    document.getElementById('summary-content').textContent = '';
    document.getElementById('results-section').classList.add('hidden');
    updateTabCounts(0, 0, 0);
}

function renderResults(result) {
    if (!result) return;
    document.getElementById('results-section').classList.remove('hidden');

    // Stats
    renderStats(result);

    // Tables
    renderDomainTable('block', result.domains_to_block || [], true);
    renderDomainTable('unblock', result.domains_to_unblock || [], true);
    renderDomainTable('test', result.domains_to_test || [], false);

    // Summary
    document.getElementById('summary-content').textContent = result.analysis_summary || '';

    // Tab counts
    updateTabCounts(
        (result.domains_to_block || []).length,
        (result.domains_to_unblock || []).length,
        (result.domains_to_test || []).length
    );
}

function renderStats(result) {
    const blockCount = (result.domains_to_block || []).length;
    const unblockCount = (result.domains_to_unblock || []).length;
    const testCount = (result.domains_to_test || []).length;
    const totalCount = blockCount + unblockCount + testCount;

    document.getElementById('stat-block').textContent = blockCount;
    document.getElementById('stat-unblock').textContent = unblockCount;
    document.getElementById('stat-test').textContent = testCount;
    document.getElementById('stat-total').textContent = totalCount;

    document.getElementById('stats-row').classList.remove('hidden');
}

function renderDomainTable(type, domains, hasCheckbox) {
    const tbody = document.getElementById(`results-${type}-body`);
    tbody.innerHTML = '';

    if (domains.length === 0) {
        const tr = document.createElement('tr');
        const colspan = hasCheckbox ? 4 : 3;
        tr.innerHTML = `<td colspan="${colspan}" style="text-align:center; color: var(--text-muted); padding: 24px;">${t('empty.no_recommendations')}</td>`;
        tbody.appendChild(tr);
        return;
    }

    domains.forEach((d, i) => {
        const tr = document.createElement('tr');
        let html = '';

        if (hasCheckbox) {
            const checked = type === 'block'
                ? (state.selectedBlock[d.domain] !== false)
                : (state.selectedUnblock[d.domain] !== false);

            html += `<td class="checkbox-cell">
        <input type="checkbox" class="custom-check" data-type="${type}" data-domain="${d.domain}"
               ${checked ? 'checked' : ''} onchange="onCheckboxChange(this)">
      </td>`;

            if (type === 'block' && state.selectedBlock[d.domain] === undefined) {
                state.selectedBlock[d.domain] = true;
            }
            if (type === 'unblock' && state.selectedUnblock[d.domain] === undefined) {
                state.selectedUnblock[d.domain] = true;
            }
        }

        html += `<td class="domain-cell">${escapeHtml(d.domain)}</td>`;
        html += `<td class="reason-cell">${escapeHtml(d.reason)}</td>`;

        if (d.confidence) {
            const level = d.confidence.toLowerCase();
            html += `<td><span class="badge badge-${level}">${d.confidence}</span></td>`;
        }

        tr.innerHTML = html;
        tbody.appendChild(tr);
    });
}

function updateTabCounts(block, unblock, test) {
    document.getElementById('count-block').textContent = block;
    document.getElementById('count-unblock').textContent = unblock;
    document.getElementById('count-test').textContent = test;
}


/* ===============================
   CHECKBOX LOGIC
   =============================== */

function onCheckboxChange(el) {
    const type = el.dataset.type;
    const domain = el.dataset.domain;
    if (type === 'block') {
        state.selectedBlock[domain] = el.checked;
    } else {
        state.selectedUnblock[domain] = el.checked;
    }
}

function toggleSelectAll(type, checked) {
    const checkboxes = document.querySelectorAll(`input[data-type="${type}"]`);
    checkboxes.forEach(cb => {
        cb.checked = checked;
        const domain = cb.dataset.domain;
        if (type === 'block') {
            state.selectedBlock[domain] = checked;
        } else {
            state.selectedUnblock[domain] = checked;
        }
    });
}


/* ===============================
   APPLY CHANGES (Block/Unblock)
   =============================== */

async function applyChanges() {
    if (!state.results) return;

    const blocklist = [];
    const unblocklist = [];

    if (state.results.domains_to_block) {
        state.results.domains_to_block.forEach(d => {
            if (state.selectedBlock[d.domain]) {
                blocklist.push({domain: d.domain, reason: d.reason, confidence: d.confidence});
            }
        });
    }

    if (state.results.domains_to_unblock) {
        state.results.domains_to_unblock.forEach(d => {
            if (state.selectedUnblock[d.domain]) {
                unblocklist.push({domain: d.domain, reason: d.reason, confidence: d.confidence});
            }
        });
    }

    if (blocklist.length === 0 && unblocklist.length === 0) {
        showToast(t('toast.no_domains_selected'), 'info');
        return;
    }

    const btn = document.getElementById('btn-apply-changes');
    btn.disabled = true;
    btn.textContent = t('btn.applying');

    try {
        if (blocklist.length > 0) {
            const resp = await fetch(`${API}/to_block`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({domains: blocklist}),
            });
            const blockResult = await resp.json();
            if (!resp.ok) throw new Error(blockResult.detail || 'Block request failed');
        }

        if (unblocklist.length > 0) {
            const resp = await fetch(`${API}/to_unblock`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({domains: unblocklist}),
            });
            const unblockResult = await resp.json();
            if (!resp.ok) throw new Error(unblockResult.detail || 'Unblock request failed');
        }

        const msgs = [];
        if (blocklist.length > 0) msgs.push(`🛑 ${t('tab.block')}: ${blocklist.length}`);
        if (unblocklist.length > 0) msgs.push(`🟢 ${t('tab.unblock')}: ${unblocklist.length}`);
        showToast(msgs.join('  ·  '), 'success');

    } catch (err) {
        showToast(`${t('toast.audit_error')}: ${err.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = `✅ ${t('btn.apply_changes')}`;
    }
}


/* ===============================
   PROMPT RULES CRUD
   =============================== */

async function loadPromptRules() {
    try {
        const resp = await fetch(`${API}/prompt-rules`);
        const data = await resp.json();
        state.rules = data.rules || [];
        renderRules();
    } catch (e) {
        console.error('Failed to load rules:', e);
    }
}

function renderRules() {
    const container = document.getElementById('rules-list');
    container.innerHTML = '';

    if (state.rules.length === 0) {
        container.innerHTML = `<div class="rules-empty">${t('empty.rules')}</div>`;
        return;
    }

    state.rules.forEach(rule => {
        const el = document.createElement('div');
        el.className = 'rule-item';
        el.innerHTML = `
      <label class="toggle">
        <input type="checkbox" ${rule.is_active ? 'checked' : ''} onchange="toggleRule('${rule.id}', this.checked)">
        <span class="toggle-slider"></span>
      </label>
      <div style="flex:1; overflow:hidden;">
        <div class="rule-name">${escapeHtml(rule.name)}</div>
        ${rule.description ? `<div class="rule-desc">${escapeHtml(rule.description)}</div>` : ''}
      </div>
      <div class="rule-actions">
        <button class="btn btn-ghost btn-sm" onclick="openEditModal('${rule.id}')" title="Edit">${t('btn.edit')}</button>
        <button class="btn btn-danger btn-sm" onclick="deleteRule('${rule.id}')" title="Delete">${t('btn.delete')}</button>
      </div>
    `;
        container.appendChild(el);
    });
}

async function toggleRule(ruleId, isActive) {
    try {
        await fetch(`${API}/prompt-rules/${ruleId}`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({is_active: isActive}),
        });
        const rule = state.rules.find(r => r.id === ruleId);
        if (rule) rule.is_active = isActive;
        showToast(isActive ? t('toast.rule_enabled') : t('toast.rule_disabled'), 'info');
    } catch (e) {
        showToast(t('toast.rule_update_error'), 'error');
    }
}

async function deleteRule(ruleId) {
    try {
        const resp = await fetch(`${API}/prompt-rules/${ruleId}`, {method: 'DELETE'});
        if (resp.ok) {
            state.rules = state.rules.filter(r => r.id !== ruleId);
            renderRules();
            showToast(t('toast.rule_deleted'), 'info');
        }
    } catch (e) {
        showToast(t('toast.rule_delete_error'), 'error');
    }
}


/* ===============================
   MODAL (Add Rule)
   =============================== */

function toggleModal(show, isEdit = false) {
    const overlay = document.getElementById('modal-overlay');
    const title = document.getElementById('modal-title');
    const btn = document.getElementById('modal-submit-btn');

    if (show) {
        overlay.classList.remove('hidden');
        document.getElementById('modal-rule-name').focus();

        if (isEdit) {
            title.setAttribute('data-i18n', 'modal.title_edit');
            btn.setAttribute('data-i18n', 'btn.save');
        } else {
            state.editingRuleId = null;
            document.getElementById('modal-form').reset();
            title.setAttribute('data-i18n', 'modal.title_new');
            btn.setAttribute('data-i18n', 'btn.create');
        }
        updateDOMTranslations();
    } else {
        overlay.classList.add('hidden');
        document.getElementById('modal-form').reset();
        state.editingRuleId = null;
    }
}

function openEditModal(ruleId) {
    const rule = state.rules.find(r => r.id === ruleId);
    if (!rule) return;
    state.editingRuleId = ruleId;
    document.getElementById('modal-rule-name').value = rule.name || '';
    document.getElementById('modal-rule-text').value = rule.text || '';
    document.getElementById('modal-rule-desc').value = rule.description || '';
    toggleModal(true, true);
}

async function saveNewRule() {
    const name = document.getElementById('modal-rule-name').value.trim();
    const text = document.getElementById('modal-rule-text').value.trim();
    const desc = document.getElementById('modal-rule-desc').value.trim();

    if (!name || !text) {
        showToast(t('toast.fill_required'), 'error');
        return;
    }

    try {
        const body = {name, text};
        if (desc) body.description = desc;

        if (state.editingRuleId) {
            const resp = await fetch(`${API}/prompt-rules/${state.editingRuleId}`, {
                method: 'PATCH',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(body),
            });

            if (resp.ok) {
                const updatedRule = await resp.json();
                const idx = state.rules.findIndex(r => r.id === state.editingRuleId);
                if (idx !== -1) {
                    state.rules[idx] = updatedRule;
                }
                renderRules();
                toggleModal(false);
                showToast(t('toast.rule_updated'), 'success');
            } else {
                const err = await resp.json();
                showToast(err.detail || t('toast.rule_update_error'), 'error');
            }
        } else {
            body.is_active = true;
            const resp = await fetch(`${API}/prompt-rules`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(body),
            });

            if (resp.ok) {
                const newRule = await resp.json();
                state.rules.push(newRule);
                renderRules();
                toggleModal(false);
                showToast(t('toast.rule_created'), 'success');
            } else {
                const err = await resp.json();
                showToast(err.detail || t('toast.rule_create_error'), 'error');
            }
        }
    } catch (e) {
        showToast(t('toast.network_error'), 'error');
    }
}


/* ===============================
   CURRENT RULES (view + manage)
   =============================== */

function toggleCurrentRules() {
    document.getElementById('current-rules-card').classList.toggle('collapsed');
}

async function loadCurrentFilters() {
    const container = document.getElementById('filters-content');
    container.innerHTML = `<div style="color: var(--text-muted); padding: 16px;">${t('filters.loading')}</div>`;
    // Make sure the card is expanded when (re)loading
    document.getElementById('current-rules-card').classList.remove('collapsed');

    try {
        const resp = await fetch(`${API}/get_actual_filter`);
        const data = await resp.json();
        state.currentRules = data;
        renderCurrentRules();
    } catch (e) {
        state.currentRules = null;
        container.innerHTML = `<div style="color: var(--red); padding: 16px;">${t('filters.error', e.message)}</div>`;
    }
}

function renderCurrentRules() {
    const container = document.getElementById('filters-content');
    const countEl = document.getElementById('cr-count');
    const data = state.currentRules;

    if (!data || !data.clean_rules_objects) return;

    const allEntries = Object.entries(data.clean_rules_objects);
    countEl.textContent = allEntries.length;

    if (allEntries.length === 0) {
        container.innerHTML = `<div class="empty-state"><div class="empty-icon">📋</div><div class="empty-title">${t('empty.no_rules')}</div></div>`;
        return;
    }

    const search = document.getElementById('cr-search').value.trim().toLowerCase();
    const typeFilter = document.getElementById('cr-filter-type').value;

    const entries = allEntries.filter(([domain, rule]) => {
        if (search && !domain.toLowerCase().includes(search)) return false;
        if (typeFilter === 'block' && rule.is_exception) return false;
        if (typeFilter === 'exception' && !rule.is_exception) return false;
        return true;
    });

    // Group by type (blocks first, then exceptions), alphabetical within group
    entries.sort((a, b) => {
        const ta = a[1].is_exception ? 1 : 0;
        const tb = b[1].is_exception ? 1 : 0;
        if (ta !== tb) return ta - tb;
        return a[0].localeCompare(b[0]);
    });

    if (entries.length === 0) {
        container.innerHTML = `<div style="color: var(--text-muted); padding: 16px; text-align:center;">${t('cr.none_found')}</div>`;
        return;
    }

    let html = `<div style="font-size:0.78rem; color:var(--text-muted); margin-bottom:8px;">${t('cr.showing', entries.length, allEntries.length)}</div>`;
    html += '<div style="max-height:400px; overflow-y:auto;">';
    html += '<table class="results-table"><thead><tr>';
    html += `<th>${t('table.domain')}</th><th style="width:120px;">${t('table.type')}</th><th>${t('table.modifiers')}</th><th style="width:170px;"></th>`;
    html += '</tr></thead><tbody>';

    for (const [domain, rule] of entries) {
        const isExc = rule.is_exception;
        const typeLabel = isExc ? t('cr.type_exception') : t('cr.type_block');
        const mods = (rule.modifiers || []).join(', ') || '-';
        const dEsc = escapeHtml(domain);
        // Change-type: an exception becomes a block, a block becomes an exception
        const changeAction = isExc ? 'block' : 'unblock';
        const changeLabel = isExc ? t('cr.to_block') : t('cr.to_unblock');
        html += `<tr>
      <td class="domain-cell">${dEsc}</td>
      <td>${typeLabel}</td>
      <td style="color:var(--text-muted); font-size:0.8rem;">${escapeHtml(mods)}</td>
      <td class="cr-actions-cell">
        <button class="btn btn-outline btn-sm cr-action" data-action="${changeAction}" data-domain="${dEsc}">${changeLabel}</button>
        <button class="btn btn-danger btn-sm cr-action" data-action="delete" data-domain="${dEsc}">${t('cr.delete')}</button>
      </td>
    </tr>`;
    }
    html += '</tbody></table></div>';
    container.innerHTML = html;

    container.querySelectorAll('.cr-action').forEach(btn => {
        btn.addEventListener('click', () => handleRuleAction(btn.dataset.action, btn.dataset.domain));
    });
}

async function handleRuleAction(action, domain) {
    if (action === 'delete') {
        if (!confirm(t('cr.confirm_delete', domain))) return;
        await sendRuleAction('to_delete', {domains: [domain]}, t('toast.rule_deleted'), t('toast.rule_delete_error'));
    } else if (action === 'block' || action === 'unblock') {
        const endpoint = action === 'block' ? 'to_block' : 'to_unblock';
        const body = {domains: [{domain, reason: 'Manual action', confidence: 'HIGH'}]};
        await sendRuleAction(endpoint, body, t('toast.rule_type_changed'), t('toast.rule_type_error'));
    }
}

async function sendRuleAction(endpoint, body, successMsg, errorMsg) {
    const container = document.getElementById('filters-content');
    container.style.opacity = '0.5';
    try {
        const resp = await fetch(`${API}/${endpoint}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body),
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.detail || 'Request failed');
        showToast(successMsg, 'success');
        await loadCurrentFilters();  // refresh from server (also restores opacity)
    } catch (e) {
        showToast(`${errorMsg}: ${e.message}`, 'error');
        container.style.opacity = '1';
    }
}

/* ===============================
   TOAST NOTIFICATIONS
   =============================== */

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icons = {success: '✅', error: '❌', info: 'ℹ️'};
    toast.innerHTML = `<span>${icons[type] || 'ℹ️'}</span> ${escapeHtml(message)}`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('toast-out');
        toast.addEventListener('animationend', () => toast.remove());
    }, 4000);
}


/* ===============================
   UTILITY
   =============================== */

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
