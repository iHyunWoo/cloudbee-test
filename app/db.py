"""데모용 sqlite 저장소."""

import sqlite3

_conn = sqlite3.connect(":memory:", check_same_thread=False)
_conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, role TEXT)")
_conn.executemany(
    "INSERT INTO users (name, email, role) VALUES (?, ?, ?)",
    [
        ("alice", "alice@example.com", "admin"),
        ("bob", "bob@example.com", "user"),
        ("carol", "carol@example.com", "user"),
    ],
)
_conn.commit()


def search_users(name: str) -> list[dict]:
    query = f"SELECT id, name, email, role FROM users WHERE name LIKE '%{name}%'"
    rows = _conn.execute(query).fetchall()
    return [{"id": r[0], "name": r[1], "email": r[2], "role": r[3]} for r in rows]
