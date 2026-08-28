import pandas as pd
import random
import os

def generate_url_dataset(filepath):
    # Sample legitimate URLs
    legit_domains = ["google.com", "facebook.com", "github.com", "amazon.com", "netflix.com", "wikipedia.org", "yahoo.com", "reddit.com", "bing.com", "microsoft.com", "apple.com", "twitter.com"]
    legit_urls = [
        f"https://www.{d}/" for d in legit_domains
    ] + [
        f"https://{d}/login" for d in legit_domains
    ] + [
        "https://stackoverflow.com/questions/123",
        "https://docs.python.org/3/library/index.html",
        "https://www.bbc.com/news",
    ]
    
    # Sample phishing URLs
    phish_urls = [
        "http://paypal-login-security.ru",
        "http://secure-update-apple.com",
        "https://facebook-verify-account.info",
        "http://login.yahoo-support.net",
        "http://192.168.1.1/login.php",
        "http://10.0.0.5/admin",
        "https://netflix-account-update.tv",
        "http://www.secure-bank-login-validate.com",
        "http://amzn-rewards-claim.xyz",
        "http://support-google.com.user-verify.ru/login"
    ]
    
    # Expand dataset
    data = []
    for _ in range(200):
        url = random.choice(legit_urls)
        # 0 = legit
        data.append({"url": url, "label": 0})
        
    for _ in range(200):
        url = random.choice(phish_urls)
        # 1 = phishing
        data.append({"url": url, "label": 1})
        
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False)
    print(f"URL dataset created at {filepath} with {len(df)} samples.")

def generate_message_dataset(filepath):
    # Sample legitimate messages
    legit_msgs = [
        "Hey, are we still meeting for lunch at 1?",
        "Can you send me the reports by tomorrow?",
        "Happy birthday! Hope you have a great day.",
        "Your package has been delivered to your front porch.",
        "Don't forget to pick up milk on your way home.",
        "The meeting has been rescheduled to 3 PM.",
        "Let me know when you're available to chat.",
        "I'll call you later tonight.",
        "Did you see the game last night?",
        "Thanks for the update."
    ]
    
    # Sample phishing messages
    phish_msgs = [
        "URGENT: Your bank account has been locked. Click here to verify immediately: http://secure-verify.com",
        "You've won a $1000 Amazon gift card! Claim your reward now: http://amazon-rewards.xyz",
        "SECURITY ALERT: Unauthorized login detected on your PayPal account. Secure it now: http://paypal-security-update.ru",
        "IRS Notice: You have an unpaid tax bill. Pay immediately to avoid arrest. Call 1-800-TAX-SCAM",
        "Netflix: Your payment failed. Please update your billing info within 24 hours: http://netflix-billing-update.com",
        "Dear customer, your parcel is pending delivery due to unpaid shipping fee. Pay here: http://post-delivery-fee.info",
        "Act NOW: Last chance to claim your exclusive discount! http://scam-store.net",
        "Your WhatsApp account will be suspended. Verify your phone number here: http://whatsapp-verify.cc",
        "Congrats! You're the lucky winner of our daily sweepstakes. Click to claim: http://winner-claim.biz",
        "Bank of America: We noticed suspicious activity. Verify your identity: http://bofa-verify-identity.com"
    ]
    
    data = []
    for _ in range(200):
        msg = random.choice(legit_msgs)
        data.append({"text": msg, "label": 0})
        
    for _ in range(200):
        msg = random.choice(phish_msgs)
        data.append({"text": msg, "label": 1})
        
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False)
    print(f"Message dataset created at {filepath} with {len(df)} samples.")

if __name__ == "__main__":
    os.makedirs("../data", exist_ok=True)
    generate_url_dataset("../data/url_dataset.csv")
    generate_message_dataset("../data/message_dataset.csv")
