import logging
import uuid
from datetime import datetime
import os
import base64

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from flask import Flask, request, jsonify
from flask_cors import CORS

from dbmgr import DatabaseManager

app = Flask(__name__)
CORS(app)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app.logger.setLevel(logging.INFO)

db_manager = None
network_utility = None
my_onion_address = None

# ==========================================
# SECURITY MIDDLEWARE (IPC)
# ==========================================
# Ephemeraler API-Key 
EPHEMERAL_API_KEY = str(uuid.uuid4()) 
# disabled for now
REQUIRE_API_KEY = False 

@app.before_request
def require_api_key():
    """Check API-key before every frontend request"""
    if request.path == '/api/receive_message':
        return
        
    if REQUIRE_API_KEY:
        key = request.headers.get('X-Aether-API-Key')
        if key != EPHEMERAL_API_KEY:
            app.logger.warning(f"[*] Unauthorized API access attempt. Key provided: {key}")
            return jsonify({"error": "Unauthorized. Invalid X-Aether-API-Key."}), 401

# ==========================================
# AUTH ENDPOINTS (Frontend -> Backend)
# ==========================================
@app.route('/api/v1/auth/register', methods=['POST'])
def register():
    """Create new Profile and Tor-Identity"""
    global db_manager, network_utility, my_onion_address
    data = request.json
    username = data.get('username')
    password = data.get('password') # placeholder for SQLCipher key
    
    if not username:
        return jsonify({"error": "Username is required"}), 400
        
    db_file = f"{username}.aetherdb"
    db_manager = DatabaseManager(db_file) 
    
    # generate Tor Keys and Onion Addresss
    app.logger.info("[*] Creating new Tor Identity for new user...")
    onion, key_type, private_key = network_utility.start_onion_service(flask_port=5000)
    if onion:
        db_manager.save_identity(onion, private_key, username)
        my_onion_address = onion
        return jsonify({
            "status": "success", 
            "message": "Profile created.", 
            "onion_address": onion
        }), 201
    else:
        return jsonify({"error": "Failed to generate Tor Identity"}), 500

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    """Unlock DB and load Tor-Keys into memory"""
    global db_manager, network_utility, my_onion_address
    data = request.json
    username = data.get('username')
    
    if not username:
        return jsonify({"error": "Username is required"}), 400
        
    app.logger.info(f"[*] Login attempt for user: {username}")
    
    db_file = f"{username}.aetherdb"
    db_manager = DatabaseManager(db_file)
    identity = db_manager.load_identity()
    
    if identity and my_onion_address == identity['onion_address']:
        return jsonify({"status": "success", "message": "Database unlocked.", "onion_address": my_onion_address}), 200

    # delete old Tor instance from memory if present upon login
    if my_onion_address and network_utility and hasattr(network_utility, 'controller'):
        try:
            network_utility.controller.remove_ephemeral_hidden_service(my_onion_address)
        except Exception as e:
            app.logger.warning(f"[*] Error removing old Tor Service: {e}")
    
    if identity:
        app.logger.info("[*] Loading existing Tor identity...")
        onion, key_type, private_key = network_utility.start_onion_service(
            flask_port=5000,
            key_type="ED25519-V3", # Tor standard
            private_key=identity['ed25519_private_key']
        )
        if onion:
            my_onion_address = onion
            return jsonify({"status": "success", "message": "Database unlocked.", "onion_address": onion}), 200
            
    return jsonify({"error": "Tor Service failed to start or Identity missing"}), 500

@app.route('/api/v1/auth/logout', methods=['POST'])
def logout():
    """Lock DB and delete Tor-Keys from memory"""
    global db_manager, my_onion_address, network_utility
    db_manager = None
    my_onion_address = None
    if network_utility and hasattr(network_utility, 'controller'):
        # stop hidden service and clear state
        pass 
    app.logger.info("[*] User logged out. RAM wiped.")
    return jsonify({"status": "success"}), 200

# ==========================================
# CONTACTS Endpoints (Frontend -> Backend)
# ==========================================
@app.route('/api/v1/contacts', methods=['GET'])
def get_contacts():
    """Return list of contacts"""
    if not db_manager:
        return jsonify({"error": "Database not initialized"}), 500
        
    with db_manager._get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, onion_address, display_name FROM contact")
        contacts = [dict(row) for row in cursor.fetchall()]
        
    return jsonify(contacts), 200

@app.route('/api/v1/contacts', methods=['POST'])
def create_contact():
    """Add new contact (TOFU)."""
    if not db_manager:
        return jsonify({"error": "Database not initialized"}), 500

    data = request.json
    if not data or not data.get('display_name') or not data.get('onion_address'):
        return jsonify({"error": "display_name and onion_address are required"}), 400

    contact_id, chat_id = db_manager.create_contact(data['display_name'], data['onion_address'])

    if contact_id is None:
        return jsonify({"error": "Contact with this onion address already exists"}), 409

    return jsonify({
        "id": contact_id, 
        "onion_address": data['onion_address'], 
        "display_name": data['display_name']
    }), 201

@app.route('/api/v1/contacts/<int:contact_id>', methods=['PUT'])
def update_contact(contact_id):
    """Refresh display_name of selected contact"""
    if not db_manager:
        return jsonify({"error": "Database not initialized"}), 500

    data = request.json
    if not data or not data.get('display_name'):
        return jsonify({"error": "display_name is required"}), 400

    db_manager.update_alias(contact_id, data['display_name'])
    return jsonify({"status": "success"}), 200

@app.route('/api/v1/contacts/<int:contact_id>', methods=['DELETE'])
def delete_contact(contact_id):
    """Delete contact and cascade to associated chats & messages"""
    if not db_manager:
        return jsonify({"error": "Database not initialized"}), 500

    db_manager.delete_contact(contact_id)
    return jsonify({"status": "success"}), 200

# ==========================================
# CHATS & MESSAGES Endpoints
# ==========================================
@app.route('/api/v1/chats', methods=['GET'])
def get_all_chats():
    """Return all Chats including each of their last message entry"""
    if not db_manager:
        return jsonify({"error": "Database not initialized"}), 500

    chats = db_manager.get_all_chats_with_last_message()
    return jsonify(chats), 200

@app.route('/api/v1/chats/<int:chat_id>/messages', methods=['GET'])
def get_chat_messages(chat_id):
    """Return associated messages of chat_id"""
    if not db_manager:
        return jsonify({"error": "Database not initialized"}), 500

    messages = db_manager.get_messages_for_chat(chat_id)
    return jsonify(messages), 200

@app.route('/api/v1/chats/<int:chat_id>', methods=['DELETE'])
def clear_chat_history(chat_id):
    """Clear chat history"""
    if not db_manager:
        return jsonify({"error": "Database not initialized"}), 500

    db_manager.clear_chat_history(chat_id)
    return jsonify({"status": "success"}), 200

@app.route('/api/v1/messages', methods=['POST'])
def send_message():
    """
    Queue outgoing message to DB (OUTGOING_CREATED).
    Background-Worker then fetches messages to send via Tor
    """
    if not db_manager:
        return jsonify({"error": "Database not initialized"}), 500

    data = request.json
    if not data or not data.get('chat_id') or not data.get('content'):
        return jsonify({"error": "chat_id and content are required"}), 400

    chat_id = data['chat_id']
    content = data['content']
    # UTC
    timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ') 

    msg_id = db_manager.save_message(
        chat_id=chat_id, 
        content=content, 
        timestamp=timestamp, 
        status="OUTGOING_CREATED", 
        sender_contact_id=None # None = sent from local user
    )

    app.logger.info(f"[*] Frontend queued message for Chat {chat_id}")
    
    return jsonify({"message_id": msg_id, "status": "OUTGOING_CREATED"}), 201

@app.route('/api/v1/messages/<int:message_id>', methods=['DELETE'])
def delete_specific_message(message_id):
    """Delete specific message"""
    if not db_manager:
        return jsonify({"error": "Database not initialized"}), 500
        
    with db_manager._get_conn() as conn:
        conn.execute("DELETE FROM message WHERE id = ?", (message_id,))
        conn.commit()
    return jsonify({"status": "success"}), 200

# ==========================================
# SYSTEM, POLLING & EXPORT Endpoints
# ==========================================
@app.route('/api/v1/system/status', methods=['GET'])
def get_system_status():
    """Return Tor Daemon Bootstrap status"""
    # Dummy logic: actual Tor progrss tracing should be done in netutil
    return jsonify({
        "tor_bootstrap_percent": 100 if my_onion_address else 0,
        "status": "ready" if my_onion_address else "starting"
    }), 200

@app.route('/api/v1/system/sync', methods=['GET'])
def system_sync():
    """Polling Endpoint for svelte stores"""
    if not db_manager:
        return jsonify({"error": "Database not initialized"}), 500
        
    since = request.args.get('since', '1970-01-01T00:00:00Z')
    
    with db_manager._get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, chat_id, sender_contact_id, content, timestamp, status FROM message WHERE timestamp > ? AND sender_contact_id NOT NULL", (since,))
        new_messages = [dict(row) for row in cursor.fetchall()]
        
    return jsonify({
        "new_messages": new_messages,
        "status_updates": [] # placeholder for status changes by worker
    }), 200

@app.route('/api/v1/export', methods=['POST'])
def export_profile():
    """generate AES-encrypted DB Backup"""
    global db_manager 
    
    if not db_manager:
        return jsonify({"error": "User not logged in"}), 401

    data = request.json
    
    backup_password = data.get('export_password') 
    
    if not backup_password:
        return jsonify({"error": "export password required"}), 400

    db_file = db_manager.db_path
    username = db_file.replace('.aetherdb', '').replace('data/', '')

    export_dir = "data"
    
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)

    backup_file = os.path.join(export_dir, f"{username}_export.aetherbak")

    try:
        app.logger.info(f"[*] Start AES encrypted Backup for user {username}...")
        
        salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(backup_password.encode()))
        fernet = Fernet(key)

        with open(db_file, 'rb') as file:
            db_data = file.read()

        encrypted_data = fernet.encrypt(db_data)

        with open(backup_file, 'wb') as file:
            file.write(salt + encrypted_data)

        app.logger.info(f"[*] Backup successfully generated: {backup_file}")

        return jsonify({
            "status": "success", 
            "message": "backup successful",
            "file_path": os.path.abspath(backup_file)
        }), 200

    except Exception as e:
        app.logger.error(f"[*] ERROR: {e}")
        return jsonify({"error": "Internal Error during Backup"}), 500
    
# ==========================================
# P2P Endpoints (Tor-Network -> Backend)
# NOT API Key protected
# ==========================================
@app.route('/api/receive_message', methods=['POST'])
def receive_message_from_peer():
    """This endpoint is called by external Tor Clients"""
    data = request.json
    if not data or not data.get('sender_onion') or not data.get('text'):
        return jsonify({"error": "Invalid payload"}), 400

    sender_onion = data.get('sender_onion')
    text = data.get('text')
    timestamp = data.get('timestamp') or datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    app.logger.info(f"\n[Tor P2P] New message from {sender_onion}")

    if not db_manager:
        return jsonify({"error": "Backend offline"}), 503

    # find chat and contact id of sender
    chat_id = db_manager.get_chat_id_by_onion(sender_onion)
    contact_id = None
    
    with db_manager._get_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM contact WHERE onion_address = ?", (sender_onion,))
        row = cursor.fetchone()
        if row: contact_id = row['id']

    # unknown contact --> reject message (TOFU)
    if not chat_id or not contact_id:
        app.logger.warning("[*] Dropped message from unknown sender.")
        return jsonify({"error": "Unauthorized / Unknown Contact"}), 403

    db_manager.save_message(
        chat_id=chat_id, 
        content=text, 
        timestamp=timestamp,
        status="INCOMING_UNREAD", 
        sender_contact_id=contact_id
    )
    
    return jsonify({"status": "ok"}), 200

# ==========================================
# RUNNER
# ==========================================
def run_flask_server(port, net_util):
    global network_utility
    network_utility = net_util

    app.logger.info(f"[*] Initializing System...")
    app.logger.info(f"[*] Ephemeral API Key for Frontend: {EPHEMERAL_API_KEY}")
    app.logger.info(f"[*] Start API Controller on Port {port}...")
    
    app.run(host='0.0.0.0', port=port, use_reloader=False)