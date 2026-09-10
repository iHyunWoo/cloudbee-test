"""CloudBees Feature Management (Rollout/rox) 연동.

flag의 존재·타입·기본값은 코드가 정의하고, 실제 값은 대시보드에서 바꾼다.
환경 키가 없으면 SDK에 연결하지 않고 각 flag의 기본값으로 동작한다.
"""

import logging
import os

from rox.core.entities.rox_int import RoxInt
from rox.core.entities.rox_string import RoxString
from rox.server.flags.rox_flag import RoxFlag
from rox.server.rox_server import Rox

logger = logging.getLogger(__name__)

ENV_KEY_VAR = "CLOUDBEES_FM_KEY"

# Rox.setup()이 돌려주는 future는 기본적으로 무한 대기한다.
# startup을 막지 않도록 여기서 상한을 둔다.
SETUP_TIMEOUT_SECONDS = 10


class Flags:
    def __init__(self) -> None:
        # 두 번째 인자의 리스트는 대시보드에서 고를 수 있는 값 목록이다.
        self.enable_items_api = RoxFlag(True)
        self.greeting_style = RoxString("plain", ["plain", "excited", "formal"])
        self.max_items = RoxInt(100, [10, 100, 1000])


flags = Flags()

_connected = False


def setup() -> bool:
    """환경 키가 있을 때만 CloudBees에 연결한다.

    앱이 한 번 실행돼야 flag가 대시보드에 등록되므로 startup에서 호출한다.
    """
    global _connected
    key = os.environ.get(ENV_KEY_VAR)
    if not key:
        return False

    Rox.register(flags)
    try:
        # 이미 초기화된 경우 setup()은 None을 돌려준다.
        future = Rox.setup(key)
        if future is not None:
            future.result(timeout=SETUP_TIMEOUT_SECONDS)
    except Exception as exc:  # 연결 실패해도 앱은 기본값으로 계속 뜬다.
        logger.warning("CloudBees Feature Management 연결 실패: %s", exc)
        return False

    _connected = True
    return True


def is_connected() -> bool:
    return _connected


def current_values() -> dict:
    return {
        "connected": _connected,
        "enable_items_api": flags.enable_items_api.is_enabled(),
        "greeting_style": flags.greeting_style.get_value(),
        "max_items": flags.max_items.get_value(),
    }
