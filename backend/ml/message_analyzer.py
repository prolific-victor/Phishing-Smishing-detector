import json
import os
import pickle
import re

MODEL_PATH = os.path.join(os.path.dirname(__file__), "message_model.pkl")
VECTORIZER_PATH = os.path.join(os.path.dirname(__file__), "vectorizer.pkl")
THRESHOLD_PATH = os.path.join(os.path.dirname(__file__), "message_threshold.json")


def analyze_message(message: str):
    """Classify smishing with a recall-tuned model, or fall back to heuristics."""
    indicators = []
    msg_lower = message.lower()
    urgency_words = ["urgent", "act now", "verify immediately", "last chance", "suspended", "locked"]
    financial_words = ["bank account", "payment", "reward", "gift card", "winner", "unpaid", "billing", "fee"]
    if any(word in msg_lower for word in urgency_words):
        indicators.append("Contains urgency keywords to pressure you")
    if any(word in msg_lower for word in financial_words):
        indicators.append("Financial bait detected (e.g., rewards or unpaid fees)")
    urls = re.findall(r"(https?://[^\s]+)", message)
    if urls:
        indicators.append(f"Contains {len(urls)} link(s)")

    probability = None
    if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
        try:
            with open(VECTORIZER_PATH, "rb") as file:
                vectorizer = pickle.load(file)
            with open(MODEL_PATH, "rb") as file:
                model = pickle.load(file)
            probability = float(model.predict_proba(vectorizer.transform([message]))[0][1])
        except Exception as exc:
            print(f"Warning: NLP model predict error ({exc}); using heuristic rules")

    if probability is not None:
        threshold = 0.5
        if os.path.exists(THRESHOLD_PATH):
            try:
                with open(THRESHOLD_PATH, "r", encoding="utf-8") as file:
                    threshold = float(json.load(file).get("threshold", threshold))
            except (OSError, ValueError, TypeError):
                pass
        score = round(probability * 100, 1)
        if probability >= threshold:
            classification = "Phishing"
            recommendation = "Do not trust this message. Avoid clicking links or providing personal information."
        elif probability >= threshold * 0.65:
            classification = "Suspicious"
            recommendation = "Be cautious. Verify the sender through a trusted channel before acting."
        else:
            classification = "Safe"
            recommendation = "No smishing signal was detected by the model; still verify unexpected requests."
    else:
        score = 0
        if "urgent" in msg_lower or "immediately" in msg_lower:
            score += 30
        if "suspend" in msg_lower or "locked" in msg_lower:
            score += 30
        if "reward" in msg_lower or "winner" in msg_lower:
            score += 20
        if urls:
            score += 20
        score = float(min(score, 100))
        if score <= 30:
            classification, recommendation = "Safe", "This message appears to be safe based on basic rules."
        elif score <= 60:
            classification, recommendation = "Suspicious", "Verify the sender before clicking links or replying."
        else:
            classification, recommendation = "Phishing", "Avoid clicking links or providing personal information."
    if not indicators:
        indicators.append("No obvious urgency, financial bait, or links detected.")
    return {"risk_score": score, "risk_level": classification, "indicators": indicators,
            "recommendation": recommendation}
