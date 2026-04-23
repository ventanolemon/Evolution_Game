"""Система частиц для визуальных эффектов слияния."""
import random
import arcade


class Particle:
    """Одна светящаяся частица."""

    def __init__(self, x: float, y: float, color: tuple):
        self.x = x
        self.y = y
        self.color    = color[:3]   # только RGB
        self.size     = random.uniform(2, 6)
        self.speed_x  = random.uniform(-80, 80)   # пикс/сек
        self.speed_y  = random.uniform(-80, 80)
        self.lifetime = random.uniform(0.3, 0.7)
        self.age      = 0.0

    @property
    def alpha(self) -> int:
        return max(0, int(255 * (1.0 - self.age / self.lifetime)))

    @property
    def alive(self) -> bool:
        return self.age < self.lifetime

    def update(self, dt: float) -> None:
        self.x   += self.speed_x * dt
        self.y   += self.speed_y * dt
        self.age += dt

    def draw(self) -> None:
        a = self.alpha
        if a > 0:
            arcade.draw_circle_filled(self.x, self.y, self.size,
                                      (*self.color, a))


class ParticleSystem:
    """Управляет пулом частиц."""

    def __init__(self):
        self._particles: list[Particle] = []

    def emit(self, x: float, y: float, color: tuple, count: int = 12) -> None:
        """Создаёт `count` частиц в точке (x, y)."""
        for _ in range(count):
            self._particles.append(Particle(x, y, color))

    def update(self, dt: float) -> None:
        self._particles = [p for p in self._particles if p.alive]
        for p in self._particles:
            p.update(dt)

    def draw(self) -> None:
        for p in self._particles:
            p.draw()
