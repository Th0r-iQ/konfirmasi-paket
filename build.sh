#!/usr/bin/env bash
# Keluar otomatis jika ada perintah yang gagal
set -o errexit

echo "=== DOWNLOAD & EXTRACT ADB LINUX ==="
mkdir -p platform-tools
wget -O platform-tools.zip https://google.com
unzip -o platform-tools.zip

echo "=== INSTALL PYTHON REQUIREMENTS ==="
pip install -r requirements.txt
