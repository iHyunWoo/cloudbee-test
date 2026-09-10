import pytest
from fastapi.testclient import TestClient

from app import main
from app.main import app


@pytest.fixture(autouse=True)
def clean_store():
    main._items.clear()
    main._next_id = 1
    yield


@pytest.fixture
def client():
    return TestClient(app)


def test_root(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.json() == {"message": "cloudbee-test FastAPI app"}


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_create_and_get_item(client):
    res = client.post("/items", json={"name": "honey", "price": 12.5})
    assert res.status_code == 201
    item = res.json()
    assert item["id"] == 1
    assert item["name"] == "honey"

    res = client.get(f"/items/{item['id']}")
    assert res.status_code == 200
    assert res.json() == item


def test_list_items(client):
    client.post("/items", json={"name": "a", "price": 1})
    client.post("/items", json={"name": "b", "price": 2})
    res = client.get("/items")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_get_missing_item_returns_404(client):
    assert client.get("/items/999").status_code == 404


def test_delete_item(client):
    item_id = client.post("/items", json={"name": "x", "price": 1}).json()["id"]
    assert client.delete(f"/items/{item_id}").status_code == 204
    assert client.get(f"/items/{item_id}").status_code == 404


def test_create_item_validation_error(client):
    res = client.post("/items", json={"name": "", "price": -1})
    assert res.status_code == 422


def test_features_endpoint_without_key(client):
    """환경 키가 없으면 연결하지 않고 flag 기본값을 그대로 반환한다."""
    res = client.get("/features")
    assert res.status_code == 200
    body = res.json()
    assert body["connected"] is False
    assert body["enable_items_api"] is True
    assert body["greeting_style"] == "plain"
    assert body["max_items"] == 100
