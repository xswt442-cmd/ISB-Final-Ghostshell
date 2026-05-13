import json
import struct
import uuid
from datetime import datetime, timezone


def pack(msg: dict) -> bytes:
    body = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    header = f"{len(body)}\n".encode("utf-8")
    return header + body


def unpack(data: bytes) -> dict:
    header_end = data.find(b"\n")
    if header_end == -1:
        raise ValueError("Incomplete header: no newline found")
    body_len = int(data[:header_end].decode("utf-8"))
    body = data[header_end + 1 : header_end + 1 + body_len]
    return json.loads(body.decode("utf-8"))


def send_msg(sock, msg: dict) -> None:
    sock.sendall(pack(msg))


def recv_msg(sock) -> dict:
    header = b""
    while b"\n" not in header:
        chunk = sock.recv(1)
        if not chunk:
            raise ConnectionError("Connection closed by peer")
        header += chunk
    body_len = int(header.decode("utf-8").strip())
    body = b""
    while len(body) < body_len:
        chunk = sock.recv(body_len - len(body))
        if not chunk:
            raise ConnectionError("Connection closed during body read")
        body += chunk
    return json.loads(body.decode("utf-8"))


def make_msg(msg_type: str, data: dict = None, ref_id: str = None) -> dict:
    return {
        "type": msg_type,
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ref_id": ref_id,
        "data": data or {},
    }
