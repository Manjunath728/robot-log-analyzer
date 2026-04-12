document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const analyzeBtn = document.getElementById('analyze-btn');
    const xmlUpload = document.getElementById('xml-upload');
    const fileDisplay = document.getElementById('file-name-display');
    const loader = document.getElementById('loader');
    const resultsContainer = document.getElementById('results-container');
    const alertBox = document.getElementById('alert-box');
    const pipelineLog = document.getElementById('pipeline-log');
    const refreshKbBtn = document.getElementById('refresh-kb-btn');
    const kbStatusChip = document.getElementById('kb-status-chip');
    const logCounter = document.getElementById('log-counter');
    const toggleLogBtn = document.getElementById('toggle-log-btn');
    const logDrawer = document.getElementById('log-drawer');

    // State
    let logEventCount = 0;
    let stats = { failures: 0, systemic: 0, analyzed: 0, total: 0 };
    let kbSynced = false;

    // Pipeline Controller
    const PipelineController = {
        stages: ['INGESTION', 'PARSE', 'GRAPH', 'AGENT', 'VECTOR', 'RCA'],
        
        reset() {
            this.stages.forEach(s => this.setStage(s, 'pending', 'Pending...'));
            stats = { failures: 0, systemic: 0, analyzed: 0, total: 0 };
            this.updateStats();
        },

        setStage(id, status, subtext) {
            const el = document.querySelector(`.step[data-stage="${id}"]`);
            if (!el) return;
            el.className = `step ${status}`;
            if (subtext) el.querySelector('.step-subtext').textContent = subtext;
            
            const iconContainer = el.querySelector('.step-icon');
            if (status === 'done') {
                iconContainer.innerHTML = '<i data-lucide="check-circle"></i>';
            } else if (status === 'active') {
                const originalIcons = {
                    INGESTION: 'file-input', PARSE: 'file-search', GRAPH: 'database',
                    AGENT: 'bot', VECTOR: 'layers', RCA: 'sparkles'
                };
                iconContainer.innerHTML = `<i data-lucide="${originalIcons[id]}"></i>`;
            }
            if (window.lucide) lucide.createIcons();
        },

        updateStats() {
            document.getElementById('stat-failures').textContent = stats.failures;
            document.getElementById('stat-systemic').textContent = stats.systemic;
            document.getElementById('stat-analyzed').textContent = `${stats.analyzed}/${stats.total}`;
        },

        handleEvent(message, type) {
            // Robust Regex Mapping
            const m = message.toLowerCase();
            
            if (m.includes("receiving file") || m.includes("uploading")) 
                this.setStage('INGESTION', 'active', 'Ingesting output.xml...');
                
            if (m.includes("parsing xml")) {
                this.setStage('INGESTION', 'done', 'File received.');
                this.setStage('PARSE', 'active', 'Extracting failure traces...');
            }
            
            if (m.includes("found")) {
                const match = message.match(/Found (\d+) failed tests/);
                if (match) {
                    stats.total = parseInt(match[1]);
                    stats.failures = stats.total;
                    this.setStage('PARSE', 'done', `Detected ${stats.failures} failures.`);
                    this.updateStats();
                }
            }
            
            if (m.includes("graph kb") || m.includes("resolving") || m.includes("connecting to graph")) {
                this.setStage('GRAPH', 'active', 'Querying knowledge graph...');
            }
            
            if (m.includes("vector") || m.includes("faiss") || m.includes("memory search")) {
                this.setStage('AGENT', 'done');
                this.setStage('VECTOR', 'active', 'Scanning similarity memory...');
            }
            
            if (m.includes("compiling") || m.includes("retrieval complete") || m.includes("ready for inference")) {
                this.setStage('VECTOR', 'done', 'Context compiled.');
            }
            
            if (m.includes("ai agent is thinking") || m.includes("invoking actual llm")) {
                this.setStage('RCA', 'active', 'Drafting analysis...');
            }
            
            if (m.includes("saved llm") || m.includes("analysis saved")) {
                this.setStage('RCA', 'done', 'Analysis stored.');
            }

            if (m.includes("pipeline finished")) {
                this.stages.forEach(s => this.setStage(s, 'done'));
            }
        }
    };

    // Log Drawer Toggle
    toggleLogBtn.addEventListener('click', () => {
        logDrawer.classList.toggle('collapsed');
        toggleLogBtn.querySelector('i').setAttribute('data-lucide', logDrawer.classList.contains('collapsed') ? 'chevron-up' : 'chevron-down');
        lucide.createIcons();
    });

    // KB Sync
    refreshKbBtn.addEventListener('click', async () => {
        try {
            refreshKbBtn.disabled = true;
            refreshKbBtn.classList.add('syncing');
            pipelineLog.innerHTML = '';
            logEventCount = 0;
            updateLogCounter();

            const response = await fetch('/api/refresh-kb', { method: 'POST' });
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();
                for (const line of lines) {
                    if (!line.trim()) continue;
                    const event = JSON.parse(line);
                    appendLog(event.message, event.type);
                    if (event.type === 'done') {
                        kbStatusChip.textContent = "KB: Synced ✓";
                        kbStatusChip.className = "kb-chip synced";
                    } else if (event.type === 'error') {
                        kbStatusChip.textContent = "KB: Error ✗";
                        kbStatusChip.className = "kb-chip error";
                    }
                }
            }
        } catch (error) {
            showAlert(error.message, 'error');
        } finally {
            refreshKbBtn.disabled = false;
            refreshKbBtn.classList.remove('syncing');
        }
    });

    function appendLog(message, type = 'status') {
        const li = document.createElement('li');
        li.className = `log-item ${type}`;
        li.textContent = message;
        pipelineLog.appendChild(li);
        logEventCount++;
        updateLogCounter();
        pipelineLog.scrollTop = pipelineLog.scrollHeight;
        PipelineController.handleEvent(message, type);
    }

    function updateLogCounter() {
        logCounter.textContent = `Agent Ops Log (${logEventCount} events)`;
    }

    xmlUpload.addEventListener('change', () => {
        const file = xmlUpload.files[0];
        fileDisplay.textContent = file ? file.name : 'Load output.xml';
    });

    analyzeBtn.addEventListener('click', async () => {
        const file = xmlUpload.files[0];
        if (!file) {
            showAlert('Please select an output.xml file first.', 'error');
            return;
        }

        resultsContainer.innerHTML = '';
        pipelineLog.innerHTML = '';
        logEventCount = 0;
        updateLogCounter();
        
        loader.classList.remove('hidden');
        PipelineController.reset();
        analyzeBtn.disabled = true;

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/analyze', { method: 'POST', body: formData });
            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';

            let currentKeywordsNeeded = [];

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();
                
                for (const line of lines) {
                    if (!line.trim()) continue;
                    const event = JSON.parse(line);
                    
                    if (event.type === 'agent_decision') {
                        currentKeywordsNeeded = event.keywords_needed || [];
                        const msg = event.needs_more ? `🔎 Fetching: ${currentKeywordsNeeded.join(', ')}` : "✓ No expansion needed";
                        PipelineController.setStage('GRAPH', 'done');
                        PipelineController.setStage('AGENT', 'active', msg);
                    } else if (event.type === 'result') {
                        stats.analyzed++;
                        if (event.data.rca && event.data.rca.is_systemic) stats.systemic++;
                        PipelineController.updateStats();
                        renderFailures([event.data], currentKeywordsNeeded);
                    } else if (event.type === 'done') {
                        PipelineController.stages.forEach(s => PipelineController.setStage(s, 'done'));
                    } else {
                        appendLog(event.message, event.type);
                    }
                }
            }
        } catch (error) {
            showAlert(error.message, 'error');
        } finally {
            loader.classList.add('hidden');
            analyzeBtn.disabled = false;
        }
    });

    function renderFailures(failures, expandedKws = []) {
        failures.forEach((f, idx) => {
            const rca = f.rca;
            const isStructured = rca && typeof rca === "object" && !rca.parse_error;
            const card = document.createElement('div');
            card.className = 'rca-card';
            
            const tagsHtml = f.tags.map(t => `<span class="tag">${t}</span>`).join('');
            const md = (text) => (window.marked ? marked.parse(text || '') : escapeHtml(text));

            const cardHeader = `
                <div class="rca-header">
                    <div class="rca-title-group">
                        <div class="rca-icon"><i data-lucide="bot"></i></div>
                        <div class="rca-title">
                            <h3>${f.test_name}</h3>
                            <div class="rca-tags">${tagsHtml}</div>
                        </div>
                    </div>
                </div>
                <div class="card-header-meta">
                    ${isStructured ? `
                        <span class="badge ${rca.is_systemic ? 'badge-red' : 'badge-green'}">${rca.is_systemic ? "SYSTEMIC" : "ISOLATED"}</span>
                        <span class="badge badge-blue">CONFIDENCE: ${rca.confidence}</span>
                        <span class="badge badge-yellow">${rca.recurrence}</span>
                    ` : ''}
                </div>
            `;

            const failureBar = `
                <div class="failure-strip">
                    <span><strong>Failed at:</strong> ${f.failed_keyword}</span>
                    <span class="failure-recurrence">System Reliability Index: 78%</span>
                </div>
            `;

            const rcaContent = isStructured ? `
                <div class="rca-sections">
                    ${createSection("Root Cause", rca.root_cause, true)}
                    ${createSection("Proposed Fix", rca.proposed_fix)}
                    ${rca.system_bug ? createSection("System Bug", rca.system_bug, false, "warn") : ""}
                    ${createSection("Recommendations", `
                        <ul class="rec-checklist">
                            ${(rca.recommendations || []).map(r => `<li class="rec-item"><i data-lucide="check-square"></i> ${r}</li>`).join('')}
                        </ul>
                    `)}
                </div>
            ` : `<div class="rca-content-text">${md(typeof rca === "object" ? JSON.stringify(rca) : rca)}</div>`;

            const contextChips = `
                <div class="card-footer">
                    ${expandedKws.length > 0 ? `
                        <span class="context-chip"><i data-lucide="zoom-in"></i> Agent Expanded Context</span>
                    ` : `<span class="context-chip"><i data-lucide="zap"></i> Sufficient Context</span>`}
                </div>
            `;

            card.innerHTML = cardHeader + failureBar + rcaContent + contextChips;
            resultsContainer.appendChild(card);
            
            // Add Section Interactivity
            card.querySelectorAll('.rca-section-header').forEach(btn => {
                btn.addEventListener('click', () => {
                    btn.parentElement.classList.toggle('open');
                    const iconContainer = btn.querySelector('.section-chevron');
                    const isOpen = btn.parentElement.classList.contains('open');
                    iconContainer.outerHTML = `<i data-lucide="${isOpen ? 'chevron-up' : 'chevron-down'}" class="section-chevron"></i>`;
                    if (window.lucide) lucide.createIcons();
                });
            });
        });
        lucide.createIcons();
    }

    function createSection(title, content, isOpen = false, extraClass ="") {
        return `
            <div class="rca-section ${isOpen ? 'open' : ''} ${extraClass}">
                <button class="rca-section-header">
                    <span>${title}</span>
                    <i data-lucide="${isOpen ? 'chevron-up' : 'chevron-down'}" class="section-chevron"></i>
                </button>
                <div class="rca-section-content">${content}</div>
            </div>
        `;
    }

    function showAlert(msg, type) {
        alertBox.textContent = msg;
        alertBox.classList.remove('hidden');
        alertBox.style.borderColor = type === 'success' ? 'var(--primary)' : 'var(--error)';
    }

    function escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }
});
