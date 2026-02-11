# dummy_writer.py
import numpy as np
import os
import time

OUTPUT_DIR = "./scans"
os.makedirs(OUTPUT_DIR, exist_ok=True)

scan_id = 0

while True:
    data = np.random.rand(10000, 6).astype(np.float32)
    filename = os.path.join(OUTPUT_DIR, f"scan_{scan_id}.npy")
    np.save(filename, data)
    print(f"Wrote {filename}")
    scan_id += 1
    time.sleep(0.1)  # 10 Hz
