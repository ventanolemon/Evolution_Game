import sqlite3
from pathlib import Path
from datetime import datetime


DB_PATH    = Path("data") / "leaderboard.db"
MAX_ENTRIES = 100   # максимум записей на один режим

_DDL = """
CREATE TABLE IF NOT EXISTS scores (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    player_name  TEXT    NOT NULL,
    mode         TEXT    NOT NULL,
    score        INTEGER NOT NULL,
    date         TEXT    NOT NULL,
    duration_sec REAL    NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_mode_score ON scores (mode, score DESC);
"""


class SaveManager:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(_DDL)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)


    def save_score(self, player_name: str, mode: str,
                   score: int, duration_sec: float = 0.0) -> None:
        date = datetime.now().strftime("%d.%m.%Y %H:%M")
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO scores (player_name, mode, score, date, duration_sec)"
                " VALUES (?, ?, ?, ?, ?)",
                (player_name.strip()[:30], mode, score, date, round(duration_sec, 1)),
            )
            # Оставляем топ MAX_ENTRIES по очкам внутри режима.
            # Подзапрос выбирает id записей, которые нужно сохранить,
            # внешний DELETE убирает всё остальное для этого же mode.
            conn.execute("""
                DELETE FROM scores
                WHERE mode = ?
                  AND id NOT IN (
                      SELECT id FROM scores
                      WHERE mode = ?
                      ORDER BY score DESC
                      LIMIT ?
                  )
            """, (mode, mode, MAX_ENTRIES))

    def get_scores(self, mode: str | None = None,
                   limit: int = 20) -> list[dict]:
        with self._connect() as conn:
            if mode:
                rows = conn.execute(
                    "SELECT player_name, mode, score, date, duration_sec"
                    " FROM scores WHERE mode=? ORDER BY score DESC LIMIT ?",
                    (mode, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT player_name, mode, score, date, duration_sec"
                    " FROM scores ORDER BY score DESC LIMIT ?",
                    (limit,),
                ).fetchall()

        return [
            {
                "rank":        i + 1,
                "player_name": r[0],
                "mode":        r[1],
                "score":       r[2],
                "date":        r[3],
                "duration_sec": r[4],
            }
            for i, r in enumerate(rows)
        ]

    def has_any(self) -> bool:
        # LIMIT 1 останавливает скан таблицы сразу после первой записи.
        with self._connect() as conn:
            return bool(conn.execute("SELECT 1 FROM scores LIMIT 1").fetchone())


manager = SaveManager()