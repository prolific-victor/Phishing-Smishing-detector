"""Fetch and normalize public, labeled phishing datasets.

The downloaded sources are processed as text only. URLs in the datasets are
never opened or visited.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import json
import urllib.request
import zipfile

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "backend" / "data"
USER_AGENT = "CyberSecurityAssistantDatasetPrep/1.0 (research and model training)"

UCI_URL_ZIP = "https://archive.ics.uci.edu/static/public/967/phiusiil%2Bphishing%2Burl%2Bdataset.zip"
MENDELEY_FILES_API = "https://data.mendeley.com/public-api/datasets/f45bkkt8pr/files?folder_id=root&version=1"


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read()


def normalized_columns(frame: pd.DataFrame) -> dict[str, str]:
    return {str(column).strip().lower().replace(" ", "_"): column for column in frame.columns}


def prepare_url_dataset() -> int:
    print("Downloading UCI PhiUSIIL URL dataset (CC BY 4.0)...")
    archive_bytes = download(UCI_URL_ZIP)
    with zipfile.ZipFile(BytesIO(archive_bytes)) as archive:
        csv_names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        csv_name = next((name for name in csv_names if "phiusiil_phishing_url_dataset.csv" in name.lower()), None)
        if not csv_name:
            raise RuntimeError(f"Could not find the PhiUSIIL CSV in archive; CSV entries: {csv_names}")
        with archive.open(csv_name) as csv_file:
            frame = pd.read_csv(csv_file, low_memory=False)

    columns = normalized_columns(frame)
    url_column = columns.get("url")
    label_column = columns.get("label")
    if url_column is None or label_column is None:
        raise RuntimeError(f"Expected URL and label columns in PhiUSIIL; found: {list(frame.columns)}")

    clean = frame[[url_column, label_column]].rename(columns={url_column: "url", label_column: "source_label"})
    clean["url"] = clean["url"].astype("string").str.strip()
    clean["source_label"] = pd.to_numeric(clean["source_label"], errors="coerce")
    clean = clean.dropna(subset=["url", "source_label"])
    clean = clean[clean["url"].str.len() > 3]
    # UCI PhiUSIIL defines 0 as phishing and 1 as legitimate.
    clean["label"] = (clean["source_label"].astype(int) == 0).astype(int)
    clean = clean[["url", "label"]]

    label_counts = clean.groupby("url")["label"].nunique()
    conflicts = set(label_counts[label_counts > 1].index)
    clean = clean[~clean["url"].isin(conflicts)].drop_duplicates(subset=["url"]).reset_index(drop=True)
    if clean["label"].nunique() != 2:
        raise RuntimeError("PhiUSIIL preparation did not produce both labels")

    destination = DATA_DIR / "real_url_dataset.csv"
    clean.to_csv(destination, index=False)
    print(f"Saved {len(clean):,} unique URL rows to {destination}")
    print("URL labels: 1=phishing, 0=legitimate")
    return len(clean)


def prepare_message_dataset() -> int:
    print("Downloading Mendeley SMS phishing dataset (CC BY 4.0)...")
    listing = json.loads(download(MENDELEY_FILES_API).decode("utf-8"))
    files = listing.get("files", listing) if isinstance(listing, dict) else listing
    zip_file = next((item for item in files if str(item.get("filename", "")).lower().endswith(".zip")), None)
    if zip_file is None:
        names = [item.get("filename") for item in files]
        raise RuntimeError(f"Could not find the SMS zip in Mendeley response; files: {names}")
    download_url = zip_file.get("content_details", {}).get("download_url")
    if not download_url:
        raise RuntimeError("Mendeley file listing did not provide a download URL")

    zip_bytes = download(download_url)
    frame = None
    with zipfile.ZipFile(BytesIO(zip_bytes)) as archive:
        csv_names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        for name in csv_names:
            with archive.open(name) as csv_file:
                try:
                    candidate = pd.read_csv(csv_file, encoding="utf-8-sig", low_memory=False)
                except UnicodeDecodeError:
                    csv_file.seek(0)
                    candidate = pd.read_csv(csv_file, encoding="latin-1", low_memory=False)
            columns = normalized_columns(candidate)
            if "label" in columns and "text" in columns:
                frame = candidate.rename(columns={columns["label"]: "source_label", columns["text"]: "text"})
                break
    if frame is None:
        raise RuntimeError(f"Could not find a CSV with LABEL and TEXT columns; entries: {csv_names}")

    clean = frame[["source_label", "text"]].copy()
    clean["source_label"] = clean["source_label"].astype("string").str.strip().str.lower()
    clean["text"] = clean["text"].astype("string").str.replace(r"\s+", " ", regex=True).str.strip()
    # Smishing is phishing (1); ham and generic spam are non-phishing (0).
    clean = clean[clean["source_label"].isin(["ham", "spam", "smishing"])]
    clean["label"] = (clean["source_label"] == "smishing").astype(int)
    class_counts = clean["source_label"].value_counts().to_dict()
    clean = clean[["text", "label"]].dropna(subset=["text"])

    label_counts = clean.groupby("text")["label"].nunique()
    conflicts = set(label_counts[label_counts > 1].index)
    clean = clean[~clean["text"].isin(conflicts)].drop_duplicates(subset=["text"]).reset_index(drop=True)
    if clean["label"].nunique() != 2:
        raise RuntimeError("SMS preparation did not produce both ham and smishing labels")

    destination = DATA_DIR / "real_message_dataset.csv"
    clean.to_csv(destination, index=False)
    print(f"Saved {len(clean):,} unique SMS rows to {destination}")
    print("SMS labels: 1=smishing, 0=ham or generic spam")
    print("Source class counts:", class_counts)
    return len(clean)


if __name__ == "__main__":
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    prepare_url_dataset()
    prepare_message_dataset()
