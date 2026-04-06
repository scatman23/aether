import requests
import time
from stem.control import Controller
from stem import SocketError


class NetworkUtility:
    def __init__(self, tor_control_port=9051, tor_socks_port=9050):
        self.control_port = tor_control_port
        self.socks_port = tor_socks_port
        self.onion_address = None
        self.controller = None

        # SOCKS5 Session for outgoing requests, DNS resolution only via TOR
        self.session = requests.Session()
        self.session.proxies = {
            'http': f'socks5h://127.0.0.1:{self.socks_port}',
            'https': f'socks5h://127.0.0.1:{self.socks_port}'
        }

    def start_onion_service(self, flask_port, key_type=None, private_key=None):
        print(f"[*] Connecting to Tor Control Port {self.control_port}...")

        # wait till tor daemon opens port
        for attempt in range(15):
            try:
                self.controller = Controller.from_port(port=self.control_port)
                self.controller.authenticate()
                break
            except SocketError:
                print(
                    f"[*] Waiting for Tor Daemon (Port {self.control_port}) - attempt {attempt+1}/15...")
                time.sleep(1)
        else:
            # error after 15 attempts
            print(f"[NetUtil] ERROR: Could'nt connect to TOR on port {self.control_port}")
            return None, None, None

        # wait until Tor Bootstrapping has completed successfully
        print("[*] Connected! Checking Tor Bootstrapping Status...")
        while True:
            bootstrap_status = self.controller.get_info(
                "status/bootstrap-phase")

            if "PROGRESS=100" in bootstrap_status:
                print("[*] Tor Network-Bootstrapping completed")
                break

            parts = dict(item.split("=")
                         for item in bootstrap_status.split(" ") if "=" in item)
            progress = parts.get("PROGRESS", "0")
            summary = parts.get("SUMMARY", "Unknown").replace('"', '')

            print(f"[*] Loading Tor... {progress}% ({summary})")
            time.sleep(1)

        print(
            f"[*] Creating Ephemeral Hidden Service (Redirecting to Port {flask_port})...")

        try:
            if key_type and private_key:
                response = self.controller.create_ephemeral_hidden_service(
                    {80: flask_port},
                    key_type=key_type,
                    key_content=private_key,
                    await_publication=True
                )
                print(
                    "[*] Fetched local identity from DB")
            else:
                response = self.controller.create_ephemeral_hidden_service(
                    {80: flask_port},
                    await_publication=True
                )
                print("[*] Generated new Tor identity")

            self.onion_address = response.service_id
            return response.service_id, response.private_key_type, response.private_key

        except Exception as e:
            print(
                f"[NetUtil] ERROR creating service: {e}")
            return None, None, None

    def send_message(self, target_onion, payload):
        """
        Sendet einen JSON-Payload (die Nachricht) über das Tor-Netzwerk an die Zieladresse.
        """
        # sanitize addr
        target = target_onion.replace(
            "http://", "").replace("https://", "").replace(".onion", "").strip()
        url = f"http://{target}.onion/api/receive_message"

        try:
            print(f"[*] Sende P2P Nachricht an {target[:8]}... via Tor")
            # Tor circuit timeout set to 45s
            response = self.session.post(url, json=payload, timeout=45)

            if response.status_code == 200:
                print(f"[*] Message sent")
                return True
            else:
                print(
                    f"[NetUtil] ERROR: Receiver answered: {response.status_code}")
                return False

        except requests.exceptions.ConnectionError:
            print(
                f"[NetUtil] ERROR: Receiver ({target[:8]}...) is offline or not reachable")
            return False
        except requests.exceptions.Timeout:
            print(f"[NetUtil] Connection Timeout")
            return False
        except requests.exceptions.RequestException as e:
            print(f"[NetUtil] Unexpected Request-ERROR: {e}")
            return False

    def stop(self):
        """Schließt die Verbindung zum Tor Controller sauber und löscht den Ephemeral Service."""
        if self.controller:
            print("[*] Stop Tor Onion Service and close Control-Connection...")
            self.controller.close()
