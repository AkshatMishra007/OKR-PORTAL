import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_deps():
    mock_user = MagicMock()
    mock_user.id = uuid.uuid4()
    mock_db = MagicMock()

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    yield
    app.dependency_overrides.clear()


@patch("app.fogs_hurdles.router.FogsHurdleService")
def test_create_fogs_hurdle_endpoint(mock_service_cls):
    okr_id = uuid.uuid4()
    hurdle_id = uuid.uuid4()

    mock_service_instance = MagicMock()
    mock_service_cls.return_value = mock_service_instance

    mock_record = MagicMock(
        id=hurdle_id,
        okr_id=okr_id,
        fogs_hurdles="Lack of server resources",
        action_points="Provision extra instances",
    )
    mock_service_instance.create_fogs_hurdle.return_value = mock_record

    response = client.post(
        f"/okrs/{okr_id}/fogs-hurdles",
        json={
            "fogs_hurdles": "Lack of server resources",
            "action_points": "Provision extra instances",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["fogs_hurdles"] == "Lack of server resources"


@patch("app.fogs_hurdles.router.FogsHurdleService")
def test_get_fogs_hurdles_for_okr_endpoint(mock_service_cls):
    okr_id = uuid.uuid4()
    mock_service_instance = MagicMock()
    mock_service_cls.return_value = mock_service_instance

    mock_record = MagicMock(
        id=uuid.uuid4(),
        okr_id=okr_id,
        fogs_hurdles="Hurdle 1",
        action_points="Action 1",
    )
    mock_service_instance.get_fogs_hurdles_for_okr.return_value = {
        "data": [mock_record],
        "pagination": {"page": 1, "size": 20, "total": 1},
    }

    response = client.get(f"/okrs/{okr_id}/fogs-hurdles")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["data"]) == 1
    assert data["pagination"]["total"] == 1


@patch("app.fogs_hurdles.router.FogsHurdleService")
def test_get_fogs_hurdle_endpoint(mock_service_cls):
    hurdle_id = uuid.uuid4()
    okr_id = uuid.uuid4()
    mock_service_instance = MagicMock()
    mock_service_cls.return_value = mock_service_instance

    mock_record = MagicMock(
        id=hurdle_id,
        okr_id=okr_id,
        fogs_hurdles="Database locks",
        action_points="Optimize queries",
    )
    mock_service_instance.get_fogs_hurdle.return_value = mock_record

    response = client.get(f"/fogs-hurdles/{hurdle_id}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(hurdle_id)


@patch("app.fogs_hurdles.router.FogsHurdleService")
def test_update_fogs_hurdle_endpoint(mock_service_cls):
    hurdle_id = uuid.uuid4()
    okr_id = uuid.uuid4()
    mock_service_instance = MagicMock()
    mock_service_cls.return_value = mock_service_instance

    mock_record = MagicMock(
        id=hurdle_id,
        okr_id=okr_id,
        fogs_hurdles="Updated hurdle text",
        action_points="Updated action point",
    )
    mock_service_instance.update_fogs_hurdle.return_value = mock_record

    response = client.put(
        f"/fogs-hurdles/{hurdle_id}",
        json={"fogs_hurdles": "Updated hurdle text"},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["fogs_hurdles"] == "Updated hurdle text"


@patch("app.fogs_hurdles.router.FogsHurdleService")
def test_delete_fogs_hurdle_endpoint(mock_service_cls):
    hurdle_id = uuid.uuid4()
    mock_service_instance = MagicMock()
    mock_service_cls.return_value = mock_service_instance

    response = client.delete(f"/fogs-hurdles/{hurdle_id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_service_instance.delete_fogs_hurdle.assert_called_once()
