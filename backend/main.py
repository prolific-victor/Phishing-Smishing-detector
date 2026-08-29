import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from backend import database, models
import backend.ml.url_analyzer as url_analyzer
import backend.ml.message_analyzer as message_analyzer

app = FastAPI(title="AI Cybersecurity Assistant API")

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

@app.get("/")
@app.get("/health")
@app.get("/api/health")
def read_root():
    return {"status": "ok", "message": "AI Cybersecurity Assistant API is running"}

@app.post("/scan/url", response_model=models.ScanResponse)
@app.post("/api/scan/url", response_model=models.ScanResponse)
def scan_url(request: models.ScanRequest, db: Session = Depends(database.get_db)):
    """Analyze a URL for phishing."""
    url = request.content
    
    # Analyze the URL using the ML model
    result = url_analyzer.analyze_url(url)
    
    # Store result in database
    try:
        db_record = database.ScanResult(
            scan_type="url",
            content=url,
            classification=result["risk_level"],
            risk_score=result["risk_score"]
        )
        db.add(db_record)
        db.commit()
    except Exception as e:
        print(f"Warning: Database write error: {e}")
    
    return result

@app.post("/scan/message", response_model=models.ScanResponse)
@app.post("/api/scan/message", response_model=models.ScanResponse)
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
            risk_score=result["risk_score"]
        )
        db.add(db_record)
        db.commit()
    except Exception as e:
        print(f"Warning: Database write error: {e}")
    
    return result

@app.get("/admin/stats", response_model=models.DashboardStats)
@app.get("/api/admin/stats", response_model=models.DashboardStats)
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

if __name__ == "__main__":
    import uvicorn
    # Host 0.0.0.0 allows connections from other devices on the same network
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
