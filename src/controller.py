import logging
from flask import Flask, request, jsonify

app = Flask(__name__)

# Flask-Logging minimieren für eine saubere CLI
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/api/receive_message', methods=['POST'])
def receive_message():
    data = request.json
    sender = data.get('sender', 'Unbekannt')
    text = data.get('text', '')
    
    # In einem echten Projekt mit GUI würde man dies per WebSocket an das Frontend senden.
    # Für unseren CLI-Test drucken wir es direkt aus.
    print(f"\n\n{'='*40}")
    print(f"NEUE NACHRICHT VON: {sender}")
    print(f"{text}")
    print(f"{'='*40}\n> ", end="")
    
    return jsonify({"status": "ok"}), 200

def run_flask_server(port):
    """Startet den Flask Server auf dem gewünschten Port."""
    app.run(host='127.0.0.1', port=port, use_reloader=False)