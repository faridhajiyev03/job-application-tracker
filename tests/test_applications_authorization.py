import pytest

pytestmark = pytest.mark.db
PAYLOAD = {"company": "Test Company", "position": "Backend Engineer"}


@pytest.mark.parametrize("method,path,payload", [
    ("GET", "/applications/", None),
    ("GET", "/applications/summary", None),
    ("GET", "/applications/1", None),
    ("POST", "/applications/", PAYLOAD),
    ("PATCH", "/applications/1", {"notes": "changed"}),
    ("DELETE", "/applications/1", None),
])
def test_application_routes_require_authentication(client, method, path, payload):
    response = client.request(method, path, json=payload)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("prefix", ["", "/api"])
@pytest.mark.parametrize("method,payload", [("GET", None), ("PATCH", {"company": "Intruder"}), ("DELETE", None)])
def test_cross_user_access_is_hidden_and_does_not_mutate(client, account, prefix, method, payload):
    _, owner_headers = account()
    _, other_headers = account("other@example.com")
    created = client.post(f"{prefix}/applications/", json=PAYLOAD, headers=owner_headers)
    assert created.status_code == 201
    original = created.json()
    path = f"{prefix}/applications/{original['id']}"
    denied = client.request(method, path, headers=other_headers, json=payload)
    assert denied.status_code == 404
    assert denied.json() == {"detail": "Application not found"}
    owned = client.get(path, headers=owner_headers)
    assert owned.status_code == 200
    assert owned.json() == original


def test_list_summary_and_owner_crud(client, account):
    _, owner = account()
    _, other = account("other@example.com")
    owned = client.post("/applications/", json=PAYLOAD, headers=owner)
    assert owned.status_code == 201
    owned_id = owned.json()["id"]
    alien = client.post("/applications/", json={**PAYLOAD, "company": "Other Company"}, headers=other)
    assert alien.status_code == 201
    changed = client.patch(f"/applications/{owned_id}", json={"status": "interview", "notes": "Follow up"}, headers=owner)
    assert changed.status_code == 200
    assert changed.json()["status"] == "interview"
    assert changed.json()["notes"] == "Follow up"
    for headers, application_id, status in [(owner, owned_id, "interview"), (other, alien.json()["id"], "applied")]:
        listing = client.get("/applications/", headers=headers)
        assert listing.status_code == 200
        assert [item["id"] for item in listing.json()] == [application_id]
        summary = client.get("/applications/summary", headers=headers)
        assert summary.status_code == 200
        expected = {"total": 1, "applied": 0, "interview": 0, "offer": 0, "rejected": 0}
        expected[status] = 1
        assert summary.json() == expected
    deleted = client.delete(f"/applications/{owned_id}", headers=owner)
    assert deleted.status_code == 204
    assert deleted.content == b""
    assert client.get(f"/applications/{owned_id}", headers=owner).status_code == 404
    assert client.get("/applications/", headers=owner).json() == []
    assert client.get(f"/applications/{alien.json()['id']}", headers=other).status_code == 200
