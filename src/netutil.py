import requests
from stem.control import Controller


class NetworkUtility:
    def __init__(self, tor_control_port=9051, tor_socks_port=9050):
        self.control_port = tor_control_port
        self.socks_port = tor_socks_port

        # SOCKS5 Session für ausgehende Requests
        self.session = requests.Session()
        self.session.proxies = {
            'http': f'socks5h://127.0.0.1:{self.socks_port}',
            'https': f'socks5h://127.0.0.1:{self.socks_port}'
        }
        self.controller = None  # Referenz halten, damit der Service aktiv bleibt

    def start_onion_service(self, flask_port, key_type=None, private_key=None):
        try:
            print("[*] Verbinde mit Tor Control Port 9051...")
            self.controller = Controller.from_port(port=self.control_port)
            self.controller.authenticate()
            print("[*] Authentifizierung erfolgreich!")

            print("[*] Erstelle Onion Service...")

            # DER FIX: Unterscheiden, ob wir einen Key haben oder einen neuen brauchen
            if key_type and private_key:
                # Alten Service wiederherstellen
                response = self.controller.create_ephemeral_hidden_service(
                    {80: flask_port},
                    key_type=key_type,
                    key_content=private_key,
                    await_publication=True
                )
            else:
                # Komplett neuen Service erstellen (stem nutzt hier automatisch NEW:BEST)
                response = self.controller.create_ephemeral_hidden_service(
                    {80: flask_port},
                    await_publication=True
                )

            self.onion_address = response.service_id
            print(
                f"[✔] Onion Service aktiv: http://{self.onion_address}.onion")
            return response.service_id, response.private_key_type, response.private_key

        except Exception as e:
            print(f"[NetUtil] Fehler bei der Kommunikation mit Tor: {e}")
            return None, None, None

    def send_message(self, target_onion, payload):
        """Sendet einen Payload an die Zieladresse."""
        target = target_onion.replace(".onion", "").replace("http://", "")
        url = f"http://{target}.onion/api/receive_message"

        try:
            response = self.session.post(url, json=payload, timeout=45)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            print(f"\n[NetUtil] Netzwerkfehler beim Senden: {e}")
            return False
