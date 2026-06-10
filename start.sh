#!/bin/bash
echo "Starting Warp..."
python3 app.py 2>/dev/null || python app.py
