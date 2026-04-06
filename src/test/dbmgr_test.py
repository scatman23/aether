import pytest
import os
import tempfile
from dbmgr import DatabaseManager

@pytest.fixture
def test_db():
    """
    Erstellt für jeden Test eine frische, isolierte Datenbank als temporäre Datei.
    Dadurch beeinträchtigen sich die Tests nicht gegenseitig.
    """
    # 1. Erstelle eine sichere temporäre Datei im Temp-Ordner des Betriebssystems
    fd, temp_path = tempfile.mkstemp(suffix=".aetherdb")
    os.close(fd) # Dateideskriptor schließen, da SQLite die Datei selbst öffnet
    
    # 2. Initialisiere den Manager mit dem echten temporären Dateipfad
    db = DatabaseManager(temp_path)
    
    yield db
    
    # 3. Teardown: Lösche die Datenbank-Datei nach Abschluss des Tests spurlos
    if os.path.exists(temp_path):
        os.remove(temp_path)

def test_save_and_load_identity(test_db):
    """Prüft, ob Tor-Identitäten korrekt gespeichert und geladen werden."""
    # Arrange & Act
    test_db.save_identity("onion_test_123", "secret_priv_key", "Alice")
    identity = test_db.load_identity()
    
    # Assert
    assert identity is not None
    assert identity["onion_address"] == "onion_test_123"
    assert identity["ed25519_private_key"] == "secret_priv_key"

def test_create_contact_success(test_db):
    """Prüft, ob ein Kontakt erfolgreich angelegt wird (TOFU)."""
    contact_id, chat_id = test_db.create_contact("Bob", "bob_onion_address")
    
    assert contact_id is not None
    assert chat_id is not None

def test_create_contact_duplicate(test_db):
    """Prüft, ob die Datenbank Duplikate bei Onion-Adressen verhindert."""
    # Erster Kontakt sollte klappen
    test_db.create_contact("Bob", "bob_onion_address")
    
    # Zweiter Kontakt mit gleicher Onion-Adresse sollte fehlschlagen/None zurückgeben
    # (Basierend auf der Logik in controller.py, wo None für 409 Conflict sorgt)
    result = test_db.create_contact("Copycat", "bob_onion_address")
    
    # Entweder liefert dein Code (None, None) oder nur None zurück
    if isinstance(result, tuple):
        assert result[0] is None
    else:
        assert result is None

def test_save_and_get_message(test_db):
    """Prüft das Einfügen und Auslesen von Nachrichten."""
    # Dummy Chat und Kontakt anlegen, um Foreign Keys zu befriedigen
    contact_id, chat_id = test_db.create_contact("Charlie", "charlie_onion")
    
    # Nachricht speichern
    msg_id = test_db.save_message(
        chat_id=chat_id,
        content="Test Nachricht",
        timestamp="2026-04-06T12:00:00Z",
        status="OUTGOING_CREATED",
        sender_contact_id=None
    )
    
    assert msg_id is not None
    
    # Nachrichten für diesen Chat abrufen
    messages = test_db.get_messages_for_chat(chat_id)
    assert len(messages) == 1
    assert messages[0]["content"] == "Test Nachricht"
    assert messages[0]["status"] == "OUTGOING_CREATED"