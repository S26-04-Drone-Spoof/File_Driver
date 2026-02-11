"""dummy_writer.py

Generate synthetic scan files for testing the sender/receiver pipeline.

This script repeatedly creates a random NumPy array and saves it to
``./scans/scan_<n>.npy`` at approximately 10 Hz. It is intended for local
testing only — replace with your real data producer in production.
"""

import numpy as np
import os
import time

# Directory to write generated .npy scan files
OUTPUT_DIR = "./scans"
os.makedirs(OUTPUT_DIR, exist_ok=True)

scan_id = 0

# Continuously write random scan files. Each file is a (10000, 6) float32
# array saved in NumPy's .npy format. The loop prints the filename after
# successfully saving so other processes (like `sender.py`) can detect it.
while True:
    data = np.random.rand(10000, 6).astype(np.float32)
    filename = os.path.join(OUTPUT_DIR, f"scan_{scan_id}.npy")
    np.save(filename, data)
    print(f"Wrote {filename}")
    scan_id += 1
    time.sleep(0.1)  # 10 Hz
