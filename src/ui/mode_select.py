"""
Экран выбора режима + карты (Tiled TMX).
"""
import arcade
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS
from src.ui.widgets import Button
from src.game.modes import MODE_CONFIGS, ModeConfig
from src.game.map_loader import load_all_maps, DEFAULT_MAP, MapConfig
from src.game.grid_layout import compute_layout
from src.game.cell_types import CellType


# Цвета для миниатюр клеток
_CELL_PREVIEW_COLORS = {
    CellType.EMPTY:   (230, 215, 185),
    CellType.WALL:    ( 70,  55,  45),
    CellType.FIRE:    (220,  70,  40),
    CellType.UPGRADE: ( 60, 170,  80),
    CellType.DEGRADE: (200,  70,  70),
}


class ModeSelectView(arcade.View):
    """Шаг 1 — выбор режима."""

    def __init__(self):
        super().__init__()
        cx  = SCREEN_WIDTH  // 2
        mcy = SCREEN_HEIGHT // 2

        modes = list(MODE_CONFIGS.values())
        card_w, card_h, gap = 172, 200, 14
        total_w = len(modes) * card_w + (len(modes) - 1) * gap
        x0 = cx - total_w // 2 + card_w // 2
        self._cards = [
            _ModeCard(x0 + i * (card_w + gap), mcy + 20, card_w, card_h, cfg)
            for i, cfg in enumerate(modes)
        ]
        self._back = Button(cx, 28, "← Назад", width=130, height=34,
                            color_key="btn_neutral", font_size=13)

    def on_show_view(self) -> None:
        arcade.set_background_color(COLORS["background"])

    def on_draw(self) -> None:
        self.clear()
        cx = SCREEN_WIDTH // 2
        arcade.draw_text("Выбери режим", cx, SCREEN_HEIGHT - 45,
                         COLORS["text_dark"], 26, bold=True,
                         anchor_x="center", anchor_y="center")
        for c in self._cards: c.draw()
        self._back.draw()
        arcade.draw_text("Клик или Enter — выбрать  •  ESC — назад",
                         cx, 62, COLORS["text_gray"], 11,
                         anchor_x="center", anchor_y="center")

    def on_mouse_motion(self, x, y, dx, dy):
        for c in self._cards: c.on_mouse_motion(x, y)
        self._back.on_mouse_motion(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if self._back.contains(x, y):
            self._go_back(); return
        for card in self._cards:
            if card.contains(x, y):
                self._pick_mode(card.cfg); return

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self._go_back()
        elif key in (arcade.key.RETURN, arcade.key.SPACE):
            for c in self._cards:
                if c.is_hovered:
                    self._pick_mode(c.cfg); return
            self._pick_mode(self._cards[0].cfg)

    def _pick_mode(self, cfg: ModeConfig):
        maps = load_all_maps()
        self.window.show_view(MapSelectView(cfg, maps))

    def _go_back(self):
        from src.ui.start_screen import StartView
        self.window.show_view(StartView())


class MapSelectView(arcade.View):
    """Шаг 2 — выбор карты."""

    def __init__(self, mode_cfg: ModeConfig, maps: list[MapConfig]):
        super().__init__()
        self._mode_cfg = mode_cfg
        self._maps = maps if maps else [DEFAULT_MAP]

        # Пейджинг: 6 карт на страницу
        self._per_page = 6
        self._page = 0

        cx = SCREEN_WIDTH // 2
        self._back = Button(cx - 110, 28, "← Назад",  width=140, height=34,
                            color_key="btn_neutral", font_size=13)
        self._next = Button(cx + 110, 28, "Страница →", width=140, height=34,
                            color_key="btn_neutral", font_size=13)

        self._rebuild_cards()

    def _rebuild_cards(self):
        page_maps = self._maps[self._page * self._per_page:
                               (self._page + 1) * self._per_page]
        cx  = SCREEN_WIDTH  // 2
        mcy = SCREEN_HEIGHT // 2 + 10

        card_w, card_h, gap = 180, 160, 14
        cols = min(3, len(page_maps))
        rows = (len(page_maps) + cols - 1) // cols

        total_w = cols * card_w + (cols - 1) * gap
        x0 = cx - total_w // 2 + card_w // 2

        self._cards: list[_MapCard] = []
        for i, m in enumerate(page_maps):
            r = i // cols
            c = i % cols
            x = x0 + c * (card_w + gap)
            y = mcy + 60 - r * (card_h + gap)
            self._cards.append(_MapCard(x, y, card_w, card_h, m))

    def on_show_view(self):
        arcade.set_background_color(COLORS["background"])

    def on_draw(self):
        self.clear()
        cx = SCREEN_WIDTH // 2
        arcade.draw_text("Выбери карту", cx, SCREEN_HEIGHT - 40,
                         COLORS["text_dark"], 24, bold=True,
                         anchor_x="center", anchor_y="center")
        arcade.draw_text(
            f"Режим: {self._mode_cfg.emoji} {self._mode_cfg.label}",
            cx, SCREEN_HEIGHT - 65, COLORS["text_gray"], 13,
            anchor_x="center", anchor_y="center",
        )
        for c in self._cards: c.draw()
        self._back.draw()
        total_pages = max(1, (len(self._maps) + self._per_page - 1) // self._per_page)
        if total_pages > 1:
            self._next.draw()
            arcade.draw_text(
                f"Страница {self._page + 1} / {total_pages}",
                cx, 62, COLORS["text_gray"], 11,
                anchor_x="center", anchor_y="center",
            )

    def on_mouse_motion(self, x, y, dx, dy):
        for c in self._cards: c.on_mouse_motion(x, y)
        self._back.on_mouse_motion(x, y)
        self._next.on_mouse_motion(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if self._back.contains(x, y):
            self.window.show_view(ModeSelectView()); return
        if self._next.contains(x, y):
            total = (len(self._maps) + self._per_page - 1) // self._per_page
            if total > 1:
                self._page = (self._page + 1) % total
                self._rebuild_cards()
            return
        for card in self._cards:
            if card.contains(x, y):
                _start_game(self.window, self._mode_cfg, card.map_cfg); return

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.show_view(ModeSelectView())


# ── Старт игры ────────────────────────────────────────────────

def _start_game(window, mode_cfg: ModeConfig, map_cfg: MapConfig) -> None:
    from src.ui.game_screen import GameView
    layout = compute_layout(map_cfg.rows, map_cfg.cols)
    view   = GameView(mode_cfg=mode_cfg, map_cfg=map_cfg, layout=layout)
    view.setup()
    window.show_view(view)


# ── Базовая карточка ──────────────────────────────────────────

class _BaseCard:
    def __init__(self, cx, cy, w, h):
        self.cx, self.cy, self.w, self.h = cx, cy, w, h
        self.is_hovered = False

    def on_mouse_motion(self, x, y):
        self.is_hovered = self.contains(x, y)

    def contains(self, x, y):
        return abs(x - self.cx) <= self.w/2 and abs(y - self.cy) <= self.h/2

    def _draw_bg(self, accent):
        cx, cy, w, h = self.cx, self.cy, self.w, self.h
        alpha = 60 if self.is_hovered else 25
        arcade.draw_lrbt_rectangle_filled(
            cx-w/2+3, cx+w/2+3, cy-h/2-3, cy+h/2-3, (0,0,0,30))
        arcade.draw_lrbt_rectangle_filled(
            cx-w/2, cx+w/2, cy-h/2, cy+h/2, (*accent, alpha))
        arcade.draw_lrbt_rectangle_outline(
            cx-w/2, cx+w/2, cy-h/2, cy+h/2, accent, 3 if self.is_hovered else 1)


class _ModeCard(_BaseCard):
    def __init__(self, cx, cy, w, h, cfg: ModeConfig):
        super().__init__(cx, cy, w, h)
        self.cfg = cfg

    def draw(self):
        accent = COLORS.get(self.cfg.accent_color, COLORS["btn_primary"])
        self._draw_bg(accent)
        cx, cy = self.cx, self.cy
        arcade.draw_text(self.cfg.emoji, cx, cy + 60, accent, 36,
                         anchor_x="center", anchor_y="center")
        arcade.draw_text(self.cfg.label, cx, cy + 20,
                         COLORS["text_dark"], 15, bold=True,
                         anchor_x="center", anchor_y="center")
        arcade.draw_text(self.cfg.description, cx, cy - 12,
                         COLORS["text_gray"], 10,
                         anchor_x="center", anchor_y="center",
                         width=int(self.w - 16), align="center")
        bw, bh = self.w - 20, 30
        by     = cy - self.h/2 + bh/2 + 8
        arcade.draw_lrbt_rectangle_filled(
            cx - bw/2, cx + bw/2, by - bh/2, by + bh/2, accent)
        arcade.draw_text("Выбрать", cx, by, COLORS["text_light"], 12, bold=True,
                         anchor_x="center", anchor_y="center")


class _MapCard(_BaseCard):
    """Превью карты с миниатюрой клеточного грида."""

    def __init__(self, cx, cy, w, h, map_cfg: MapConfig):
        super().__init__(cx, cy, w, h)
        self.map_cfg = map_cfg

    def draw(self):
        accent = COLORS["btn_primary"]
        self._draw_bg(accent)
        cx, cy = self.cx, self.cy
        self._draw_grid_preview(cx, cy + 25)

        arcade.draw_text(self.map_cfg.name, cx, cy - 28,
                         COLORS["text_dark"], 13, bold=True,
                         anchor_x="center", anchor_y="center")
        arcade.draw_text(f"{self.map_cfg.rows}×{self.map_cfg.cols}",
                         cx, cy - 45, COLORS["text_gray"], 10,
                         anchor_x="center", anchor_y="center")
        if self.map_cfg.description:
            arcade.draw_text(
                self.map_cfg.description, cx, cy - 60,
                COLORS["text_gray"], 9,
                anchor_x="center", anchor_y="center",
                width=int(self.w - 12), align="center",
            )

    def _draw_grid_preview(self, cx: float, cy: float):
        r, c = self.map_cfg.rows, self.map_cfg.cols
        cell = min(int(60 / max(r, c)), 12)
        gw, gh = c * cell, r * cell
        x0, y0 = cx - gw/2, cy + gh/2      # верхний-левый угол превью
        for ri in range(r):
            for ci in range(c):
                ct = self.map_cfg.cells[ri][ci]
                color = _CELL_PREVIEW_COLORS.get(ct, (220, 210, 180))
                x = x0 + ci * cell
                y = y0 - ri * cell            # рисуем сверху вниз
                arcade.draw_lrbt_rectangle_filled(
                    x + 1, x + cell - 1, y - cell + 1, y - 1,
                    color)
                arcade.draw_lrbt_rectangle_outline(
                    x, x + cell, y - cell, y,
                    (120, 95, 70, 200), 1)
