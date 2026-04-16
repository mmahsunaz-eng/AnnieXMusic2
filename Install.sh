#!/bin/bash

# Bersihin pip rusak
rm -rf /usr/local/lib/python3.12/site-packages/-wh-pip* || true

# Update pip (pakai python -m biar pasti kena env yang benar)
python3 -m pip install --upgrade pip

# Bersihin yt-dlp lama
pip uninstall yt-dlp -y || true
pip uninstall yt-dlp -y || true

# Install yt-dlp terbaru tanpa cache
pip install --no-cache-dir -U yt-dlp
