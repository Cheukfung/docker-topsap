"""Verify the real UDS framing contract without requiring VPN credentials."""
import importlib.util
import json
from pathlib import Path
import socket
import tempfile
import threading
import unittest

spec = importlib.util.spec_from_file_location("topsap", Path(__file__).parents[1] / "topsap.py")
topsap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(topsap)


class ControlTransportTest(unittest.TestCase):
    def test_half_close_and_fragmented_response(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "test.sock")
            captured = []
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
                server.bind(path)
                server.listen(1)

                def receive():
                    with server.accept()[0] as connection:
                        connection.settimeout(3)
                        chunks = []
                        while chunk := connection.recv(64):
                            chunks.append(chunk)
                        captured.append(json.loads(b"".join(chunks)))
                        connection.sendall(b'{"err_code":')
                        connection.sendall(b'0,"value":"ok"}')

                worker = threading.Thread(target=receive)
                worker.start()
                result = topsap.request({"method": "test", "user": "a+b=", "label": "中文"}, path)
                worker.join(timeout=5)
                self.assertFalse(worker.is_alive())
                self.assertEqual(result, {"err_code": 0, "value": "ok"})
                self.assertEqual(captured, [{"method": "test", "user": "a%2Bb=", "label": "中文"}])


if __name__ == "__main__":
    unittest.main()
