"""SQLite-backed persistence for messages and thread metadata."""

import sqlite3
import threading
import json
from pathlib import Path

_DB_PATH = Path(__file__).parent.parent / "db" / "chat_history.db"


class ChatHistoryService:
    """CRUD operations for conversation history and thread-level metadata."""

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
        """Create/migrate schema and indexes needed by chat history queries."""

        with self._lock:
            cursor = self.conn.cursor()

            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                thread_id TEXT,
                thread_title TEXT,
                role TEXT,
                message TEXT,
                sources TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

            cursor.execute(
                "PRAGMA table_info(chat_history)"
            )

            columns = {
                row[1]
                for row in cursor.fetchall()
            }

            if "thread_id" not in columns:
                cursor.execute(
                    "ALTER TABLE chat_history ADD COLUMN thread_id TEXT"
                )

            if "thread_title" not in columns:
                cursor.execute(
                    "ALTER TABLE chat_history ADD COLUMN thread_title TEXT"
                )

            if "sources" not in columns:
                cursor.execute(
                    "ALTER TABLE chat_history ADD COLUMN sources TEXT"
                )

            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_history(user_id)"
            )

            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_chat_user_thread ON chat_history(user_id, thread_id)"
            )

        self.conn.commit()

    def add_message(
        self,
        user_id,
        thread_id,
        role,
        message,
        sources=None
    ):
        """Insert one user/assistant message row into history."""

        with self._lock:
            cursor = self.conn.cursor()

            cursor.execute(
                """
            INSERT INTO chat_history
            (
                user_id,
                thread_id,
                thread_title,
                role,
                message,
                sources
            )
            VALUES
            (?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    thread_id,
                    None,
                    role,
                    message,
                    json.dumps(sources) if sources else None
                )
            )

            self.conn.commit()

    def get_history(
        self,
        user_id,
        thread_id=None,
        limit=20
    ):
        """Return recent messages for a user, optionally scoped to one thread."""

        with self._lock:
            cursor = self.conn.cursor()

            if thread_id:
                cursor.execute(
                    """
                SELECT role, message
                FROM chat_history
                WHERE user_id=? AND thread_id=?
                ORDER BY id DESC
                LIMIT ?
                """,
                    (
                        user_id,
                        thread_id,
                        limit
                    )
                )
            else:
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
        """Delete all messages for a user (global history clear)."""

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

    def get_threads(
        self,
        user_id,
        limit=50
    ):
        """Return thread summaries for sidebar rendering."""

        with self._lock:
            cursor = self.conn.cursor()

            cursor.execute(
                """
            SELECT
                thread_id,
                COALESCE(
                    MAX(
                        CASE
                            WHEN thread_title IS NOT NULL AND TRIM(thread_title) != '' THEN thread_title
                            ELSE NULL
                        END
                    ),
                    MAX(
                        CASE
                            WHEN role = 'user' THEN SUBSTR(message, 1, 60)
                            ELSE NULL
                        END
                    ),
                    'New Chat'
                ) AS title,
                MAX(created_at) AS updated_at,
                COUNT(*) AS message_count,
                MAX(id) AS max_id
            FROM chat_history
            WHERE user_id=? AND thread_id IS NOT NULL AND TRIM(thread_id) != ''
            GROUP BY thread_id
            ORDER BY max_id DESC
            LIMIT ?
            """,
                (
                    user_id,
                    limit
                )
            )

            rows = cursor.fetchall()

        return [
            {
                "thread_id": row[0],
                "title": row[1],
                "updated_at": row[2],
                "message_count": row[3]
            }
            for row in rows
        ]

    def get_thread_messages(
        self,
        user_id,
        thread_id,
        limit=200
    ):
        """Return ordered messages for one thread to rebuild conversation view."""

        with self._lock:
            cursor = self.conn.cursor()

            cursor.execute(
                """
            SELECT role, message, created_at, sources
            FROM chat_history
            WHERE user_id=? AND thread_id=?
            ORDER BY id ASC
            LIMIT ?
            """,
                (
                    user_id,
                    thread_id,
                    limit
                )
            )

            rows = cursor.fetchall()

        return [
            {
                "role": row[0],
                "content": row[1],
                "created_at": row[2],
                "sources": json.loads(row[3]) if row[3] else None
            }
            for row in rows
        ]

    def delete_thread(
        self,
        user_id,
        thread_id
    ):
        """Delete one thread and all of its messages."""

        with self._lock:
            cursor = self.conn.cursor()

            cursor.execute(
                """
            DELETE FROM chat_history
            WHERE user_id=? AND thread_id=?
            """,
                (
                    user_id,
                    thread_id
                )
            )

            deleted = cursor.rowcount > 0

            self.conn.commit()

        return deleted

    def rename_thread(
        self,
        user_id,
        thread_id,
        title
    ):
        """Persist a custom thread title across all rows of the thread."""

        with self._lock:
            cursor = self.conn.cursor()

            cursor.execute(
                """
            UPDATE chat_history
            SET thread_title=?
            WHERE user_id=? AND thread_id=?
            """,
                (
                    title,
                    user_id,
                    thread_id
                )
            )

            renamed = cursor.rowcount > 0

            self.conn.commit()

        return renamed