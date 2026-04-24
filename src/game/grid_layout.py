from dataclasses import dataclass
from config import (
    TILE_SIZE, TILE_MARGIN,
    SCREEN_WIDTH, SCREEN_HEIGHT, HUD_TOP, HUD_BOTTOM,
)


@dataclass(frozen=True)
class GridLayout:
    rows:      int
    cols:      int
    tile_size: int
    cell_step: int
    origin_x:  float
    origin_y:  float
    grid_w:    float
    grid_h:    float

    def cell_center(self, row: float, col: float) -> tuple[float, float]:
        x = self.origin_x + col * self.cell_step + self.tile_size // 2
        y = self.origin_y - row * self.cell_step - self.tile_size // 2
        return x, y


def compute_layout(rows: int, cols: int) -> GridLayout:
    avail_w = SCREEN_WIDTH  - TILE_MARGIN
    avail_h = SCREEN_HEIGHT - HUD_TOP - HUD_BOTTOM - TILE_MARGIN

    max_by_w = (avail_w - TILE_MARGIN * (cols - 1)) // cols
    max_by_h = (avail_h - TILE_MARGIN * (rows - 1)) // rows
    tile_size = min(TILE_SIZE, max_by_w, max_by_h)
    cell_step = tile_size + TILE_MARGIN

    grid_w = cols * cell_step - TILE_MARGIN
    grid_h = rows * cell_step - TILE_MARGIN

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
