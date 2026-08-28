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

                if (!response.ok) throw new Error("API Request Failed");

                const result = await response.json();

                // Remove loading and add bot response
                removeMessage(loadingId);
                addBotResult(result);
            } catch (error) {
                console.error("Error:", error);
                removeMessage(loadingId);
                addMessage("Sorry, I couldn't reach the detection server. Is it running?", "assistant");
            } finally {
                sendBtn.disabled = false;
                userInput.focus();
            }
        });
    }
});

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
            ${result.indicators.map(i => `<li>${i}</li>`).join('')}
        </ul>`;
    }

    let alertIcon = 'fa-info-circle';
    if (riskClass === 'phishing') alertIcon = 'fa-exclamation-triangle';
    if (riskClass === 'safe') alertIcon = 'fa-check-circle';

    msgDiv.innerHTML = `
        <div class="message-avatar"><i class="fas fa-robot"></i></div>
        <div class="message-content">
            <p><strong><i class="fas ${alertIcon}"></i> Analysis Complete</strong></p>
            
            <div class="result-card ${riskClass}">
                <p>Detection Result: <strong>${result.risk_level}</strong></p>
                <div class="risk-score">Risk Score: ${result.risk_score}%</div>
                
                ${indicatorsHtml ? `<p style="margin-top:12px; color:var(--text-muted); font-size:13px;">Detected Indicators:</p>${indicatorsHtml}` : ''}
                
                <div class="recommendation">
                    Recommendation: ${result.recommendation}
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
async function loadAdminStats() {
    try {
        const response = await fetch(`${API_BASE}/admin/stats`);
        const stats = await response.json();

        document.getElementById('statTotal').innerText = stats.total_scanned;
        document.getElementById('statPhishing').innerText = stats.phishing_detected;
        document.getElementById('statSuspicious').innerText = stats.suspicious_detected;
        document.getElementById('statSafe').innerText = stats.safe_detected;

        const tableBody = document.getElementById('recentScansBody');
        tableBody.innerHTML = '';

        stats.recent_scans.forEach(scan => {
            const tr = document.createElement('tr');

            const date = new Date(scan.timestamp).toLocaleString();
            const riskClass = scan.classification.toLowerCase();
            const truncatedContent = scan.content.length > 50 ? scan.content.substring(0, 50) + '...' : scan.content;

            tr.innerHTML = `
                <td>${date}</td>
                <td><span style="color:var(--text-muted); text-transform:uppercase; font-size:12px; font-weight:700;">${scan.scan_type}</span></td>
                <td><code style="background:rgba(0,0,0,0.3); padding:2px 6px; border-radius:4px;">${escapeHTML(truncatedContent)}</code></td>
                <td><span class="badge ${riskClass}">${scan.classification}</span></td>
                <td><strong>${scan.risk_score}%</strong></td>
            `;
            tableBody.appendChild(tr);
        });

    } catch (error) {
        console.error("Failed to load admin stats:", error);
    }
}

if (window.location.pathname.includes('admin.html')) {
    document.addEventListener("DOMContentLoaded", loadAdminStats);
    // Refresh stats every 10 seconds
    setInterval(loadAdminStats, 10000);
}
