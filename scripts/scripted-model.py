"""Starts toskar-sdks' scripted model (an OpenAI-compatible server that
answers "You said: <message>") and points a Toskar at it, so a test needs
no model download. Asked for JSON, as Toskar asks for an answer that fits a
schema, it answers {"labels": ["bug"]}.

    python3 scripts/scripted-model.py <toskar-sdks/conformance> <port> <toskar url>
"""

import io
import json
import sys
import threading
import urllib.request
from http.server import ThreadingHTTPServer

sys.path.insert(0, sys.argv[1])
import run  # noqa: E402

class Model(run.ScriptedModel):
    """The scripted model, answering a request for JSON with labels."""

    def do_POST(self) -> None:
        raw = self.rfile.read(int(self.headers["Content-Length"]))
        req = json.loads(raw)
        if not any("Reply with only JSON" in str(m.get("content")) for m in req.get("messages", [])):
            self.rfile = io.BytesIO(raw)
            return super().do_POST()
        text = '{"labels": ["bug"]}'
        if not req.get("stream"):
            message = {"role": "assistant", "content": text}
            return self._json({"id": "c", "object": "chat.completion", "created": 0, "model": "echo",
                               "choices": [{"index": 0, "message": message, "finish_reason": "stop"}]})
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        self._chunk({"delta": {"content": text}, "finish_reason": None})
        self._chunk({"delta": {}, "finish_reason": "stop"})
        self.wfile.write(b"data: [DONE]\n\n")


port, toskar = int(sys.argv[2]), sys.argv[3]
server = ThreadingHTTPServer(("127.0.0.1", port), Model)
# Serving before Toskar is told, so its first look at the model list finds it.
serving = threading.Thread(target=server.serve_forever, daemon=True)
serving.start()
body = json.dumps({"base_url": f"http://127.0.0.1:{port}/v1"}).encode()
req = urllib.request.Request(toskar + "/api/v1/external-server", data=body, method="PUT", headers={"Content-Type": "application/json"})
urllib.request.urlopen(req, timeout=30).read()
serving.join()
