import pytest
import os
import tempfile
from dbmgr import DatabaseManager

@pytest.fixture
def test_db():
    fd, temp_path = tempfile.mkstemp(suffix=".aetherdb")
    os.close(fd)

    db = DatabaseManager(temp_path)

    yield db

    try:
        db._get_conn().close()
    except Exception:
        pass

    if os.path.exists(temp_path):
        os.remove(temp_path)

def test_save_and_load_identity(test_db):
    test_db.save_identity("onion_test_123", "secret_priv_key", "Alice")
    identity = test_db.load_identity()

    assert identity is not None
    assert identity["onion_address"] == "onion_test_123"
    assert identity["ed25519_private_key"] == "secret_priv_key"

def test_create_contact_success(test_db):
    contact_id, chat_id = test_db.create_contact("Bob", "bob_onion_address")

    assert contact_id is not None
    assert chat_id is not None

def test_create_contact_duplicate(test_db):
    test_db.create_contact("Bob", "bob_onion_address")

    result = test_db.create_contact("Copycat", "bob_onion_address")

    if isinstance(result, tuple):
        assert result[0] is None
    else:
        assert result is None

def test_save_and_get_message(test_db):
    contact_id, chat_id = test_db.create_contact("Charlie", "charlie_onion")

    msg_id = test_db.save_message(
        chat_id=chat_id,
        content="Test Nachricht",
        timestamp="2026-04-06T12:00:00Z",
        status="OUTGOING_CREATED",
        sender_contact_id=None
    )

    assert msg_id is not None

    messages = test_db.get_messages_for_chat(chat_id)
    assert len(messages) == 1
    assert messages[0]["content"] == "Test Nachricht"
    assert messages[0]["status"] == "OUTGOING_CREATED"

def test_get_pending_messages(test_db):
    contact_id, chat_id = test_db.create_contact("WorkerTest", "worker_onion")

    test_db.save_message(
        chat_id=chat_id,
        content="Diese Nachricht hängt in der Warteschlange",
        timestamp="2026-04-06T12:00:00Z",
        status="OUTGOING_CREATED",
        sender_contact_id=None
    )

    pending = test_db.get_pending_messages()

    assert len(pending) == 1
    assert pending[0]["content"] == "Diese Nachricht hängt in der Warteschlange"
    assert pending[0]["status"] == "OUTGOING_CREATED"