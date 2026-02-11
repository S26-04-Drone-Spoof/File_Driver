# File_Driver

**Overview**
- **Purpose**: A simple file-transfer test pipeline that writes NumPy scan files locally, sends them over TCP to a receiver, and saves received files for later processing or validation.
- **Use case**: Local testing or sending scan files from a host to a remote receiver (e.g., a Raspberry Pi).

**Components**
- `dummy_writer.py`: Generates synthetic NumPy scan files into `./scans` for testing.
- `sender.py`: Watches `./scans` for `.npy` files, waits until each file stops growing, and transmits it to the configured receiver over TCP.
- `receiver.py`: TCP server that accepts connections, reads an 8-byte file-size header then the file bytes, and writes them into `./data/incoming`.
- `verify_transfer.py`: Helper utility that compares the latest file in `./scans` with the latest file in `./data/incoming` (size, SHA256, NumPy equality).

**Protocol (on-the-wire)**
- **Header**: 8-byte big-endian unsigned integer representing the file length in bytes.
- **Payload**: Raw bytes of the `.npy` file.

This simple protocol allows the receiver to know how many bytes to read for each incoming file.

**Prerequisites**
- **Python**: Python 3.8+ (the repo was developed and tested with Python 3.13 on the author machine).
- **Packages**: `numpy` (used by `dummy_writer.py` and `verify_transfer.py`).

**Quick Setup (Windows PowerShell)**
1. Confirm a working Python interpreter. If `python` isn't available, locate the installed interpreter with a full path (example shown below was valid on the developer machine):

```powershell
C:\Users\izzyb\AppData\Local\Programs\Python\Python313\python.exe --version
```

2. Recommended: create and activate a virtual environment from the project root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install numpy
```

3. If you cannot use a venv, install NumPy for your user:

```powershell
python -m pip install --user numpy
```

**Run Locally (single machine)**
- Edit `sender.py` and ensure `TARGET_IP = "127.0.0.1"` for local testing.
- Open three PowerShell windows (project root) and run:

Terminal 1 — start the receiver:
```powershell
python .\receiver.py
```

Terminal 2 — start the dummy writer:
```powershell
python .\dummy_writer.py
```

Terminal 3 — start the sender:
```powershell
python .\sender.py
```

Expected behaviour: `dummy_writer` writes files to `./scans`, `sender` detects and sends them, and `receiver` saves files to `./data/incoming`.

**Run Across Machines (host -> remote receiver)**
- On the receiver (remote machine) run `python receiver.py` and ensure port `5000` is reachable (firewall/router rules).
- On the sender machine set `TARGET_IP` in `sender.py` to the receiver's IP (for example `192.168.1.50`) and run `sender.py` and `dummy_writer.py` as above.

**Validate Transfers**
- Quick file listing (PowerShell):

```powershell
Get-ChildItem .\scans -Filter *.npy | Sort-Object LastWriteTime -Descending | Select-Object Name,Length,LastWriteTime -First 5
Get-ChildItem .\data\incoming -Filter *.npy | Sort-Object LastWriteTime -Descending | Select-Object Name,Length,LastWriteTime -First 5
```

- Compare SHA256 (PowerShell):

```powershell
Get-FileHash .\scans\scan_0.npy -Algorithm SHA256
Get-FileHash .\data\incoming\scan_1671234567890.npy -Algorithm SHA256
```

- Use the provided verifier (recommended):

```powershell
python .\verify_transfer.py            # compares latest in ./scans vs latest in ./data/incoming
python .\verify_transfer.py a.npy b.npy  # compare two specific files
```

**Troubleshooting**
- `FileNotFoundError: './scans'` from `sender.py`: the folder didn't exist — the repo now auto-creates `./scans` at startup.
- `ModuleNotFoundError: No module named 'numpy'`: install `numpy` in your active Python environment (see Setup section).
- `The term 'py' is not recognized`: your system may not have `py` in PATH — run Python with the full interpreter path or add Python to your PATH.
- `Connection refused` when sender connects: ensure `receiver.py` is running and that port `5000` is open and reachable from the sender.

**Recommended Improvements (optional)**
- Send original filenames as part of the transfer so the receiver can preserve names instead of using timestamps.
- Stream file data instead of reading whole file into memory for large files.
- Add checksums or application-level acknowledgements to ensure integrity and retries on failure.
- Harden the receiver to robustly read exactly 8 bytes for the header (in case of partial reads) and stream incoming data directly to disk to avoid large memory usage.

**Files in this repo**
- `dummy_writer.py` — synthetic data producer
- `sender.py` — file watcher + TCP sender
- `receiver.py` — TCP server that saves incoming files
- `verify_transfer.py` — helper to compare source vs received files
