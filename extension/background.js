const API_URL = "http://127.0.0.1:8000/api/scan/url";

chrome.runtime.onInstalled.addListener(() => {
    chrome.contextMenus.create({
        id: "scanLink",
        title: "Scan link for phishing",
        contexts: ["link"]
    });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === "scanLink" && info.linkUrl) {

        // Save URL temporarily and open popup
        chrome.storage.local.set({ scanUrl: info.linkUrl }, () => {
            // Unfortuantely Chrome requires user interaction to open a popup
            // We can show a notification instead or open a new tab depending on the preference.

            // For this extension, we will do a background scan and show a notification alert.
            performScan(info.linkUrl);
        });
    }
});

async function performScan(url) {
    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ content: url })
        });

        const result = await response.json();

        let title = "CyberGuard AI";
        let message = `Detection: ${result.risk_level} (Score: ${result.risk_score}%)`;

        let iconUrl = "icon.png";

        // Use basic chrome notifications api
        chrome.notifications.create({
            type: "basic",
            iconUrl: iconUrl,
            title: title,
            message: message + "\n" + result.recommendation,
            priority: 2
        });

    } catch (err) {
        chrome.notifications.create({
            type: "basic",
            iconUrl: "icon.png",
            title: "CyberGuard AI Error",
            message: "Failed to connect to the analysis engine.",
            priority: 2
        });
    }
}
