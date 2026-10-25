"""Transfer HTTP and HTTPS pages through the real HTTP and SOCKS5 listeners."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import socket
import ssl
import tempfile
import subprocess
import threading
import time

BODY = b"proxy-transfer-test\n" * 4096


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
    for port in (1080, 1082):
        deadline = time.monotonic() + 10
        while True:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=1):
                    break
            except ConnectionRefusedError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.1)
    with tempfile.TemporaryDirectory() as directory:
        cert, key = f"{directory}/cert.pem", f"{directory}/key.pem"
        subprocess.run(
            ["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1",
             "-subj", "/CN=localhost", "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1",
             "-keyout", key, "-out", cert],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, key)
        secure_origin = ThreadingHTTPServer(("127.0.0.1", 0), Origin)
        secure_origin.socket = context.wrap_socket(secure_origin.socket, server_side=True)
        threading.Thread(target=secure_origin.serve_forever, daemon=True).start()
        try:
            for scheme, server in (("http", origin), ("https", secure_origin)):
                for host in ("127.0.0.1", "localhost"):
                    url = f"{scheme}://{host}:{server.server_port}/?q=" + "x" * 16384
                    for mode, proxy, extra in (
                        ("SOCKS5", "socks5h://127.0.0.1:1080", []),
                        ("HTTP", "http://127.0.0.1:1082", []),
                        ("HTTP CONNECT", "http://127.0.0.1:1082", ["--proxytunnel"]),
                    ):
                        result = subprocess.run(
                            ["curl", "--silent", "--show-error", "--fail", "--noproxy", "",
                             "--max-time", "10", "--cacert", cert, "--proxy", proxy, *extra, url],
                            capture_output=True,
                        )
                        if result.returncode or result.stdout != BODY:
                            raise RuntimeError(
                                f"{mode} {scheme} {host} transfer failed: "
                                f"{result.stderr.decode(errors='replace')[-500:]}"
                            )
                        print(f"{mode} {scheme} {host}: 16KB URL and 64KB+ body passed")
        finally:
            secure_origin.shutdown()
            secure_origin.server_close()
finally:
    origin.shutdown()
    origin.server_close()
