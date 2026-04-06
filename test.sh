#!/bin/bash

echo "================================================="
echo "Start Aether P2P Test (2 Clients)..."
echo "================================================="

docker compose -f docker-compose.test.yml up -d --build

echo "[*] Waiting for Frontend-Server..."
sleep 4

echo "[*] Open Browser..."

URL1="http://localhost:5173"
URL2="http://localhost:5174"

if which open > /dev/null; then
    # macOS
    open $URL1
    open $URL2
elif which xdg-open > /dev/null; then
    # Linux
    xdg-open $URL1
    xdg-open $URL2
elif which start > /dev/null; then
    # Windows (Git Bash / WSL)
    start $URL1
    start $URL2
else
    # Fallback
    echo "[!] Browser could't be opened"
    echo "Please open manually: $URL1 and $URL2"
fi

echo "================================================="
echo "Test Environment is running in background"
echo "to end test type and execute: docker compose -f docker-compose.test.yml down"
echo "================================================="