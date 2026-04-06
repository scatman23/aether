import os
import sys
import pytest
from unittest.mock import patch, MagicMock

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, src_path)

import controller

@pytest.fixture
def client():
    controller.app.config["TESTING"] = True
    with controller.app.test_client() as client:
        yield client

@pytest.fixture
def mock_db():
    with patch("controller.DatabaseManager") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        controller.db_manager = mock_instance
        yield mock_instance

@pytest.fixture
def mock_net():
    mock_instance = MagicMock()
    controller.network_utility = mock_instance
    yield mock_instance

@pytest.fixture(autouse=True)
def cleanup_controller_db():
    yield
    if controller.db_manager is not None:
        try:
            controller.db_manager._get_conn().close()
        except Exception:
            pass
        controller.db_manager = None