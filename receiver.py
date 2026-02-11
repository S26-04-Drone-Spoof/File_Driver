"""receiver.py

Simple TCP server that accepts a connection, reads an 8-byte big-endian
file-size header, then receives that many bytes and saves them as an
`.npy` file in ``./data/incoming``. Each incoming connection is handled in
its own thread so multiple senders can transfer files concurrently.
"""

import socket
import os
import threading
import time

# Bind address and port for the receiver. Use 0.0.0.0 to accept connections
# from any network interface (suitable for a Pi on a LAN).
HOST = "0.0.0.0"
PORT = 5000

BASE_DIR = "./data"
INCOMING = os.path.join(BASE_DIR, "incoming")
os.makedirs(INCOMING, exist_ok=True)


def handle_client(conn):
    """Handle a single client connection.

    Reads an 8-byte big-endian length prefix, then receives exactly that many
    bytes and writes them to a new file whose name contains the current
    timestamp (milliseconds). The connection is closed when finished.
    """
    try:
        size_bytes = conn.recv(8)
        if not size_bytes:
            return
        size = int.from_bytes(size_bytes, 'big')

        # Accumulate data until we've received *size* bytes.
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
    """Start the TCP server and accept incoming connections.

    Each accepted connection spawns a daemon thread that runs ``handle_client``.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print("Pi Receiver Listening...")

        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn,), daemon=True).start()


if __name__ == "__main__":
    start_server()
