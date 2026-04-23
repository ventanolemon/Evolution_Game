from enum import Enum
from dataclasses import dataclass
from config import (
    TIMER_CLASSIC, TIME_PER_MERGE_CLASSIC, MERGE_TIME_CAP_CLASSIC,
    TIMER_TIMED, TIMER_INFINITE,
)


class GameMode(Enum):
    CLASSIC  = "classic"
    TIMED    = "timed"
    INFINITE = "infinite"


@dataclass(frozen=True)
class ModeConfig:
    mode:           GameMode
    label:          str
    description:    str
    emoji:          str
    initial_time:   float
    time_per_merge: float
    merge_time_cap: int
    accent_color:   str

MODE_CONFIGS: dict[GameMode, ModeConfig] = {
    GameMode.CLASSIC: ModeConfig(
        mode           = GameMode.CLASSIC,
        label          = "Классика",
        description    = f"{int(TIMER_CLASSIC)}с • +{TIME_PER_MERGE_CLASSIC}с за слияние",
        emoji          = "⏱",
        initial_time   = TIMER_CLASSIC,
        time_per_merge = TIME_PER_MERGE_CLASSIC,
        merge_time_cap = MERGE_TIME_CAP_CLASSIC,
        accent_color   = "mode_classic",
    ),
    GameMode.TIMED: ModeConfig(
        mode           = GameMode.TIMED,
        label          = "На время",
        description    = f"{int(TIMER_TIMED)}с • без бонусов",
        emoji          = "⚡",
        initial_time   = TIMER_TIMED,
        time_per_merge = 0.0,
        merge_time_cap = 0,
        accent_color   = "mode_timed",
    ),
    GameMode.INFINITE: ModeConfig(
        mode           = GameMode.INFINITE,
        label          = "Бесконечный",
        description    = "Без таймера • до конца ходов",
        emoji          = "♾",
        initial_time   = TIMER_INFINITE,
        time_per_merge = 0.0,
        merge_time_cap = 0,
        accent_color   = "mode_infinite",
    ),
}

DEFAULT_MODE = GameMode.CLASSIC
