#!/usr/bin/env python3
"""verify_transfer.py

Utility to verify that a file written to ``./scans`` by the producer was
successfully received and saved in ``./data/incoming``.

This script prints file sizes, SHA256 hashes and compares NumPy array
contents (shape, dtype and element-wise equality). It is intended to help
validate transfers performed by ``sender.py`` and ``receiver.py``.

Usage:
    python verify_transfer.py             # compare latest from scans vs latest from incoming
    python verify_transfer.py a.npy b.npy # compare two specific files
"""
import sys
import os
import hashlib
from pathlib import Path

try:
    import numpy as np
except Exception as e:
    print("NumPy is required to run this script. Install with: pip install numpy")
    raise


def latest_file(folder):
    p = Path(folder)
    files = sorted(p.glob("*.npy"), key=lambda x: x.stat().st_mtime, reverse=True)
    return files[0] if files else None


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def compare_files(a_path, b_path):
    print(f"A: {a_path}")
    print(f"  size: {os.path.getsize(a_path)} bytes")
    print(f"  sha256: {sha256(a_path)}")
    print(f"B: {b_path}")
    print(f"  size: {os.path.getsize(b_path)} bytes")
    print(f"  sha256: {sha256(b_path)}")

    a = np.load(a_path)
    b = np.load(b_path)

    print(f"shape: {a.shape} vs {b.shape}")
    print(f"dtype: {a.dtype} vs {b.dtype}")

    if a.shape != b.shape or a.dtype != b.dtype:
        print("Result: DIFFER (shape or dtype mismatch)")
        return 2

    if np.array_equal(a, b):
        print("Result: MATCH (arrays are identical)")
        return 0

    # arrays differ — report summary
    try:
        diff = np.abs(a.astype(np.float64) - b.astype(np.float64))
        print(f"Result: DIFFER (max abs diff = {float(diff.max())})")
        print(f"allclose (rtol=1e-6, atol=1e-6): {np.allclose(a, b, rtol=1e-6, atol=1e-6)}")
    except Exception:
        print("Result: DIFFER (could not compute numeric diff)")
    return 1


def main(argv):
    if len(argv) == 3:
        a_path, b_path = argv[1], argv[2]
    else:
        a = latest_file("./scans")
        b = latest_file("./data/incoming")
        if not a or not b:
            print("Could not find files to compare. Ensure ./scans and ./data/incoming contain .npy files.")
            return 3
        a_path, b_path = str(a), str(b)

    return compare_files(a_path, b_path)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
