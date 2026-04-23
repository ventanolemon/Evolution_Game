"""
Глобальные константы проекта.
Не импортирует arcade — загружается самым первым.
Все «магические числа» живут только здесь.
"""

# ── Сетка ─────────────────────────────────────────────────────
ROWS        = 4
COLS        = 4
TILE_MARGIN = 12
TILE_SIZE   = 148
CELL_STEP   = TILE_SIZE + TILE_MARGIN   # 160 px

# ── Окно (вычисляется из сетки, вписывается в 768p+) ──────────
HUD_TOP     = 55
HUD_BOTTOM  = 38

SCREEN_WIDTH  = COLS * CELL_STEP + TILE_MARGIN           # 652
SCREEN_HEIGHT = HUD_TOP + ROWS * CELL_STEP + HUD_BOTTOM  # 733
SCREEN_TITLE  = "🧬 Эволюция"
FPS           = 60

GRID_ORIGIN_X = TILE_MARGIN // 2
GRID_ORIGIN_Y = SCREEN_HEIGHT - HUD_TOP

# ── Таймер / режимы ───────────────────────────────────────────
TIMER_CLASSIC          = 90.0   # секунд
TIME_PER_MERGE_CLASSIC = 1.5    # бонус за слияние
MERGE_TIME_CAP_CLASSIC = 3      # макс учитываемых слияний за ход

TIMER_TIMED   = 45.0
TIMER_INFINITE = 0.0            # 0 = нет таймера

# ── Цвета (чистые RGB/RGBA, без arcade) ───────────────────────
COLORS = {
    "background":       (245, 240, 225),
    "grid_bg":          (200, 170, 130, 80),
    "grid_line":        (140,  90,  40),
    "empty_tile":       (210, 195, 175),
    "text_dark":        ( 80,  50,  20),
    "text_light":       (255, 255, 255),
    "text_gray":        (140, 130, 120),
    "text_gold":        (200, 160,   0),
    "text_red":         (200,  40,  40),
    "text_green":       ( 40, 150,  40),
    "btn_primary":      ( 70, 110, 220),
    "btn_hover":        ( 40,  80, 200),
    "btn_danger":       (190,  60,  60),
    "btn_danger_hover": (160,  40,  40),
    "btn_success":      ( 50, 150,  80),
    "btn_neutral":      (120, 110, 100),
    "btn_neutral_hover":(100,  90,  80),
    "overlay_dark":     (  0,   0,   0, 160),
    "merge_flash":      (255, 215,   0, 110),
    "mode_classic":     ( 70, 130, 180),
    "mode_timed":       (180,  80,  60),
    "mode_infinite":    ( 60, 140,  80),
    # aliases for backward compat
    "text":             ( 80,  50,  20),
    "grid":             (140,  90,  40),
}

# ── UI ────────────────────────────────────────────────────────
BTN_W = 220
BTN_H = 46
