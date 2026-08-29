import json
import sys
import os
from http.server import BaseHTTPRequestHandler

# Add root directory to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend import database

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        try:
            db_gen = database.get_db()
            db = next(db_gen)
            
            total = db.query(database.ScanResult).count()
            phishing = db.query(database.ScanResult).filter(database.ScanResult.classification == "Phishing").count()
            suspicious = db.query(database.ScanResult).filter(database.ScanResult.classification == "Suspicious").count()
            safe = db.query(database.ScanResult).filter(database.ScanResult.classification == "Safe").count()
            recent = db.query(database.ScanResult).order_by(database.ScanResult.timestamp.desc()).limit(10).all()
            
            recent_list = []
            for item in recent:
                recent_list.append({
                    "id": item.id,
                    "scan_type": item.scan_type,
                    "content": item.content,
                    "classification": item.classification,
                    "risk_score": item.risk_score,
                    "timestamp": item.timestamp.isoformat() if item.timestamp else ""
                })
                
            stats = {
                "total_scanned": total,
                "phishing_detected": phishing,
                "suspicious_detected": suspicious,
                "safe_detected": safe,
                "recent_scans": recent_list
            }
        except Exception as e:
            stats = {
                "total_scanned": 0,
                "phishing_detected": 0,
                "suspicious_detected": 0,
                "safe_detected": 0,
                "recent_scans": []
            }
            
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(stats).encode('utf-8'))
