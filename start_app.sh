if [ ! -d "aether_data" ]; then
    echo "[*] Init local backup folder..."
    mkdir -p aether_data
    chmod 777 aether_data 2>/dev/null || true
fi

# check backend status
BACKEND_RUNNING=$(docker ps -q -f name=aether-backend)

if [ -z "$BACKEND_RUNNING" ]; then
    echo "[*] Backend inactive. Start Tor-Node..."
    docker compose up -d aether-backend
else
    echo "[*] Tor-Backend running"
fi

# Frontend start
echo "[*] Start UI-Server..."
docker compose up -d aether-frontend

echo "[*] Waiting for frontend..."
while ! curl -s http://localhost:5173 > /dev/null; do
    sleep 1
done
echo "[*] Frontend-Server ist online!"

echo "[*] Start Electron Desktop App..."

cd src-frontend

FRONTEND_URL="http://localhost:5173" AETHER_API_PORT=5000 npm run dev:electron &
ELECTRON_PID=$!

cd - > /dev/null

# Graceful Shutdown
trap "echo -e '\n[*] Schließe App...'; kill $ELECTRON_PID 2>/dev/null; docker compose stop aether-frontend; exit 0" INT TERM
wait