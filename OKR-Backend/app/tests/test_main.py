def test_home_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "OKR Backend Running",
    }


def test_homeapp_endpoint(client):
    response = client.get("/home/")
    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": "Home app",
    }
