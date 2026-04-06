import sqlite3

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        """Hilfsmethode für sauberes Connection-Management und Foreign Keys."""
        conn = sqlite3.connect(self.db_path)
        # Automatic delete of associated data as per architecture definition (CASCADE)
        conn.execute("PRAGMA foreign_keys = ON;")
        # Enable secure deletion at the connection level
        conn.execute("PRAGMA secure_delete = ON;")

        conn.row_factory = sqlite3.Row 
        return conn

    def _init_db(self):
        """Initialize DB according to schema"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Identity (user's Tor-Address & Keys - strict constraint: max 1 row)
            cursor.execute('''CREATE TABLE IF NOT EXISTS "identity" (
                                "id" INTEGER PRIMARY KEY CHECK ("id" = 1), 
                                "onion_address" TEXT NOT NULL UNIQUE,
                                "ed25519_private_key" TEXT NOT NULL, 
                                "display_name" TEXT)''')
            
            # Contacts
            cursor.execute('''CREATE TABLE IF NOT EXISTS "contact" (
                                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                                "onion_address" TEXT NOT NULL UNIQUE,
                                "noise_public_key" TEXT,
                                "display_name" TEXT NOT NULL)''')
            
            # Chats
            cursor.execute('''CREATE TABLE IF NOT EXISTS "chat" (
                                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                                "is_group" INTEGER NOT NULL DEFAULT 0 CHECK ("is_group" IN (0, 1)),
                                "title" TEXT)''')
            
            # Chat Member (Junction Table for n:m relations)
            cursor.execute('''CREATE TABLE IF NOT EXISTS "chat_member" (
                                "chat_id" INTEGER NOT NULL,
                                "contact_id" INTEGER NOT NULL,
                                PRIMARY KEY ("chat_id", "contact_id"),
                                FOREIGN KEY ("chat_id") REFERENCES "chat"("id") ON DELETE CASCADE,
                                FOREIGN KEY ("contact_id") REFERENCES "contact"("id") ON DELETE CASCADE)''')
            
            # Messages
            cursor.execute('''CREATE TABLE IF NOT EXISTS "message" (
                                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                                "chat_id" INTEGER NOT NULL,
                                "sender_contact_id" INTEGER,
                                "content" TEXT NOT NULL,
                                "timestamp" DATETIME DEFAULT CURRENT_TIMESTAMP,
                                "status" TEXT NOT NULL CHECK ("status" IN ('OUTGOING_CREATED', 'OUTGOING_RECEIVED', 'INCOMING_UNREAD', 'INCOMING_READ')),
                                FOREIGN KEY ("chat_id") REFERENCES "chat"("id") ON DELETE CASCADE,
                                FOREIGN KEY ("sender_contact_id") REFERENCES "contact"("id") ON DELETE CASCADE,
                                CONSTRAINT "chk_sender_integrity" CHECK (
                                    ("status" IN ('OUTGOING_CREATED','OUTGOING_RECEIVED') AND "sender_contact_id" IS NULL) OR 
                                    ("status" IN ('INCOMING_UNREAD','INCOMING_READ') AND "sender_contact_id" IS NOT NULL)
                                ))''')
            
            # Indices for UI performance
            cursor.execute('CREATE INDEX IF NOT EXISTS "idx_message_chat_id" ON "message"("chat_id");')
            
            conn.commit()

    # ==========================================
    # IDENTITY METHODS
    # ==========================================
    def load_identity(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT onion_address, ed25519_private_key, display_name FROM identity WHERE id = 1")
            row = cursor.fetchone()
            return dict(row) if row else None

    def save_identity(self, onion_address, ed25519_private_key, display_name=None):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM identity")
            cursor.execute("INSERT INTO identity (id, onion_address, ed25519_private_key, display_name) VALUES (1, ?, ?, ?)",
                           (onion_address, ed25519_private_key, display_name))
            conn.commit()

    # ==========================================
    # CONTACT & CHAT METHODS
    # ==========================================
    def create_contact(self, display_name, onion_address, noise_public_key=None):
        """Creates a contact and an associated chat"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            try:
                # create contact
                cursor.execute("INSERT INTO contact (display_name, onion_address, noise_public_key) VALUES (?, ?, ?)", 
                               (display_name, onion_address, noise_public_key))
                contact_id = cursor.lastrowid
                
                # create direct chat
                cursor.execute("INSERT INTO chat (is_group) VALUES (0)")
                chat_id = cursor.lastrowid
                
                # link contact and chat
                cursor.execute("INSERT INTO chat_member (chat_id, contact_id) VALUES (?, ?)", (chat_id, contact_id))
                
                conn.commit()
                return contact_id, chat_id
            except sqlite3.IntegrityError:
                # if onion_address already exists
                return None, None

    def delete_contact(self, contact_id):
        """Delete contact (deletes associated chat memberships and messages via CASCADE)."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM contact WHERE id = ?", (contact_id,))
            conn.commit()

    def update_alias(self, contact_id, new_display_name):
        with self._get_conn() as conn:
            conn.execute("UPDATE contact SET display_name = ? WHERE id = ?", (new_display_name, contact_id))
            conn.commit()

    def get_onion_for_chat(self, chat_id):
        """Get receiver onion address for chat"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT c.onion_address FROM contact c
                              JOIN chat_member cm ON c.id = cm.contact_id
                              WHERE cm.chat_id = ? LIMIT 1''', (chat_id,))
            row = cursor.fetchone()
            return row['onion_address'] if row else None

    def get_chat_id_by_onion(self, onion_address):
        """search chat associated to sender onion address"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT cm.chat_id FROM chat_member cm
                              JOIN contact c ON cm.contact_id = c.id
                              WHERE c.onion_address = ? LIMIT 1''', (onion_address,))
            row = cursor.fetchone()
            return row['chat_id'] if row else None

    # ==========================================
    # MESSAGE METHODS
    # ==========================================
    def save_message(self, chat_id, content, timestamp, status, sender_contact_id=None):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO message (chat_id, sender_contact_id, content, timestamp, status) 
                              VALUES (?, ?, ?, ?, ?)''', 
                           (chat_id, sender_contact_id, content, timestamp, status))
            conn.commit()
            return cursor.lastrowid

    def get_messages_for_chat(self, chat_id):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id as id, content, timestamp, sender_contact_id, status FROM message WHERE chat_id = ?", (chat_id,))
            return [dict(row) for row in cursor.fetchall()]

    def delete_message(self, message_id, chat_id):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM message WHERE id = ? AND chat_id = ?", (message_id, chat_id))
            conn.commit()

    def clear_chat_history(self, chat_id):
        with self._get_conn() as conn:
            conn.execute("DELETE FROM message WHERE chat_id = ?", (chat_id,))
            conn.commit()

    def get_all_chats_with_last_message(self):
        """get all chats, combine each with associated contact and last message entry"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            # use subselect to get most recent message per chat
            query = '''
                SELECT 
                    ch.id as chat_id,
                    ch.is_group,
                    ch.title,
                    c.id as contact_id, 
                    c.display_name,
                    m.id as msg_id,
                    m.content, 
                    m.timestamp, 
                    m.status
                FROM chat ch
                JOIN chat_member cm ON ch.id = cm.chat_id
                JOIN contact c ON cm.contact_id = c.id
                LEFT JOIN message m ON m.id = (
                    SELECT id FROM message 
                    WHERE chat_id = ch.id 
                    ORDER BY id DESC LIMIT 1
                )
            '''
            cursor.execute(query)
            
            results = []
            for row in cursor.fetchall():
                chat_obj = {
                    "chat_id": row['chat_id'],
                    "is_group": row['is_group'],
                    "title": row['title'],
                    "display_name": row['display_name'],
                    "contact_ids": [{"contact_id": row['contact_id']}],
                }
                # if messages already exist, then attach last_message
                if row['content'] is not None:
                    chat_obj["last_message"] = {
                        "id": row['msg_id'],
                        "content": row['content'],
                        "timestamp": row['timestamp'],
                        "status": row['status']
                    }
                else:
                    chat_obj["last_message"] = None
                    
                results.append(chat_obj)
                
            return results
        
    # ==========================================
    # WORKER METHODS
    # ==========================================
    def get_pending_messages(self):
        """
        searches all unsent outgoing messages
        """
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, chat_id, content, timestamp, status 
                FROM message 
                WHERE status = 'OUTGOING_CREATED'
            ''')
            return [dict(row) for row in cursor.fetchall()]