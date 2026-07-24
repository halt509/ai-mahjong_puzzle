from mahjong_puzzle.sprites import (
    TILE_TRANSPARENT_COLOR,
    TILE_SPRITE_SIZE,
    build_placeholder_tile_atlas,
    iter_tile_sprite_entries,
    tile_sprite_uv,
)
from mahjong_puzzle.tiles import Honor, Suit, TileType


def test_all_34_tile_types_have_unique_sprite_slots() -> None:
    entries = iter_tile_sprite_entries()

    assert len(entries) == 34
    assert len({tile_type for tile_type, _ in entries}) == 34
    assert len({uv for _, uv in entries}) == 34


def test_suits_and_honors_use_expected_atlas_rows() -> None:
    assert tile_sprite_uv(TileType.suited(Suit.MANZU, 1)) == (0, 0)
    assert tile_sprite_uv(TileType.suited(Suit.PINZU, 9)) == (
        8 * TILE_SPRITE_SIZE,
        TILE_SPRITE_SIZE,
    )
    assert tile_sprite_uv(TileType.suited(Suit.SOUZU, 5)) == (
        4 * TILE_SPRITE_SIZE,
        2 * TILE_SPRITE_SIZE,
    )
    assert tile_sprite_uv(TileType.honor_tile(Honor.EAST)) == (
        0,
        3 * TILE_SPRITE_SIZE,
    )
    assert tile_sprite_uv(TileType.honor_tile(Honor.RED)) == (
        6 * TILE_SPRITE_SIZE,
        3 * TILE_SPRITE_SIZE,
    )


class PixelImage:
    def __init__(self) -> None:
        self.pixels: dict[tuple[int, int], int] = {}

    def pset(self, x: int, y: int, color: int) -> None:
        self.pixels[(x, y)] = color

    def rect(
        self, x: int, y: int, width: int, height: int, color: int
    ) -> None:
        for pixel_y in range(y, y + height):
            for pixel_x in range(x, x + width):
                self.pset(pixel_x, pixel_y, color)

    def rectb(
        self, x: int, y: int, width: int, height: int, color: int
    ) -> None:
        for pixel_x in range(x, x + width):
            self.pset(pixel_x, y, color)
            self.pset(pixel_x, y + height - 1, color)
        for pixel_y in range(y, y + height):
            self.pset(x, pixel_y, color)
            self.pset(x + width - 1, pixel_y, color)

    def line(
        self, x1: int, y1: int, x2: int, y2: int, color: int
    ) -> None:
        if x1 == x2:
            for pixel_y in range(min(y1, y2), max(y1, y2) + 1):
                self.pset(x1, pixel_y, color)
            return
        if y1 == y2:
            for pixel_x in range(min(x1, x2), max(x1, x2) + 1):
                self.pset(pixel_x, y1, color)
            return
        raise AssertionError("テスト用画像は水平・垂直線だけを扱います")

    def text(
        self, x: int, y: int, value: str, color: int
    ) -> None:
        # このテストではPyxel組み込みフォントの形状は対象外。
        del x, y, value, color


def test_transparency_does_not_erase_dark_souzu_details() -> None:
    image = PixelImage()

    build_placeholder_tile_atlas(image)

    souzu_one_u, souzu_one_v = tile_sprite_uv(
        TileType.suited(Suit.SOUZU, 1)
    )
    assert image.pixels[(souzu_one_u, souzu_one_v)] == TILE_TRANSPARENT_COLOR
    assert image.pixels[(souzu_one_u + 6, souzu_one_v + 7)] == 0
    assert TILE_TRANSPARENT_COLOR != 0


def test_four_winds_use_directional_arrow_glyphs() -> None:
    image = PixelImage()
    build_placeholder_tile_atlas(image)
    glyphs: dict[Honor, frozenset[tuple[int, int]]] = {}

    for honor in (Honor.EAST, Honor.SOUTH, Honor.WEST, Honor.NORTH):
        u, v = tile_sprite_uv(TileType.honor_tile(honor))
        colored = frozenset(
            (x - u, y - v)
            for (x, y), color in image.pixels.items()
            if u <= x < u + TILE_SPRITE_SIZE
            and v <= y < v + TILE_SPRITE_SIZE
            and color == 12
        )
        glyphs[honor] = colored
        assert len(colored) >= 13

    assert len(set(glyphs.values())) == 4
    assert glyphs[Honor.WEST] == frozenset(
        (14 - x, y) for x, y in glyphs[Honor.EAST]
    )
    assert glyphs[Honor.SOUTH] == frozenset(
        (x, 14 - y) for x, y in glyphs[Honor.NORTH]
    )


def test_dragons_use_white_green_and_red_filled_faces() -> None:
    image = PixelImage()
    build_placeholder_tile_atlas(image)
    expected_colors = {
        Honor.WHITE: 15,
        Honor.GREEN: 11,
        Honor.RED: 8,
    }

    for honor, expected_color in expected_colors.items():
        u, v = tile_sprite_uv(TileType.honor_tile(honor))
        assert image.pixels[(u + 7, v + 7)] == expected_color
