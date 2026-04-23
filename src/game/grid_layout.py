"""
GridLayout — вычисляемые параметры сетки для текущей карты.

Создаётся один раз при старте игры (или при смене карты).
Передаётся в GameBoard и EvolutionTile вместо глобальных констант.
"""
from dataclasses import dataclass
from config import (
    TILE_SIZE, TILE_MARGIN, CELL_STEP,
    SCREEN_WIDTH, SCREEN_HEIGHT, HUD_TOP, HUD_BOTTOM,
)


@dataclass(frozen=True)
class GridLayout:
    """Описывает геометрию игрового поля для заданного числа рядов/колонок."""
    rows:      int
    cols:      int
    tile_size: int    # px, сторона плитки
    cell_step: int    # px, шаг сетки (tile + margin)
    origin_x:  float  # px, левый верхний угол сетки (X)
    origin_y:  float  # px, левый верхний угол сетки (Y — arcade: 0 внизу)
    grid_w:    float  # полная ширина сетки
    grid_h:    float  # полная высота сетки

    def cell_center(self, row: float, col: float) -> tuple[float, float]:
        """Центр ячейки (row, col) в экранных координатах."""
        x = self.origin_x + col * self.cell_step + self.tile_size // 2
        y = self.origin_y - row * self.cell_step - self.tile_size // 2
        return x, y


def compute_layout(rows: int, cols: int) -> GridLayout:
    """
    Вычисляет GridLayout для произвольного поля (rows × cols).
    Масштабирует плитку так, чтобы поле всегда вписывалось в окно.
    """
    avail_w = SCREEN_WIDTH  - TILE_MARGIN
    avail_h = SCREEN_HEIGHT - HUD_TOP - HUD_BOTTOM - TILE_MARGIN

    # Максимальный размер плитки при данных rows/cols
    max_by_w = (avail_w - TILE_MARGIN * (cols - 1)) // cols
    max_by_h = (avail_h - TILE_MARGIN * (rows - 1)) // rows
    tile_size = min(TILE_SIZE, max_by_w, max_by_h)   # никогда не больше дефолта
    cell_step = tile_size + TILE_MARGIN

    grid_w = cols * cell_step - TILE_MARGIN
    grid_h = rows * cell_step - TILE_MARGIN

    # Центрирование по горизонтали, прижато к HUD сверху
    origin_x = (SCREEN_WIDTH  - grid_w) / 2
    origin_y = SCREEN_HEIGHT - HUD_TOP - TILE_MARGIN // 2

    return GridLayout(
        rows      = rows,
        cols      = cols,
        tile_size = tile_size,
        cell_step = cell_step,
        origin_x  = origin_x,
        origin_y  = origin_y,
        grid_w    = grid_w,
        grid_h    = grid_h,
    )
