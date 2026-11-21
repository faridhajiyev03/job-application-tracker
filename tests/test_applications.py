import pytest


def create_application(client, headers, **fields):
    payload = {"company": "Acme", "position": "Backend Developer", **fields}
    response = client.post("/applications/", json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


def set_status(client, headers, application_id, status):
    response = client.patch(
        f"/applications/{application_id}",
        json={"status": status},
        headers=headers,
    )
    assert response.status_code == 200, response.text


def companies(response):
    assert response.status_code == 200, response.text
    return [item["company"] for item in response.json()["items"]]


# Create and update


def test_new_application_starts_as_applied(client, account):
    _, headers = account()

    created = create_application(client, headers, notes="Found on LinkedIn")

    assert created["status"] == "applied"
    assert created["notes"] == "Found on LinkedIn"
    assert created["vacancy_url"] is None


@pytest.mark.parametrize(
    "payload",
    [
        {"company": "", "position": "Developer"},
        {"company": "Acme"},
        {"company": "x" * 101, "position": "Developer"},
    ],
)
def test_invalid_application_is_rejected(client, account, payload):
    _, headers = account()

    response = client.post("/applications/", json=payload, headers=headers)

    assert response.status_code == 422


def test_partial_update_keeps_other_fields(client, account):
    _, headers = account()
    created = create_application(client, headers, notes="First call on Monday")

    response = client.patch(
        f"/applications/{created['id']}",
        json={"position": "Senior Backend Developer"},
        headers=headers,
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["position"] == "Senior Backend Developer"
    assert updated["company"] == created["company"]
    assert updated["notes"] == "First call on Monday"


@pytest.mark.parametrize(
    "payload",
    [
        {"company": None},
        {"position": None},
        {"status": None},
        {"status": "hired"},
        {"company": ""},
    ],
)
def test_invalid_update_is_rejected(client, account, payload):
    _, headers = account()
    created = create_application(client, headers)

    response = client.patch(
        f"/applications/{created['id']}", json=payload, headers=headers
    )

    assert response.status_code == 422


def test_missing_application_returns_404(client, account):
    _, headers = account()

    response = client.get("/applications/999", headers=headers)

    assert response.status_code == 404
    assert response.json() == {"detail": "Application not found"}


# Search, filter and pagination


def test_search_matches_company_or_position_ignoring_case(client, account):
    _, headers = account()
    create_application(client, headers, company="Siemens", position="Python Developer")
    create_application(client, headers, company="DATEV", position="Java Developer")

    by_company = client.get("/applications/", params={"search": "siem"}, headers=headers)
    by_position = client.get("/applications/", params={"search": "PYTHON"}, headers=headers)

    assert companies(by_company) == ["Siemens"]
    assert companies(by_position) == ["Siemens"]


def test_search_treats_percent_sign_as_plain_text(client, account):
    _, headers = account()
    create_application(client, headers, company="100% Remote GmbH")
    create_application(client, headers, company="Acme")

    response = client.get("/applications/", params={"search": "%"}, headers=headers)

    assert companies(response) == ["100% Remote GmbH"]


def test_filter_by_status(client, account):
    _, headers = account()
    offer = create_application(client, headers, company="Offer Company")
    create_application(client, headers, company="Applied Company")
    set_status(client, headers, offer["id"], "offer")

    response = client.get("/applications/", params={"status": "offer"}, headers=headers)

    assert companies(response) == ["Offer Company"]


def test_unknown_status_filter_is_rejected(client, account):
    _, headers = account()

    response = client.get("/applications/", params={"status": "hired"}, headers=headers)

    assert response.status_code == 422


def test_pagination_with_limit_and_offset(client, account):
    _, headers = account()
    for company in ["A", "B", "C", "D", "E"]:
        create_application(client, headers, company=company)

    response = client.get(
        "/applications/", params={"limit": 2, "offset": 2}, headers=headers
    )

    assert companies(response) == ["C", "D"]
    assert response.json()["total"] == 5
    assert response.json()["limit"] == 2
    assert response.json()["offset"] == 2


def test_total_counts_only_matching_applications(client, account):
    _, headers = account()
    for company in ["Siemens", "Siemens Energy", "DATEV"]:
        create_application(client, headers, company=company)

    response = client.get(
        "/applications/", params={"search": "siemens", "limit": 1}, headers=headers
    )

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["total"] == 2


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
def test_invalid_pagination_is_rejected(client, account, params):
    _, headers = account()

    response = client.get("/applications/", params=params, headers=headers)

    assert response.status_code == 422


# Summary


def test_summary_of_new_user_is_all_zero(client, account):
    _, headers = account()

    response = client.get("/applications/summary", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "total": 0,
        "applied": 0,
        "interview": 0,
        "offer": 0,
        "rejected": 0,
    }


def test_summary_counts_each_status(client, account):
    _, headers = account()
    statuses = ["applied", "interview", "interview", "offer", "rejected"]
    for number, status in enumerate(statuses):
        created = create_application(client, headers, company=f"Company {number}")
        if status != "applied":
            set_status(client, headers, created["id"], status)

    response = client.get("/applications/summary", headers=headers)

    assert response.status_code == 200
    assert response.json() == {
        "total": 5,
        "applied": 1,
        "interview": 2,
        "offer": 1,
        "rejected": 1,
    }
