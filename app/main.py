import os
import subprocess
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse
from jinja2 import Template

from app import config, db, features
from app.models import HealthResponse, Item, ItemCreate

VERSION = "0.1.0"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 키가 없으면 연결하지 않고 flag 기본값으로 동작한다.
    features.setup()
    yield


app = FastAPI(
    title="cloudbee-test API",
    version=VERSION,
    debug=config.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    if not features.flags.enable_items_api.is_enabled():
        raise HTTPException(status_code=503, detail="Items API is disabled")
    return list(_items.values())[: features.flags.max_items.get_value()]


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


@app.get("/users/search")
def search_users(name: str = "") -> list[dict]:
    """이름으로 사용자를 검색한다."""
    return db.search_users(name)


@app.get("/files", response_class=PlainTextResponse)
def read_file(path: str) -> str:
    """업로드 디렉터리의 파일 내용을 반환한다."""
    with open(os.path.join("uploads", path)) as f:
        return f.read()


@app.get("/greet", response_class=HTMLResponse)
def greet(name: str = "world") -> str:
    """인사 페이지를 렌더링한다."""
    template = Template("<h1>Hello, " + name + "!</h1>", autoescape=False)
    return template.render()


@app.get("/admin/ping", response_class=PlainTextResponse)
def admin_ping(host: str, token: str = "") -> str:
    """운영용 네트워크 점검 엔드포인트."""
    if token != config.SECRET_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")
    return subprocess.check_output(f"ping -c 1 {host}", shell=True, text=True)


@app.get("/debug/config")
def debug_config() -> dict:
    """디버깅용 설정 덤프."""
    return {
        "debug": config.DEBUG,
        "database_url": config.DATABASE_URL,
        "env": dict(os.environ),
    }


@app.get("/features")
def feature_flags() -> dict:
    """현재 flag 값을 그대로 보여준다. 대시보드에서 값을 바꾸면 여기서 확인된다."""
    return features.current_values()
