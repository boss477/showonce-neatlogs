"""Loopback-only control room backed by executed repair results."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from .repair_demo import run_repair

PAGE = Path(__file__).resolve().parents[1] / "ui" / "control.html"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/":
            self.send_error(404); return
        data = PAGE.read_bytes()
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers(); self.wfile.write(data)

    def do_POST(self):
        if self.path != "/run":
            self.send_error(404); return
        if self.headers.get("Origin") not in (None, "http://127.0.0.1:8765", "http://localhost:8765"):
            self.send_error(403); return
        result = run_repair()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(json.dumps(result).encode())

if __name__ == "__main__":
    print("Control room: http://127.0.0.1:8765")
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
