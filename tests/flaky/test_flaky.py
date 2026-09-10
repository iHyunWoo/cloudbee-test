"""의도적으로 불안정한 테스트.

Smart Tests의 flaky 탐지·불건전 테스트 리포트를 확인하기 위한 것이다.
실행마다 결과가 달라지므로 CI 판정에는 쓰지 않는다
(워크플로우에서 별도 스위트로 돌리고 실패를 무시한다).
"""

import random
import time

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_flaky_high_failure_rate():
    """약 40% 확률로 실패한다. 가장 눈에 띄는 flaky 후보."""
    assert random.random() > 0.4, "무작위 실패 (의도된 flaky)"


def test_flaky_medium_failure_rate():
    """약 20% 확률로 실패한다."""
    assert random.random() > 0.2, "무작위 실패 (의도된 flaky)"


def test_flaky_low_failure_rate():
    """약 5% 확률로 실패한다. 드물게 터지는 유형."""
    assert random.random() > 0.05, "무작위 실패 (의도된 flaky)"


def test_flaky_timing_dependent():
    """짝수 초에만 통과한다. 시간 의존 테스트의 전형."""
    assert int(time.time()) % 2 == 0, "홀수 초에 실행됨 (시간 의존)"


def test_flaky_order_dependent(client):
    """앞선 테스트가 남긴 상태에 의존한다. 격리되지 않은 테스트의 전형."""
    from app import main

    client.post("/items", json={"name": "leaked", "price": 1})
    assert len(main._items) == 1, "다른 테스트가 남긴 상태 때문에 실패"


def test_slow_but_stable():
    """항상 통과하지만 느리다. 실행시간 리포트용."""
    time.sleep(1.5)
    assert True


def test_moderately_slow():
    """중간 정도로 느린 테스트."""
    time.sleep(0.6)
    assert True
