"""
Игровое поле с поддержкой специальных клеток (стена/огонь/апгрейд/деградация).

Ключевые механики:
  — Стена полностью блокирует линию сдвига: ряд/столбец разбивается
    на независимые сегменты, каждый обрабатывается отдельно.
  — Огонь/апгрейд/деградация применяются к плитке, когда та ОСТАНАВЛИВАЕТСЯ
    на клетке. После применения клетка превращается в EMPTY (одноразовая).
  — Плитка на стадии 0, попавшая на деградатор, уничтожается.
"""
import random
import arcade
from typing import Callable, Optional

from src.game.evolution_chain import EVOLUTION_CHAIN
from src.game.tile import EvolutionTile
from src.game.modes import ModeConfig, MODE_CONFIGS, DEFAULT_MODE
from src.game.grid_layout import GridLayout, compute_layout
from src.game.cell_types import CellType
from src.game.map_loader import MapConfig, DEFAULT_MAP

SoundCallback = Callable[[str, float], None]


class GameBoard:
    """
    layout   → GridLayout для размеров поля
    mode_cfg → режим (таймер, бонусы)
    map_cfg  → карта (клеточный грид)
    sound_cb → колбэк звука
    """

    def __init__(self,
                 layout:   Optional[GridLayout] = None,
                 mode_cfg: Optional[ModeConfig] = None,
                 map_cfg:  Optional[MapConfig]  = None,
                 sound_cb: Optional[SoundCallback] = None):
        self._map_cfg = map_cfg or DEFAULT_MAP
        self._layout  = layout or compute_layout(self._map_cfg.rows, self._map_cfg.cols)
        self._mode    = mode_cfg or MODE_CONFIGS[DEFAULT_MODE]
        self._play    = sound_cb or (lambda _n, _v: None)

        # Мутабельная копия клеточного грида (клетки-эффекты расходуются)
        self._cells: list[list[CellType]] = [
            list(row) for row in self._map_cfg.cells
        ]

        self.tiles:     arcade.SpriteList        = arcade.SpriteList(use_spatial_hash=True)
        self.tile_dict: dict[str, EvolutionTile] = {}

        self.score        = 0
        self.game_over    = False
        self.won          = False
        self.lose_reason  = ""

        self.input_locked    = False
        self.spawn_pending   = False
        self.wait_counter    = 0
        self.max_wait_frames = 120

        self.timer            = self._mode.initial_time
        self.merges_this_move = 0
        self.session_time     = 0.0

        # События для UI (GameView может их прочитать и сбросить)
        self.cell_events: list[dict] = []

    @property
    def rows(self) -> int: return self._layout.rows
    @property
    def cols(self) -> int: return self._layout.cols

    # ── Клетки ────────────────────────────────────────────────

    def cell_at(self, row: int, col: int) -> CellType:
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self._cells[row][col]
        return CellType.WALL   # за границей — считаем стеной

    def _is_wall(self, row: int, col: int) -> bool:
        return self.cell_at(row, col) == CellType.WALL

    # ── Плитки ────────────────────────────────────────────────

    def add_random_tile(self, animate: bool = True) -> bool:
        """Ставит случайную плитку в любую пустую клетку (кроме стен)."""
        empty = [
            (r, c)
            for r in range(self.rows) for c in range(self.cols)
            if f"{r}{c}" not in self.tile_dict
            and self._cells[r][c] != CellType.WALL
        ]
        if not empty:
            return False
        row, col = random.choice(empty)
        stage    = 0 if random.random() < 0.9 else 1
        tile     = EvolutionTile(stage, row, col,
                                 layout=self._layout,
                                 animate_spawn=animate)
        self.tiles.append(tile)
        self.tile_dict[f"{row}{col}"] = tile
        return True

    # ── Сегменты для сдвига ───────────────────────────────────

    def _collect_segments(self, direction: str, index: int
                          ) -> list[tuple[list[EvolutionTile], list[tuple[int, int]]]]:
        """
        Возвращает список сегментов: [(tiles, target_positions), ...]
        Стены разрывают линию на сегменты. В каждом сегменте tiles и
        target_positions упорядочены по направлению сдвига: первая плитка
        списка окажется на первой позиции сегмента.
        """
        segments: list[tuple[list[EvolutionTile], list[tuple[int, int]]]] = []
        cur_tiles: list[EvolutionTile] = []
        cur_slots: list[tuple[int, int]] = []

        def finalize() -> None:
            # Сегмент добавляем, только если в нём есть хотя бы один слот
            if cur_slots:
                segments.append((cur_tiles.copy(), cur_slots.copy()))
            cur_tiles.clear()
            cur_slots.clear()

        horizontal = direction in ("left", "right")
        if horizontal:
            row = index
            seq = range(self.cols) if direction == "left" else reversed(range(self.cols))
            for c in seq:
                if self._is_wall(row, c):
                    finalize()
                    continue
                cur_slots.append((row, c))
                t = self.tile_dict.get(f"{row}{c}")
                if t:
                    cur_tiles.append(t)
        else:
            col = index
            seq = range(self.rows) if direction == "up" else reversed(range(self.rows))
            for r in seq:
                if self._is_wall(r, col):
                    finalize()
                    continue
                cur_slots.append((r, col))
                t = self.tile_dict.get(f"{r}{col}")
                if t:
                    cur_tiles.append(t)
        finalize()
        return segments

    def _process_segment(self, tiles: list[EvolutionTile],
                         target_slots: list[tuple[int, int]]) -> bool:
        """Сливает и размещает плитки в target_slots."""
        if not tiles:
            return False

        changed = False
        merged_keys: set[str] = set()
        result: list[EvolutionTile] = []

        # Шаг 1: слияния одинаковых соседей
        for tile in tiles:
            if result:
                last = result[-1]
                if tile.can_merge_with(last) and last.get_key() not in merged_keys:
                    last.upgrade()
                    self.score += 2 ** (last.stage_index + 1)
                    self.merges_this_move += 1
                    merged_keys.add(last.get_key())
                    tile._marked_for_removal = True
                    self.tile_dict.pop(tile.get_key(), None)
                    tile.remove_from_sprite_lists()
                    self._play("merge", 0.7)
                    changed = True
                    continue
            result.append(tile)

        # Шаг 2: сдвиги в таргет-позиции сегмента
        for idx, tile in enumerate(result):
            if tile._marked_for_removal:
                continue
            new_r, new_c = target_slots[idx]
            if tile.row != new_r or tile.col != new_c:
                self.tile_dict.pop(f"{tile.row}{tile.col}", None)
                tile.start_move_to(new_r, new_c)
                self.tile_dict[f"{new_r}{new_c}"] = tile
                changed = True
        return changed

    def move_direction(self, direction: str) -> bool:
        if direction not in ("up", "down", "left", "right") or self.input_locked:
            return False
        self.input_locked     = True
        self.spawn_pending    = False
        self.wait_counter     = 0
        self.merges_this_move = 0

        indices = range(self.rows) if direction in ("left", "right") else range(self.cols)
        moved   = False
        for idx in indices:
            for tiles, slots in self._collect_segments(direction, idx):
                if self._process_segment(tiles, slots):
                    moved = True

        self._cleanup_removed()
        if moved:
            self.spawn_pending = True
            self._play("move", 0.3)
        else:
            self.input_locked = False
        return moved

    def _cleanup_removed(self) -> None:
        for tile in list(self.tiles):
            if getattr(tile, "_marked_for_removal", False):
                tile.remove_from_sprite_lists()

    # ── Завершение хода ───────────────────────────────────────

    def _try_finish_move(self) -> None:
        if not self.spawn_pending or not self.input_locked:
            return
        self.wait_counter += 1
        if self.wait_counter >= self.max_wait_frames:
            self._finish_move()
            return
        active = [t for t in self.tile_dict.values() if not t._marked_for_removal]
        if all(not t.is_moving and not t.spawn_anim for t in active):
            self._finish_move()

    def _apply_cell_effects(self) -> None:
        """
        Применяет эффекты клеток ко всем плиткам, остановившимся на них.
        После применения клетка становится EMPTY (одноразовая).
        Заполняет self.cell_events для UI (для спавна частиц).
        """
        used_cells: list[tuple[int, int]] = []

        for tile in list(self.tile_dict.values()):
            if tile._marked_for_removal:
                continue
            cell = self._cells[tile.row][tile.col]

            if cell == CellType.FIRE:
                self.cell_events.append({
                    "type": "fire",
                    "x": tile.center_x, "y": tile.center_y,
                })
                tile._marked_for_removal = True
                self.tile_dict.pop(f"{tile.row}{tile.col}", None)
                tile.remove_from_sprite_lists()
                used_cells.append((tile.row, tile.col))
                self._play("lose", 0.35)

            elif cell == CellType.UPGRADE:
                if tile.stage_index < len(EVOLUTION_CHAIN) - 1:
                    self.cell_events.append({
                        "type": "upgrade",
                        "x": tile.center_x, "y": tile.center_y,
                    })
                    tile.upgrade()
                    self.score += 2 ** (tile.stage_index + 1)
                    used_cells.append((tile.row, tile.col))
                    self._play("merge", 0.6)

            elif cell == CellType.DEGRADE:
                self.cell_events.append({
                    "type": "degrade",
                    "x": tile.center_x, "y": tile.center_y,
                })
                destroyed = tile.degrade()
                if destroyed:
                    tile._marked_for_removal = True
                    self.tile_dict.pop(f"{tile.row}{tile.col}", None)
                    tile.remove_from_sprite_lists()
                used_cells.append((tile.row, tile.col))
                self._play("move", 0.4)

        # Гасим использованные клетки
        for r, c in used_cells:
            self._cells[r][c] = CellType.EMPTY

        self._cleanup_removed()

    def _finish_move(self) -> None:
        # Бонус времени
        if self._mode.time_per_merge > 0 and self._mode.initial_time > 0:
            capped      = min(self.merges_this_move, self._mode.merge_time_cap)
            self.timer += capped * self._mode.time_per_merge
        self.merges_this_move = 0

        # Эффекты клеток
        self._apply_cell_effects()

        self.add_random_tile(animate=True)
        self.spawn_pending = False
        self._check_game_state()
        self.input_locked  = False
        self.wait_counter  = 0

    # ── Проверка состояния ────────────────────────────────────

    def _check_game_state(self) -> None:
        if not self.tile_dict:
            return
        max_stage = max(t.stage_index for t in self.tile_dict.values())
        if max_stage >= len(EVOLUTION_CHAIN) - 1:
            self.won = True
            self._play("win", 0.9)
            return

        # Клетки, в которые можно поставить тайл
        placeable = sum(
            1
            for r in range(self.rows) for c in range(self.cols)
            if self._cells[r][c] != CellType.WALL
        )
        if len(self.tile_dict) >= placeable and not self._has_moves():
            self.game_over   = True
            self.lose_reason = "no_moves"
            self._play("lose", 0.6)

    def _has_moves(self) -> bool:
        """Проверяет, возможен ли хотя бы один продуктивный ход."""
        # 1. Есть клетки с эффектами под плитками — это всегда даст изменение
        for tile in self.tile_dict.values():
            if self._cells[tile.row][tile.col] != CellType.EMPTY:
                return True

        # 2. Есть соседи для слияния (учитывая стены между ними)
        for tile in self.tile_dict.values():
            for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                nr, nc = tile.row + dr, tile.col + dc
                if not (0 <= nr < self.rows and 0 <= nc < self.cols):
                    continue
                if self._cells[nr][nc] == CellType.WALL:
                    continue
                nb = self.tile_dict.get(f"{nr}{nc}")
                if nb and tile.can_merge_with(nb):
                    return True
        return False

    # ── Сброс ─────────────────────────────────────────────────

    def reset(self) -> None:
        self.tiles     = arcade.SpriteList(use_spatial_hash=True)
        self.tile_dict.clear()
        self._cells = [list(row) for row in self._map_cfg.cells]   # восстановить клетки
        self.score        = 0
        self.game_over    = False
        self.won          = False
        self.lose_reason  = ""
        self.input_locked = False
        self.spawn_pending = False
        self.wait_counter  = 0
        self.timer         = self._mode.initial_time
        self.merges_this_move = 0
        self.session_time     = 0.0
        self.cell_events.clear()
        for _ in range(2):
            self.add_random_tile(animate=False)
