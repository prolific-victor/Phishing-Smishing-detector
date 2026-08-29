import pickle
import os
import re
from urllib.parse import urlparse

MODEL_PATH = os.path.join(os.path.dirname(__file__), "url_model.pkl")

def extract_features(url: str):
    """Extract features from a URL for ML classification."""
    parsed_url = urlparse(url)
    
    # 1. Length of URL
    length = len(url)
    
    # 2. Number of dots in domain
    num_dots = parsed_url.netloc.count('.')
    
    # 3. Suspicious characters
    has_at = 1 if '@' in url else 0
    has_dash = 1 if '-' in parsed_url.netloc else 0
    has_double_slash_redirect = 1 if url.rfind('//') > 7 else 0 # 7 is length of http://
    
    # 4. Suspicious words
    suspicious_words = ['login', 'verify', 'secure', 'update', 'account', 'banking', 'confirm']
    has_suspicious_word = 1 if any(word in url.lower() for word in suspicious_words) else 0
    
    # 5. IP Address used instead of domain
    is_ip = 1 if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", parsed_url.netloc) else 0
    
    # 6. HTTPS vs HTTP
    is_https = 1 if parsed_url.scheme == 'https' else 0
    
    return [length, num_dots, has_at, has_dash, has_double_slash_redirect, has_suspicious_word, is_ip, is_https]

def analyze_url(url: str):
    """Analyze the URL using the trained model and return a risk assessment."""
    indicators = []
    
    features = extract_features(url)
    
    # Add some rule-based indicators for explanation
    if features[3] == 1: indicators.append("Suspicious domain name (contains dash)")
    if features[5] == 1: indicators.append("Contains suspicious bait keywords like 'login' or 'verify'")
    if features[6] == 1: indicators.append("Uses IP address instead of domain name")
    if features[7] == 0: indicators.append("Unsecured connection (HTTP instead of HTTPS)")
    if features[1] > 2: indicators.append("Suspicious subdomain structure")
    
    risk_score = None
    classification = "Safe"
    
    if os.path.exists(MODEL_PATH):
        try:
            with open(MODEL_PATH, "rb") as f:
                model = pickle.load(f)
            probability = model.predict_proba([features])[0][1] # Probability of class 1 (Phishing)
            risk_score = min(round(probability * 100, 1), 100.0)
        except Exception as e:
            print(f"Warning: ML model predict error ({e}), falling back to heuristic rules")
            risk_score = None
            
    if risk_score is None:
        # Fallback to rule-based logic
        score = 0
        if features[3]: score += 20
        if features[5]: score += 30
        if features[6]: score += 40
        if not features[7]: score += 10
        if features[1] > 2: score += 15
        risk_score = min(float(score), 100.0)
    
    if risk_score <= 30.0:
        classification = "Safe"
        recommendation = "This link appears to be safe. You can proceed."
        if not indicators:
            indicators.append("No suspicious patterns detected.")
    elif risk_score <= 60.0:
        classification = "Suspicious"
        recommendation = "Proceed with caution. Verify the source before entering any personal information."
    else:
        classification = "Phishing"
        recommendation = "Do not enter your credentials on this website. High risk of phishing."
        
    return {
        "risk_score": risk_score,
        "risk_level": classification,
        "indicators": indicators,
        "recommendation": recommendation
    }
