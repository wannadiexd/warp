# Warp
Send files between your PC and phone over Wi-Fi. No cables, no cloud, no accounts.

## How it works
Run the server on your PC, scan the QR code with your phone, and drop files from either side.

## Requirements
- Python 3.9+
- Both devices on the same Wi-Fi network

## Quick start
**Windows** - double-click `start.bat`

**macOS / Linux**
```bash
chmod +x start.sh
./start.sh
```

## Setup
```bash
git clone https://github.com/your-username/warp
cd warp
python app.py
```
A browser window opens automatically. On your phone scan the QR code shown on screen.

## Usage
**From PC -> Phone**
1. Open `http://localhost:645` in your browser
2. Drop files into the upload zone
3. Download them on your phone via the QR link

**From Phone -> PC**
1. Scan the QR code
2. Tap the upload zone and pick files
3. Files land in `~/Warp` on your PC

## File storage
All files are saved to `~/Warp` (`C:\Users\<you>\Warp` on Windows).  
They persist between sessions - stopping the server does not delete anything.