import subprocess
import os


def install(executable_path, interval_minutes=5):
    try:
        # Read current crontab
        result = subprocess.run(
            ["crontab", "-l"], capture_output=True, text=True
        )
        current = result.stdout if result.returncode == 0 else ""

        # Check if already installed
        if executable_path in current:
            return {"status": "ok", "message": "already installed"}

        # Append new entry
        new_entry = f"*/{interval_minutes} * * * * {executable_path} --daemon 2>/dev/null\n"
        new_crontab = current.rstrip("\n") + "\n" + new_entry if current.strip() else new_entry

        subprocess.run(["crontab", "-"], input=new_crontab, text=True, check=True)
        return {"status": "ok", "message": f"installed (interval={interval_minutes} min)"}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"crontab failed: {e.stderr or e}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def remove(executable_path):
    try:
        result = subprocess.run(
            ["crontab", "-l"], capture_output=True, text=True
        )
        if result.returncode != 0:
            return {"status": "ok", "message": "no crontab to remove"}

        lines = [line for line in result.stdout.splitlines()
                 if executable_path not in line]
        new_crontab = "\n".join(lines) + "\n" if lines else ""

        subprocess.run(["crontab", "-"], input=new_crontab, text=True, check=True)
        return {"status": "ok", "message": "removed"}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"crontab failed: {e.stderr or e}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def is_installed(executable_path):
    try:
        result = subprocess.run(
            ["crontab", "-l"], capture_output=True, text=True
        )
        return executable_path in result.stdout
    except Exception:
        return False
