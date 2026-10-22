"""Servidor para testar o GiroCerto na própria máquina, sem AWS.

Faz o papel do API Gateway (/api/* chama o handler da Lambda crud) e do
bucket S3 (serve a pasta web/). Uso:

    DB_HOST=127.0.0.1 DB_USER=$(whoami) DB_PASSWORD=x DB_SSL=off python3 scripts/servidor_local.py

Depois abra http://localhost:8765/app.html
"""

import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl, urlsplit

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "backend", "crud"))
import app  # noqa: E402

PORTA = int(os.environ.get("PORTA", "8765"))


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(REPO, "web"), **kwargs)

    def _api(self):
        url = urlsplit(self.path)
        if url.path == "/config.js":
            corpo = f'window.GIROCERTO_CONFIG = {{ apiUrl: "http://localhost:{PORTA}/api" }};'.encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript")
            self.end_headers()
            self.wfile.write(corpo)
            return True
        if not url.path.startswith("/api/"):
            return False
        tamanho = int(self.headers.get("Content-Length") or 0)
        evento = {
            "httpMethod": self.command,
            "path": url.path[4:],
            "pathParameters": {"proxy": url.path[5:]},
            "queryStringParameters": dict(parse_qsl(url.query)) or None,
            "body": self.rfile.read(tamanho).decode() if tamanho else None,
        }
        resp = app.handler(evento, None)
        self.send_response(resp["statusCode"])
        for chave, valor in resp["headers"].items():
            self.send_header(chave, valor)
        self.end_headers()
        self.wfile.write(resp["body"].encode())
        return True

    def end_headers(self):
        # Sem cache, para o navegador pegar na hora as mudanças em web/
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_GET(self):
        if not self._api():
            super().do_GET()

    do_POST = do_PUT = do_DELETE = do_OPTIONS = _api


if __name__ == "__main__":
    print(f"GiroCerto local em http://localhost:{PORTA}/app.html (Ctrl+C para parar)")
    ThreadingHTTPServer(("127.0.0.1", PORTA), Handler).serve_forever()
