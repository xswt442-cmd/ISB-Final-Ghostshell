import os
import base64


def receive_file(path, content_b64):
    try:
        content = base64.b64decode(content_b64)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)
        return {"status": "ok", "path": path, "size": len(content)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def send_file(path):
    try:
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            return {"status": "error", "message": f"File not found: {path}"}
        if not os.path.isfile(path):
            return {"status": "error", "message": f"Not a regular file: {path}"}
        with open(path, "rb") as f:
            content = f.read()
        content_b64 = base64.b64encode(content).decode()
        return {"status": "ok", "path": path, "content": content_b64, "size": len(content)}
    except Exception as e:
        return {"status": "error", "message": str(e)}
