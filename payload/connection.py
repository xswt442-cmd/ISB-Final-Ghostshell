import socket
import random


def connect_to_c2(host, port, timeout=30):
    sock = socket.create_connection((host, port), timeout=timeout)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 30)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
    return sock


def get_reconnect_delay(attempt_count, base=5, max_delay=120):
    delay = min(base * (2 ** attempt_count), max_delay)
    jitter = delay * 0.2 * (random.random() * 2 - 1)
    return delay + jitter
