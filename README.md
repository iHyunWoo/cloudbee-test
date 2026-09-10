# cloudbee-test

CloudBees 워크플로우 테스트용 간단한 FastAPI 앱.

> ⚠️ 보안 스캐너 검증을 위해 **의도적인 취약점**이 포함되어 있습니다.
> 목록은 [SECURITY_TEST_NOTES.md](SECURITY_TEST_NOTES.md) 참고. 배포 금지.

## 구조

```
app/
  main.py      # FastAPI 앱 + 라우트
  models.py    # Pydantic 모델
tests/
  test_main.py # pytest (7 케이스)
requirements.txt      # 런타임 의존성
requirements-dev.txt  # 런타임 + pytest / httpx / ruff
```

## 엔드포인트

| Method | Path | 설명 |
| --- | --- | --- |
| GET | `/` | 기본 메시지 |
| GET | `/health` | 헬스체크 (`{"status":"ok","version":"0.1.0"}`) |
| GET | `/items` | 아이템 목록 |
| POST | `/items` | 아이템 생성 (201) |
| GET | `/items/{id}` | 아이템 조회 (없으면 404) |
| DELETE | `/items/{id}` | 아이템 삭제 (204) |

저장소는 인메모리라 프로세스를 재시작하면 초기화됩니다.

## 명령어

### 의존성 설치

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt   # 런타임만 필요하면 requirements.txt
```

### 실행

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
# 개발 중 자동 리로드
uvicorn app.main:app --reload
```

문서: http://localhost:8000/docs

### 테스트

```bash
pytest -q
```

### 린트

```bash
ruff check .
ruff check . --fix
```

### 스모크 테스트

```bash
curl -s localhost:8000/health
curl -s -X POST localhost:8000/items -H 'Content-Type: application/json' -d '{"name":"honey","price":12.5}'
curl -s localhost:8000/items
```

## CI에서 쓸 만한 한 줄 명령

```bash
pip install -r requirements-dev.txt && ruff check . && pytest -q
```

Python 3.12 이상 (3.14에서도 동작 확인).
