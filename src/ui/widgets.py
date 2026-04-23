"""
Переиспользуемые UI-виджеты для всех экранов.

Button  — прямоугольная кнопка с hover-эффектом.
Panel   — фоновая панель с тенью.
Label   — текстовая метка через arcade.Text (быстрее draw_text).
"""
import arcade
from config import COLORS, BTN_W, BTN_H


# ── Вспомогательная: рисует «скруглённый» прямоугольник ──────────
# Arcade не имеет встроенного rounded_rect, имитируем 3-слойным методом.
def draw_rounded_rect(cx: float, cy: float, w: float, h: float,
                      color: tuple, r: int = 6) -> None:
    """Рисует прямоугольник с псевдо-скруглёнными углами."""
    l, b, rt, t = cx - w/2, cy - h/2, cx + w/2, cy + h/2
    arcade.draw_lrbt_rectangle_filled(l + r, rt - r, b,     t,     color)
    arcade.draw_lrbt_rectangle_filled(l,     rt,     b + r, t - r, color)
    arcade.draw_circle_filled(l  + r, b + r, r, color)
    arcade.draw_circle_filled(rt - r, b + r, r, color)
    arcade.draw_circle_filled(l  + r, t - r, r, color)
    arcade.draw_circle_filled(rt - r, t - r, r, color)


def draw_rounded_rect_outline(cx: float, cy: float, w: float, h: float,
                               color: tuple, r: int = 6, lw: int = 2) -> None:
    l, b, rt, t = cx - w/2, cy - h/2, cx + w/2, cy + h/2
    arcade.draw_line(l + r, b,  rt - r, b,  color, lw)
    arcade.draw_line(l + r, t,  rt - r, t,  color, lw)
    arcade.draw_line(l, b + r,  l,  t - r,  color, lw)
    arcade.draw_line(rt, b + r, rt, t - r,  color, lw)


# ── Button ────────────────────────────────────────────────────────

class Button:
    """
    Кнопка с hover-состоянием.

    Пример:
        btn = Button(cx, cy, "Старт", color_key="btn_primary")
        # В on_mouse_motion:   btn.on_mouse_motion(x, y)
        # В on_draw:           btn.draw()
        # В on_mouse_press:    if btn.is_hovered: do_something()
    """

    def __init__(
        self,
        cx: float, cy: float,
        text: str,
        width:      int   = BTN_W,
        height:     int   = BTN_H,
        color_key:  str   = "btn_primary",
        hover_key:  str   = "",
        font_size:  int   = 17,
        bold:       bool  = True,
        text_color: tuple | None = None,
        radius:     int   = 6,
        subtitle:   str   = "",   # маленькая подпись под текстом
    ):
        self.cx, self.cy = cx, cy
        self.w,  self.h  = width, height
        self.radius      = radius
        self.color_key   = color_key
        self.hover_key   = hover_key or (color_key + "_hover")
        self.is_hovered  = False
        self._text_color = text_color or COLORS["text_light"]

        self._label = arcade.Text(
            text, cx, cy + (8 if subtitle else 0),
            self._text_color, font_size,
            anchor_x="center", anchor_y="center", bold=bold,
        )
        self._sub = arcade.Text(
            subtitle, cx, cy - 12,
            (*COLORS["text_light"][:3], 180), 11,
            anchor_x="center", anchor_y="center",
        ) if subtitle else None

    def on_mouse_motion(self, x: float, y: float) -> None:
        self.is_hovered = (
            abs(x - self.cx) <= self.w / 2 and
            abs(y - self.cy) <= self.h / 2
        )

    def contains(self, x: float, y: float) -> bool:
        return (abs(x - self.cx) <= self.w / 2 and
                abs(y - self.cy) <= self.h / 2)

    def draw(self) -> None:
        key = self.hover_key if self.is_hovered else self.color_key
        color = COLORS.get(key, COLORS["btn_primary"])

        # Тень
        draw_rounded_rect(self.cx + 2, self.cy - 2, self.w, self.h,
                          (0, 0, 0, 50), self.radius)
        # Тело
        draw_rounded_rect(self.cx, self.cy, self.w, self.h,
                          color, self.radius)
        # Контур
        draw_rounded_rect_outline(self.cx, self.cy, self.w, self.h,
                                  (0, 0, 0, 40), self.radius)
        self._label.draw()
        if self._sub:
            self._sub.draw()


# ── Panel ─────────────────────────────────────────────────────────

class Panel:
    """Фоновая панель с тенью."""

    def __init__(self, cx: float, cy: float, w: float, h: float,
                 color: tuple = (255, 255, 255, 200), radius: int = 10):
        self.cx, self.cy = cx, cy
        self.w,  self.h  = w, h
        self.color, self.radius = color, radius

    def draw(self) -> None:
        draw_rounded_rect(self.cx + 3, self.cy - 3,
                          self.w, self.h, (0, 0, 0, 40), self.radius)
        draw_rounded_rect(self.cx, self.cy,
                          self.w, self.h, self.color, self.radius)
