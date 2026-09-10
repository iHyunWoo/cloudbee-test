# 보안 스캐너 검증용 노트

> **이 레포는 CloudBees 파이프라인 테스트 전용입니다. 절대 배포하지 마세요.**
> 스캐너가 무엇을 잡고 무엇을 놓치는지 확인하려고 아래 취약점을 **의도적으로** 심어두었습니다.
> 스캔 결과를 이 표와 대조하면 탐지율을 바로 볼 수 있습니다.

## 심어둔 취약점 목록

| # | 위치 | 유형 | CWE | 기대 탐지 도구 |
| --- | --- | --- | --- | --- |
| 1 | `app/config.py:7-10` | 하드코딩된 시크릿 (API 키, DB 비밀번호, AWS 키) | CWE-798 | Secret scanning |
| 2 | `app/config.py:17` | MD5로 비밀번호 해싱 (약한 해시) | CWE-327 / CWE-916 | SAST |
| 3 | `app/db.py:22` | f-string SQL 조립 → SQL Injection | CWE-89 | SAST (taint) |
| 4 | `app/main.py` `/files` | `os.path.join`에 사용자 입력 → Path Traversal | CWE-22 | SAST (taint) |
| 5 | `app/main.py` `/greet` | Jinja2 `autoescape=False` + 사용자 입력 → XSS | CWE-79 | SAST |
| 6 | `app/main.py` `/admin/ping` | `subprocess(..., shell=True)` → Command Injection | CWE-78 | SAST (taint) |
| 7 | `app/main.py` `/debug/config` | 인증 없이 환경변수·DB URL 노출 | CWE-200 | SAST / DAST |
| 8 | `app/main.py` CORS | `allow_origins=["*"]` + `allow_credentials=True` | CWE-942 | SAST |
| 9 | `app/main.py` | `FastAPI(debug=True)` 프로덕션 디버그 모드 | CWE-489 | SAST |
| 10 | `requirements.txt` | `jinja2==3.1.2` (CVE-2024-22195, CVE-2024-34064 등) | - | SCA / 의존성 스캔 |
| 11 | `Dockerfile` | root 유저로 실행, `USER` 지시자 없음 | CWE-250 | 컨테이너 스캔 |

## 재현 방법

### 3번 — SQL Injection

```bash
curl -sG localhost:8000/users/search --data-urlencode "name=' UNION SELECT 1,sqlite_version(),'x','y'--"
```

`LIKE '%...%'` 조건을 우회해 전체 사용자와 sqlite 버전이 함께 반환됩니다. (검증 완료)

### 5번 — XSS

```bash
curl -sG localhost:8000/greet --data-urlencode "name=<script>alert(1)</script>"
# -> <h1>Hello, <script>alert(1)</script>!</h1>
```

이스케이프 없이 그대로 렌더링됩니다. (검증 완료)

### 6번 — Command Injection

```bash
curl -sG localhost:8000/admin/ping \
  --data-urlencode "token=a7f3b5c8d2e9a4f7b1c6d8e0f2a4b6c8d1e3f5a7" \
  --data-urlencode "host=127.0.0.1; id"
```

토큰 자체가 소스에 하드코딩돼 있어 1번 취약점과 연결됩니다.

### 4번 — Path Traversal

```bash
curl -s "localhost:8000/files?path=../requirements.txt"
```

## 참고

- `ruff check .`는 기본 룰셋(pycodestyle/pyflakes)만 돌기 때문에 위 항목을 **하나도 잡지 못합니다.**
  로컬에서 먼저 걸러보고 싶으면 `ruff check --select S .` (bandit 룰) 또는 `bandit -r app/`를 쓰세요.
  스캐너 성능을 순수하게 보려면 CI 린트 설정은 지금 상태로 두는 편이 낫습니다.
- 기존 테스트 7개는 그대로 통과합니다. 취약점은 테스트 커버리지 밖에 있습니다.

## 이미 잡힌 것 (참고)

- **GitHub push protection**이 최초 커밋 시 `SECRET_KEY`의 `sk_live_...` 형태를
  Stripe API 키로 탐지해 푸시를 차단했습니다. 그래서 해당 값은 provider 패턴이 아닌
  일반 hex 문자열로 바꿔 올렸습니다. 여전히 하드코딩된 시크릿(CWE-798)이므로
  SAST 룰에는 걸려야 정상입니다.
- `AWS_ACCESS_KEY_ID`는 AWS 공식 문서의 예제 키라 push protection은 통과했습니다.
  CloudBees 스캐너가 이걸 잡는지 보는 것도 관전 포인트입니다.

## 원복

전부 되돌리려면 이 커밋만 revert 하면 됩니다.
