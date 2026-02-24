import threading
import time
import sys
from src.controller import run_flask_server
from src.netutil import NetworkUtility
from src.dbmgr import DatabaseManager

def main():
    print("================================")
    print("      TOR P2P CHAT CLIENT       ")
    print("================================\n")
    
    try:
        flask_port = int(input("Wähle einen lokalen Port (z.B. 5000): "))
    except ValueError:
        print("Bitte eine gültige Zahl eingeben.")
        sys.exit(1)

    # 1. Flask Server im Hintergrund starten
    flask_thread = threading.Thread(target=run_flask_server, args=(flask_port,), daemon=True)
    flask_thread.start()
    time.sleep(1)

    # 2. Module initialisieren
    db = DatabaseManager(f"peer_{flask_port}.db")
    net = NetworkUtility()

    # 3. Identität aus DB laden und an NetworkUtility übergeben
    saved_identity = db.load_identity()
    
    print("[*] Verbinde mit Tor...")
    if saved_identity:
        onion, key_type, private_key = saved_identity
        print(f"[*] Stelle existierende Identität wieder her...")
        my_onion, _, _ = net.start_onion_service(flask_port, key_type, private_key)
    else:
        print("[*] Erstelle neue .onion Adresse (das dauert kurz)...")
        my_onion, new_type, new_key = net.start_onion_service(flask_port)
        if my_onion:
            db.save_identity(my_onion, new_type, new_key)

    if not my_onion:
        print("[!] Fehler beim Starten des Tor Services. Beende.")
        sys.exit(1)

    print("\n" + "*"*50)
    print(f" DEINE ADRESSE: {my_onion}")
    print("*"*50 + "\n")

    # 4. Chat User-Interface Schleife
    target_onion = input("Ziel-Adresse eingeben (ohne .onion): ")
    if target_onion:
        print(f"[*] Chat mit {target_onion}.onion gestartet! ('/exit' zum Beenden)")

    while True:
        try:
            msg = input("> ")
            if msg == '/exit':
                break
            elif msg.strip() == '':
                continue

            payload = {
                "sender": my_onion,
                "text": msg
            }
            
            print("[*] Sende...")
            success = net.send_message(target_onion, payload)
            
            if success:
                print("[✔] Zugestellt!")
            else:
                print("[❌] Fehler: Konnte Nachricht nicht zustellen.")

        except KeyboardInterrupt:
            print("\n[*] Beende Client...")
            break

if __name__ == "__main__":
    main()