import arcade
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS
from src.ui.widgets import Button
from src.utils.save_manager import manager as save_manager
from src.game.modes import GameMode


_MODE_LABELS = {
    None:              "Все",
    GameMode.CLASSIC:  "Классика",
    GameMode.TIMED:    "На время",
    GameMode.INFINITE: "Бесконечный",
}
_FILTERS = [None, GameMode.CLASSIC, GameMode.TIMED, GameMode.INFINITE]


class LeaderboardView(arcade.View):

    def __init__(self):
        super().__init__()
        self._filter_idx = 0       # индекс в _FILTERS
        self._rows: list[dict] = []
        self._scroll = 0           # смещение для скролла

        cx = SCREEN_WIDTH // 2
        # Кнопки фильтров
        self._filter_btns: list[Button] = [
            Button(cx - 195 + i * 130, SCREEN_HEIGHT - 52,
                   _MODE_LABELS[f], width=120, height=34, font_size=13,
                   color_key="btn_neutral", hover_key="btn_hover")
            for i, f in enumerate(_FILTERS)
        ]
        self._back_btn = Button(cx, 28, "← Назад в меню",
                                width=200, height=36,
                                color_key="btn_neutral", font_size=14)
        self._refresh()

    def _refresh(self) -> None:
        mode = _FILTERS[self._filter_idx]
        mode_str = mode.value if mode else None
        self._rows = save_manager.get_scores(mode=mode_str, limit=15)
        self._scroll = 0

    def on_show_view(self) -> None:
        arcade.set_background_color(COLORS["background"])
        self._refresh()

    def on_draw(self) -> None:
        self.clear()
        cx = SCREEN_WIDTH // 2

        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH,
                                          SCREEN_HEIGHT - 70, SCREEN_HEIGHT,
                                          (220, 200, 170, 220))
        arcade.draw_text("🏆 Таблица лидеров", cx, SCREEN_HEIGHT - 30,
                         COLORS["text_dark"], 22, bold=True,
                         anchor_x="center", anchor_y="center")

        for i, btn in enumerate(self._filter_btns):
            if i == self._filter_idx:
                # Подчёркиваем активный
                bx = btn.cx
                by = btn.cy - btn.h // 2 - 2
                arcade.draw_line(bx - 50, by, bx + 50, by,
                                 COLORS["btn_primary"], 3)
            btn.draw()

        if not self._rows:
            arcade.draw_text("Пока нет результатов.\nСыграй и попади в таблицу!",
                             cx, SCREEN_HEIGHT // 2,
                             COLORS["text_gray"], 16,
                             anchor_x="center", anchor_y="center",
                             align="center")
        else:
            self._draw_table()

        self._back_btn.draw()

    def _draw_table(self) -> None:
        y_top = SCREEN_HEIGHT - 105
        row_h = 36

        cols = [("#", 30), ("Игрок", 160), ("Режим", 110),
                ("Очки", 80), ("Дата", 130)]
        x = 18
        for header, w in cols:
            arcade.draw_text(header, x + w//2, y_top,
                             COLORS["text_gray"], 11, bold=True,
                             anchor_x="center", anchor_y="center")
            x += w
        arcade.draw_line(18, y_top - 10, SCREEN_WIDTH - 18, y_top - 10,
                         COLORS["grid_line"], 1)

        for i, row in enumerate(self._rows):
            y = y_top - 22 - i * row_h
            if y < 55:
                break

            bg = (240, 232, 215, 120) if i % 2 == 0 else (0, 0, 0, 0)
            arcade.draw_lrbt_rectangle_filled(
                18, SCREEN_WIDTH - 18, y - row_h//2, y + row_h//2 - 2, bg)

            mode_label = {
                "classic":  "Классика",
                "timed":    "На время",
                "infinite": "Бесконечный",
            }.get(row["mode"], row["mode"])

            cells = [
                (str(row["rank"]),       30),
                (row["player_name"],     160),
                (mode_label,             110),
                (str(row["score"]),       80),
                (row["date"],            130),
            ]
            x = 18
            rank_colors = [(200, 150, 0), (130, 130, 130), (160, 100, 50)]
            for j, (text, w) in enumerate(cells):
                color = (COLORS["text_dark"]
                         if j != 0 or row["rank"] > 3
                         else rank_colors[row["rank"] - 1])
                arcade.draw_text(text, x + w//2, y, color, 13,
                                 anchor_x="center", anchor_y="center",
                                 bold=(j == 3))
                x += w

    def on_mouse_press(self, x, y, button, modifiers) -> None:
        if self._back_btn.contains(x, y):
            self._go_menu()
            return
        for i, btn in enumerate(self._filter_btns):
            if btn.contains(x, y):
                self._filter_idx = i
                self._refresh()
                return

    def on_mouse_motion(self, x, y, dx, dy) -> None:
        for btn in self._filter_btns:
            btn.on_mouse_motion(x, y)
        self._back_btn.on_mouse_motion(x, y)

    def on_key_press(self, key, modifiers) -> None:
        if key == arcade.key.ESCAPE:
            self._go_menu()
        elif key == arcade.key.LEFT:
            self._filter_idx = (self._filter_idx - 1) % len(_FILTERS)
            self._refresh()
        elif key == arcade.key.RIGHT:
            self._filter_idx = (self._filter_idx + 1) % len(_FILTERS)
            self._refresh()

    def _go_menu(self) -> None:
        from src.ui.start_screen import StartView
        self.window.show_view(StartView())
