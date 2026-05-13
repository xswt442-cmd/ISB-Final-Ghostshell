import subprocess
import os
import signal


def execute(command, timeout=30):
    try:
        proc = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            preexec_fn=os.setsid,
            text=True,
        )
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            stdout, stderr = proc.communicate()
            return {
                "output": stdout or "",
                "error": f"Command timed out after {timeout}s\n{stderr or ''}",
                "exit_code": -1,
            }
        return {
            "output": stdout or "",
            "error": stderr or "",
            "exit_code": exit_code,
        }
    except Exception as e:
        return {
            "output": "",
            "error": str(e),
            "exit_code": -1,
        }
