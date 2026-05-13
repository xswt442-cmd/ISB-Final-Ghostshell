import platform
import ctypes


def set_process_name(name: str):
    if platform.system() != "Linux":
        return
    try:
        libc = ctypes.CDLL("libc.so.6")
        PR_SET_NAME = 15
        libc.prctl(PR_SET_NAME, name.encode(), 0, 0, 0)
    except Exception:
        pass
