"""34牌種の16×16採用スプライトアトラス。"""

from __future__ import annotations

from typing import Any

from mahjong_puzzle.tiles import Honor, Suit, TileType, all_tile_types

TILE_SPRITE_SIZE = 16
TILE_IMAGE_BANK = 0
TILE_TRANSPARENT_COLOR = 14

_SUIT_ROWS = {
    Suit.MANZU: 0,
    Suit.PINZU: 1,
    Suit.SOUZU: 2,
}
_HONOR_COLUMNS = {honor: index for index, honor in enumerate(Honor)}
_DRAGON_FILL_COLORS = {
    Honor.WHITE: 15,
    Honor.GREEN: 11,
    Honor.RED: 8,
}
_WIND_GLYPHS = {
    Honor.EAST: (
        "....#..",
        ".....#.",
        "......#",
        "#######",
        "......#",
        ".....#.",
        "....#..",
    ),
    Honor.SOUTH: (
        "...#...",
        "...#...",
        "...#...",
        "#..#..#",
        ".#.#.#.",
        "..###..",
        "...#...",
    ),
    Honor.WEST: (
        "..#....",
        ".#.....",
        "#......",
        "#######",
        "#......",
        ".#.....",
        "..#....",
    ),
    Honor.NORTH: (
        "...#...",
        "..###..",
        ".#.#.#.",
        "#..#..#",
        "...#...",
        "...#...",
        "...#...",
    ),
}


def tile_sprite_uv(tile_type: TileType) -> tuple[int, int]:
    """牌種に対応するアトラス左上座標を返す。"""

    if not isinstance(tile_type, TileType):
        raise TypeError("tile_typeにはTileTypeが必要です")
    if tile_type.suit is not None:
        assert tile_type.rank is not None
        return (
            (tile_type.rank - 1) * TILE_SPRITE_SIZE,
            _SUIT_ROWS[tile_type.suit] * TILE_SPRITE_SIZE,
        )
    assert tile_type.honor is not None
    return (
        _HONOR_COLUMNS[tile_type.honor] * TILE_SPRITE_SIZE,
        3 * TILE_SPRITE_SIZE,
    )


def iter_tile_sprite_entries() -> tuple[tuple[TileType, tuple[int, int]], ...]:
    return tuple((tile_type, tile_sprite_uv(tile_type)) for tile_type in all_tile_types())


def _draw_face(image: Any, u: int, v: int) -> None:
    image.rect(
        u,
        v,
        TILE_SPRITE_SIZE,
        TILE_SPRITE_SIZE,
        TILE_TRANSPARENT_COLOR,
    )
    image.rect(u + 2, v + 1, 13, 15, 4)
    image.rect(u + 1, v, 13, 15, 7)
    image.rectb(u + 1, v, 13, 15, 5)
    image.pset(u + 1, v, TILE_TRANSPARENT_COLOR)
    image.pset(u + 13, v, TILE_TRANSPARENT_COLOR)


_PIP_LAYOUTS = {
    1: ((1, 1),),
    2: ((0, 0), (2, 2)),
    3: ((0, 0), (1, 1), (2, 2)),
    4: ((0, 0), (2, 0), (0, 2), (2, 2)),
    5: ((0, 0), (2, 0), (1, 1), (0, 2), (2, 2)),
    6: ((0, 0), (2, 0), (0, 1), (2, 1), (0, 2), (2, 2)),
    7: ((0, 0), (2, 0), (0, 1), (1, 1), (2, 1), (0, 2), (2, 2)),
    8: ((0, 0), (1, 0), (2, 0), (0, 1), (2, 1), (0, 2), (1, 2), (2, 2)),
    9: tuple((x, y) for y in range(3) for x in range(3)),
}


def _draw_pinzu(image: Any, u: int, v: int, rank: int) -> None:
    positions = (4, 7, 10)
    for index, (grid_x, grid_y) in enumerate(_PIP_LAYOUTS[rank]):
        x = u + positions[grid_x]
        y = v + 3 + positions[grid_y] - 3
        color = 8 if index % 3 == 1 else 12
        image.rect(x - 1, y - 1, 3, 3, color)
        image.pset(x, y, 7)


def _draw_souzu(image: Any, u: int, v: int, rank: int) -> None:
    positions = (4, 7, 10)
    for index, (grid_x, grid_y) in enumerate(_PIP_LAYOUTS[rank]):
        x = u + positions[grid_x]
        y = v + 2 + grid_y * 4
        color = 8 if rank >= 5 and index == len(_PIP_LAYOUTS[rank]) // 2 else 11
        image.line(x, y, x, y + 3, color)
        image.pset(x - 1, y + 1, 0)
        image.pset(x + 1, y + 2, 0)


def _draw_bitmap(
    image: Any,
    u: int,
    v: int,
    rows: tuple[str, ...],
    color: int,
) -> None:
    x_offset = (TILE_SPRITE_SIZE - len(rows[0])) // 2
    y_offset = (TILE_SPRITE_SIZE - len(rows)) // 2
    for row_index, row in enumerate(rows):
        for column_index, pixel in enumerate(row):
            if pixel == "#":
                image.pset(
                    u + x_offset + column_index,
                    v + y_offset + row_index,
                    color,
                )


def build_placeholder_tile_atlas(image: Any) -> None:
    """Pyxel Image互換バンクへ採用した牌スプライトを描く。

    関数名は既存APIとの互換性のため維持する。
    """

    for tile_type, (u, v) in iter_tile_sprite_entries():
        _draw_face(image, u, v)
        if tile_type.suit is Suit.MANZU:
            assert tile_type.rank is not None
            image.text(u + 3, v + 2, str(tile_type.rank), 12)
            image.text(u + 5, v + 8, "M", 8)
        elif tile_type.suit is Suit.PINZU:
            assert tile_type.rank is not None
            _draw_pinzu(image, u, v, tile_type.rank)
        elif tile_type.suit is Suit.SOUZU:
            assert tile_type.rank is not None
            _draw_souzu(image, u, v, tile_type.rank)
        else:
            assert tile_type.honor is not None
            glyph = _WIND_GLYPHS.get(tile_type.honor)
            if glyph is not None:
                _draw_bitmap(image, u, v, glyph, 12)
            else:
                image.rect(
                    u + 2,
                    v + 1,
                    11,
                    13,
                    _DRAGON_FILL_COLORS[tile_type.honor],
                )
