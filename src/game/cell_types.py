from enum import Enum


class CellType(Enum):
    EMPTY   = "empty"
    WALL    = "wall"
    FIRE    = "fire"
    UPGRADE = "upgrade"
    DEGRADE = "degrade"


CELL_SPRITES: dict[CellType, str | None] = {
    CellType.EMPTY:   None,
    CellType.WALL:    "assets/cells/wall.png",
    CellType.FIRE:    "assets/cells/fire.png",
    CellType.UPGRADE: "assets/cells/upgrade.png",
    CellType.DEGRADE: "assets/cells/degrade.png",
}
