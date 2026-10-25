"""Actual HTTP, HTTP CONNECT and SOCKS5 transfers through one mixed port."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import socket
import subprocess
import threading
import time

BODY = b"mixed-proxy-test\n" * 4096


class Origin(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Length", str(len(BODY)))
        self.end_headers()
        self.wfile.write(BODY)

    def log_message(self, *args):
        pass


origin = ThreadingHTTPServer(("127.0.0.1", 0), Origin)
threading.Thread(target=origin.serve_forever, daemon=True).start()
try:
    for port in (1080, 1081, 1082):
        deadline = time.monotonic() + 10
        while True:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=1):
                    break
            except ConnectionRefusedError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.1)
    url = f"http://127.0.0.1:{origin.server_port}/?q=" + "x" * 16384
    for mode, proxy, extra in (
        ("SOCKS5", "socks5h://127.0.0.1:1080", []),
        ("HTTP", "http://127.0.0.1:1082", []),
        ("HTTP CONNECT", "http://127.0.0.1:1082", ["--proxytunnel"]),
    ):
        result = subprocess.run(
            ["curl", "--silent", "--show-error", "--fail", "--noproxy", "",
             "--max-time", "10", "--proxy", proxy, *extra, url], capture_output=True,
        )
        if result.returncode or result.stdout != BODY:
            raise RuntimeError(f"{mode} transfer failed: {result.stderr.decode(errors='replace')[-500:]}")
        print(f"{mode}: split SOCKS5/HTTP ports, 16KB URL and 64KB+ body passed")
finally:
    origin.shutdown()
    origin.server_close()
