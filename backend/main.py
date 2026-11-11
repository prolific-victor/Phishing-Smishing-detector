import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from backend import database, models
from backend.reputation import check_url
import backend.ml.url_analyzer as url_analyzer
import backend.ml.message_analyzer as message_analyzer

app = FastAPI(title="AI Cybersecurity Assistant API")
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Database
database.init_db()

@app.get("/health")
@app.get("/api")
@app.get("/api/")
@app.get("/api/health")
@app.get("/api/index.py/health")
@app.get("/api/index/health")
def read_root():
    return {"status": "ok", "message": "AI Cybersecurity Assistant API is running"}

@app.get("/", include_in_schema=False)
def frontend_home():
    return FileResponse(os.path.join(frontend_dir, "index.html"))

@app.post("/scan/url", response_model=models.ScanResponse)
@app.post("/api/scan/url", response_model=models.ScanResponse)
@app.post("/api/index.py/scan/url", response_model=models.ScanResponse)
@app.post("/api/index/scan/url", response_model=models.ScanResponse)
@app.post("/api/index.py/api/scan/url", response_model=models.ScanResponse)
def scan_url(request: models.ScanRequest, db: Session = Depends(database.get_db)):
    """Analyze a URL for phishing."""
    url = request.content
    
    # Analyze the URL using the ML model
    result = url_analyzer.analyze_url(url)
    reputation = check_url(url)
    result["live_reputation"] = reputation
    if reputation["status"] == "threat_found":
        result["risk_score"] = 100.0
        result["risk_level"] = "Phishing"
        result["indicators"].append("Google Safe Browsing reports this URL as potentially unsafe.")
        result["recommendation"] = "Avoid opening this link or entering information. Google Safe Browsing reported a threat; review the provider advisory for details."
    elif reputation["status"] == "no_threat_found":
        result["indicators"].append("No threat was listed by Google Safe Browsing at scan time; this does not prove the URL is safe.")
    
    # Store result in database
    try:
        db_record = database.ScanResult(
            scan_type="url",
            content=url,
            classification=result["risk_level"],
            risk_score=result["risk_score"],
            result_details=json.dumps(result, ensure_ascii=False)
        )
        db.add(db_record)
        db.commit()
    except Exception as e:
        print(f"Warning: Database write error: {e}")
    
    return result

@app.post("/scan/message", response_model=models.ScanResponse)
@app.post("/api/scan/message", response_model=models.ScanResponse)
@app.post("/api/index.py/scan/message", response_model=models.ScanResponse)
@app.post("/api/index/scan/message", response_model=models.ScanResponse)
@app.post("/api/index.py/api/scan/message", response_model=models.ScanResponse)
def scan_message(request: models.ScanRequest, db: Session = Depends(database.get_db)):
    """Analyze a text message for phishing intent."""
    message = request.content
    
    # Analyze message using NLP
    result = message_analyzer.analyze_message(message)
    
    # Store result in database
    try:
        db_record = database.ScanResult(
            scan_type="message",
            content=message,
            classification=result["risk_level"],
            risk_score=result["risk_score"],
            result_details=json.dumps(result, ensure_ascii=False)
        )
        db.add(db_record)
        db.commit()
    except Exception as e:
        print(f"Warning: Database write error: {e}")
    
    return result

@app.get("/admin/stats", response_model=models.DashboardStats)
@app.get("/api/admin/stats", response_model=models.DashboardStats)
@app.get("/api/index.py/admin/stats", response_model=models.DashboardStats)
@app.get("/api/index/admin/stats", response_model=models.DashboardStats)
@app.get("/api/index.py/api/admin/stats", response_model=models.DashboardStats)
def get_admin_stats(db: Session = Depends(database.get_db)):
    """Get statistics for the admin dashboard."""
    try:
        total = db.query(database.ScanResult).count()
        phishing = db.query(database.ScanResult).filter(database.ScanResult.classification == "Phishing").count()
        suspicious = db.query(database.ScanResult).filter(database.ScanResult.classification == "Suspicious").count()
        safe = db.query(database.ScanResult).filter(database.ScanResult.classification == "Safe").count()
        recent = db.query(database.ScanResult).order_by(database.ScanResult.timestamp.desc()).limit(10).all()
        
        return {
            "total_scanned": total,
            "phishing_detected": phishing,
            "suspicious_detected": suspicious,
            "safe_detected": safe,
            "recent_scans": recent
        }
    except Exception as e:
        print(f"Warning: Database read error: {e}")
        return {
            "total_scanned": 0,
            "phishing_detected": 0,
            "suspicious_detected": 0,
            "safe_detected": 0,
            "recent_scans": []
        }

@app.delete("/admin/history")
@app.delete("/api/admin/history")
def delete_scan_history(scan_id: Optional[int] = None, db: Session = Depends(database.get_db)):
    """Delete one saved scan when scan_id is provided, or clear all history."""
    if scan_id is not None:
        scan = db.query(database.ScanResult).filter(database.ScanResult.id == scan_id).first()
        if scan is None:
            raise HTTPException(status_code=404, detail="Scan history entry not found")
        db.delete(scan)
        deleted = 1
    else:
        deleted = db.query(database.ScanResult).delete(synchronize_session=False)
    db.commit()
    return {"deleted": deleted}

# Serve the web app from the same origin as the API so browser requests to
# /api/... work when running locally.
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    # Host 0.0.0.0 allows connections from other devices on the same network
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
