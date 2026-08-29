import pickle
import os
import re

MODEL_PATH = os.path.join(os.path.dirname(__file__), "message_model.pkl")
VECTORIZER_PATH = os.path.join(os.path.dirname(__file__), "vectorizer.pkl")

def analyze_message(message: str):
    """Analyze the message using NLP and the trained model."""
    indicators = []
    
    msg_lower = message.lower()
    
    # 1. Urgency words
    urgency_words = ['urgent', 'act now', 'verify immediately', 'last chance', 'suspended', 'locked']
    if any(word in msg_lower for word in urgency_words):
        indicators.append("Contains urgency keywords to pressure you")
        
    # 2. Financial bait
    financial_words = ['bank account', 'payment', 'reward', 'gift card', 'winner', 'unpaid', 'billing', 'fee']
    if any(word in msg_lower for word in financial_words):
        indicators.append("Financial bait detected (e.g., rewards or unpaid fees)")
        
    # 3. Suspicious links
    urls = re.findall(r'(https?://[^\s]+)', message)
    if urls:
        indicators.append(f"Contains {len(urls)} link(s)")
        
    risk_score = None
    classification = "Safe"
    
    if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
        try:
            with open(VECTORIZER_PATH, "rb") as f:
                vectorizer = pickle.load(f)
            with open(MODEL_PATH, "rb") as f:
                model = pickle.load(f)
                
            features = vectorizer.transform([message])
            probability = model.predict_proba(features)[0][1]
            risk_score = min(round(probability * 100, 1), 100.0)
        except Exception as e:
            print(f"Warning: NLP model predict error ({e}), falling back to heuristic rules")
            risk_score = None
            
    if risk_score is None:
        # Fallback to rule-based logic
        score = 0
        if "urgent" in msg_lower or "immediately" in msg_lower: score += 30
        if "suspend" in msg_lower or "locked" in msg_lower: score += 30
        if "reward" in msg_lower or "winner" in msg_lower: score += 20
        if urls: score += 20
        risk_score = min(float(score), 100.0)

    if risk_score <= 30.0:
        classification = "Safe"
        recommendation = "This message appears to be safe."
        if not indicators:
            indicators.append("No suspicious context detected.")
    elif risk_score <= 60.0:
        classification = "Suspicious"
        recommendation = "Be careful. Verify the sender's identity before clicking any links or replying."
    else:
        classification = "Phishing"
        recommendation = "Do not trust this message. Avoid clicking any links or providing personal info."
        
    return {
        "risk_score": risk_score,
        "risk_level": classification,
        "indicators": indicators,
        "recommendation": recommendation
    }
