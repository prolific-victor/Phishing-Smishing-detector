import pandas as pd
import numpy as np
import pickle
import os
import sys
import spacy
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score

# Add root project dir to path to import backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.ml.url_analyzer import extract_features

# Ensure spacy model is downloaded (python -m spacy download en_core_web_sm)
nlp = spacy.load("en_core_web_sm")

def train_url_model():
    print("Training URL Phishing Detection Model...")
    df = pd.read_csv("../data/url_dataset.csv")
    
    # Extract features
    X = []
    y = df['label'].values
    
    for url in df['url']:
        features = extract_features(url)
        X.append(features)
        
    X = np.array(X)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"URL Model Accuracy: {accuracy * 100:.2f}%")
    
    with open("url_model.pkl", "wb") as f:
        pickle.dump(model, f)
    print("Saved url_model.pkl")

def train_message_model():
    print("Training Message Phishing Detection Model...")
    df = pd.read_csv("../data/message_dataset.csv")
    
    # Preprocess text
    X = df['text'].values
    y = df['label'].values
    
    vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
    X_tfidf = vectorizer.fit_transform(X)
    
    X_train, X_test, y_train, y_test = train_test_split(X_tfidf, y, test_size=0.2, random_state=42)
    
    model = LogisticRegression() # Using Logistic Regression for text classification
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Message Model Accuracy: {accuracy * 100:.2f}%")
    
    with open("vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)
    
    with open("message_model.pkl", "wb") as f:
        pickle.dump(model, f)
    print("Saved message_model.pkl and vectorizer.pkl")

if __name__ == "__main__":
    from dataset_generator import generate_url_dataset, generate_message_dataset
    os.makedirs("../data", exist_ok=True)
    generate_url_dataset("../data/url_dataset.csv")
    generate_message_dataset("../data/message_dataset.csv")
    
    train_url_model()
    train_message_model()
    print("ML Pipeline execution completed successfully.")
