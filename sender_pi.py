"""
sender.py

Continuously watch a folder for newly created NumPy files and transmit each
one over TCP as soon as it appears and finishes writing.

Protocol:
- Wait for a new .npz file to appear.
- Wait until the file stops growing.
- Send an 8‑byte big‑endian size header followed by the raw file bytes.
- Delete the file after successful transmission.
"""

import os
import time
import socket

SOURCE_FOLDER = "./data/incoming"
TARGET_IP = "192.168.1.52"
TARGET_PORT = 6000

os.makedirs(SOURCE_FOLDER, exist_ok=True)


def wait_until_complete(path):
    """Block until the file at *path* stops changing size."""
    prev_size = -1
    while True:
        try:
            size = os.path.getsize(path)
        except FileNotFoundError:
            time.sleep(0.05)
            continue

        if size == prev_size:
            return
        prev_size = size
        time.sleep(0.05)


def send_file(path):
    """Send the file using the 8‑byte length header protocol."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((TARGET_IP, TARGET_PORT))

        with open(path, "rb") as f:
            data = f.read()

        s.sendall(len(data).to_bytes(8, "big"))
        s.sendall(data)

    print(f"Sent {path}")


def main():
    print("Watching for new files...")

    seen = set(os.listdir(SOURCE_FOLDER))

    while True:
        current = set(os.listdir(SOURCE_FOLDER))
        new_files = [f for f in (current - seen) if f.endswith(".npz")]

        if new_files:
            for fname in sorted(new_files):
                full_path = os.path.join(SOURCE_FOLDER, fname)
                print(f"Detected new file: {fname}")

                wait_until_complete(full_path)
                send_file(full_path)

                # Delete after sending
                try:
                    os.remove(full_path)
                    print(f"Deleted {fname}")
                except FileNotFoundError:
                    print(f"Warning: {fname} disappeared before deletion.")
                except Exception as e:
                    print(f"Error deleting {fname}: {e}")

        seen = current
        time.sleep(0.05)


if __name__ == "__main__":
    main()