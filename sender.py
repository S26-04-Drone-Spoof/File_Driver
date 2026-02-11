"""sender.py

Watch a folder for NumPy scan files and transmit them over TCP to a
receiver. For each detected ``.npy`` file this script:

- waits until the file stops growing (to avoid sending partial writes),
- opens a TCP connection to ``TARGET_IP:TARGET_PORT``,
- sends an 8-byte big-endian file-size header followed by the raw file bytes.

This is a minimal sender implementation intended for testing and small
transfers. It keeps an in-memory set of already-sent file paths to avoid
re-sending the same file during a run.
"""

import os
import time
import socket

# Folder to watch for .npy files
SOURCE_FOLDER = "./scans"
# Default target (use 127.0.0.1 for local testing). Change to the receiver's
# IP when sending to another machine (e.g., a Raspberry Pi).
TARGET_IP = "127.0.0.1"
TARGET_PORT = 5000

# Ensure the folder exists so os.listdir() won't raise if the directory is
# missing when the script starts.
os.makedirs(SOURCE_FOLDER, exist_ok=True)


def wait_until_complete(path):
    """Block until the file at *path* stops changing size.

    This checks the file size repeatedly and returns once two consecutive
    checks yield the same size (with a short sleep between checks).
    """
    prev_size = -1
    while True:
        size = os.path.getsize(path)
        if size == prev_size:
            return
        prev_size = size
        time.sleep(0.05)


def send_file(path):
    """Send the entire file at *path* to the configured target.

    Protocol: send 8-byte big-endian length, then the file bytes.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((TARGET_IP, TARGET_PORT))

        with open(path, "rb") as f:
            data = f.read()

        # Send file length, then data.
        s.sendall(len(data).to_bytes(8, 'big'))
        s.sendall(data)

    print(f"Sent {path}")


sent_files = set()

# Main loop: poll the source folder for new .npy files, and send any that
# haven't been sent yet. The sleep at the end keeps CPU usage reasonable.
while True:
    files = sorted([f for f in os.listdir(SOURCE_FOLDER) if f.endswith(".npy")])
    for file in files:
        full_path = os.path.join(SOURCE_FOLDER, file)
        if full_path not in sent_files:
            wait_until_complete(full_path)
            send_file(full_path)
            sent_files.add(full_path)
    time.sleep(0.05)
