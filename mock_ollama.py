import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = '0.0.0.0'
PORT = 11434

class Handler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, headers=None):
        self.send_response(status)
        if headers:
            for k, v in headers.items():
                self.send_header(k, v)
        self.end_headers()

    def do_GET(self):
        if self.path.startswith('/api/tags'):
            self._set_headers(200, {'Content-Type': 'application/json'})
            payload = {'models': [{'name': 'gemma3:latest', 'size': 123456789}],}
            self.wfile.write(json.dumps(payload).encode('utf-8'))
        elif self.path.startswith('/api/ps'):
            self._set_headers(200, {'Content-Type': 'application/json'})
            self.wfile.write(json.dumps([]).encode('utf-8'))
        else:
            self._set_headers(404)

    def do_POST(self):
        if self.path.startswith('/api/chat') or self.path.startswith('/api/generate'):
            # Read request body (not strictly required)
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length) if length else b''
            try:
                req = json.loads(body.decode('utf-8') or '{}')
            except Exception:
                req = {}

            # Stream a few JSON lines, alternating content and thinking
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()

            model = req.get('model', 'gemma3')
            stream = req.get('stream', False)
            think = req.get('think', False) or (req.get('options', {}) or {}).get('think', False)

            # Simulate streaming response
            for i in range(3):
                # send a visible delta
                item = { 'message': { 'content': f'visible chunk {i+1} from {model}' } }
                line = json.dumps(item) + '\n'
                self.wfile.write(line.encode('utf-8'))
                self.wfile.flush()
                time.sleep(0.2)

                # if thinking enabled, send an internal thought chunk
                if think:
                    thought = { 'message': { 'thinking': f'(~thinking~) internal thought {i+1}' } }
                    line = json.dumps(thought) + '\n'
                    self.wfile.write(line.encode('utf-8'))
                    self.wfile.flush()
                    time.sleep(0.15)

            # done
            done_line = json.dumps({'done': True}) + '\n'
            self.wfile.write(done_line.encode('utf-8'))
            self.wfile.flush()
        else:
            self._set_headers(404)

if __name__ == '__main__':
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Mock Ollama listening on {HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        print('Mock server stopped')
