"""
Система достижений.

Достижения хранятся в data/achievements.json.
Определения живут прямо здесь — добавить новое = добавить словарь в DEFINITIONS.
Проверка вызывается из GameView после каждого хода и в конце партии.
"""
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable

ACHIEVEMENTS_FILE = Path("data") / "achievements.json"
ACHIEVEMENTS_FILE.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class AchievementDef:
    """Определение одного достижения."""
    id:          str
    title:       str
    description: str
    emoji:       str
    # checker(board, stats) → True если условие выполнено
    checker:     Callable = field(repr=False)


# ── Определения достижений ────────────────────────────────────
# checker получает board (GameBoard) и stats (dict из save_manager)

DEFINITIONS: list[AchievementDef] = [
    AchievementDef(
        id="first_merge", title="Первое слияние", emoji="🔗",
        description="Слей две плитки в первый раз",
        checker=lambda b, s: b.score > 0,
    ),
    AchievementDef(
        id="score_500", title="Полтысячи", emoji="⭐",
        description="Набери 500 очков за одну партию",
        checker=lambda b, s: b.score >= 500,
    ),
    AchievementDef(
        id="score_2000", title="Две тысячи!", emoji="🌟",
        description="Набери 2000 очков за одну партию",
        checker=lambda b, s: b.score >= 2000,
    ),
    AchievementDef(
        id="reach_wolf", title="Вожак стаи", emoji="🐺",
        description="Получи плитку «Волк» (стадия 7)",
        checker=lambda b, s: any(t.stage_index >= 6 for t in b.tile_dict.values()),
    ),
    AchievementDef(
        id="reach_human", title="Homo sapiens", emoji="🧑",
        description="Получи плитку «Человек» (стадия 9)",
        checker=lambda b, s: any(t.stage_index >= 8 for t in b.tile_dict.values()),
    ),
    AchievementDef(
        id="reach_cyborg", title="Киборг создан!", emoji="🤖",
        description="Эволюционируй до Киборга — победи!",
        checker=lambda b, s: b.won,
    ),
    AchievementDef(
        id="games_5", title="Постоянный игрок", emoji="🎮",
        description="Сыграй 5 партий",
        checker=lambda b, s: (s or {}).get("games_played", 0) >= 5,
    ),
    AchievementDef(
        id="survive_timed", title="Гонщик", emoji="⚡",
        description="Выиграй в режиме «На время»",
        checker=lambda b, s: b.won and getattr(b, "_mode_name", "") == "timed",
    ),
    AchievementDef(
        id="infinite_2500", title="Без остановки", emoji="♾",
        description="Набери 2500 очков в Бесконечном режиме",
        checker=lambda b, s: (getattr(b, "_mode_name", "") == "infinite"
                              and b.score >= 2500),
    ),
]

_DEF_MAP = {d.id: d for d in DEFINITIONS}


# ── Менеджер ──────────────────────────────────────────────────

class AchievementManager:
    """Загружает, проверяет и сохраняет достижения."""

    def __init__(self):
        self._unlocked: set[str] = self._load()
        # Буфер для показа в UI (new unlocks за текущий ход)
        self.newly_unlocked: list[AchievementDef] = []

    def _load(self) -> set[str]:
        try:
            data = json.loads(ACHIEVEMENTS_FILE.read_text())
            return set(data.get("unlocked", []))
        except Exception:
            return set()

    def _save(self) -> None:
        ACHIEVEMENTS_FILE.write_text(
            json.dumps({"unlocked": sorted(self._unlocked)}, ensure_ascii=False, indent=2)
        )

    def check(self, board, stats: dict | None = None) -> list[AchievementDef]:
        """
        Проверяет все достижения. Возвращает список только что разблокированных.
        Результаты накапливаются в self.newly_unlocked.
        """
        new: list[AchievementDef] = []
        for d in DEFINITIONS:
            if d.id in self._unlocked:
                continue
            try:
                if d.checker(board, stats):
                    self._unlocked.add(d.id)
                    new.append(d)
            except Exception:
                pass
        if new:
            self._save()
            self.newly_unlocked.extend(new)
        return new

    def is_unlocked(self, achievement_id: str) -> bool:
        return achievement_id in self._unlocked

    def all_with_status(self) -> list[tuple[AchievementDef, bool]]:
        return [(d, d.id in self._unlocked) for d in DEFINITIONS]

    def pop_newly_unlocked(self) -> list[AchievementDef]:
        """Забирает и очищает буфер новых достижений (для отображения в UI)."""
        result = list(self.newly_unlocked)
        self.newly_unlocked.clear()
        return result


# Синглтон
manager = AchievementManager()
