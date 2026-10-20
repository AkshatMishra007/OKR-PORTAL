import uuid
from unittest.mock import patch, MagicMock

def mock_role(role_id=None):
    return {
        "id": str(role_id or uuid.uuid4()),
        "name": "Admin",
        "description": "Administrator role",
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00",
    }


def test_tc_01_create_role_success(client):

    with patch("app.rbac.router.create_role_service") as mock_service:

        role_id = uuid.uuid4()

        mock_service.return_value = mock_role(role_id)

        response = client.post(
            "/roles/",
            json={
                "name": "Admin",
                "description": "Administrator role",
            },
        )

        assert response.status_code == 201

        data = response.json()

        assert data["name"] == "Admin"

        mock_service.assert_called_once()


def test_tc_02_create_role_validation_error(client):

    response = client.post(
        "/roles/",
        json={
            "description": "Missing name",
        },
    )

    assert response.status_code == 422


def test_tc_03_get_role_success(client):

    with patch("app.rbac.router.get_role_service") as mock_service:

        role_id = uuid.uuid4()

        mock_service.return_value = mock_role(role_id)

        response = client.get(
            f"/roles/{role_id}",
        )

        assert response.status_code == 200

        assert response.json()["name"] == "Admin"

        mock_service.assert_called_once()


def test_tc_04_get_role_invalid_uuid(client):

    response = client.get(
        "/roles/invalid-id",
    )

    assert response.status_code == 422


def test_tc_05_list_roles_success(client):

    with patch("app.rbac.router.list_roles_service") as mock_service:

        mock_service.return_value = (
            [
                mock_role()
            ],
            1,
        )

        response = client.get(
            "/roles/",
        )

        assert response.status_code == 200

        data = response.json()

        assert data["page"] == 1
        assert data["size"] == 10
        assert data["total"] == 1
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "Admin"

        mock_service.assert_called_once()


def test_tc_06_list_roles_with_pagination(client):

    with patch("app.rbac.router.list_roles_service") as mock_service:

        mock_service.return_value = (
            [],
            0,
        )

        response = client.get(
            "/roles/?page=2&size=20&search=admin",
        )

        assert response.status_code == 200

        data = response.json()

        assert data["page"] == 2
        assert data["size"] == 20
        assert data["total"] == 0

        args = mock_service.call_args.args

        assert args[1] == 2
        assert args[2] == 20
        assert args[3] == "admin"


def test_tc_07_update_role_success(client):

    with patch("app.rbac.router.update_role_service") as mock_service:

        role_id = uuid.uuid4()

        mock_service.return_value = {
                "id": str(role_id),
                "name": "Updated Admin",
                "description": "Updated role",
                "created_at": "2026-01-01T00:00:00",
                "updated_at": "2026-01-01T00:00:00",
            }

        response = client.put(
            f"/roles/{role_id}",
            json={
                "name": "Updated Admin",
            },
        )

        assert response.status_code == 200

        assert response.json()["name"] == "Updated Admin"

        mock_service.assert_called_once()


def test_tc_08_update_role_invalid_uuid(client):

    response = client.put(
        "/roles/test",
        json={
            "name": "Admin",
        },
    )

    assert response.status_code == 422


def test_tc_09_delete_role_success(client):

    with patch("app.rbac.router.delete_role_service") as mock_service:

        role_id = uuid.uuid4()

        response = client.delete(
            f"/roles/{role_id}",
        )

        assert response.status_code == 200

        assert response.json() == {
            "success": True,
            "message": "Role deleted successfully.",
        }

        mock_service.assert_called_once()


def test_tc_10_delete_role_invalid_uuid(client):

    response = client.delete(
        "/roles/test",
    )

    assert response.status_code == 422