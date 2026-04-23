"""
Загрузчик карт Tiled (формат TMX).

Формат:
  — ортогональная карта (orientation="orthogonal")
  — один слой "cells" в CSV-encoding
  — тайлсет ссылкой (<tileset source="..."/>) с custom-property "type"
    у каждого тайла: wall | fire | upgrade | degrade

Custom-properties карты (<map><properties>...):
  id, name, description — читаются и попадают в MapConfig.

Как создать карту в Tiled:
  1. Файл → Новая карта: ортогональная, размер 4×4…8×8, тайл 64×64
     Формат слоя тайлов: CSV
  2. Карта → Свойства карты → добавить string-свойства id/name/description
  3. Карта → Добавить внешний тайлсет → выбрать maps/tilesets/special_cells.tsx
  4. Добавить слой тайлов с точным именем "cells"
  5. Рисовать стены/огонь/апгрейдеры/деградаторы где нужно
  6. Сохранить как .tmx в папку maps/
"""
import xml.etree.ElementTree as ET
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from src.game.cell_types import CellType


MAPS_DIR = Path("maps")
ROWS_RANGE = (2, 10)
COLS_RANGE = (2, 10)


@dataclass(frozen=True)
class MapConfig:
    id:          str
    name:        str
    description: str
    rows:        int
    cols:        int
    cells:       tuple[tuple[CellType, ...], ...]   # [row][col]


class MapValidationError(Exception):
    pass


# ── Парсинг внешнего тайлсета (.tsx) ──────────────────────────

def _parse_tileset(tsx_path: Path, firstgid: int) -> dict[int, CellType]:
    """Читает .tsx и возвращает словарь GID → CellType."""
    try:
        tree = ET.parse(tsx_path)
    except (ET.ParseError, OSError) as exc:
        raise MapValidationError(f"Не удалось открыть тайлсет {tsx_path.name}: {exc}")

    root = tree.getroot()
    gid_to_type: dict[int, CellType] = {}

    for tile in root.findall("tile"):
        tile_id = int(tile.attrib["id"])
        for prop in tile.findall("properties/property"):
            if prop.attrib.get("name") == "type":
                val = prop.attrib.get("value", "").strip().lower()
                try:
                    gid_to_type[firstgid + tile_id] = CellType(val)
                except ValueError:
                    raise MapValidationError(
                        f"Неизвестный тип клетки '{val}' в {tsx_path.name}")
                break
    return gid_to_type


# ── Парсинг TMX ───────────────────────────────────────────────

def _parse_tmx(path: Path) -> MapConfig:
    """Основной парсер. Бросает MapValidationError при проблемах."""
    try:
        tree = ET.parse(path)
    except ET.ParseError as exc:
        raise MapValidationError(f"Ошибка XML в {path.name}: {exc}")

    root = tree.getroot()
    if root.tag != "map":
        raise MapValidationError(f"{path.name}: корневой элемент не <map>")

    # ── Размеры ──────────────────────────────────────────────
    try:
        rows = int(root.attrib["height"])
        cols = int(root.attrib["width"])
    except (KeyError, ValueError) as exc:
        raise MapValidationError(f"{path.name}: некорректные width/height: {exc}")

    if not (ROWS_RANGE[0] <= rows <= ROWS_RANGE[1]):
        raise MapValidationError(f"{path.name}: rows={rows} вне {ROWS_RANGE}")
    if not (COLS_RANGE[0] <= cols <= COLS_RANGE[1]):
        raise MapValidationError(f"{path.name}: cols={cols} вне {COLS_RANGE}")

    # ── GID → CellType из всех тайлсетов ─────────────────────
    gid_to_type: dict[int, CellType] = {}
    for ts_elem in root.findall("tileset"):
        firstgid = int(ts_elem.attrib.get("firstgid", 1))
        source   = ts_elem.attrib.get("source")
        if source:
            ts_path = path.parent / source
            gid_to_type.update(_parse_tileset(ts_path, firstgid))
        else:
            # Встроенный тайлсет
            for tile in ts_elem.findall("tile"):
                tile_id = int(tile.attrib["id"])
                for prop in tile.findall("properties/property"):
                    if prop.attrib.get("name") == "type":
                        val = prop.attrib.get("value", "").strip().lower()
                        try:
                            gid_to_type[firstgid + tile_id] = CellType(val)
                        except ValueError:
                            raise MapValidationError(
                                f"{path.name}: неизвестный тип '{val}'")

    # ── Слой "cells" ──────────────────────────────────────────
    cells_layer = None
    for layer in root.findall("layer"):
        if layer.attrib.get("name") == "cells":
            cells_layer = layer
            break
    if cells_layer is None:
        raise MapValidationError(
            f"{path.name}: не найден слой 'cells'. "
            "Создай в Tiled Layer→New Tile Layer с именем 'cells'.")

    data = cells_layer.find("data")
    if data is None:
        raise MapValidationError(f"{path.name}: слой 'cells' без <data>")

    encoding = data.attrib.get("encoding", "").lower()
    if encoding != "csv":
        raise MapValidationError(
            f"{path.name}: поддерживается только CSV-кодировка слоя. "
            "В Tiled: Правка → Настройки → Формат слоя тайлов = CSV.")

    # ── CSV ───────────────────────────────────────────────────
    text = (data.text or "").strip()
    grid: list[list[CellType]] = []
    for line in text.split("\n"):
        line = line.strip().rstrip(",")
        if not line:
            continue
        row_cells: list[CellType] = []
        for token in line.split(","):
            try:
                gid = int(token.strip())
            except ValueError:
                raise MapValidationError(
                    f"{path.name}: некорректный GID '{token}' в CSV")
            if gid == 0:
                row_cells.append(CellType.EMPTY)
            else:
                ct = gid_to_type.get(gid)
                if ct is None:
                    raise MapValidationError(
                        f"{path.name}: неизвестный GID {gid} в CSV")
                row_cells.append(ct)
        if len(row_cells) != cols:
            raise MapValidationError(
                f"{path.name}: в строке CSV {len(row_cells)} элементов, ожидается {cols}")
        grid.append(row_cells)

    if len(grid) != rows:
        raise MapValidationError(
            f"{path.name}: CSV содержит {len(grid)} строк, ожидается {rows}")

    # ── Custom-properties карты ───────────────────────────────
    props: dict[str, str] = {}
    for prop in root.findall("properties/property"):
        props[prop.attrib["name"]] = prop.attrib.get("value", "")

    return MapConfig(
        id          = props.get("id", path.stem),
        name        = props.get("name", path.stem),
        description = props.get("description", ""),
        rows        = rows,
        cols        = cols,
        cells       = tuple(tuple(row) for row in grid),
    )


# ── Публичные функции ────────────────────────────────────────

def load_map(path: Path) -> Optional[MapConfig]:
    """Загружает одну карту. Ошибки логируются, возвращает None."""
    try:
        return _parse_tmx(path)
    except MapValidationError as exc:
        print(f"⚠ {exc}")
        return None
    except Exception as exc:
        print(f"⚠ Неожиданная ошибка в {path.name}: {exc}")
        return None


def load_all_maps() -> list[MapConfig]:
    """Загружает все .tmx из папки maps/."""
    if not MAPS_DIR.exists():
        MAPS_DIR.mkdir(exist_ok=True)
        return [DEFAULT_MAP]
    maps: list[MapConfig] = []
    for f in sorted(MAPS_DIR.glob("*.tmx")):
        m = load_map(f)
        if m:
            maps.append(m)
    if not maps:
        print("⚠ Карт не найдено, использую дефолтную")
        return [DEFAULT_MAP]
    return maps


# Fallback
DEFAULT_MAP = MapConfig(
    id          = "default_4x4",
    name        = "Обычное поле",
    description = "Классика 4×4",
    rows        = 4,
    cols        = 4,
    cells       = tuple(tuple(CellType.EMPTY for _ in range(4)) for _ in range(4)),
)
