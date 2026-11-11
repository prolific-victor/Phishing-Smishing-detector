import json
import sys
import os
from http.server import BaseHTTPRequestHandler

# Add root directory to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import backend.ml.url_analyzer as url_analyzer
from backend import database

database.init_db()

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
        
        try:
            payload = json.loads(post_data.decode('utf-8'))
            url = payload.get('content', '')
            
            result = url_analyzer.analyze_url(url)
            
            # Record in database if possible
            try:
                db_gen = database.get_db()
                db = next(db_gen)
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
                print(f"DB error: {e}")
                
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
