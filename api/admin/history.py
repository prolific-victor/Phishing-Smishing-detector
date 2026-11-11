import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlsplit

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend import database

database.init_db()


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_DELETE(self):
        query = parse_qs(urlsplit(self.path).query)
        scan_ids = query.get("scan_id")
        db = database.SessionLocal()
        try:
            if scan_ids:
                try:
                    scan_id = int(scan_ids[0])
                except ValueError:
                    self._send_json(400, {"detail": "scan_id must be an integer"})
                    return
                scan = db.query(database.ScanResult).filter(database.ScanResult.id == scan_id).first()
                if scan is None:
                    self._send_json(404, {"detail": "Scan history entry not found"})
                    return
                db.delete(scan)
                deleted = 1
            else:
                deleted = db.query(database.ScanResult).delete(synchronize_session=False)

            db.commit()
            self._send_json(200, {"deleted": deleted})
        except Exception:
            db.rollback()
            self._send_json(500, {"detail": "Could not delete scan history"})
        finally:
            db.close()

    def _send_json(self, status, payload):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode("utf-8"))
