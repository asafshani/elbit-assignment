from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
import ssl
import os

class HolidayHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/holidays" or self.path == "/":
            try:
                holidays = self.get_holidays()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(holidays, indent=2, ensure_ascii=False).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                error = {"error": str(e)}
                self.wfile.write(json.dumps(error).encode("utf-8"))
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode("utf-8"))
        else:
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Not found"}).encode("utf-8"))

    def get_holidays(self):
        today = datetime.now()
        end_date = today + timedelta(days=90)

        params = urllib.parse.urlencode({
            "v": "1",
            "cfg": "json",
            "maj": "on",
            "min": "on",
            "start": today.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
            "i": "off",
            "lg": "s"
        })

        url = f"https://www.hebcal.com/hebcal?{params}"

        ctx = ssl.create_default_context()
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "ElbitAssignment/1.0")

        with urllib.request.urlopen(req, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        holidays = []
        for item in data.get("items", []):
            if item.get("category") in ["holiday", "roshchodesh"]:
                holidays.append({
                    "name": item.get("title", ""),
                    "hebrew": item.get("hebrew", ""),
                    "date": item.get("date", ""),
                    "category": item.get("category", "")
                })

        return {
            "description": "Jewish holidays for the upcoming quarter",
            "period": {
                "from": today.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d")
            },
            "total_holidays": len(holidays),
            "holidays": holidays
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HolidayHandler)
    print(f"Server running on port {port}")
    server.serve_forever()