"""
Анимированный экран победы с конфетти на физическом движке.

Изменения (v2):
  — Конфетти реализованы как arcade.SpriteSolidColor, а не рисуются
    вручную через draw_polygon_filled.
  — Каждая частица получает свой arcade.PhysicsEngineSimple с невидимым
    полом (floor_wall) — движок обрабатывает гравитацию и отскок.
  — Гравитация применяется вручную через change_y; движок отвечает за
    обнаружение коллизии спрайта с полом и сброс change_y при отскоке.
"""
import math
import random
import arcade
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS
from src.ui.widgets import Button

# Константы физики конфетти
_GRAVITY     = 0.25   # пикселей/кадр² убывания change_y
_BOUNCE      = 0.35   # коэффициент отскока (0 = нет отскока, 1 = упругий)
_FLOOR_Y     = 5      # y-координата пола

_CONFETTI_COLORS = [
    (255, 215,   0),
    (255, 180,  30),
    (255, 255, 100),
    (100, 220, 100),
    (100, 180, 255),
    (255, 100, 200),
]


class ConfettiSprite(arcade.SpriteSolidColor):
    """
    Одна конфетти-частица — полноценный arcade.Sprite.
    Физику (гравитацию + коллизию с полом) обеспечивает
    arcade.PhysicsEngineSimple в WinOverlay.
    """

    def __init__(self, start_y_min: float = SCREEN_HEIGHT,
                       start_y_max: float = SCREEN_HEIGHT + 200):
        color = (*random.choice(_CONFETTI_COLORS), 255)
        w = random.randint(6, 14)
        h = random.randint(5, 10)
        super().__init__(width=w, height=h, color=color)

        self.center_x    = random.uniform(0, SCREEN_WIDTH)
        self.center_y    = random.uniform(start_y_min, start_y_max)
        self.change_x    = random.uniform(-1.5, 1.5)
        self.change_y    = random.uniform(-4.0, -1.5)
        self.change_angle = random.uniform(-3.5, 3.5)

    @property
    def alive(self) -> bool:
        return self.center_y > -30


class WinOverlay:
    """
    Отрисовывается поверх GameView.
    Вызывай .update(dt) и .draw() каждый кадр.

    Конфетти используют arcade.PhysicsEngineSimple:
      — floor_wall — невидимый спрайт-«пол» у нижней границы экрана
      — для каждой частицы создаётся свой PhysicsEngineSimple
      — гравитация применяется вручную (change_y -= _GRAVITY),
        движок отрабатывает коллизию с полом
    """

    MAX_CONFETTI = 100
    SPAWN_RATE   = 8    # штук/сек

    def __init__(self, score: int):
        self.score  = score
        self._timer = 0.0
        self._spawn_acc = 0.0

        # ── Невидимый пол для физического движка ──────────────
        floor = arcade.SpriteSolidColor(
            width=SCREEN_WIDTH * 3, height=10,
            color=(0, 0, 0, 0),
        )
        floor.center_x = SCREEN_WIDTH // 2
        floor.center_y = _FLOOR_Y
        self._floor_wall = arcade.SpriteList(use_spatial_hash=True)
        self._floor_wall.append(floor)

        # ── SpriteList для батч-рендера ────────────────────────
        self._confetti_list: arcade.SpriteList = arcade.SpriteList()

        # Параллельный список физических движков (1 движок = 1 спрайт)
        self._engines: list[arcade.PhysicsEngineSimple] = []

        # Предзаполняем конфетти для мгновенного эффекта
        for _ in range(30):
            self._spawn_one(start_y_min=50, start_y_max=SCREEN_HEIGHT)

        cx = SCREEN_WIDTH  // 2
        cy = SCREEN_HEIGHT // 2
        self._btn_new  = Button(cx - 115, cy - 85, "▶ Играть снова",
                                width=200, height=44,
                                color_key="btn_primary", font_size=16)
        self._btn_menu = Button(cx + 115, cy - 85, "← Меню",
                                width=200, height=44,
                                color_key="btn_neutral", font_size=16)

    # ── Фабрика частиц ────────────────────────────────────────

    def _spawn_one(self, start_y_min: float = SCREEN_HEIGHT,
                         start_y_max: float = SCREEN_HEIGHT + 200) -> None:
        """Создаёт одну конфетти-частицу и регистрирует для неё движок."""
        sp     = ConfettiSprite(start_y_min, start_y_max)
        engine = arcade.PhysicsEngineSimple(sp, self._floor_wall)
        self._confetti_list.append(sp)
        self._engines.append(engine)

    # ── Обновление ────────────────────────────────────────────

    def update(self, dt: float) -> None:
        self._timer     += dt
        self._spawn_acc += self.SPAWN_RATE * dt

        # Добавляем новые конфетти
        while (self._spawn_acc >= 1
               and len(self._confetti_list) < self.MAX_CONFETTI):
            self._spawn_one()
            self._spawn_acc -= 1

        # Применяем гравитацию вручную + обновляем физику
        for sp, engine in zip(self._confetti_list, self._engines):
            sp.change_y -= _GRAVITY
            # При касании пола — имитируем отскок
            if sp.center_y <= _FLOOR_Y + sp.height / 2 + 2:
                sp.change_y = abs(sp.change_y) * _BOUNCE
            engine.update()

        # Удаляем мёртвые частицы и соответствующие движки
        alive_pairs = [
            (sp, eng)
            for sp, eng in zip(self._confetti_list, self._engines)
            if sp.alive
        ]
        if len(alive_pairs) < len(self._engines):
            # Удаляем мёртвые спрайты из SpriteList
            for sp in list(self._confetti_list):
                if not sp.alive:
                    sp.remove_from_sprite_lists()
            self._engines = [eng for _, eng in alive_pairs]

    # ── Отрисовка ─────────────────────────────────────────────

    def draw(self) -> None:
        # Конфетти рисуются батч-вызовом через SpriteList
        self._confetti_list.draw()

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

    # ── Обработка мыши ────────────────────────────────────────

    def on_mouse_motion(self, x: float, y: float) -> None:
        self._btn_new.on_mouse_motion(x, y)
        self._btn_menu.on_mouse_motion(x, y)

    def btn_new_hit(self, x: float, y: float) -> bool:
        return self._btn_new.contains(x, y)

    def btn_menu_hit(self, x: float, y: float) -> bool:
        return self._btn_menu.contains(x, y)