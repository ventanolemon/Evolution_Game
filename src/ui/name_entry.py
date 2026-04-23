"""
Экран ввода имени игрока после окончания партии.
Использует on_text() — правильный способ ввода текста в arcade.
"""
import arcade
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS, BTN_W, BTN_H
from src.ui.widgets import Panel, Button, draw_rounded_rect
from src.utils.save_manager import manager as save_manager


class NameEntryView(arcade.View):
    """
    Показывается после game_over/won.
    Принимает имя, сохраняет счёт, переходит на следующий экран.
    """

    MAX_LEN = 20

    def __init__(self, score: int, mode_str: str,
                 duration_sec: float, on_done_factory):
        """
        on_done_factory — callable без аргументов,
        возвращающий arcade.View для перехода после сохранения.
        """
        super().__init__()
        self.score        = score
        self.mode_str     = mode_str
        self.duration_sec = duration_sec
        self.on_done      = on_done_factory

        self.name       = ""
        self._blink     = 0       # счётчик кадров для мигающего курсора
        self._saved     = False

        cx = SCREEN_WIDTH  // 2
        cy = SCREEN_HEIGHT // 2

        self._panel = Panel(cx, cy, 420, 260, (245, 238, 220, 245), radius=12)
        self._btn_save = Button(cx, cy - 60, "Сохранить и продолжить",
                                color_key="btn_success")
        self._btn_skip = Button(cx, cy - 115, "Пропустить",
                                color_key="btn_neutral", font_size=14)

    # ── Жизненный цикл ────────────────────────────────────────

    def on_show_view(self) -> None:
        arcade.set_background_color(COLORS["background"])

    # ── Отрисовка ─────────────────────────────────────────────

    def on_draw(self) -> None:
        self.clear()
        cx = SCREEN_WIDTH  // 2
        cy = SCREEN_HEIGHT // 2

        self._panel.draw()

        arcade.draw_text("Введите ваше имя:", cx, cy + 90,
                         COLORS["text_dark"], 20, bold=True,
                         anchor_x="center", anchor_y="center")

        arcade.draw_text(f"Счёт: {self.score}  |  Режим: {self.mode_str}",
                         cx, cy + 55,
                         COLORS["text_gray"], 13,
                         anchor_x="center", anchor_y="center")

        # Поле ввода
        bw, bh = 320, 42
        arcade.draw_lrbt_rectangle_filled(
            cx - bw//2, cx + bw//2, cy - bh//2 + 10, cy + bh//2 + 10,
            (255, 255, 255, 230),
        )
        arcade.draw_lrbt_rectangle_outline(
            cx - bw//2, cx + bw//2, cy - bh//2 + 10, cy + bh//2 + 10,
            COLORS["btn_primary"], 2,
        )
        cursor = "|" if self._blink < 30 else ""
        display = self.name + cursor
        arcade.draw_text(display, cx, cy + 10,
                         COLORS["text_dark"], 18,
                         anchor_x="center", anchor_y="center", bold=True)

        self._btn_save.draw()
        self._btn_skip.draw()

        arcade.draw_text("Enter — сохранить  •  ESC — пропустить",
                         cx, 18, COLORS["text_gray"], 11,
                         anchor_x="center", anchor_y="center")

    # ── Обновление ────────────────────────────────────────────

    def on_update(self, _dt: float) -> None:
        self._blink = (self._blink + 1) % 60

    # ── Ввод ──────────────────────────────────────────────────

    def on_text(self, text: str) -> None:
        """Arcade вызывает on_text для каждого введённого символа."""
        if len(self.name) < self.MAX_LEN and text.isprintable():
            self.name += text

    def on_key_press(self, key, modifiers) -> None:
        if key == arcade.key.BACKSPACE:
            self.name = self.name[:-1]
        elif key == arcade.key.RETURN:
            self._do_save()
        elif key == arcade.key.ESCAPE:
            self._do_skip()

    def on_mouse_press(self, x, y, button, modifiers) -> None:
        if self._btn_save.contains(x, y):
            self._do_save()
        elif self._btn_skip.contains(x, y):
            self._do_skip()

    def on_mouse_motion(self, x, y, dx, dy) -> None:
        self._btn_save.on_mouse_motion(x, y)
        self._btn_skip.on_mouse_motion(x, y)

    # ── Внутренние ────────────────────────────────────────────

    def _do_save(self) -> None:
        name = self.name.strip() or "Игрок"
        save_manager.save_score(name, self.mode_str, self.score, self.duration_sec)
        self._go_next()

    def _do_skip(self) -> None:
        self._go_next()

    def _go_next(self) -> None:
        self.window.show_view(self.on_done())
