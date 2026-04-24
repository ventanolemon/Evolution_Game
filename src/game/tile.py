import os
import arcade

from src.game.evolution_chain import EVOLUTION_CHAIN, BG_COLORS
from src.utils.helpers import lerp

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.game.grid_layout import GridLayout


def _load_textures() -> list[arcade.Texture]:
    textures: list[arcade.Texture] = []
    for i, stage in enumerate(EVOLUTION_CHAIN):
        path = stage["image"]
        try:
            if os.path.exists(path):
                textures.append(arcade.load_texture(path))
                print(f"✓ {path}")
            else:
                print(f"⚠ Не найден: {path} — заглушка")
                textures.append(arcade.make_circle_texture(64, BG_COLORS[i % len(BG_COLORS)]))
        except Exception as exc:
            print(f"⚠ Ошибка загрузки {path}: {exc}")
            textures.append(arcade.make_circle_texture(64, BG_COLORS[i % len(BG_COLORS)]))
    return textures


EVOLUTION_TEXTURES: list[arcade.Texture] = _load_textures()


class EvolutionTile(arcade.Sprite):
    def __init__(self, stage_index: int, row: int, col: int,
                 layout: "GridLayout",
                 animate_spawn: bool = True):
        texture = EVOLUTION_TEXTURES[stage_index]
        scale   = (layout.tile_size * 0.75) / max(texture.width, texture.height, 1)
        super().__init__(texture, scale=scale)

        self._layout     = layout
        self.stage_index = stage_index

        self.row, self.col   = row, col          # целевая клетка (логические координаты)
        self.vrow, self.vcol = float(row), float(col)  # текущая позиция во время анимации
        self.trow, self.tcol = row, col          # целевая клетка активного перемещения

        self.is_moving   = False
        self.progress    = 0.0
        self.move_speed  = 0.18

        self.merge_effect = False
        self.merge_timer  = 0

        self.spawn_anim  = animate_spawn
        self.spawn_scale = 0.0 if animate_spawn else 1.0

        self.bg_color: tuple = BG_COLORS[stage_index % len(BG_COLORS)]
        self._marked_for_removal = False

        self.center_x, self.center_y = layout.cell_center(row, col)

    def start_move_to(self, row: int, col: int) -> None:
        if self.row == row and self.col == col:
            return
        self.trow, self.tcol = row, col
        self.is_moving = True
        self.progress  = 0.0

    def on_merge(self) -> None:
        self.merge_effect = True
        self.merge_timer  = 25

    def _apply_stage_change(self) -> None:
        new_tex      = EVOLUTION_TEXTURES[self.stage_index]
        self.texture = new_tex
        self.scale   = (self._layout.tile_size * 0.75) / max(new_tex.width, new_tex.height, 1)
        self.bg_color = BG_COLORS[self.stage_index % len(BG_COLORS)]

    def upgrade(self) -> None:
        if self.stage_index < len(EVOLUTION_TEXTURES) - 1:
            self.stage_index += 1
            self._apply_stage_change()
            self.on_merge()

    def degrade(self) -> bool:
        if self.stage_index == 0:
            return True
        self.stage_index -= 1
        self._apply_stage_change()
        self.on_merge()
        return False

    def can_merge_with(self, other: "EvolutionTile") -> bool:
        # merge_effect активен сразу после слияния — блокирует повторное слияние в том же ходу.
        return self.stage_index == other.stage_index and not self.merge_effect

    def get_key(self) -> str:
        # Во время движения плитка уже зарезервировала целевую клетку в tile_dict,
        # поэтому ключ берётся по trow/tcol, а не по текущей анимационной позиции.
        if self.is_moving:
            return f"{self.trow}{self.tcol}"
        return f"{self.row}{self.col}"

    def update(self, delta_time: float = 1 / 60) -> None:
        if self.spawn_anim:
            self.spawn_scale = min(1.0, self.spawn_scale + 0.12)
            if self.spawn_scale >= 1.0:
                self.spawn_anim = False

        if self.is_moving:
            self.progress += self.move_speed
            if self.progress >= 1.0:
                self.progress  = 1.0
                self.is_moving = False
                self.row,  self.col  = self.trow, self.tcol
                self.vrow, self.vcol = float(self.row), float(self.col)
            else:
                self.vrow = lerp(float(self.row), float(self.trow), self.progress)
                self.vcol = lerp(float(self.col), float(self.tcol), self.progress)
            self.center_x, self.center_y = self._layout.cell_center(self.vrow, self.vcol)
        else:
            self.center_x, self.center_y = self._layout.cell_center(self.row, self.col)

        if self.merge_effect:
            self.merge_timer -= 1
            if self.merge_timer <= 0:
                self.merge_effect = False

    def update_animation(self, delta_time: float = 1 / 60) -> None:
        pass