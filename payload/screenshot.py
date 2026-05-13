import base64


def capture_base64():
    try:
        import mss
        import mss.tools
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            img = sct.grab(monitor)
            png_bytes = mss.tools.to_png(img.rgb, img.size)
        b64_str = base64.b64encode(png_bytes).decode()
        return {"status": "ok", "image": b64_str, "format": "png"}
    except ImportError as e:
        return {"status": "error", "message": f"mss not available: {e}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
