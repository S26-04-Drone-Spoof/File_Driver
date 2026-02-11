# pi_receiver.py
import socket
import os
import threading
import time

HOST = "0.0.0.0"
PORT = 5000

BASE_DIR = "./data"
INCOMING = os.path.join(BASE_DIR, "incoming")
os.makedirs(INCOMING, exist_ok=True)

def handle_client(conn):
    try:
        size_bytes = conn.recv(8)
        if not size_bytes:
            return
        size = int.from_bytes(size_bytes, 'big')

        data = b''
        while len(data) < size:
            packet = conn.recv(8192)
            if not packet:
                break
            data += packet

        filename = f"scan_{int(time.time()*1000)}.npy"
        path = os.path.join(INCOMING, filename)

        with open(path, "wb") as f:
            f.write(data)

        print(f"Saved {filename}")

    finally:
        conn.close()

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print("Pi Receiver Listening...")

        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

if __name__ == "__main__":
    start_server()
