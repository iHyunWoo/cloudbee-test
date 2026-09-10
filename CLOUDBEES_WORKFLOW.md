# CloudBees 워크플로우 작성 가이드

이 레포(FastAPI 앱)를 CloudBees 플랫폼에서 빌드/테스트할 때 참고할 내용입니다.
워크플로우 YAML은 직접 작성하는 것을 전제로, 문법과 주의점만 정리했습니다.

## 1. 파일 위치

```
.cloudbees/workflows/ci.yaml
```

이 경로(`.cloudbees/workflows/` 하위, `.yaml` 또는 `.yml`)에 있어야 CloudBees 플랫폼이
워크플로우로 인식합니다. 다른 곳에 두면 무시됩니다.

## 2. 기본 뼈대

```yaml
apiVersion: automation.cloudbees.io/v1alpha1
kind: workflow
name: ci

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main
  workflow_dispatch:

jobs:
  test:
    steps:
      - name: Checkout
        uses: cloudbees-io/checkout@v1

      - name: Lint and test
        uses: docker://python:3.12-slim
        run: |
          pip install --no-cache-dir -r requirements-dev.txt
          ruff check .
          pytest -q
```

## 3. 문법 포인트

| 항목 | 내용 |
| --- | --- |
| `apiVersion` / `kind` | 고정값. 없으면 워크플로우로 파싱되지 않습니다 |
| `name` | 플랫폼 UI에 표시되는 워크플로우 이름 |
| `on` | `push`, `pull_request`, `workflow_dispatch`, `schedule` 지원 |
| `uses: cloudbees-io/checkout@v1` | 소스 체크아웃 액션 |
| `uses: docker://<image>` + `run:` | 임의 컨테이너에서 셸 명령 실행 |
| 변수 참조 | `${{ secrets.NAME }}`, `${{ vars.NAME }}`, `${{ cloudbees.scm.sha }}` |

### 가장 자주 걸리는 부분: step 간 상태 공유

같은 job 안에서 **워크스페이스(파일)는 공유되지만, 컨테이너는 step마다 새로 뜹니다.**
따라서 앞 step에서 `pip install`한 패키지는 다음 step에 남지 않습니다.

해결책은 두 가지입니다.

**(A) 한 step에 묶기** — 가장 단순합니다. 위 2번 예시가 이 방식입니다.

**(B) venv를 워크스페이스 안에 만들어 공유하기**

```yaml
      - name: Install
        uses: docker://python:3.12-slim
        run: |
          python -m venv .venv
          .venv/bin/pip install --no-cache-dir -r requirements-dev.txt

      - name: Lint
        uses: docker://python:3.12-slim
        run: .venv/bin/ruff check .

      - name: Test
        uses: docker://python:3.12-slim
        run: .venv/bin/pytest -q
```

`.venv/`는 워크스페이스에 남으므로 다음 step에서 그대로 씁니다.
step을 나눠 어디서 실패했는지 UI에서 바로 보고 싶을 때 이 방식을 쓰세요.

## 4. 스모크 테스트 step (선택)

앱이 실제로 뜨는지까지 확인하려면:

```yaml
      - name: Smoke test
        uses: docker://python:3.12-slim
        run: |
          pip install --no-cache-dir -r requirements.txt
          uvicorn app.main:app --host 127.0.0.1 --port 8000 &
          for i in $(seq 1 30); do
            python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" 2>/dev/null && break
            sleep 1
          done
          python -c "
          import json, urllib.request
          r = json.load(urllib.request.urlopen('http://127.0.0.1:8000/health'))
          print(r)
          assert r['status'] == 'ok'
          "
```

`python:3.12-slim` 이미지에는 `curl`이 없습니다. `curl`을 쓰고 싶으면
`apt-get update && apt-get install -y curl`을 앞에 넣거나, 위처럼 `urllib.request`로 대체하세요.

## 5. 빌드 step

순수 파이썬이라 컴파일은 없지만, CI에서 "빌드"라고 부를 만한 산출물은 두 가지입니다.

### (A) 컨테이너 이미지 — 레포에 `Dockerfile` 있음

로컬 명령:

```bash
docker build -t cloudbee-test:local .
docker run --rm -p 8000:8000 cloudbee-test:local
```

CloudBees에서는 kaniko 액션을 씁니다:

```yaml
  build:
    needs: test
    steps:
      - name: Checkout
        uses: cloudbees-io/checkout@v1

      - name: Build and push image
        uses: cloudbees-io/kaniko@v1
        with:
          destination: your-registry/cloudbee-test:${{ cloudbees.scm.sha }}
          context: .
          dockerfile: Dockerfile
```

레지스트리에 푸시하지 않고 빌드만 검증하려면 `destination`을 빼고 `--no-push`에
해당하는 옵션을 쓰거나, 단순히 docker 이미지 step에서 빌드만 돌려도 됩니다.

### (B) wheel / sdist — 레포에 `pyproject.toml` 있음

```bash
pip install build
python -m build          # dist/cloudbee_test-0.1.0-py3-none-any.whl
```

워크플로우 step:

```yaml
      - name: Build wheel
        uses: docker://python:3.12-slim
        run: |
          pip install --no-cache-dir build
          python -m build
          ls -l dist/
```

`dist/`는 워크스페이스에 남으므로 다음 step에서 아티팩트로 올릴 수 있습니다.

### job 순서

`needs`로 test → build 순서를 잡습니다:

```yaml
jobs:
  test:
    steps: [...]
  build:
    needs: test
    steps: [...]
```

## 6. 이 레포에서 쓰는 명령어

| 목적 | 명령어 |
| --- | --- |
| 의존성 설치 (개발/CI) | `pip install -r requirements-dev.txt` |
| 의존성 설치 (런타임만) | `pip install -r requirements.txt` |
| 린트 | `ruff check .` |
| 테스트 | `pytest -q` |
| 서버 실행 | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| CI 한 줄 | `pip install -r requirements-dev.txt && ruff check . && pytest -q` |
| 이미지 빌드 | `docker build -t cloudbee-test:local .` |
| wheel 빌드 | `pip install build && python -m build` |

현재 테스트는 7케이스이고 로컬(Python 3.14)에서 전부 통과합니다.
빌드 산출물은 컨테이너 이미지(`Dockerfile`) 또는 wheel(`pyproject.toml`) 중 선택하면 됩니다.

## 7. 확인이 필요한 부분

- `cloudbees-io/checkout@v1`의 정확한 버전 태그는 조직의 CloudBees 버전에 따라 다를 수 있습니다.
- `jobs.<job>.kind: build` 같은 job 레벨 옵션(아티팩트 등록 등)도 버전별로 차이가 있습니다.
- 첫 실행에서 파싱 에러가 나면 CloudBees 문서의 action 카탈로그와 대조해 보세요.

## 8. Python 버전 주의

`requirements.txt`의 pydantic은 `>=2.12.0`으로 두었습니다.
Python 3.14에서 `pydantic==2.11.9`는 pydantic-core 휠 빌드가 실패하기 때문입니다.
CI 이미지를 `python:3.12-slim`으로 고정한다면 버전을 다시 pin 해도 됩니다.

## 9. 보안 스캔 테스트

이 레포에는 스캐너 검증용 취약점이 **의도적으로** 심어져 있습니다.
목록과 재현 방법은 `SECURITY_TEST_NOTES.md`를 보세요. 절대 배포하지 마세요.
