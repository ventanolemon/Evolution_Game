"""🧬 Эволюция — точка входа."""
import arcade
from config import SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, FPS
from src.ui.start_screen import StartView


class EvolutionGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE,
                         resizable=False)
        self.set_update_rate(1 / FPS)
        self.show_view(StartView())


def main() -> None:
    print("🚀 Эволюция запускается…")
    print("🎮 ← ↑ → ↓ — ходы  |  R — рестарт  |  M — музыка  |  ESC — меню")
    EvolutionGame()
    arcade.run()


if __name__ == "__main__":
    main()
