from fastapi import FastAPI, HTTPException

from app.models import HealthResponse, Item, ItemCreate

VERSION = "0.1.0"

app = FastAPI(title="cloudbee-test API", version=VERSION)

# 데모용 인메모리 저장소 (프로세스 재시작 시 초기화됨)
_items: dict[int, Item] = {}
_next_id = 1


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "cloudbee-test FastAPI app"}


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version=VERSION)


@app.get("/items", response_model=list[Item])
def list_items() -> list[Item]:
    return list(_items.values())


@app.post("/items", response_model=Item, status_code=201)
def create_item(payload: ItemCreate) -> Item:
    global _next_id
    item = Item(id=_next_id, **payload.model_dump())
    _items[item.id] = item
    _next_id += 1
    return item


@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int) -> Item:
    item = _items.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int) -> None:
    if _items.pop(item_id, None) is None:
        raise HTTPException(status_code=404, detail="Item not found")
