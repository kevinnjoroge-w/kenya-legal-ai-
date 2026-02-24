/* =============================================================================
   Kenya Legal AI — Frontend Application
   Handles API communication, chat interface, search, and tab navigation
   ============================================================================= */

const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'https://kenya-legal-ai-api.onrender.com'; // Replace with actual Render URL after deployment

// ─── State ───────────────────────────────────────────────────────────────────

const state = {
    currentTab: 'chat',
    currentMode: 'research',
    isLoading: false,
    chatHistory: [],              // full response objects for display
    conversationHistory: [],      // {role, content} pairs sent to the API for memory
};

// ─── DOM Ready ───────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initChat();
    initSearch();
    initConstitution();
    checkApiHealth();
});

// ─── Navigation ──────────────────────────────────────────────────────────────

function initNavigation() {
    // Tab switching
    document.querySelectorAll('.nav-link[data-tab]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            switchTab(link.dataset.tab);
        });
    });

    // Mobile toggle
    const toggle = document.getElementById('navToggle');
    const links = document.getElementById('navLinks');
    if (toggle && links) {
        toggle.addEventListener('click', () => {
            links.classList.toggle('open');
        });
    }

    // Scroll navbar effect
    window.addEventListener('scroll', () => {
        const navbar = document.getElementById('navbar');
        if (navbar) {
            navbar.style.background = window.scrollY > 50
                ? 'rgba(10, 14, 23, 0.95)'
                : 'rgba(10, 14, 23, 0.85)';
        }
    });
}

function switchTab(tabName) {
    state.currentTab = tabName;

    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.toggle('active', link.dataset.tab === tabName);
    });

    // Update panels
    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.toggle('active', panel.id === `panel-${tabName}`);
    });

    // Handle focus mode for chat
    document.body.classList.toggle('chat-focus-mode', tabName === 'chat');

    // Close mobile nav
    const links = document.getElementById('navLinks');
    if (links) links.classList.remove('open');

    // Hide hero when not on first load
    const hero = document.getElementById('hero');
    if (hero) {
        hero.style.display = tabName === 'chat' && state.chatHistory.length === 0 ? '' : 'none';
    }

    // Scroll to content
    if (tabName !== 'chat' || state.chatHistory.length > 0) {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
}

function scrollToChat() {
    switchTab('chat');
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.focus();
        chatInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

// ─── Chat ────────────────────────────────────────────────────────────────────

function initChat() {
    const chatInput = document.getElementById('chatInput');
    const charCount = document.getElementById('charCount');

    if (chatInput) {
        // Auto-resize textarea
        chatInput.addEventListener('input', () => {
            chatInput.style.height = 'auto';
            chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
            if (charCount) {
                charCount.textContent = `${chatInput.value.length} / 2000`;
            }
        });

        // Send on Enter (Shift+Enter for newline)
        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }

    // Mode buttons (compatibility)
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.currentMode = btn.dataset.mode;

            // Sync with dropdown if exists
            const select = document.getElementById('chatModeSelect');
            if (select) select.value = state.currentMode;
        });
    });

    // New Mode Dropdown
    const modeSelect = document.getElementById('chatModeSelect');
    if (modeSelect) {
        modeSelect.addEventListener('change', (e) => {
            state.currentMode = e.target.value;
        });
    }

    // Nav Menu Button
    const navMenuBtn = document.getElementById('navMenuBtn');
    if (navMenuBtn) {
        navMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            showNavMenu(navMenuBtn);
        });
    }
}

function showNavMenu(anchor) {
    // Create a simple dropdown menu for other tabs
    const existing = document.getElementById('dynamicNavMenu');
    if (existing) {
        existing.remove();
        return;
    }

    const menu = document.createElement('div');
    menu.id = 'dynamicNavMenu';
    menu.className = 'dynamic-menu';

    const tabs = [
        { id: 'search', label: 'Case Search', icon: '🔍' },
        { id: 'constitution', label: 'Constitution', icon: '📜' },
        { id: 'about', label: 'About', icon: 'ℹ️' }
    ];

    menu.innerHTML = tabs.map(t => `
        <div class="menu-item" onclick="switchTab('${t.id}'); document.getElementById('dynamicNavMenu').remove();">
            <span>${t.icon}</span> ${t.label}
        </div>
    `).join('');

    document.body.appendChild(menu);

    // Position menu above/near the button
    const rect = anchor.getBoundingClientRect();
    menu.style.position = 'fixed';
    menu.style.bottom = (window.innerHeight - rect.top + 10) + 'px';
    menu.style.left = rect.left + 'px';

    // Close on click outside
    const closeMenu = (e) => {
        if (!menu.contains(e.target) && e.target !== anchor) {
            menu.remove();
            document.removeEventListener('click', closeMenu);
        }
    };
    setTimeout(() => document.addEventListener('click', closeMenu), 0);
}

function useExample(btn) {
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.value = btn.textContent;
        chatInput.dispatchEvent(new Event('input'));
        sendMessage();
    }
}

function askFollowUp(btn) {
    const question = btn.dataset.question;
    if (!question) return;
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.value = question;
        chatInput.dispatchEvent(new Event('input'));
        sendMessage();
    }
}

async function sendMessage() {
    const chatInput = document.getElementById('chatInput');
    const query = chatInput?.value.trim();

    if (!query || state.isLoading) return;

    state.isLoading = true;

    // Hide hero and welcome
    const hero = document.getElementById('hero');
    if (hero) hero.style.display = 'none';
    const welcome = document.querySelector('.chat-welcome');
    if (welcome) welcome.style.display = 'none';

    // Add user message
    addMessage('user', query);
    chatInput.value = '';
    chatInput.style.height = 'auto';
    document.getElementById('charCount').textContent = '0 / 2000';

    // Show loading
    const loadingId = addLoadingMessage();

    // Get filters
    const docType = document.getElementById('filterDocType')?.value || null;
    const court = document.getElementById('filterCourt')?.value || null;

    try {
        const response = await fetch(`${API_BASE}/api/v1/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                mode: state.currentMode,
                document_type: docType || null,
                court: court || null,
                history: state.conversationHistory,
            }),
        });

        removeMessage(loadingId);

        if (!response.ok) {
            let errorMsg;
            try {
                const errData = await response.json();
                const detail = errData.detail;
                if (typeof detail === 'object' && detail.message) {
                    errorMsg = detail.message;
                } else if (typeof detail === 'string') {
                    errorMsg = detail;
                } else {
                    errorMsg = `Server error (${response.status})`;
                }
            } catch {
                errorMsg = `Server error (${response.status})`;
            }
            addMessage('ai', `⚠️ ${errorMsg}`, [], []);
        } else {
            const data = await response.json();
            addMessage('ai', data.response, data.sources, data.follow_up_questions || [], data.grounding_notice, data.disclaimer, data.disclaimer_level);
            state.chatHistory.push({ query, response: data });
            // Append turns to conversation history for multi-turn memory
            state.conversationHistory.push({ role: 'user', content: query });
            state.conversationHistory.push({ role: 'assistant', content: data.response });
            // Keep history bounded to last 20 turns (10 exchanges) to avoid token bloat
            if (state.conversationHistory.length > 20) {
                state.conversationHistory = state.conversationHistory.slice(-20);
            }
        }

    } catch (error) {
        removeMessage(loadingId);
        addMessage('ai', getErrorMessage(error), []);
    }

    state.isLoading = false;
    updateSendButton();
}

function addMessage(type, content, sources = [], followUpQuestions = [], groundingNotice = null, disclaimer = null, disclaimerLevel = 'research') {
    const messagesDiv = document.getElementById('chatMessages');
    const messageId = `msg-${Date.now()}`;

    const messageEl = document.createElement('div');
    messageEl.className = `message message-${type}`;
    messageEl.id = messageId;

    if (type === 'user') {
        messageEl.innerHTML = `
            <div class="message-content">${escapeHtml(content)}</div>
        `;
    } else {
        const formattedContent = formatMarkdown(content);
        let sourcesHtml = '';

        if (sources && sources.length > 0) {
            const sourceTags = sources
                .filter(s => s.title || s.citation)
                .map(s => {
                    const label = s.citation || s.title || 'Source';
                    const meta = [s.court, s.date].filter(Boolean).join(' · ');
                    return `<span class="source-tag" title="${escapeHtml(meta)}">${escapeHtml(label)}</span>`;
                })
                .join('');

            if (sourceTags) {
                sourcesHtml = `
                    <div class="message-sources">
                        <div class="sources-title">Sources cited</div>
                        ${sourceTags}
                    </div>
                `;
            }
        }

        // Follow-up question chips
        let followUpHtml = '';
        if (followUpQuestions && followUpQuestions.length > 0) {
            const chips = followUpQuestions
                .map(q => `<button class="followup-chip" onclick="askFollowUp(this)" data-question="${escapeHtml(q)}">${escapeHtml(q)}</button>`)
                .join('');
            followUpHtml = `
                <div class="followup-questions">
                    <div class="followup-title">Explore further</div>
                    <div class="followup-chips">${chips}</div>
                </div>
            `;
        }

        // Grounding Notice (RAG warning)
        let warningHtml = '';
        if (groundingNotice) {
            warningHtml = `
                <div class="message-warning grounding-notice">
                    ${formatMarkdown(groundingNotice)}
                </div>
            `;
        }

        // Disclaimer
        let disclaimerHtml = '';
        if (disclaimer) {
            disclaimerHtml = `
                <div class="message-disclaimer disclaimer-${disclaimerLevel}">
                    ${formatMarkdown(disclaimer)}
                </div>
            `;
        }

        messageEl.innerHTML = `
            <div class="message-avatar">⚖️</div>
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
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });

    return messageId;
}

function addLoadingMessage() {
    const messagesDiv = document.getElementById('chatMessages');
    const messageId = `loading-${Date.now()}`;

    const messageEl = document.createElement('div');
    messageEl.className = 'message message-ai message-loading';
    messageEl.id = messageId;
    messageEl.innerHTML = `
        <div class="message-avatar">⚖️</div>
        <div class="message-content">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;

    messagesDiv.appendChild(messageEl);
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });

    return messageId;
}

function removeMessage(messageId) {
    const el = document.getElementById(messageId);
    if (el) el.remove();
}

function updateSendButton() {
    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn) {
        sendBtn.disabled = state.isLoading;
    }
}

// ─── Search ──────────────────────────────────────────────────────────────────

function initSearch() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') performSearch();
        });
    }
}

async function performSearch() {
    const searchInput = document.getElementById('searchInput');
    const query = searchInput?.value.trim();
    if (!query) return;

    const resultsDiv = document.getElementById('searchResults');
    const docType = document.getElementById('searchDocType')?.value || null;
    const court = document.getElementById('searchCourt')?.value || null;
    const topK = parseInt(document.getElementById('searchResultCount')?.value || '10');

    resultsDiv.innerHTML = `
        <div class="search-empty">
            <div class="empty-icon">🔍</div>
            <p>Searching legal database...</p>
        </div>
    `;

    try {
        const response = await fetch(`${API_BASE}/api/v1/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                top_k: topK,
                document_type: docType || null,
                court: court || null,
            }),
        });

        if (!response.ok) throw new Error(`API error: ${response.status}`);

        const data = await response.json();
        renderSearchResults(data.results, query);

    } catch (error) {
        resultsDiv.innerHTML = `
            <div class="search-empty">
                <div class="empty-icon">⚠️</div>
                <p>${getErrorMessage(error)}</p>
            </div>
        `;
    }
}

function renderSearchResults(results, query) {
    const resultsDiv = document.getElementById('searchResults');

    if (!results || results.length === 0) {
        resultsDiv.innerHTML = `
            <div class="search-empty">
                <div class="empty-icon">📭</div>
                <p>No results found for "${escapeHtml(query)}". Try broadening your search.</p>
            </div>
        `;
        return;
    }

    const html = results.map((r, i) => `
        <div class="result-card" style="animation-delay: ${i * 0.05}s">
            <div class="result-header">
                <span class="result-title">${escapeHtml(r.document_title || 'Untitled Document')}</span>
                <span class="result-score">${(r.score * 100).toFixed(1)}% match</span>
            </div>
            <div class="result-meta">
                ${r.document_type ? `<span class="result-meta-tag">📄 ${escapeHtml(capitalize(r.document_type))}</span>` : ''}
                ${r.court ? `<span class="result-meta-tag">🏛️ ${escapeHtml(r.court)}</span>` : ''}
                ${r.date ? `<span class="result-meta-tag">📅 ${escapeHtml(r.date)}</span>` : ''}
                ${r.section ? `<span class="result-meta-tag">§ ${escapeHtml(r.section)}</span>` : ''}
                ${r.citation ? `<span class="result-meta-tag">📌 ${escapeHtml(r.citation)}</span>` : ''}
            </div>
            <div class="result-text">${escapeHtml(r.text || '')}</div>
        </div>
    `).join('');

    resultsDiv.innerHTML = `
        <div style="margin-bottom: 16px; font-size: 14px; color: var(--text-secondary);">
            Found <strong style="color: var(--text-gold)">${results.length}</strong> results for "${escapeHtml(query)}"
        </div>
        ${html}
    `;
}

// ─── Constitution ────────────────────────────────────────────────────────────

function initConstitution() {
    const input = document.getElementById('constitutionInput');
    if (input) {
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') searchConstitution();
        });
    }
}

async function searchConstitution() {
    const input = document.getElementById('constitutionInput');
    const query = input?.value.trim();
    if (!query) return;

    const resultsDiv = document.getElementById('constitutionResults');
    resultsDiv.innerHTML = `
        <div class="search-empty">
            <div class="empty-icon">📜</div>
            <p>Searching the Constitution of Kenya 2010...</p>
        </div>
    `;

    try {
        const response = await fetch(
            `${API_BASE}/api/v1/constitution?q=${encodeURIComponent(query)}&top_k=5`
        );

        if (!response.ok) throw new Error(`API error: ${response.status}`);

        const data = await response.json();
        renderSearchResultsTo(data.results, query, resultsDiv);

    } catch (error) {
        resultsDiv.innerHTML = `
            <div class="search-empty">
                <div class="empty-icon">⚠️</div>
                <p>${getErrorMessage(error)}</p>
            </div>
        `;
    }
}

function searchConstitutionTopic(topic) {
    const input = document.getElementById('constitutionInput');
    if (input) {
        input.value = topic;
        searchConstitution();
    }
}

function renderSearchResultsTo(results, query, container) {
    if (!results || results.length === 0) {
        container.innerHTML = `
            <div class="search-empty">
                <div class="empty-icon">📭</div>
                <p>No constitutional provisions found for "${escapeHtml(query)}"</p>
            </div>
        `;
        return;
    }

    const html = results.map((r, i) => `
        <div class="result-card" style="animation-delay: ${i * 0.05}s">
            <div class="result-header">
                <span class="result-title">${escapeHtml(r.document_title || r.section || 'Constitutional Provision')}</span>
                <span class="result-score">${(r.score * 100).toFixed(1)}%</span>
            </div>
            ${r.section ? `<div class="result-meta"><span class="result-meta-tag">§ ${escapeHtml(r.section)}</span></div>` : ''}
            <div class="result-text">${escapeHtml(r.text || '')}</div>
        </div>
    `).join('');

    container.innerHTML = `
        <div style="margin: 16px 0; font-size: 14px; color: var(--text-secondary);">
            Found <strong style="color: var(--text-gold)">${results.length}</strong> provisions for "${escapeHtml(query)}"
        </div>
        ${html}
    `;
}

// ─── API Health Check ────────────────────────────────────────────────────────

async function checkApiHealth() {
    const statusGrid = document.getElementById('statusGrid');
    if (!statusGrid) return;

    try {
        const response = await fetch(`${API_BASE}/api/v1/health`);
        const data = await response.json();

        const apiOnline = data.status === 'healthy';
        const vectorDb = data.vector_db || {};
        const vectorOnline = !vectorDb.error;
        const docCount = vectorDb.points_count || 0;
        const aiMode = vectorOnline && docCount > 0 ? 'RAG (citation-backed)' : 'Direct LLM';
        const aiModeClass = vectorOnline && docCount > 0 ? 'online' : 'offline';

        statusGrid.innerHTML = `
            <div class="status-item">
                <span class="status-dot ${apiOnline ? 'online' : 'offline'}"></span>
                <span>API Server: <strong>${apiOnline ? 'Online' : 'Offline'}</strong></span>
            </div>
            <div class="status-item">
                <span class="status-dot ${vectorOnline ? 'online' : 'offline'}"></span>
                <span>Vector Database: <strong>${vectorOnline ? 'Connected' : 'Not configured'}</strong></span>
            </div>
            <div class="status-item">
                <span class="status-dot ${docCount > 0 ? 'online' : 'offline'}"></span>
                <span>Indexed Documents: <strong>${docCount.toLocaleString()} chunks</strong></span>
            </div>
            <div class="status-item">
                <span class="status-dot ${aiModeClass}"></span>
                <span>AI Mode: <strong>${aiMode}</strong>${aiModeClass === 'offline' ? ' — run data pipeline for citation-backed answers' : ''}</span>
            </div>
        `;
    } catch {
        statusGrid.innerHTML = `
            <div class="status-item">
                <span class="status-dot offline"></span>
                <span>API Server: <strong>Offline</strong> — Start with: <code>uvicorn src.api.main:app --reload</code></span>
            </div>
        `;
    }
}

// ─── Utilities ───────────────────────────────────────────────────────────────

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1).replace(/_/g, ' ');
}

function formatMarkdown(text) {
    if (!text) return '';

    let html = escapeHtml(text);

    // Headers
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Italic
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

    // Lists
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>');

    // Wrap consecutive <li> in <ul>
    html = html.replace(/((?:<li>.*?<\/li>\n?)+)/g, '<ul>$1</ul>');

    // Source references [Source N]
    html = html.replace(
        /\[Source (\d+)\]/g,
        '<span class="source-tag" style="display:inline; font-size:11px; padding:1px 6px;">Source $1</span>'
    );

    // Paragraphs
    html = html.replace(/\n\n/g, '</p><p>');
    html = '<p>' + html + '</p>';

    // Clean up empty paragraphs
    html = html.replace(/<p>\s*<\/p>/g, '');
    html = html.replace(/<p>\s*(<[hul])/g, '$1');
    html = html.replace(/(<\/[hul]\w*>)\s*<\/p>/g, '$1');

    return html;
}

function getErrorMessage(error) {
    if (error.message?.includes('Failed to fetch') || error.message?.includes('NetworkError')) {
        return '⚠️ **Could not connect to the API server.** Make sure the backend is running with:\n\n' +
            'venv/bin/uvicorn src.api.main:app --reload --port 8000';
    }
    if (error.message?.includes('API key')) {
        return '⚠️ **OpenAI API key not configured.** Add your key to the .env file:\n\n' +
            'OPENAI_API_KEY=sk-your-key-here';
    }
    return `⚠️ **An error occurred:** ${error.message || 'Unknown error'}. Please try again.`;
}

// Periodically check health
setInterval(checkApiHealth, 30000);
