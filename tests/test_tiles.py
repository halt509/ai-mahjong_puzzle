from collections import Counter

import pytest

from mahjong_puzzle.tiles import (
    Honor,
    Suit,
    Tile,
    TileType,
    create_full_tile_set,
    normalize_tile_types,
)


def test_full_tile_set_has_136_unique_physical_tiles() -> None:
    tiles = create_full_tile_set()

    assert len(tiles) == 136
    assert len({tile.tile_id for tile in tiles}) == 136
    assert set(Counter(tile.kind for tile in tiles).values()) == {4}


def test_tile_types_have_stable_sort_order_and_display() -> None:
    types = [
        TileType.honor_tile(Honor.RED),
        TileType.suited(Suit.PINZU, 9),
        TileType.suited(Suit.MANZU, 1),
        TileType.honor_tile(Honor.EAST),
    ]

    assert [str(tile_type) for tile_type in sorted(types)] == ["1萬", "9筒", "東", "中"]


@pytest.mark.parametrize("rank", [0, 10])
def test_suited_tile_rejects_invalid_rank(rank: int) -> None:
    with pytest.raises(ValueError, match="1から9"):
        TileType.suited(Suit.MANZU, rank)


def test_normalization_rejects_duplicate_physical_ids() -> None:
    kind = TileType.suited(Suit.MANZU, 1)
    tile = Tile(kind=kind, copy_index=0)

    with pytest.raises(ValueError, match="個体ID"):
        normalize_tile_types([tile, tile])


def test_normalization_rejects_more_than_four_of_one_kind() -> None:
    kind = TileType.suited(Suit.MANZU, 1)

    with pytest.raises(ValueError, match="4枚"):
        normalize_tile_types([kind] * 5)
