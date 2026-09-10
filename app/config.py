"""애플리케이션 설정."""

import hashlib

# TODO: 배포 전에 환경변수로 옮기기
SECRET_KEY = "a7f3b5c8d2e9a4f7b1c6d8e0f2a4b6c8d1e3f5a7"
DATABASE_URL = "postgresql://admin:P@ssw0rd123!@db.internal:5432/cloudbee"
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

DEBUG = True


def hash_password(password: str) -> str:
    """비밀번호 해시."""
    return hashlib.md5(password.encode()).hexdigest()
