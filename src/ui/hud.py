import arcade
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS, HUD_TOP
from src.game.modes import ModeConfig


def draw_hud(score: int, timer: float, mode_cfg: ModeConfig,
             music_on: bool, map_name: str = "") -> None:
    arcade.draw_lrbt_rectangle_filled(
        0, SCREEN_WIDTH,
        SCREEN_HEIGHT - HUD_TOP, SCREEN_HEIGHT,
        (220, 200, 165, 210),
    )
    arcade.draw_line(0, SCREEN_HEIGHT - HUD_TOP,
                     SCREEN_WIDTH, SCREEN_HEIGHT - HUD_TOP,
                     COLORS["grid_line"], 1)

    arcade.draw_text(f"Счёт: {score}",
                     14, SCREEN_HEIGHT - 18,
                     COLORS["text_dark"], 17, bold=True,
                     anchor_y="center")

    accent = COLORS.get(mode_cfg.accent_color, COLORS["btn_primary"])
    arcade.draw_text(f"{mode_cfg.emoji} {mode_cfg.label}",
                     SCREEN_WIDTH // 2, SCREEN_HEIGHT - 14,
                     accent, 13, bold=True,
                     anchor_x="center", anchor_y="center")
    if map_name:
        arcade.draw_text(f"🗺 {map_name}",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT - 36,
                         COLORS["text_gray"], 11,
                         anchor_x="center", anchor_y="center")

    if mode_cfg.initial_time > 0:
        t_color = COLORS["text_red"] if timer < 10 else COLORS["text_green"]
        arcade.draw_text(f"⏱ {timer:.0f}с",
                         SCREEN_WIDTH - 12, SCREEN_HEIGHT - 18,
                         t_color, 17, bold=True,
                         anchor_x="right", anchor_y="center")

    icon = "🔊" if music_on else "🔇"
    arcade.draw_text(f"{icon} M    ESC — меню    R — рестарт",
                     SCREEN_WIDTH // 2, 14,
                     COLORS["text_gray"], 11,
                     anchor_x="center", anchor_y="center")


def draw_game_over_overlay(lose_reason: str, score: int) -> None:
    cx = SCREEN_WIDTH  // 2
    cy = SCREEN_HEIGHT // 2
    arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT,
                                      (0, 0, 0, 150))
    arcade.draw_lrbt_rectangle_filled(cx-250, cx+250, cy-100, cy+110,
                                      (245, 238, 220, 240))
    arcade.draw_lrbt_rectangle_outline(cx-250, cx+250, cy-100, cy+110,
                                       COLORS["grid_line"], 2)
    if lose_reason == "time":
        headline = "⏰ Время вышло"
        subtitle = "Таймер добежал до нуля"
    elif lose_reason == "no_moves":
        headline = "🚫 Нет ходов"
        subtitle = "Поле заполнено — слияний нет"
    else:
        headline, subtitle = "Игра окончена", ""
    arcade.draw_text(headline, cx, cy + 72, COLORS["text_red"], 30,
                     bold=True, anchor_x="center", anchor_y="center")
    if subtitle:
        arcade.draw_text(subtitle, cx, cy + 35, COLORS["text_dark"], 16,
                         anchor_x="center", anchor_y="center")
    arcade.draw_text(f"Итог: {score} очков", cx, cy + 2,
                     COLORS["text_dark"], 18, bold=True,
                     anchor_x="center", anchor_y="center")
    arcade.draw_text("R — снова    ESC — сохранить и в меню",
                     cx, cy - 50, COLORS["text_gray"], 12,
                     anchor_x="center", anchor_y="center")
