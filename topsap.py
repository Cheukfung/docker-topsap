"""Headless password login for the official TopSAP 3.6.3.31.2.22375 amd64 SDK.

Request fields and RSA encoding follow the package's sv_init.js. The native
sv_websrv reads a JSON request through EOF and returns one callback, then closes.
"""

import base64
import json
import os
from pathlib import Path
import socket
import sys
import time
from urllib.parse import quote, urlsplit

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding

SOCKET_PATH = "/tmp/TopSAP_ELE/topsap.sock"
PUBLIC_KEY = b"""-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCq0GDTn2LRnHkCceiKG7cLo5V/JH5Q0huwbLMAkVa2GzbwD7W5X7hmOVrT5xtju74k+J8/ltvhlS6vGNqew6RAU52M/t5+uWJ+RkRuS0yhhw58SsZaxybpgwkjFopHDc8Z7lsweVhzNSdsKoDZnZLQR9fXIw7oTamg+Ifz+BIeYwIDAQAB
-----END PUBLIC KEY-----"""


def request(payload, socket_path=SOCKET_PATH):
    data = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).replace("+", "%2B").encode()
    # sv_websrv's input buffer holds 4095 bytes; never submit a truncated command.
    if len(data) > 4095:
        raise ValueError("TopSAP control request exceeds the SDK's 4095-byte input buffer")
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(70)
        client.connect(socket_path)
        client.sendall(data)
        client.shutdown(socket.SHUT_WR)
        chunks = []
        while chunk := client.recv(65536):
            chunks.append(chunk)
    return json.loads(b"".join(chunks))


def checked_request(payload):
    reply = request(payload)
    code = reply["err_code"]
    if int(code) != 0:
        raise RuntimeError(f"TopSAP {payload['method']} failed: err_code={code}")
    return reply


def login():
    address = urlsplit("https://" + os.environ["SERVER_ADDRESS"])
    if not address.hostname or address.path or address.query or address.fragment or address.username:
        raise ValueError("SERVER_ADDRESS must be a hostname or IP with optional :port, without https:// or path")
    host, port = address.hostname, str(address.port or 443)
    user = quote(base64.b64encode(os.environ["USER_NAME"].encode()).decode(), safe="")
    key = serialization.load_pem_public_key(PUBLIC_KEY)
    password = base64.b64encode(key.encrypt(os.environ["PASSWORD"].encode(), padding.PKCS1v15())).decode()
    proxy = {"type": "0", "addr": "", "port": "", "user": "", "pwd": "", "domain": ""}
    request({"method": "client_system_config", "addr": host})
    auth = checked_request({
        "method": "get_auth_param", "serverAddr": host, "serverPort": port,
        "proxyType": "0", "proxyAddr": "", "proxyPort": "", "proxyUser": "",
        "proxyPwd": "", "proxyDomain": "", "user": user, "pwd": password, "_flag": 1,
    })
    if auth.get("gid") == "on" or auth.get("login_check_verify") == "on":
        raise RuntimeError("Gateway requires a graphical verification code; this image supports password-only login")
    # These defaults match getAuthParamSuccess in the official sv_init.js.
    protocol = auth.get("auth_protocol") or "0"
    checked_request({
        "method": "login_by_pwd",
        "vone": {"addr": host, "port": port, "user": user, "pwd": password, "_flag": 1},
        "proxy": proxy, "vpn_version": auth.get("vpn_version") or "sm2",
        "auth_protocol": protocol,
        "auth_port": port if str(protocol) == "0" else auth.get("auth_port") or "443",
        "data_port": port if str(protocol) == "0" else auth.get("data_port") or "443",
        "data_protocol": auth.get("data_protocol") or "0", "cert_type": auth.get("cert_type") or "0",
        "remember_pwd": "off", "auto_login": "off",
    })
    checked_request({"method": "get_config_info"})
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        status = request({"method": "query_statistics"})
        code = int(status["terr_code"])
        if code not in (0, -85, 85):
            raise RuntimeError(f"TopSAP tunnel failed: terr_code={code}")
        if int(status["tstate_id"]) in (6, 16) and Path("/sys/class/net/tun0").exists():
            print("TopSAP authenticated; tun0 is ready", flush=True)
            return
        time.sleep(1)
    raise TimeoutError("TopSAP did not establish tun0 within 60 seconds")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "probe":
        result = request({"method": "client_system_config", "addr": ""})
        if not isinstance(result, dict):
            raise RuntimeError("TopSAP returned an invalid configuration response")
        print("TopSAP native SDK answered client_system_config")
    elif len(sys.argv) == 1:
        login()
    else:
        raise SystemExit("Usage: python3 topsap.py [probe]")
