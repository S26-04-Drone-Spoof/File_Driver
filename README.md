# File_Driver

**Overview**
- **Purpose**: A simple file-transfer test pipeline that writes NumPy scan files locally, sends them over TCP to a receiver, and saves received files for later processing or validation
- **Use case**: Local testing or sending scan files from a host to a remote receiver (Raspberry Pi)

**Components**
- `dummy_writer.py`: Generates synthetic NumPy scan files into `./scans` for testing.
- `sender.py`: Watches `./scans` for `.npz` files, waits until each file stops growing, and transmits it to the configured receiver over TCP.
- `receiver.py`: TCP server that accepts connections, reads an 8-byte file-size header then the file bytes, and writes them into `./data/incoming`.
- `verify_transfer.py`: Helper utility that compares the latest file in `./scans` with the latest file in `./data/incoming` (size, SHA256, NumPy equality).

**Raspberry Pi Components:**
- `receiver_pi.py`: Listens for file send requests over the local network and pulls files into a temporary folder
- `sender_pi.py`: Scans folder specified by the receiver_pi script and sends all files over the network once found, deleting the files locally after to save space.
- `receiver.service/sender.service`: Linux services to automatically start/restart receiver_pi.py and sender_pi.py respectively

**Protocol (on-the-wire)**
- **Header**: 8-byte big-endian unsigned integer representing the file length in bytes.
- **Payload**: Raw bytes of the `.npz` file.

This simple protocol allows the receiver to know how many bytes to read for each incoming file.

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

**Test Locally (single machine)**
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
Get-ChildItem .\scans -Filter *.npz | Sort-Object LastWriteTime -Descending | Select-Object Name,Length,LastWriteTime -First 5
Get-ChildItem .\data\incoming -Filter *.npz | Sort-Object LastWriteTime -Descending | Select-Object Name,Length,LastWriteTime -First 5
```

- Compare SHA256 (PowerShell):

```powershell
Get-FileHash .\scans\scan_0.npz -Algorithm SHA256
Get-FileHash .\data\incoming\scan_1671234567890.npz -Algorithm SHA256
```

- Use the provided verifier (recommended):

```powershell
python .\verify_transfer.py            # compares latest in ./scans vs latest in ./data/incoming
python .\verify_transfer.py a.npz b.npz  # compare two specific files
```
**Raspberry Pi HIL Configuration/Setup**

*Definitions:*

Simulation Machine: Machine generating simulated LiDAR data to be sent to the ML Machine

Raspberry Pi: Raspberry Pi SBC in the loop intercepting receive requests from Simulation Machine and retransmitting data to ML Machine

ML Machine: End device that receives simulated LiDAR data

*Setup:*

1. Install preferred Linux OS on the Raspberry Pi.
*Note: For this example we are using **Raspberry Pi OS Lite** for the pre-installed drivers and the ease of use*

2. Clone repository into preferred installation folder for all devices
  
3. Configure Services on the Raspberry Pi:
```powershell
sudo vim sender.service
sudo vim receiver.service
```
- Propagate "User=" and "WorkingDirectory=" lines with the username and working directory of your install for both services
- Move service files to /etc/systemd/system/
- Run the following to update systemd with the new services:
```powershell
sudo systemctl daemon-reload
```

4. Configure Static IPs (Linux):
- Do the following for all networked devices:
```powershell
sudo nmtui
```
- Find the eth0 connection and select Edit
- Change IPv4 Configuration to Manual
- Set Address to the desired static IPv4 address for that machine
- Set DNS Servers to 8.8.8.8 (or desired DNS server)
- Select Ok and then navigate back to command line
Example:
<img width="528" height="438" alt="image" src="https://github.com/user-attachments/assets/fd023f50-ecd3-4a42-a473-f9cd6085790f" />

*Note: If using Windows for any devices, simply navigate to Settings->Network and Internet->Ethernet->IP Assignment and set IP assignment to Manual, Select IPv4 and fill fields as necessary.*

5. Configure Scripts:
- (Raspberry Pi) Edit receiver_pi.py to set the PORT for all send requests from the Simulation Machine and the desired folder to save files
- (Simulation Machine) Edit sender.py to set the TARGET_IP and PORT to the Raspberry Pi's Static IPv4 Address and Port, as well as the desired folder to pull files from
- (ML Machine) Edit receiver.py to set the PORT for all send requests from the Raspberry Pi and the desired folder to save files
- (Raspberry Pi) Edit sender_pi.py to set the TARGET_IP and PORT to the ML Machine's Static IPv4 Address and Port, as well as the folder where files are saved

6. Start Services:
- Run the following to start the linux services:
```powershell
sudo systemctl start sender.service
sudo systemctl start receiver.service
```

7. Testing Installation
- (Simulation Machine) Generate .npz data using simulation or pre-existing dataset and store in sender.py's specified data folder
- (ML Machine) Start receiver.py using
```powershell
python3 .\receiver.py
```
- (Simulation Machine) Start sender.py using
```powershell
python3 .\sender.py
```
- (ML Machine) Verify transferred files are accurate and able to be loaded into the neural network

**Troubleshooting**
- `FileNotFoundError: './scans'` from `sender.py`: the folder didn't exist — the repo now auto-creates `./scans` at startup.
- `ModuleNotFoundError: No module named 'numpy'`: install `numpy` in your active Python environment (see Setup section).
- `The term 'py' is not recognized`: your system may not have `py` in PATH — run Python with the full interpreter path or add Python to your PATH.
- `Connection refused` when sender connects: ensure `receiver.py` is running and that port `5000` is open and reachable from the sender. (This may require lowering the firewall on Windows machines)

**Recommended Improvements (optional)**
- Send original filenames as part of the transfer so the receiver can preserve names instead of using timestamps.
- Stream file data instead of reading whole file into memory for large files.
- Add checksums or application-level acknowledgements to ensure integrity and retries on failure.
- Harden the receiver to robustly read exactly 8 bytes for the header (in case of partial reads) and stream incoming data directly to disk to avoid large memory usage.
