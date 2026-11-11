// Auto-detect API base: works for local dev and Vercel production (same origin)
const API_BASE = "/api";

document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chatForm");
    const userInput = document.getElementById("userInput");
    const chatHistory = document.getElementById("chatHistory");
    const sendBtn = document.getElementById("sendBtn");

    if (chatForm) {
        chatForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const text = userInput.value.trim();
            if (!text) return;

            // Add user message
            addMessage(text, "user");
            userInput.value = "";
            sendBtn.disabled = true;

            // Add loading indicator
            const loadingId = addLoading();

            try {
                // Determine if URL or Message
                const urlRegex = /(https?:\/\/[^\s]+)/g;
                const isUrlOnly = text.match(urlRegex) && text.match(urlRegex)[0] === text;
                const endpoint = isUrlOnly ? "/scan/url" : "/scan/message";

                // If it's a mix like "Check this link http://link.com", extract the intent using the message endpoint
                // or just pass it to the message API which detects URLs.
                // For simplicity, we'll route simple URLs to /scan/url, everything else to /scan/message

                let targetEndpoint = '/scan/message';
                let payload = text;

                // Try to extract URL if user typed "Check this link http..."
                const urls = text.match(urlRegex);
                if (urls && urls.length > 0 && text.toLowerCase().includes("check")) {
                    targetEndpoint = '/scan/url';
                    payload = urls[0];
                } else if (text.startsWith("http")) {
                    targetEndpoint = '/scan/url';
                }

                const response = await fetch(`${API_BASE}${targetEndpoint}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ content: payload })
                });

                if (!response.ok) {
                    let errDetail = "";
                    try {
                        const errJson = await response.json();
                        errDetail = errJson.detail || JSON.stringify(errJson);
                    } catch (_) {
                        errDetail = await response.text();
                    }
                    console.error("API response error:", response.status, errDetail);
                    throw new Error(`HTTP ${response.status} - ${errDetail || "Request failed"}`);
                }

                const result = await response.json();

                // Remove loading and add bot response
                removeMessage(loadingId);
                addBotResult(result);
            } catch (error) {
                console.error("Scan Error:", error);
                removeMessage(loadingId);
                const urlMatch = text.match(/https?:\/\/[^\s]+/i);
                const scanUrl = text.startsWith("http") || (urlMatch && text.toLowerCase().includes("check"));
                const offlineContent = text.startsWith("http") ? text : (scanUrl ? urlMatch[0] : text);
                addBotResult(analyzeOffline(offlineContent, scanUrl ? "url" : "message"));
            } finally {
                sendBtn.disabled = false;
                userInput.focus();
            }
        });
    }
});

// Lightweight browser-only fallback for when the API is not running.
// It does not use the trained model or perform a live reputation lookup.
function analyzeOffline(content, type) {
    const indicators = [];
    let score = 0;

    if (type === "url") {
        const value = content.trim();
        let parsed;
        try {
            parsed = new URL(value.includes("://") ? value : `http://${value}`);
        } catch (_) {
            parsed = new URL("http://invalid.local");
        }
        const host = parsed.hostname;
        if (host.includes("-")) {
            score += 20;
            indicators.push("The hostname contains a dash.");
        }
        if (/login|verify|secure|update|account|banking|confirm/i.test(value)) {
            score += 30;
            indicators.push("The URL contains common account or verification bait words.");
        }
        if (/^(\d{1,3}\.){3}\d{1,3}$/.test(host)) {
            score += 40;
            indicators.push("The URL uses an IP address instead of a domain name.");
        }
        if (parsed.protocol !== "https:") {
            score += 10;
            indicators.push("The URL does not use HTTPS.");
        }
        if (host.split(".").length > 3) {
            score += 15;
            indicators.push("The hostname has several subdomain levels.");
        }
    } else {
        const lower = content.toLowerCase();
        const urls = content.match(/https?:\/\/[^\s]+/g) || [];
        if (lower.includes("urgent") || lower.includes("immediately")) {
            score += 30;
            indicators.push("The message uses urgent or immediate-pressure wording.");
        }
        if (lower.includes("suspend") || lower.includes("locked")) {
            score += 30;
            indicators.push("The message claims an account is suspended or locked.");
        }
        if (lower.includes("reward") || lower.includes("winner")) {
            score += 20;
            indicators.push("The message mentions a reward or prize.");
        }
        if (urls.length) {
            score += 20;
            indicators.push(`The message contains ${urls.length} link(s).`);
        }
    }

    score = Math.min(score, 100);
    const risk_level = score <= 30 ? "Safe" : score <= 60 ? "Suspicious" : "Phishing";
    if (!indicators.length) indicators.push("No suspicious patterns detected by the local heuristic.");
    indicators.push("Offline heuristic only; no trained-model or live reputation check was available.");
    const recommendation = risk_level === "Phishing"
        ? "Treat this as high risk. Do not open the link or share credentials."
        : risk_level === "Suspicious"
            ? "Proceed with caution. Verify the sender or site through a trusted channel."
            : "No obvious warning signs were detected, but this heuristic cannot guarantee safety.";
    return { risk_score: score, risk_level, indicators, recommendation };
}

function fillInput(text) {
    document.getElementById("userInput").value = text;
    document.getElementById("userInput").focus();
}

function addMessage(text, sender) {
    const chatHistory = document.getElementById("chatHistory");
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${sender}`;

    const icon = sender === 'user' ? 'fa-user' : 'fa-robot';

    msgDiv.innerHTML = `
        <div class="message-avatar"><i class="fas ${icon}"></i></div>
        <div class="message-content"><p>${escapeHTML(text)}</p></div>
    `;

    chatHistory.appendChild(msgDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    return msgDiv.id = 'msg-' + Date.now();
}

function addLoading() {
    const chatHistory = document.getElementById("chatHistory");
    const id = 'loading-' + Date.now();
    const msgDiv = document.createElement("div");
    msgDiv.className = `message assistant`;
    msgDiv.id = id;

    msgDiv.innerHTML = `
        <div class="message-avatar"><i class="fas fa-robot"></i></div>
        <div class="message-content">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;

    chatHistory.appendChild(msgDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    return id;
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function addBotResult(result) {
    const chatHistory = document.getElementById("chatHistory");
    const msgDiv = document.createElement("div");
    msgDiv.className = `message assistant`;

    const riskClass = result.risk_level.toLowerCase();

    let indicatorsHtml = '';
    if (result.indicators && result.indicators.length > 0) {
        indicatorsHtml = `<ul class="indicators">
            ${result.indicators.map(i => `<li>${escapeHTML(String(i))}</li>`).join('')}
        </ul>`;
    }
    const reputation = result.live_reputation;
    let reputationHtml = '';
    if (reputation) {
        const statusText = {
            threat_found: 'Live check: threat reported by Google Safe Browsing.',
            no_threat_found: 'Live check: no listing found. This does not prove the URL is safe.',
            not_configured: 'Live reputation check is not configured on this backend.',
            unavailable: 'Live reputation service could not be reached; model analysis only.'
        }[reputation.status] || 'Live reputation status unavailable.';
        const attribution = reputation.status === 'threat_found'
            ? ` <a href="https://safebrowsing.google.com/" target="_blank" rel="noopener noreferrer">Google Safe Browsing advisory</a>.`
            : '';
        reputationHtml = `<p class="reputation-status">${escapeHTML(statusText)}${attribution}</p>`;
    }

    let alertIcon = 'fa-info-circle';
    if (riskClass === 'phishing') alertIcon = 'fa-exclamation-triangle';
    if (riskClass === 'safe') alertIcon = 'fa-check-circle';

    msgDiv.innerHTML = `
        <div class="message-avatar"><i class="fas fa-robot"></i></div>
        <div class="message-content">
            <p><strong><i class="fas ${alertIcon}"></i> Analysis Complete</strong></p>
            
            <div class="result-card ${riskClass}">
                <p>Detection Result: <strong>${escapeHTML(String(result.risk_level))}</strong></p>
                <div class="risk-score">Risk Score: ${escapeHTML(String(result.risk_score))}%</div>
                
                ${indicatorsHtml ? `<p style="margin-top:12px; color:var(--text-muted); font-size:13px;">Detected Indicators:</p>${indicatorsHtml}` : ''}
                ${reputationHtml}
                
                <div class="recommendation">
                    Recommendation: ${escapeHTML(String(result.recommendation))}
                </div>
            </div>
        </div>
    `;

    chatHistory.appendChild(msgDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function escapeHTML(str) {
    return str.replace(/[&<>'"]/g,
        tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag] || tag)
    );
}

// Admin Dashboard Functions
let adminStatsRequestInFlight = false;
let adminStatsRefreshPending = false;
let historyDeletionInFlight = false;

function showSavedScan(scan) {
    const dialog = document.getElementById('scanDetailDialog');
    const body = document.getElementById('scanDetailBody');
    if (!dialog || !body) return;

    let details = null;
    try {
        details = scan.result_details ? JSON.parse(scan.result_details) : null;
    } catch (error) {
        console.warn('Could not read saved scan details:', error);
    }

    const date = new Date(scan.timestamp);
    const when = Number.isNaN(date.getTime()) ? 'Unknown time' : date.toLocaleString();
    const classification = String(scan.classification || details?.risk_level || 'Unknown');
    const score = scan.risk_score ?? details?.risk_score ?? '—';
    const indicators = Array.isArray(details?.indicators) ? details.indicators : [];
    const indicatorsHtml = indicators.length
        ? `<section><h3>Detected indicators</h3><ul>${indicators.map(item => `<li>${escapeHTML(String(item))}</li>`).join('')}</ul></section>`
        : '';
    const recommendationHtml = details?.recommendation
        ? `<section class="scan-detail-recommendation"><h3>Recommendation</h3><p>${escapeHTML(String(details.recommendation))}</p></section>`
        : '';
    const reputation = details?.live_reputation;
    const reputationHtml = reputation?.status
        ? `<p class="scan-detail-meta">Live reputation: ${escapeHTML(String(reputation.status).replaceAll('_', ' '))}</p>`
        : '';
    const archivedNotice = details
        ? ''
        : '<p class="scan-detail-note">This scan was saved before detailed result history was enabled. Its original content, classification, and score are available; indicators and recommendation were not stored.</p>';

    body.innerHTML = `
        <p class="scan-detail-meta">${escapeHTML(when)} · ${escapeHTML(String(scan.scan_type || 'scan').toUpperCase())}</p>
        <p><strong>${escapeHTML(classification)} · ${escapeHTML(String(score))}% risk</strong></p>
        <section><h3>Scanned content</h3><div class="scan-detail-content">${escapeHTML(String(scan.content || ''))}</div></section>
        ${indicatorsHtml}${recommendationHtml}${reputationHtml}${archivedNotice}
    `;
    if (!dialog.open) dialog.showModal();
}

function setupScanDetailDialog() {
    const dialog = document.getElementById('scanDetailDialog');
    const closeButton = document.getElementById('closeScanDetail');
    if (!dialog || !closeButton) return;
    closeButton.addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', event => {
        if (event.target === dialog) dialog.close();
    });
}

async function deleteScanHistory(scanId = null) {
    if (historyDeletionInFlight) return;
    const clearAll = scanId === null;
    const scanCount = Number(document.getElementById('clearScanHistory')?.dataset.scanCount || 0);
    const prompt = clearAll
        ? `Permanently delete all ${scanCount} saved scan${scanCount === 1 ? '' : 's'}?`
        : 'Permanently delete this saved scan?';
    if (!window.confirm(prompt)) return;

    historyDeletionInFlight = true;
    const clearButton = document.getElementById('clearScanHistory');
    if (clearButton) clearButton.disabled = true;
    try {
        const url = scanId === null
            ? `${API_BASE}/admin/history`
            : `${API_BASE}/admin/history?scan_id=${encodeURIComponent(scanId)}`;
        const response = await fetch(url, { method: 'DELETE' });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(payload.detail || `Delete failed (HTTP ${response.status})`);
        await loadAdminStats();
    } catch (error) {
        console.error('Failed to delete scan history:', error);
        window.alert(error.message || 'Could not delete scan history. Check that the backend is running.');
    } finally {
        historyDeletionInFlight = false;
        if (clearButton) clearButton.disabled = false;
        loadAdminStats();
    }
}

async function loadAdminStats() {
    if (adminStatsRequestInFlight) {
        adminStatsRefreshPending = true;
        return;
    }
    adminStatsRequestInFlight = true;
    try {
        const response = await fetch(`${API_BASE}/admin/stats`, { cache: "no-store" });
        if (!response.ok) {
            throw new Error(`Stats API returned HTTP ${response.status}`);
        }
        const stats = await response.json();
        if (!Array.isArray(stats.recent_scans)) {
            throw new Error("Stats API response is missing recent scan data");
        }

        document.getElementById('statTotal').innerText = stats.total_scanned;
        document.getElementById('statPhishing').innerText = stats.phishing_detected;
        document.getElementById('statSuspicious').innerText = stats.suspicious_detected;
        document.getElementById('statSafe').innerText = stats.safe_detected;

        const clearButton = document.getElementById('clearScanHistory');
        if (clearButton) {
            clearButton.dataset.scanCount = String(stats.total_scanned);
            clearButton.disabled = stats.total_scanned === 0 || historyDeletionInFlight;
        }

        const tableBody = document.getElementById('recentScansBody');
        tableBody.innerHTML = '';

        if (stats.recent_scans.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="6" class="dashboard-message">No scans yet. Run a URL or message scan and it will appear here.</td></tr>';
            return;
        }

        stats.recent_scans.forEach(scan => {
            const tr = document.createElement('tr');
            tr.className = 'scan-history-row';
            tr.tabIndex = 0;
            tr.setAttribute('role', 'button');

            const parsedDate = new Date(scan.timestamp);
            const date = Number.isNaN(parsedDate.getTime()) ? 'Unknown time' : parsedDate.toLocaleString();
            const classification = String(scan.classification || 'Unknown');
            const riskClass = classification.toLowerCase();
            const content = String(scan.content || '');
            const truncatedContent = content.length > 50 ? content.substring(0, 50) + '...' : content;
            tr.setAttribute('aria-label', `Load saved ${String(scan.scan_type || 'scan')} result: ${truncatedContent}`);
            tr.addEventListener('click', () => showSavedScan(scan));
            tr.addEventListener('keydown', event => {
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    showSavedScan(scan);
                }
            });

            tr.innerHTML = `
                <td>${escapeHTML(date)}</td>
                <td><span style="color:var(--text-muted); text-transform:uppercase; font-size:12px; font-weight:700;">${escapeHTML(String(scan.scan_type || 'unknown'))}</span></td>
                <td><code style="background:rgba(0,0,0,0.3); padding:2px 6px; border-radius:4px;">${escapeHTML(truncatedContent)}</code></td>
                <td><span class="badge ${escapeHTML(riskClass)}">${escapeHTML(classification)}</span></td>
                <td><strong>${escapeHTML(String(scan.risk_score ?? '—'))}%</strong></td>
                <td class="scan-actions">
                    <button type="button" class="view-scan-result">View result</button>
                    <button type="button" class="delete-scan-result">Delete</button>
                </td>
            `;
            tr.querySelector('.view-scan-result').addEventListener('click', event => {
                event.stopPropagation();
                showSavedScan(scan);
            });
            tr.querySelector('.delete-scan-result').addEventListener('click', event => {
                event.stopPropagation();
                deleteScanHistory(scan.id);
            });
            tableBody.appendChild(tr);
        });

    } catch (error) {
        console.error("Failed to load admin stats:", error);
        const tableBody = document.getElementById('recentScansBody');
        if (tableBody) {
            tableBody.innerHTML = '<tr><td colspan="6" class="dashboard-message dashboard-error">Dashboard data could not be loaded. Check that the backend is running, then reopen this page.</td></tr>';
        }
    } finally {
        adminStatsRequestInFlight = false;
        if (adminStatsRefreshPending) {
            adminStatsRefreshPending = false;
            loadAdminStats();
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    // Detect the dashboard by its DOM so it also works at deployment aliases
    // such as /admin, where the browser URL does not contain "admin.html".
    if (!document.getElementById('recentScansBody')) return;
    setupScanDetailDialog();
    document.getElementById('clearScanHistory')?.addEventListener('click', () => deleteScanHistory());
    loadAdminStats();
    // Refresh stats every 10 seconds.
    setInterval(loadAdminStats, 10000);
});
