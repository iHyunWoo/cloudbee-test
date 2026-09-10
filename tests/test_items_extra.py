"""파라미터화로 케이스 수를 늘린 정상 테스트. 항상 통과해야 한다."""

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


@pytest.mark.parametrize(
    "name,price",
    [
        ("honey", 12.5),
        ("bee", 0.0),
        ("hive", 999.99),
        ("한글이름", 3.14),
        ("x" * 100, 1.0),
    ],
)
def test_create_item_accepts_valid_payloads(client, name, price):
    res = client.post("/items", json={"name": name, "price": price})
    assert res.status_code == 201
    assert res.json()["name"] == name


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "", "price": 1},
        {"name": "ok", "price": -1},
        {"name": "x" * 101, "price": 1},
        {"price": 1},
        {"name": "ok"},
        {"name": "ok", "price": "비싸다"},
    ],
)
def test_create_item_rejects_invalid_payloads(client, payload):
    assert client.post("/items", json=payload).status_code == 422


@pytest.mark.parametrize("item_id", [0, -1, 999, 10**9])
def test_get_missing_item(client, item_id):
    assert client.get(f"/items/{item_id}").status_code == 404


@pytest.mark.parametrize("count", [1, 3, 10])
def test_list_returns_all_created(client, count):
    for i in range(count):
        client.post("/items", json={"name": f"item-{i}", "price": float(i)})
    assert len(client.get("/items").json()) == count


def test_delete_is_not_idempotent(client):
    item_id = client.post("/items", json={"name": "a", "price": 1}).json()["id"]
    assert client.delete(f"/items/{item_id}").status_code == 204
    assert client.delete(f"/items/{item_id}").status_code == 404


def test_ids_increment(client):
    ids = [
        client.post("/items", json={"name": f"n{i}", "price": 1}).json()["id"]
        for i in range(3)
    ]
    assert ids == sorted(ids) and len(set(ids)) == 3


@pytest.mark.skip(reason="대시보드에서 skip 집계를 확인하기 위한 케이스")
def test_skipped_example():
    raise AssertionError("실행되지 않아야 한다")


@pytest.mark.xfail(reason="알려진 미구현 기능: 아이템 수정")
def test_update_item_not_implemented(client):
    item_id = client.post("/items", json={"name": "a", "price": 1}).json()["id"]
    assert client.put(f"/items/{item_id}", json={"name": "b", "price": 2}).status_code == 200
