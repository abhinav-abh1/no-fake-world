import uuid

from fastapi.testclient import TestClient

PAYLOAD = {
    "name": "BBC News",
    "feed_url": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "country": "GB",
    "language": "en",
}


def test_create_then_list_source(client: TestClient) -> None:
    created = client.post("/sources", json=PAYLOAD)
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "BBC News"
    assert body["is_active"] is True

    listed = client.get("/sources")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [body["id"]]


def test_duplicate_feed_url_is_rejected(client: TestClient) -> None:
    assert client.post("/sources", json=PAYLOAD).status_code == 201
    second = client.post("/sources", json=PAYLOAD)
    assert second.status_code == 409


def test_invalid_payload_is_rejected(client: TestClient) -> None:
    bad = client.post("/sources", json={**PAYLOAD, "country": "GBR"})
    assert bad.status_code == 422


def test_get_unknown_source_returns_404(client: TestClient) -> None:
    response = client.get(f"/sources/{uuid.uuid4()}")
    assert response.status_code == 404


def test_database_health(client: TestClient) -> None:
    assert client.get("/health/db").json() == {"status": "ok"}


def test_url_without_host_is_rejected(client: TestClient) -> None:
    bad = client.post("/sources", json={**PAYLOAD, "feed_url": "https://"})
    assert bad.status_code == 422


def test_country_is_stored_in_capitals(client: TestClient) -> None:
    response = client.post("/sources", json={**PAYLOAD, "country": "gb"})
    assert response.status_code == 201
    assert response.json()["country"] == "GB"
