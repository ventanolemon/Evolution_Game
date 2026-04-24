"""Главное меню."""
import arcade
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS
from src.ui.widgets import Button


class StartView(arcade.View):

    def __init__(self):
        super().__init__()
        cx  = SCREEN_WIDTH  // 2
        mcy = SCREEN_HEIGHT // 2

        self._btn_play = Button(cx, mcy + 30, "▶  Играть",
                                width=240, height=52,
                                color_key="btn_primary", font_size=20)
        self._btn_lb   = Button(cx, mcy - 42, "🏆  Таблица лидеров",
                                width=240, height=42,
                                color_key="btn_neutral", font_size=16)
        self._btn_quit = Button(cx, mcy - 102, "Выход",
                                width=240, height=36,
                                color_key="btn_danger", font_size=14)

    # ── Жизненный цикл ────────────────────────────────────────

    def on_show_view(self) -> None:
        arcade.set_background_color(COLORS["background"])

    # ── Отрисовка ─────────────────────────────────────────────

    def on_draw(self) -> None:
        self.clear()
        cx  = SCREEN_WIDTH  // 2
        cy  = SCREEN_HEIGHT // 2

        # Заголовок
        arcade.draw_text("🧬 ЭВОЛЮЦИЯ", cx, cy + 155,
                         COLORS["text_dark"], 48, bold=True,
                         anchor_x="center", anchor_y="center")
        arcade.draw_text("Соединяй животных — эволюционируй!",
                         cx, cy + 105, COLORS["text_gray"], 16,
                         anchor_x="center", anchor_y="center")

        # Разделитель
        arcade.draw_line(cx - 130, cy + 80, cx + 130, cy + 80,
                         COLORS["grid_line"], 1)

        self._btn_play.draw()
        self._btn_lb.draw()
        self._btn_quit.draw()

        arcade.draw_text("ПРОБЕЛ — начать  •  ESC — выход",
                         cx, 18, COLORS["text_gray"], 11,
                         anchor_x="center", anchor_y="center")

    # ── Управление ────────────────────────────────────────────

    def on_mouse_motion(self, x, y, dx, dy) -> None:
        for btn in (self._btn_play, self._btn_lb, self._btn_quit):
            btn.on_mouse_motion(x, y)

    def on_mouse_press(self, x, y, button, modifiers) -> None:
        if self._btn_play.contains(x, y):
            self._go_mode_select()
        elif self._btn_lb.contains(x, y):
            self._go_leaderboard()
        elif self._btn_quit.contains(x, y):
            arcade.exit()

    def on_key_press(self, key, modifiers) -> None:
        if key in (arcade.key.SPACE, arcade.key.RETURN):
            self._go_mode_select()
        elif key == arcade.key.ESCAPE:
            arcade.exit()

    # ── Навигация ─────────────────────────────────────────────

    def _go_mode_select(self) -> None:
        from src.ui.mode_select import ModeSelectView
        self.window.show_view(ModeSelectView())

    def _go_leaderboard(self) -> None:
        from src.ui.leaderboard_screen import LeaderboardView
        self.window.show_view(LeaderboardView())
