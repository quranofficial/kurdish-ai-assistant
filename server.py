import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import urllib.request
import urllib.error

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "8080"))
API_KEY = os.environ.get("GEMINI_API_KEY", "")
MODEL = "gemini-3.5-flash"


class AssistantHandler(BaseHTTPRequestHandler):
    def send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self.send_json(200, {"ok": True, "service": "Kurdish AI Assistant"})
        else:
            self.send_json(404, {"error": "Not found"})

    def do_POST(self):
        if self.path != "/chat":
            self.send_json(404, {"error": "Not found"})
            return

        if not API_KEY:
            self.send_json(500, {"error": "GEMINI_API_KEY is not configured"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 20000:
                self.send_json(400, {"error": "Invalid request size"})
                return

            data = json.loads(self.rfile.read(length).decode("utf-8"))
            message = str(data.get("message", "")).strip()

            if not message or len(message) > 5000:
                self.send_json(400, {"error": "Enter a message"})
                return

            prompt = (
                "تۆ یاریدەدەری زیرەکی بە ناوی سڵاو یاریدەدەری. "
                "بە زمانی کوردی سۆرانی، بە شێوەیەکی ڕوون و ڕێزدارانە "
                "وەڵامی بەکارهێنەر بدەرەوە. ئەگەر پرسیارەکە بە زمانێکی "
                "تر بوو، هەوڵ بدە بە کوردی سۆرانی وەڵام بدەیتەوە.\n\n"
                "پرسیاری بەکارهێنەر: " + message
            )

            payload = json.dumps({
                "contents": [{
                    "parts": [{"text": prompt}]
                }]
            }).encode("utf-8")

            request = urllib.request.Request(
                "https://generativelanguage.googleapis.com/v1beta/models/"
                + MODEL + ":generateContent",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": API_KEY
                },
                method="POST"
            )

            with urllib.request.urlopen(request, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))

            candidates = result.get("candidates", [])
            if not candidates:
                self.send_json(502, {"error": "AI did not return an answer"})
                return

            parts = candidates[0].get("content", {}).get("parts", [])
            answer = "".join(
                part.get("text", "") for part in parts
            ).strip()

            self.send_json(200, {"answer": answer})

        except urllib.error.HTTPError as error:
            self.send_json(502, {
                "error": "Gemini API request failed",
                "status": error.code
            })
        except Exception:
            self.send_json(500, {"error": "Internal server error"})


if __name__ == "__main__":
    print("Kurdish AI Assistant server starting...")
    HTTPServer((HOST, PORT), AssistantHandler).serve_forever()
