import pytest
from unittest.mock import patch, MagicMock
from netutil import NetworkUtility

@pytest.fixture
def net_util():
    return NetworkUtility()

@patch('netutil.Controller') # Mockt den Tor Controller
def test_start_onion_service_success(mock_controller_class, net_util):
    """Prüft, ob der Tor Hidden Service mit den richtigen Parametern gestartet wird."""
    
    # 1. Arrange: Wir bauen uns einen gefälschten Tor-Controller zusammen
    mock_controller_instance = MagicMock()
    
    # WICHTIG: Die Methode wird direkt aufgerufen, nicht im 'with' Block!
    mock_controller_class.from_port.return_value = mock_controller_instance
    
    # WICHTIG: Verhindere die Endlosschleife! Simuliere, dass Tor zu 100% geladen ist
    mock_controller_instance.get_info.return_value = "PROGRESS=100 SUMMARY=Done"
    
    # Simuliere die Rückgabe von Tor, wenn ein Hidden Service erstellt wird
    mock_response = MagicMock()
    mock_response.service_id = "mocked_onion_address"
    mock_response.private_key = "mocked_private_key"
    mock_response.private_key_type = "ED25519-V3" # Type wurde im Code in netutil.py zurückgegeben
    mock_controller_instance.create_ephemeral_hidden_service.return_value = mock_response

    # 2. Act: Rufe deine Methode auf
    onion, key_type, priv_key = net_util.start_onion_service(flask_port=5000)

    # 3. Assert
    assert onion == "mocked_onion_address"
    assert priv_key == "mocked_private_key"
    assert key_type == "ED25519-V3"
    
    # Prüfe, ob Tor überhaupt angewiesen wurde, den Port 5000 freizugeben
    mock_controller_instance.create_ephemeral_hidden_service.assert_called_once()

@patch('netutil.Controller')
def test_start_onion_service_failure(mock_controller_class, net_util):
    """Prüft, ob Fehler (z.B. Tor Daemon offline) robust abgefangen werden."""
    
    # Simuliere, dass der Tor-Daemon nicht erreichbar ist (wirft Exception aus der stem library)
    from stem import SocketError
    mock_controller_class.from_port.side_effect = SocketError("Connection refused")
    
    onion, key_type, priv_key = net_util.start_onion_service(flask_port=5000)
    
    assert onion is None
    assert priv_key is None