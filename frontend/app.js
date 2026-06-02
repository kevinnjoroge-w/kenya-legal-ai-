/* =============================================================================
   Kenya Legal AI — Frontend Application
   ============================================================================= */

const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://kenya-legal-ai.onrender.com';

const state = {
    currentTab: 'chat',
    currentMode: 'research',
    isLoading: false,
    conversationHistory: [],
};

window.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initChat();
    initSearch();
    initConstitution();
    attachModeSelector();
    checkApiHealth();
});

function initNavigation() {
    document.querySelectorAll('.nav-pill').forEach(pill => {
        pill.addEventListener('click', () => switchTab(pill.dataset.tab));
    });
}

function switchTab(tabName) {
    state.currentTab = tabName;
    document.querySelectorAll('.nav-pill').forEach(pill => {
        pill.classList.toggle('active', pill.dataset.tab === tabName);
    });
    document.querySelectorAll('.panel').forEach(panel => {
        panel.classList.toggle('active', panel.id === `panel-${tabName}`);
    });
    const hero = document.getElementById('hero');
    if (hero) hero.style.display = tabName === 'chat' && !hasChatMessages() ? 'grid' : 'none';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function hasChatMessages() {
    return document.querySelectorAll('#chatMessages .message').length > 0;
}

function initChat() {
    const chatInput = document.getElementById('chatInput');
    const charCount = document.getElementById('charCount');
    if (!chatInput) return;

    const resizeInput = () => {
        window.requestAnimationFrame(() => {
            chatInput.style.height = 'auto';
            chatInput.style.height = `${Math.min(chatInput.scrollHeight, 150)}px`;
        });
    };

    chatInput.addEventListener('input', () => {
        resizeInput();
        if (charCount) charCount.textContent = `${chatInput.value.length} / 2000`;
    });

    chatInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });

    resizeInput();
    updateSendButton();
}

function attachModeSelector() {
    const modeSelect = document.getElementById('chatModeSelect');
    const modeItems = document.querySelectorAll('.mode-item');
    const activeLabel = document.getElementById('activeModeLabel');

    const setMode = (mode) => {
        state.currentMode = mode;
        const label = mode.replace(/_/g, ' ').replace(/\b\w/g, char => char.toUpperCase());
        if (activeLabel) activeLabel.textContent = label;
        modeItems.forEach(item => item.classList.toggle('active', item.dataset.mode === mode));
        if (modeSelect) modeSelect.value = mode;
    };

    modeItems.forEach(item => item.addEventListener('click', () => setMode(item.dataset.mode || 'research')));
    if (modeSelect) modeSelect.addEventListener('change', () => setMode(modeSelect.value));
    setMode(state.currentMode);
}

function addMessage(type, content, sources = [], followUpQuestions = [], groundingNotice = null, disclaimer = null, disclaimerLevel = 'research') {
    const messagesDiv = document.getElementById('chatMessages');
    if (!messagesDiv) return null;

    const messageEl = document.createElement('div');
    messageEl.className = `message message-${type}`;

    if (type === 'user') {
        messageEl.innerHTML = `<div class="message-content">${escapeHtml(content)}</div>`;
    } else {
        const formattedContent = formatMarkdown(content);
        const sourcesHtml = sources.length
            ? `<div class="message-sources">${sources
                .filter(source => source.title || source.citation)
                .map(source => {
                    const label = source.citation || source.title || 'Source';
                    const meta = [source.court, source.date].filter(Boolean).join(' · ');
                    return `<span class="source-tag" title="${escapeHtml(meta)}">${escapeHtml(label)}</span>`;
                }).join('')}</div>`
            : '';

        const followUpHtml = followUpQuestions.length
            ? `<div class="followup-questions"><div class="followup-title">Explore further</div><div class="followup-chips">${followUpQuestions.map(question => `<button class="followup-chip" onclick="askFollowUp(this)" data-question="${escapeHtml(question)}">${escapeHtml(question)}</button>`).join('')}</div></div>`
            : '';

        const warningHtml = groundingNotice ? `<div class="message-warning grounding-notice">${formatMarkdown(groundingNotice)}</div>` : '';
        const disclaimerHtml = disclaimer ? `<div class="message-disclaimer disclaimer-${disclaimerLevel}">${formatMarkdown(disclaimer)}</div>` : '';

        messageEl.innerHTML = `
            <div class="message-content">
                ${warningHtml}
                ${formattedContent}
                ${sourcesHtml}
                ${followUpHtml}
                ${disclaimerHtml}
            </div>
        `;
    }

    messagesDiv.appendChild(messageEl);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return messageEl;
}

function addLoadingMessage() {
    const messagesDiv = document.getElementById('chatMessages');
    if (!messagesDiv) return null;
    const messageEl = document.createElement('div');
    messageEl.className = 'message message-ai message-loading';
    messageEl.innerHTML = `
        <div class="message-content">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        </div>
    `;
    messagesDiv.appendChild(messageEl);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return messageEl;
}

function updateSendButton() {
    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn) sendBtn.disabled = state.isLoading;
}

function askFollowUp(button) {
    const question = button.dataset.question;
    if (!question) return;
    const chatInput = document.getElementById('chatInput');
    if (!chatInput) return;
    chatInput.value = question;
    chatInput.dispatchEvent(new Event('input'));
    sendMessage();
}

async function sendMessage() {
    const chatInput = document.getElementById('chatInput');
    if (!chatInput) return;

    const query = chatInput.value.trim();
    if (!query || state.isLoading) return;

    state.isLoading = true;
    updateSendButton();

    document.getElementById('hero')?.style.setProperty('display', 'none');
    document.querySelector('.message-empty')?.classList.add('hidden');

    addMessage('user', query);
    chatInput.value = '';
    chatInput.style.height = 'auto';
    const charCount = document.getElementById('charCount');
    if (charCount) charCount.textContent = '0 / 2000';

    const loadingElement = addLoadingMessage();
    const docType = document.getElementById('filterDocType')?.value || null;
    const court = document.getElementById('filterCourt')?.value || null;

    try {
        const response = await fetch(`${API_BASE}/api/v1/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query,
                mode: state.currentMode,
                document_type: docType || null,
                court: court || null,
                history: state.conversationHistory,
            }),
        });

        if (loadingElement) loadingElement.remove();

        if (!response.ok) {
            const body = await response.json().catch(() => ({}));
            const detail = body.detail;
            const message = typeof detail === 'string' ? detail : detail?.message || `Server error (${response.status})`;
            addMessage('ai', `⚠️ ${message}`);
        } else {
            const data = await response.json();
            addMessage('ai', data.response, data.sources || [], data.follow_up_questions || [], data.grounding_notice, data.disclaimer, data.disclaimer_level);
            state.conversationHistory.push({ role: 'user', content: query });
            state.conversationHistory.push({ role: 'assistant', content: data.response });
            if (state.conversationHistory.length > 20) {
                state.conversationHistory = state.conversationHistory.slice(-20);
            }
        }
    } catch (error) {
        if (loadingElement) loadingElement.remove();
        addMessage('ai', getErrorMessage(error));
    }

    state.isLoading = false;
    updateSendButton();
}

function initSearch() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;
    searchInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') performSearch();
    });
}

async function performSearch() {
    const query = document.getElementById('searchInput')?.value.trim();
    if (!query) return;
    const resultsDiv = document.getElementById('searchResults');
    if (!resultsDiv) return;

    resultsDiv.innerHTML = `<div class="search-empty"><div class="empty-icon">🔎</div><p>Searching legal database...</p></div>`;
    const body = {
        query,
        top_k: parseInt(document.getElementById('searchResultCount')?.value || '10', 10),
        document_type: document.getElementById('searchDocType')?.value || null,
        court: document.getElementById('searchCourt')?.value || null,
    };

    try {
        const response = await fetch(`${API_BASE}/api/v1/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });

        if (!response.ok) throw new Error(`API error: ${response.status}`);
        const data = await response.json();
        renderSearchResults(data.results, query);
    } catch (error) {
        resultsDiv.innerHTML = `<div class="search-empty"><div class="empty-icon">⚠️</div><p>${getErrorMessage(error)}</p></div>`;
    }
}

function renderSearchResults(results, query) {
    const resultsDiv = document.getElementById('searchResults');
    if (!resultsDiv) return;
    if (!results || !results.length) {
        resultsDiv.innerHTML = `<div class="search-empty"><div class="empty-icon">📭</div><p>No results found for "${escapeHtml(query)}".</p></div>`;
        return;
    }

    resultsDiv.innerHTML = results.map((result, index) => `
        <div class="result-card" style="animation-delay: ${index * 0.05}s">
            <div class="result-header">
                <span class="result-title">${escapeHtml(result.document_title || 'Untitled')}</span>
                <span class="result-score">${(result.score * 100).toFixed(1)}% match</span>
            </div>
            <div class="result-meta">
                ${result.document_type ? `<span class="result-meta-tag">📄 ${escapeHtml(capitalize(result.document_type))}</span>` : ''}
                ${result.court ? `<span class="result-meta-tag">🏛️ ${escapeHtml(result.court)}</span>` : ''}
                ${result.date ? `<span class="result-meta-tag">📅 ${escapeHtml(result.date)}</span>` : ''}
                ${result.section ? `<span class="result-meta-tag">§ ${escapeHtml(result.section)}</span>` : ''}
                ${result.citation ? `<span class="result-meta-tag">📌 ${escapeHtml(result.citation)}</span>` : ''}
            </div>
            <div class="result-text">${escapeHtml(result.text || '')}</div>
        </div>
    `).join('');
}

function initConstitution() {
    const constitutionInput = document.getElementById('constitutionInput');
    if (!constitutionInput) return;
    constitutionInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') searchConstitution();
    });
}

async function searchConstitution() {
    const query = document.getElementById('constitutionInput')?.value.trim();
    const resultsDiv = document.getElementById('constitutionResults');
    if (!query || !resultsDiv) return;

    resultsDiv.innerHTML = `<div class="search-empty"><div class="empty-icon">📜</div><p>Searching the Constitution...</p></div>`;
    try {
        const response = await fetch(`${API_BASE}/api/v1/constitution?q=${encodeURIComponent(query)}&top_k=5`);
        if (!response.ok) throw new Error(`API error: ${response.status}`);
        const data = await response.json();
        renderSearchResultsTo(data.results, query, resultsDiv);
    } catch (error) {
        resultsDiv.innerHTML = `<div class="search-empty"><div class="empty-icon">⚠️</div><p>${getErrorMessage(error)}</p></div>`;
    }
}

function renderSearchResultsTo(results, query, container) {
    if (!container) return;
    if (!results || !results.length) {
        container.innerHTML = `<div class="search-empty"><div class="empty-icon">📭</div><p>No constitutional references found for "${escapeHtml(query)}".</p></div>`;
        return;
    }

    container.innerHTML = results.map((result, index) => `
        <div class="result-card" style="animation-delay: ${index * 0.05}s">
            <div class="result-header">
                <span class="result-title">${escapeHtml(result.document_title || result.section || 'Constitution')}</span>
                <span class="result-score">${(result.score * 100).toFixed(1)}%</span>
            </div>
            ${result.section ? `<div class="result-meta"><span class="result-meta-tag">§ ${escapeHtml(result.section)}</span></div>` : ''}
            <div class="result-text">${escapeHtml(result.text || '')}</div>
        </div>
    `).join('');
}

async function checkApiHealth() {
    const statusGrid = document.getElementById('statusGrid');
    if (!statusGrid) return;
    try {
        const response = await fetch(`${API_BASE}/api/v1/health`);
        const data = await response.json();
        const apiOnline = data.status === 'healthy';
        const vectorOnline = !data.vector_db?.error;
        const docCount = data.vector_db?.points_count || 0;
        statusGrid.innerHTML = `
            <div class="status-item"><span class="status-dot ${apiOnline ? 'online' : 'offline'}"></span><span>API: <strong>${apiOnline ? 'Online' : 'Offline'}</strong></span></div>
            <div class="status-item"><span class="status-dot ${vectorOnline ? 'online' : 'offline'}"></span><span>Vector DB: <strong>${vectorOnline ? 'Connected' : 'Unavailable'}</strong></span></div>
            <div class="status-item"><span class="status-dot ${docCount > 0 ? 'online' : 'offline'}"></span><span>Indexed chunks: <strong>${docCount.toLocaleString()}</strong></span></div>
        `;
    } catch {
        statusGrid.innerHTML = `<div class="status-item"><span class="status-dot offline"></span><span>API health unavailable</span></div>`;
    }
}

function escapeHtml(value) {
    if (!value) return '';
    const div = document.createElement('div');
    div.textContent = value;
    return div.innerHTML;
}

function capitalize(value) {
    if (!value) return '';
    return value.charAt(0).toUpperCase() + value.slice(1).replace(/_/g, ' ');
}

function formatMarkdown(text) {
    if (!text) return '';
    const lines = text.split('\n');
    let html = '';
    let listOpen = false;
    let paragraphOpen = false;

    const closeParagraph = () => {
        if (paragraphOpen) {
            html += '</p>';
            paragraphOpen = false;
        }
    };

    const closeList = () => {
        if (listOpen) {
            html += '</ul>';
            listOpen = false;
        }
    };

    const addText = (content) => {
        if (!paragraphOpen) {
            html += '<p>';
            paragraphOpen = true;
        }
        html += content;
    };

    const inlineFormat = (value) => value
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>');

    for (const rawLine of lines) {
        const line = rawLine.trim();
        if (!line) {
            closeParagraph();
            closeList();
            continue;
        }

        if (/^#{1,6}\s+/.test(line)) {
            closeParagraph();
            closeList();
            const level = line.match(/^#{1,6}/)[0].length;
            const content = escapeHtml(line.replace(/^#{1,6}\s+/, ''));
            html += `<h${level}>${inlineFormat(content)}</h${level}>`;
            continue;
        }

        const listMatch = line.match(/^[-*+]\s+(.+)/);
        if (listMatch) {
            closeParagraph();
            if (!listOpen) {
                html += '<ul>';
                listOpen = true;
            }
            html += `<li>${inlineFormat(escapeHtml(listMatch[1]))}</li>`;
            continue;
        }

        const orderedMatch = line.match(/^\d+\.\s+(.+)/);
        if (orderedMatch) {
            closeParagraph();
            if (!listOpen) {
                html += '<ul>';
                listOpen = true;
            }
            html += `<li>${inlineFormat(escapeHtml(orderedMatch[1]))}</li>`;
            continue;
        }

        closeList();
        addText(inlineFormat(escapeHtml(line)));
    }

    closeParagraph();
    closeList();
    return html;
}

function getErrorMessage(error) {
    const message = error?.message || error || 'Unknown error';
    if (message.includes('Failed to fetch') || message.includes('NetworkError')) {
        return '⚠️ Could not connect to the API server. Start the backend with: venv/bin/uvicorn src.api.main:app --reload --port 8000';
    }
    return `⚠️ ${message}`;
}

setInterval(checkApiHealth, 30000);
