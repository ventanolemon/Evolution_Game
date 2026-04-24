import os
import math
import random
import arcade

from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS
from src.game.board import GameBoard
from src.game.particles import ParticleSystem
from src.game.evolution_chain import EVOLUTION_CHAIN
from src.game.modes import ModeConfig, MODE_CONFIGS, DEFAULT_MODE
from src.game.grid_layout import GridLayout, compute_layout
from src.game.achievements import manager as ach_manager
from src.game.cell_types import CellType, CELL_SPRITES
from src.game.map_loader import MapConfig, DEFAULT_MAP
from src.ui.hud import draw_hud, draw_game_over_overlay
from src.ui.win_screen import WinOverlay

_SHAKE_DURATION  = 0.45   # секунд
_SHAKE_AMPLITUDE = 9.0    # пикселей в начале тряски
# За одну секунду амплитуда упадёт до нуля: AMPLITUDE / DECAY ≈ 0.41 с < DURATION.
_SHAKE_DECAY     = 22.0

_AURA_INTERVAL   = 0.5    # как часто проверять collide спецклеток (в сек)

_cell_textures: dict[CellType, arcade.Texture] = {}
for ct, path in CELL_SPRITES.items():
    if path and os.path.exists(path):
        try:
            _cell_textures[ct] = arcade.load_texture(path)
            print(f"✓ {path}")
        except Exception as exc:
            print(f"⚠ Не загружен {path}: {exc}")


class GameView(arcade.View):

    NOTIF_DURATION = 3.0

    def __init__(self,
                 mode_cfg: ModeConfig | None = None,
                 map_cfg:  MapConfig  | None = None,
                 layout:   GridLayout | None = None):
        super().__init__()
        self._map_cfg  = map_cfg  or DEFAULT_MAP
        self._mode_cfg = mode_cfg or MODE_CONFIGS[DEFAULT_MODE]
        self._layout   = layout   or compute_layout(self._map_cfg.rows, self._map_cfg.cols)

        # board создаётся один раз в setup(), чтобы при рестарте не пересоздавать объект.
        self.board:     GameBoard      = None   # type: ignore
        self.particles: ParticleSystem = ParticleSystem()

        self._cell_sprites: arcade.SpriteList = arcade.SpriteList()

        self._sounds: dict[str, arcade.Sound] = {}
        self._music_on = False

        self._win_overlay: WinOverlay | None = None
        self._notif_queue: list[list] = []

        # Две камеры: game_camera может трястись, ui_camera всегда стабильна —
        # счёт и таймер не дёргаются при проигрыше.
        self._game_camera = arcade.Camera2D()
        self._ui_camera   = arcade.Camera2D()

        self._shake_timer:     float = 0.0
        self._shake_amplitude: float = 0.0
        self._was_game_over:   bool  = False

        self._aura_timer: float = 0.0


    def setup(self) -> None:
        if self.board is None:
            self.board = GameBoard(layout=self._layout,
                                   mode_cfg=self._mode_cfg,
                                   map_cfg=self._map_cfg,
                                   sound_cb=self._play_sound)
            self.board._mode_name = self._mode_cfg.mode.value
            self._load_sounds()
        self.board.reset()
        self._rebuild_cell_sprites()
        self.particles    = ParticleSystem()
        self._win_overlay = None
        self._notif_queue.clear()

        self._shake_timer     = 0.0
        self._shake_amplitude = 0.0
        self._was_game_over   = False
        self._aura_timer      = 0.0

        cx = SCREEN_WIDTH  / 2
        cy = SCREEN_HEIGHT / 2
        self._game_camera.position = (cx, cy)
        self._ui_camera.position   = (cx, cy)

    def _rebuild_cell_sprites(self) -> None:
        self._cell_sprites = arcade.SpriteList()
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                ct = self.board._cells[r][c]
                if ct == CellType.EMPTY:
                    continue
                tex = _cell_textures.get(ct)
                if not tex:
                    continue
                scale = (self._layout.tile_size * 0.85) / max(tex.width, tex.height, 1)
                sp = arcade.Sprite(tex, scale=scale)
                sp.center_x, sp.center_y = self._layout.cell_center(r, c)
                sp.row       = r
                sp.col       = c
                sp.cell_type = ct
                self._cell_sprites.append(sp)

    def _load_sounds(self) -> None:
        effects = {
            "merge": ("assets/sounds/merge.wav", ":resources:sounds/jump1.wav"),
            "move":  ("assets/sounds/move.wav",  ":resources:sounds/phaseJump1.wav"),
            "win":   ("assets/sounds/win.wav",   ":resources:sounds/upgrade1.wav"),
            "lose":  ("assets/sounds/lose.wav",  ":resources:sounds/error2.wav"),
        }
        for name, (primary, fallback) in effects.items():
            for path in (primary, fallback):
                try:
                    self._sounds[name] = arcade.load_sound(path)
                    break
                except Exception:
                    continue

        # Фоновая музыка: загружаем отдельно, храним звук и медиаплеер.
        self._music: arcade.Sound | None = None
        self._music_player = None
        try:
            self._music = arcade.load_sound("assets/sounds/music.wav")
        except Exception:
            pass

    def _play_sound(self, name: str, volume: float = 0.5) -> None:
        s = self._sounds.get(name)
        if s:
            arcade.play_sound(s, volume=volume)

    def _start_music(self) -> None:
        if self._music is None:
            return
        self._stop_music()
        # loop=True обеспечивает бесконечное воспроизведение без ручного перезапуска.
        self._music_player = self._music.play(volume=0.3, loop=True)

    def _stop_music(self) -> None:
        if self._music_player is not None:
            try:
                self._music.stop(self._music_player)
            except Exception:
                pass
            self._music_player = None

    def on_show_view(self) -> None:
        arcade.set_background_color(COLORS["background"])

    def on_hide_view(self) -> None:
        # Останавливаем музыку при уходе с экрана, чтобы она не играла в меню.
        self._stop_music()

    def on_draw(self) -> None:
        self.clear()

        if self._shake_timer > 0:
            dx = random.uniform(-self._shake_amplitude, self._shake_amplitude)
            dy = random.uniform(-self._shake_amplitude, self._shake_amplitude)
            self._game_camera.position = (
                SCREEN_WIDTH  / 2 + dx,
                SCREEN_HEIGHT / 2 + dy,
            )
        else:
            self._game_camera.position = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

        self._game_camera.use()
        self._draw_grid()
        self._cell_sprites.draw()
        self.board.tiles.draw()
        self._draw_tile_overlays()
        self.particles.draw()

        self._ui_camera.use()
        draw_hud(self.board.score, self.board.timer,
                 self._mode_cfg, self._music_on,
                 map_name=self._map_cfg.name)
        if self._win_overlay:
            self._win_overlay.draw()
        elif self.board.game_over:
            draw_game_over_overlay(False, self.board.lose_reason,
                                   self.board.score)
        self._draw_notifications()

    def _draw_grid(self) -> None:
        lay = self._layout
        gx, gy = lay.origin_x, lay.origin_y

        arcade.draw_lrbt_rectangle_filled(
            gx - 4, gx + lay.grid_w + 4,
            gy - lay.grid_h - 4, gy + 4,
            COLORS["grid_bg"],
        )

        for r in range(lay.rows):
            for c in range(lay.cols):
                if self.board._cells[r][c] == CellType.WALL:
                    cx, cy = lay.cell_center(r, c)
                    s = lay.cell_step
                    arcade.draw_lrbt_rectangle_filled(
                        cx - s/2, cx + s/2, cy - s/2, cy + s/2,
                        (70, 55, 45, 180),
                    )

        for i in range(lay.rows + 1):
            y = gy - i * lay.cell_step
            arcade.draw_line(gx, y, gx + lay.grid_w, y, COLORS["grid_line"], 2)
        for j in range(lay.cols + 1):
            x = gx + j * lay.cell_step
            arcade.draw_line(x, gy, x, gy - lay.grid_h, COLORS["grid_line"], 2)

    def _draw_tile_overlays(self) -> None:
        tile_size = self._layout.tile_size
        for tile in self.board.tile_dict.values():
            if tile._marked_for_removal:
                continue
            if tile.merge_effect:
                pulse = 1.0 + 0.15 * abs(math.sin(tile.merge_timer * 0.4))
                s = tile_size * tile.spawn_scale * pulse * 1.4
                arcade.draw_lrbt_rectangle_filled(
                    tile.center_x - s/2, tile.center_x + s/2,
                    tile.center_y - s/2, tile.center_y + s/2,
                    COLORS["merge_flash"],
                )
                # Частицы эмиттируем один раз: на предпоследнем кадре эффекта (25→24).
                if tile.merge_timer == 24:
                    self.particles.emit(tile.center_x, tile.center_y,
                                        (255, 215, 0), count=10)
            arcade.draw_text(
                EVOLUTION_CHAIN[tile.stage_index]["name"],
                tile.center_x, tile.center_y - tile_size // 3,
                COLORS["text_dark"], max(7, tile_size // 17),
                bold=True, anchor_x="center", anchor_y="center",
                width=int(tile_size * 0.9), align="center",
            )

    def _draw_notifications(self) -> None:
        if not self._notif_queue:
            return
        cx = SCREEN_WIDTH // 2
        y  = SCREEN_HEIGHT // 2 + 80
        for item in self._notif_queue[:3]:
            ach = item[0]
            t   = item[1]
            # Плавное появление и исчезновение: нарастает первые 0.25 с, убывает последние 0.25 с.
            alpha = max(0, int(255 * min(1.0, min(t, self.NOTIF_DURATION - t) * 4)))
            arcade.draw_lrbt_rectangle_filled(
                cx - 190, cx + 190, y - 22, y + 22,
                (50, 40, 30, alpha),
            )
            arcade.draw_text(
                f"{ach.emoji}  {ach.title}  — {ach.description}",
                cx, y, (255, 240, 180, alpha), 12, bold=True,
                anchor_x="center", anchor_y="center",
            )
            y -= 52

    def on_update(self, dt: float) -> None:
        b = self.board

        if self._win_overlay:
            self._win_overlay.update(dt)

        b.session_time += dt

        if not b.won and not b.game_over:
            b.tiles.update(dt)
            b.tiles.update_animation(dt)
            b._try_finish_move()
            self.particles.update(dt)

            if b.cell_events:
                for ev in b.cell_events:
                    color = {
                        "fire":    (240, 90,  40),
                        "upgrade": (80,  220, 100),
                        "degrade": (220, 80,  80),
                    }.get(ev["type"], (200, 200, 200))
                    self.particles.emit(ev["x"], ev["y"], color, count=18)
                b.cell_events.clear()
                # Спецклетки израсходованы — перестраиваем спрайты, чтобы убрать исчезнувшие.
                self._rebuild_cell_sprites()

            if self._mode_cfg.initial_time > 0:
                b.timer -= dt
                if b.timer <= 0.0:
                    b.timer       = 0.0
                    b.game_over   = True
                    b.lose_reason = "time"
                    self._play_sound("lose", 0.6)

            self._aura_timer += dt
            if self._aura_timer >= _AURA_INTERVAL and self._cell_sprites:
                self._aura_timer = 0.0
                self._emit_cell_aura()

            # Проверяем достижения не каждый кадр, а раз в ~0.2 с (каждые 2 единицы * 0.1).
            if int(b.session_time * 10) % 20 == 0:
                for a in ach_manager.check(b):
                    self._notif_queue.append([a, self.NOTIF_DURATION])

        # _was_game_over — флаг, чтобы тряска стартовала ровно один раз, а не каждый кадр.
        if b.game_over and not self._was_game_over:
            self._was_game_over   = True
            self._shake_timer     = _SHAKE_DURATION
            self._shake_amplitude = _SHAKE_AMPLITUDE

        if self._shake_timer > 0:
            self._shake_timer     -= dt
            self._shake_amplitude  = max(0.0, self._shake_amplitude - _SHAKE_DECAY * dt)

        if b.won and self._win_overlay is None:
            self._win_overlay = WinOverlay(b.score)
            ach_manager.check(b)
            for a in ach_manager.pop_newly_unlocked():
                self._notif_queue.append([a, self.NOTIF_DURATION])

        for item in self._notif_queue:
            item[1] -= dt
        self._notif_queue = [x for x in self._notif_queue if x[1] > 0]

    def _emit_cell_aura(self) -> None:
        _AURA_COLORS: dict[CellType, tuple] = {
            CellType.FIRE:    (240, 90,  40),
            CellType.UPGRADE: (80,  220, 100),
            CellType.DEGRADE: (220, 80,  80),
        }
        for tile in self.board.tiles:
            # Движущуюся плитку пропускаем: её логическая позиция ещё не совпадает
            # с пикселями спрайта клетки, коллизия дала бы ложное срабатывание.
            if tile._marked_for_removal or tile.is_moving:
                continue
            hits = arcade.check_for_collision_with_list(tile, self._cell_sprites)
            for cell_sp in hits:
                ct = getattr(cell_sp, "cell_type", None)
                color = _AURA_COLORS.get(ct)
                if color:
                    self.particles.emit(
                        tile.center_x, tile.center_y,
                        color, count=4,
                    )

    def on_key_press(self, key, modifiers) -> None:
        b = self.board
        if key == arcade.key.M:
            self._music_on = not self._music_on
            if self._music_on:
                self._start_music()
            else:
                self._stop_music()
            return
        if self._win_overlay:
            if key == arcade.key.R:
                self.setup()
            elif key == arcade.key.ESCAPE:
                self._after_game()
            return
        if b.game_over:
            if key == arcade.key.R:
                self.setup()
            elif key == arcade.key.ESCAPE:
                self._after_game()
            return
        if key == arcade.key.ESCAPE:
            self._go_menu()
            return
        dirs = {
            arcade.key.LEFT:  "left",
            arcade.key.RIGHT: "right",
            arcade.key.UP:    "up",
            arcade.key.DOWN:  "down",
        }
        if key in dirs and not b.input_locked:
            b.move_direction(dirs[key])

    def on_mouse_press(self, x, y, button, modifiers) -> None:
        if self._win_overlay:
            if self._win_overlay.btn_new_hit(x, y):
                self.setup()
            elif self._win_overlay.btn_menu_hit(x, y):
                self._after_game()

    def on_mouse_motion(self, x, y, dx, dy) -> None:
        if self._win_overlay:
            self._win_overlay.on_mouse_motion(x, y)

    def _after_game(self) -> None:
        from src.ui.name_entry import NameEntryView
        from src.ui.start_screen import StartView
        self.window.show_view(
            NameEntryView(
                score           = self.board.score,
                mode_str        = self._mode_cfg.mode.value,
                duration_sec    = self.board.session_time,
                on_done_factory = lambda: StartView(),
            )
        )

    def _go_menu(self) -> None:
        from src.ui.start_screen import StartView
        self.window.show_view(StartView())