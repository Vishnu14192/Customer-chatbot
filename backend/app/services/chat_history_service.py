import sqlite3
import threading
from pathlib import Path

_DB_PATH = Path(__file__).parent.parent / "db" / "chat_history.db"


class ChatHistoryService:

    def __init__(self):

        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        db_path = _DB_PATH

        self._lock = threading.Lock()

        self.conn = sqlite3.connect(
            db_path,
            check_same_thread=False
        )

        self.create_table()

    def create_table(self):

        with self._lock:
            cursor = self.conn.cursor()

            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                role TEXT,
                message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        self.conn.commit()

    def add_message(
        self,
        user_id,
        role,
        message
    ):

        with self._lock:
            cursor = self.conn.cursor()

            cursor.execute(
                """
            INSERT INTO chat_history
            (
                user_id,
                role,
                message
            )
            VALUES
            (?, ?, ?)
            """,
                (
                    user_id,
                    role,
                    message
                )
            )

            self.conn.commit()

    def get_history(
        self,
        user_id,
        limit=20
    ):

        with self._lock:
            cursor = self.conn.cursor()

            cursor.execute(
                """
            SELECT role, message
            FROM chat_history
            WHERE user_id=?
            ORDER BY id DESC
            LIMIT ?
            """,
                (
                    user_id,
                    limit
                )
            )

            rows = cursor.fetchall()

        rows.reverse()

        return [
            {
                "role": row[0],
                "content": row[1]
            }
            for row in rows
        ]

    def clear_history(
        self,
        user_id
    ):

        with self._lock:
            cursor = self.conn.cursor()

            cursor.execute(
                """
            DELETE FROM chat_history
            WHERE user_id=?
            """,
                (
                    user_id,
                )
            )

            self.conn.commit()