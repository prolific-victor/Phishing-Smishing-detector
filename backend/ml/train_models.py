import pandas as pd
import numpy as np
import pickle
import os
import sys
from urllib.parse import urlparse
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, balanced_accuracy_score, precision_score, recall_score, f1_score

# Resolve paths from this file so training works regardless of the current
# working directory.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(PROJECT_ROOT, "backend", "data")
MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.ml.url_analyzer import extract_features


def save_pickle_atomically(value, destination):
    temporary = destination + ".tmp"
    with open(temporary, "wb") as file:
        pickle.dump(value, file)
        file.flush()
        os.fsync(file.fileno())
    os.replace(temporary, destination)

def train_url_model():
    print("Training URL Phishing Detection Model...")
    dataset_path = os.path.join(DATA_DIR, "real_url_dataset.csv")
    if not os.path.exists(dataset_path):
        dataset_path = os.path.join(DATA_DIR, "url_dataset.csv")
        print("Using the small synthetic URL dataset; fetch real datasets for meaningful evaluation.")
    else:
        print("Using the real labeled PhiUSIIL URL dataset.")
    df = pd.read_csv(dataset_path).drop_duplicates(subset=["url", "label"])
    
    # Extract features
    X = []
    y = df['label'].values
    
    for url in df['url']:
        features = extract_features(url)
        X.append(features)
        
    X = np.array(X)
    
    # Keep all URLs from a host in one fold so near-duplicate URLs from the
    # same domain cannot appear in both training and validation data.
    groups = np.array([urlparse(url if "://" in url else f"http://{url}").hostname for url in df["url"]])
    group_labels = df.assign(_group=groups)[["_group", "label"]].drop_duplicates()
    min_class_groups = int(group_labels.groupby("label")["_group"].nunique().min())
    n_splits = min(3, min_class_groups)
    scores = []
    balanced_scores = []
    precisions = []
    recalls = []
    f1_scores = []
    if n_splits >= 2:
        cv = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=42)
        for train_idx, test_idx in cv.split(X, y, groups):
            fold_model = RandomForestClassifier(n_estimators=48, random_state=42, n_jobs=-1)
            fold_model.fit(X[train_idx], y[train_idx])
            predictions = fold_model.predict(X[test_idx])
            scores.append(accuracy_score(y[test_idx], predictions))
            balanced_scores.append(balanced_accuracy_score(y[test_idx], predictions))
            precisions.append(precision_score(y[test_idx], predictions, zero_division=0))
            recalls.append(recall_score(y[test_idx], predictions, zero_division=0))
            f1_scores.append(f1_score(y[test_idx], predictions, zero_division=0))
        print(f"URL host-held-out CV ({n_splits} folds): accuracy={np.mean(scores) * 100:.2f}%, "
              f"balanced_accuracy={np.mean(balanced_scores) * 100:.2f}%, "
              f"phishing_precision={np.mean(precisions) * 100:.2f}%, "
              f"phishing_recall={np.mean(recalls) * 100:.2f}%, "
              f"phishing_F1={np.mean(f1_scores) * 100:.2f}%")
    else:
        print("URL validation skipped: not enough distinct hosts in each class.")

    model = RandomForestClassifier(n_estimators=48, random_state=42, n_jobs=-1)
    model.fit(X, y)
    
    save_pickle_atomically(model, os.path.join(MODEL_DIR, "url_model.pkl"))
    print("Saved url_model.pkl")

def train_message_model():
    print("Training Message Phishing Detection Model...")
    dataset_path = os.path.join(DATA_DIR, "real_message_dataset.csv")
    if not os.path.exists(dataset_path):
        dataset_path = os.path.join(DATA_DIR, "message_dataset.csv")
        print("Using the small synthetic message dataset; fetch real datasets for meaningful evaluation.")
    else:
        print("Using the real labeled Mendeley SMS dataset (ham, generic spam, and smishing).")
    df = pd.read_csv(dataset_path).drop_duplicates(subset=["text", "label"])
    
    # Preprocess text
    X = df['text'].values
    y = df['label'].values
    
    n_splits = min(5, int(np.bincount(y).min()))
    scores = []
    balanced_scores = []
    precisions = []
    recalls = []
    f1_scores = []
    oof_probabilities = np.zeros(len(y), dtype=float)
    if n_splits >= 2:
        cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        for train_idx, test_idx in cv.split(X, y):
            fold_vectorizer = TfidfVectorizer(max_features=5000, stop_words="english")
            X_train = fold_vectorizer.fit_transform(X[train_idx])
            X_test = fold_vectorizer.transform(X[test_idx])
            fold_model = LogisticRegression(max_iter=1000, random_state=42, class_weight="balanced")
            fold_model.fit(X_train, y[train_idx])
            probabilities = fold_model.predict_proba(X_test)[:, 1]
            oof_probabilities[test_idx] = probabilities
            predictions = (probabilities >= 0.5).astype(int)
            scores.append(accuracy_score(y[test_idx], predictions))
            balanced_scores.append(balanced_accuracy_score(y[test_idx], predictions))
            precisions.append(precision_score(y[test_idx], predictions, zero_division=0))
            recalls.append(recall_score(y[test_idx], predictions, zero_division=0))
            f1_scores.append(f1_score(y[test_idx], predictions, zero_division=0))
        print(f"Message stratified CV ({n_splits} folds): accuracy={np.mean(scores) * 100:.2f}%, "
              f"balanced_accuracy={np.mean(balanced_scores) * 100:.2f}%, "
              f"smishing_precision={np.mean(precisions) * 100:.2f}%, "
              f"smishing_recall={np.mean(recalls) * 100:.2f}%, "
              f"smishing_F1={np.mean(f1_scores) * 100:.2f}%")
        from sklearn.metrics import precision_recall_curve
        precisions_curve, recalls_curve, thresholds = precision_recall_curve(y, oof_probabilities)
        eligible = np.flatnonzero(precisions_curve[:-1] >= 0.80)
        if len(eligible):
            best = eligible[np.argmax(recalls_curve[eligible])]
            threshold = float(thresholds[best])
        else:
            threshold = 0.5
        threshold = min(max(threshold, 0.01), 0.99)
        tuned_predictions = (oof_probabilities >= threshold).astype(int)
        print(f"OOF threshold for >=80% smishing precision: {threshold:.4f}; "
              f"precision={precision_score(y, tuned_predictions, zero_division=0) * 100:.2f}%, "
              f"recall={recall_score(y, tuned_predictions, zero_division=0) * 100:.2f}%, "
              f"F1={f1_score(y, tuned_predictions, zero_division=0) * 100:.2f}%")
    else:
        print("Message validation skipped: not enough unique examples in each class.")
        threshold = 0.5

    # Fit vocabulary only on the training set in each validation fold above;
    # fit the persisted production artifacts on all unique examples now.
    vectorizer = TfidfVectorizer(max_features=5000, stop_words="english")
    X_tfidf = vectorizer.fit_transform(X)
    model = LogisticRegression(max_iter=1000, random_state=42, class_weight="balanced")
    model.fit(X_tfidf, y)
    
    save_pickle_atomically(model, os.path.join(MODEL_DIR, "message_model.pkl"))
    save_pickle_atomically(vectorizer, os.path.join(MODEL_DIR, "vectorizer.pkl"))
    threshold_path = os.path.join(MODEL_DIR, "message_threshold.json")
    temporary_threshold_path = threshold_path + ".tmp"
    with open(temporary_threshold_path, "w", encoding="utf-8") as file:
        import json
        json.dump({"threshold": threshold, "precision_floor": 0.80}, file)
        file.flush()
        os.fsync(file.fileno())
    os.replace(temporary_threshold_path, threshold_path)
    print("Saved message_model.pkl and vectorizer.pkl")

if __name__ == "__main__":
    from dataset_generator import generate_url_dataset, generate_message_dataset
    os.makedirs(DATA_DIR, exist_ok=True)
    url_dataset = os.path.join(DATA_DIR, "url_dataset.csv")
    message_dataset = os.path.join(DATA_DIR, "message_dataset.csv")
    if not os.path.exists(url_dataset):
        generate_url_dataset(url_dataset)
    if not os.path.exists(message_dataset):
        generate_message_dataset(message_dataset)
    
    train_url_model()
    train_message_model()
    print("ML Pipeline execution completed successfully.")
