"""Вспомогательные математические утилиты."""


def lerp(start: float, end: float, t: float) -> float:
    """Линейная интерполяция: t=0 → start, t=1 → end."""
    return start + (end - start) * min(max(t, 0.0), 1.0)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Ограничивает значение диапазоном [min_val, max_val]."""
    return max(min_val, min(value, max_val))
