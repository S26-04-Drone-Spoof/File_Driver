# sender.py
import os
import time
import socket

SOURCE_FOLDER = "./scans"
TARGET_IP = "127.0.0.1"
TARGET_PORT = 5000

# Ensure source folder exists so the watcher doesn't crash if folder is missing
os.makedirs(SOURCE_FOLDER, exist_ok=True)

def wait_until_complete(path):
    prev_size = -1
    while True:
        size = os.path.getsize(path)
        if size == prev_size:
            return
        prev_size = size
        time.sleep(0.05)

def send_file(path):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((TARGET_IP, TARGET_PORT))

        with open(path, "rb") as f:
            data = f.read()

        s.sendall(len(data).to_bytes(8, 'big'))
        s.sendall(data)

    print(f"Sent {path}")

sent_files = set()

while True:
    files = sorted([f for f in os.listdir(SOURCE_FOLDER) if f.endswith(".npy")])
    for file in files:
        full_path = os.path.join(SOURCE_FOLDER, file)
        if full_path not in sent_files:
            wait_until_complete(full_path)
            send_file(full_path)
            sent_files.add(full_path)
    time.sleep(0.05)
