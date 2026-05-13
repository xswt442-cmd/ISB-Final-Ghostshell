#!/usr/bin/env python3
"""Build script: run on Linux to compile payload ELF via PyInstaller."""
import subprocess
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SPEC_FILE = Path(__file__).resolve().parent / "payload.spec"
BUILD_TEMP = PROJECT_ROOT / "build" / "build_temp"
DIST_DIR = PROJECT_ROOT / "build" / "dist"


def clean():
    import shutil
    for d in [BUILD_TEMP, DIST_DIR]:
        if d.exists():
            shutil.rmtree(d)
    print("[*] Cleaned build artifacts.")


def build():
    clean()
    os.chdir(PROJECT_ROOT)
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        f"--workpath={BUILD_TEMP}",
        f"--distpath={DIST_DIR}",
        str(SPEC_FILE),
    ]
    print(f"[*] Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    output = DIST_DIR / "things.txt"
    if output.exists():
        size = output.stat().st_size
        print(f"[*] Build successful: {output} ({size:,} bytes)")
    else:
        print("[!] Build failed: output not found.")
        sys.exit(1)


def verify():
    output = DIST_DIR / "things.txt"
    if not output.exists():
        print("[!] things.txt not found. Run build first.")
        sys.exit(1)
    result = subprocess.run(["file", str(output)], capture_output=True, text=True)
    print(result.stdout.strip())
    if "ELF" not in result.stdout:
        print("[!] Warning: output does not appear to be an ELF file.")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Build Ghostshell payload")
    parser.add_argument("--verify", action="store_true", help="Verify output file type")
    parser.add_argument("--clean-only", action="store_true", help="Only clean build artifacts")
    args = parser.parse_args()

    if args.clean_only:
        clean()
    else:
        build()
        if args.verify:
            verify()


if __name__ == "__main__":
    main()
