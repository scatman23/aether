#!/bin/bash

echo "================================================="
echo "Start Aether P2P Test (2 Clients)..."
echo "================================================="

docker compose -f docker-compose.test.yml up -d --build

echo "[*] Waiting for Frontend-Servers to boot..."
# wait till Vite returns a code on port 5173
while ! curl -s http://localhost:5173 > /dev/null; do
    echo "    ... waiting for Client 1 (5173)"
    sleep 1
done

# wait till Vite returns a code on port 5174
while ! curl -s http://localhost:5174 > /dev/null; do
    echo "    ... waiting for Client 2 (5174)"
    sleep 1
done

echo "[*] Starting Electron Desktop Clients..."

cd src-frontend

# client 1
FRONTEND_URL="http://localhost:5173" AETHER_API_PORT=5000 npm run dev:electron &
ELECTRON_PID1=$!

# client 2
FRONTEND_URL="http://localhost:5174" AETHER_API_PORT=5001 npm run dev:electron &
ELECTRON_PID2=$!

cd - > /dev/null

echo "--- Linting Score ---"
pylint src/ --rcfile=src/.pylintrc | grep "Your code has been rated"

echo "================================================="
echo "Test Environment is running in background"
echo "To end docker test environment type: docker compose -f docker-compose.test.yml down"
echo "================================================="

# Clean-Up
trap "kill $ELECTRON_PID1 $ELECTRON_PID2 2>/dev/null; exit" INT TERM
wait