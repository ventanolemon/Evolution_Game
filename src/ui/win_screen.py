"""
Анимированный экран победы с золотыми частицами.
Показывается поверх GameView когда board.won == True.
"""
import math
import random
import arcade
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS
from src.ui.widgets import Button


class _Confetti:
    """Одна конфетти-частица."""
    COLORS = [
        (255, 215,   0), (255, 180,  30), (255, 255, 100),
        (100, 220, 100), (100, 180, 255), (255, 100, 200),
    ]

    def __init__(self):
        self.x     = random.uniform(0, SCREEN_WIDTH)
        self.y     = random.uniform(SCREEN_HEIGHT, SCREEN_HEIGHT + 200)
        self.vx    = random.uniform(-60, 60)
        self.vy    = random.uniform(-200, -60)
        self.size  = random.uniform(5, 12)
        self.angle = random.uniform(0, 360)
        self.spin  = random.uniform(-180, 180)
        self.color = random.choice(self.COLORS)
        self.alpha = 255

    def update(self, dt: float) -> None:
        self.x     += self.vx * dt
        self.y     += self.vy * dt
        self.angle += self.spin * dt
        # Гравитация
        self.vy    -= 120 * dt
        # Затухание у нижней части экрана
        if self.y < 100:
            self.alpha = max(0, int(255 * self.y / 100))

    @property
    def alive(self) -> bool:
        return self.y > -20 and self.alpha > 0

    def draw(self) -> None:
        if self.alpha > 0:
            s = self.size
            # Рисуем как повёрнутый квадрат
            rad = math.radians(self.angle)
            c, si = math.cos(rad), math.sin(rad)
            pts = [
                (self.x + (-s*c + -s*si), self.y + (-s*si + s*c)),
                (self.x + ( s*c + -s*si), self.y + ( s*si + s*c)),
                (self.x + ( s*c +  s*si), self.y + ( s*si - s*c)),
                (self.x + (-s*c +  s*si), self.y + (-s*si - s*c)),
            ]
            arcade.draw_polygon_filled(pts, (*self.color, self.alpha))


class WinOverlay:
    """
    Отрисовывается поверх GameView.
    Вызывай .update(dt) и .draw() каждый кадр.
    """

    MAX_CONFETTI = 120
    SPAWN_RATE   = 8   # штук/сек

    def __init__(self, score: int):
        self.score      = score
        self._particles: list[_Confetti] = []
        self._timer     = 0.0
        self._spawn_acc = 0.0
        # Предзаполним немного для мгновенного эффекта
        for _ in range(30):
            p = _Confetti()
            p.y = random.uniform(50, SCREEN_HEIGHT)
            self._particles.append(p)

        cx = SCREEN_WIDTH  // 2
        cy = SCREEN_HEIGHT // 2
        self._btn_new  = Button(cx - 115, cy - 85, "▶ Играть снова",
                                width=200, height=44,
                                color_key="btn_primary", font_size=16)
        self._btn_menu = Button(cx + 115, cy - 85, "← Меню",
                                width=200, height=44,
                                color_key="btn_neutral", font_size=16)

    def update(self, dt: float) -> None:
        self._timer     += dt
        self._spawn_acc += self.SPAWN_RATE * dt
        while self._spawn_acc >= 1 and len(self._particles) < self.MAX_CONFETTI:
            self._particles.append(_Confetti())
            self._spawn_acc -= 1
        self._particles = [p for p in self._particles if p.alive]
        for p in self._particles:
            p.update(dt)

    def draw(self) -> None:
        for p in self._particles:
            p.draw()

        cx = SCREEN_WIDTH  // 2
        cy = SCREEN_HEIGHT // 2

        # Полупрозрачный оверлей
        arcade.draw_lrbt_rectangle_filled(
            cx - 265, cx + 265, cy - 110, cy + 120,
            (245, 238, 220, 230),
        )
        arcade.draw_lrbt_rectangle_outline(
            cx - 265, cx + 265, cy - 110, cy + 120,
            COLORS["grid_line"], 2,
        )

        # Пульсирующий заголовок
        pulse = 1.0 + 0.04 * math.sin(self._timer * 4)
        arcade.draw_text(
            "🎉 ПОБЕДА! 🎉",
            cx, cy + 80, COLORS["text_gold"],
            int(36 * pulse), bold=True,
            anchor_x="center", anchor_y="center",
        )
        arcade.draw_text(
            "Вы создали Киборга!",
            cx, cy + 40, COLORS["text_dark"], 18,
            anchor_x="center", anchor_y="center",
        )
        arcade.draw_text(
            f"Итоговый счёт: {self.score}",
            cx, cy + 8, COLORS["text_dark"], 22, bold=True,
            anchor_x="center", anchor_y="center",
        )

        self._btn_new.draw()
        self._btn_menu.draw()

    def on_mouse_motion(self, x: float, y: float) -> None:
        self._btn_new.on_mouse_motion(x, y)
        self._btn_menu.on_mouse_motion(x, y)

    def btn_new_hit(self,  x: float, y: float) -> bool:
        return self._btn_new.contains(x, y)

    def btn_menu_hit(self, x: float, y: float) -> bool:
        return self._btn_menu.contains(x, y)
