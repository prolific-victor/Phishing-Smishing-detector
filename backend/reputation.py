"""Google Safe Browsing v5 URL reputation lookup."""
from __future__ import annotations

import json
import os
import threading
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

_cache: dict[str, tuple[float, dict]] = {}
_cache_lock = threading.Lock()


def check_url(url: str) -> dict:
    api_key = os.environ.get("GOOGLE_SAFE_BROWSING_API_KEY", "").strip()
    if not api_key:
        return {"status": "not_configured", "provider": "Google Safe Browsing"}
    now = time.monotonic()
    with _cache_lock:
        cached = _cache.get(url)
        if cached and cached[0] > now:
            return cached[1]
    endpoint = "https://safebrowsing.googleapis.com/v5/urls:search?" + urlencode({"key": api_key, "urls": url})
    request = Request(endpoint, headers={"Accept": "application/json", "User-Agent": "CyberSecurityAssistant/1.0"})
    try:
        with urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
        threats = payload.get("threats") or []
        duration = str(payload.get("cacheDuration", "300s"))
        try:
            ttl = min(max(int(float(duration.rstrip("s"))), 1), 86_400)
        except (TypeError, ValueError):
            ttl = 300
        result = {
            "status": "threat_found" if threats else "no_threat_found",
            "provider": "Google Safe Browsing",
            "threat_types": sorted({str(item.get("threatType", "UNKNOWN")) for item in threats}),
            "advisory_url": "https://safebrowsing.google.com/",
        }
    except Exception:
        # Never expose provider response bodies, URL, or API key in logs/output.
        return {"status": "unavailable", "provider": "Google Safe Browsing"}
    with _cache_lock:
        _cache[url] = (now + ttl, result)
    return result
