"""Типы специальных клеток на игровом поле."""
from enum import Enum


class CellType(Enum):
    EMPTY   = "empty"      # обычная проходимая клетка
    WALL    = "wall"       # непроходимая — разрывает линию сдвига
    FIRE    = "fire"       # уничтожает плитку, остановившуюся на ней (одноразово)
    UPGRADE = "upgrade"    # повышает стадию плитки на 1 (одноразово)
    DEGRADE = "degrade"    # понижает стадию плитки на 1 (одноразово; 0 → уничтожение)


# Путь к спрайту каждого типа (None — ничего не рисуем)
CELL_SPRITES: dict[CellType, str | None] = {
    CellType.EMPTY:   None,
    CellType.WALL:    "assets/cells/wall.png",
    CellType.FIRE:    "assets/cells/fire.png",
    CellType.UPGRADE: "assets/cells/upgrade.png",
    CellType.DEGRADE: "assets/cells/degrade.png",
}
