from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class ScanRequest(BaseModel):
    content: str

class ScanResponse(BaseModel):
    risk_score: float
    risk_level: str # "Safe", "Suspicious", "Phishing"
    indicators: list[str]
    recommendation: str
    live_reputation: Optional[dict[str, Any]] = None

class ScanResultDB(BaseModel):
    id: int
    scan_type: str
    content: str
    classification: str
    risk_score: float
    result_details: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    total_scanned: int
    phishing_detected: int
    suspicious_detected: int
    safe_detected: int
    recent_scans: list[ScanResultDB]
