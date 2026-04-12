document.addEventListener('DOMContentLoaded', () => {
    const analyzeBtn = document.getElementById('analyze-btn');
    const xmlUpload = document.getElementById('xml-upload');
    const fileDisplay = document.getElementById('file-name-display');
    const loader = document.getElementById('loader');
    const resultsContainer = document.getElementById('results-container');
    const alertBox = document.getElementById('alert-box');

    const refreshKbBtn = document.getElementById('refresh-kb-btn');

    refreshKbBtn.addEventListener('click', async () => {
        try {
            refreshKbBtn.disabled = true;
            refreshKbBtn.classList.add('syncing');
            showAlert('Synchronizing Knowledge Base... Please wait.', 'success');

            const response = await fetch('/api/refresh-kb', { method: 'POST' });
            const data = await response.json();

            if (response.ok) {
                showAlert(data.message, 'success');
            } else {
                throw new Error(data.detail || 'Refresh Failed');
            }
        } catch (error) {
            showAlert(error.message, 'error');
        } finally {
            refreshKbBtn.disabled = false;
            refreshKbBtn.classList.remove('syncing');
        }
    });

    xmlUpload.addEventListener('change', () => {
        const file = xmlUpload.files[0];
        if (file) {
            fileDisplay.textContent = file.name;
            fileDisplay.style.color = 'white';
        } else {
            fileDisplay.textContent = 'Choose output.xml...';
            fileDisplay.style.color = 'var(--text-muted)';
        }
    });

    analyzeBtn.addEventListener('click', async () => {
        const file = xmlUpload.files[0];
        if (!file) {
            showAlert('Please select an output.xml file first.', 'error');
            return;
        }

        // Reset UI
        resultsContainer.innerHTML = '';
        alertBox.classList.add('hidden');
        
        const loader = document.getElementById('loader');
        const pipelineLogList = document.getElementById('pipeline-log');
        pipelineLogList.innerHTML = '';
        loader.classList.remove('hidden');
        
        analyzeBtn.disabled = true;
        analyzeBtn.style.opacity = '0.5';

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.detail || 'API Request Failed');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                
                buffer = lines.pop(); // Keep the string without trailing newline here

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        handleStreamEvent(JSON.parse(line));
                    } catch (e) {
                        console.error('JSON parse error:', line, e);
                    }
                }
            }

            if (buffer.trim()) {
                try {
                    handleStreamEvent(JSON.parse(buffer));
                } catch (e) {}
            }

        } catch (error) {
            showAlert(error.message, 'error');
        } finally {
            setTimeout(() => {
                loader.classList.add('hidden');
            }, 5000); // Give user time to see final steps
            analyzeBtn.disabled = false;
            analyzeBtn.style.opacity = '1';
        }
    });

    function handleStreamEvent(event) {
        const logList = document.getElementById('pipeline-log');
        if (event.type === 'status' || event.type === 'error' || event.type === 'done') {
            const li = document.createElement('li');
            li.className = 'log-item';
            if (event.type === 'error') li.classList.add('error');
            if (event.type === 'done') li.classList.add('done');
            li.textContent = event.message;
            logList.appendChild(li);
            logList.scrollTop = logList.scrollHeight; // Auto-scroll
            
            if (event.type === 'error') showAlert(event.message, 'error');
            if (event.type === 'done' && event.message === 'All Tests Passed!') showAlert(event.message, 'success');
        } else if (event.type === 'result') {
            renderFailures([event.data]);
        }
    }

    function renderFailures(failures) {
        failures.forEach((f, idx) => {
            const card = document.createElement('div');
            card.className = 'rca-card';
            card.style.animationDelay = `${idx * 0.15}s`;

            const tagsHtml = f.tags.map(t => `<span class="tag">${t}</span>`).join('');
            const md = (text) => (window.marked ? marked.parse(text || '') : escapeHtml(text));

            card.innerHTML = `
                <div class="rca-header">
                    <div class="rca-title-group">
                        <div class="rca-icon"><i data-lucide="bot"></i></div>
                        <div class="rca-title">
                            <h3>${f.test_name}</h3>
                            <div class="rca-tags">${tagsHtml}</div>
                        </div>
                    </div>
                </div>
                
                <div class="rca-body">
                    <div class="err-pill">
                        <strong>Failed at:</strong> ${f.failed_keyword}<br>
                        <strong>Reason:</strong> ${f.error_message}
                    </div>
                    
                    <div class="rca-analysis glass-inset">
                        <div class="rca-segment-header"><i data-lucide="sparkles"></i> Agentic Root Cause Analysis</div>
                        <div class="rca-content-text">${md(f.rca)}</div>
                    </div>
                </div>
            `;
            resultsContainer.appendChild(card);
        });
        if (window.lucide) lucide.createIcons();
    }

    function showAlert(msg, type) {
        alertBox.textContent = msg;
        alertBox.classList.remove('hidden');
        if (type === 'success') {
            alertBox.style.background = 'rgba(102, 252, 241, 0.1)';
            alertBox.style.borderColor = 'var(--primary)';
            alertBox.style.color = 'var(--primary)';
        } else {
            alertBox.style.background = 'rgba(244, 63, 94, 0.1)';
            alertBox.style.borderColor = 'var(--error)';
            alertBox.style.color = 'var(--error)';
        }
    }

    function escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
    }
});
