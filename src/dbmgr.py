import sqlite3

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS identity (
                                id INTEGER PRIMARY KEY, onion_address TEXT,
                                key_type TEXT, private_key TEXT)''')
            conn.commit()

    def load_identity(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT onion_address, key_type, private_key FROM identity LIMIT 1")
            return cursor.fetchone()

    def save_identity(self, onion_address, key_type, private_key):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM identity")
            cursor.execute("INSERT INTO identity (onion_address, key_type, private_key) VALUES (?, ?, ?)",
                           (onion_address, key_type, private_key))
            conn.commit()