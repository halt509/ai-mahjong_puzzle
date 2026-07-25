import random

import pytest

from mahjong_puzzle.hand import (
    FourPairsDecomposition,
    MeldKind,
    enumerate_decompositions,
    find_four_pairs_decomposition,
)
from mahjong_puzzle.tiles import Honor, Suit, TileType


def s(rank: int, suit: Suit = Suit.MANZU) -> TileType:
    return TileType.suited(suit, rank)


def h(honor: Honor) -> TileType:
    return TileType.honor_tile(honor)


@pytest.mark.parametrize(
    ("tiles", "meld_kinds"),
    [
        ([s(1), s(2), s(3), s(4), s(5), s(6), s(9), s(9)], {MeldKind.SEQUENCE}),
        ([s(1)] * 3 + [s(2)] * 3 + [s(9)] * 2, {MeldKind.TRIPLET}),
        (
            [s(1), s(2), s(3)] + [h(Honor.EAST)] * 3 + [s(9)] * 2,
            {MeldKind.SEQUENCE, MeldKind.TRIPLET},
        ),
    ],
)
def test_enumerates_valid_332_shapes(
    tiles: list[TileType], meld_kinds: set[MeldKind]
) -> None:
    decompositions = enumerate_decompositions(tiles)

    assert decompositions
    assert {meld.kind for meld in decompositions[0].melds} == meld_kinds


def test_input_order_does_not_change_decompositions() -> None:
    tiles = [s(1), s(2), s(3), s(4), s(5), s(6), s(9), s(9)]
    shuffled = tiles.copy()
    random.Random(20260724).shuffle(shuffled)

    assert enumerate_decompositions(shuffled) == enumerate_decompositions(tiles)


def test_honors_are_not_used_as_sequences() -> None:
    tiles = [
        h(Honor.EAST),
        h(Honor.SOUTH),
        h(Honor.WEST),
        s(1),
        s(2),
        s(3),
        s(9),
        s(9),
    ]

    assert enumerate_decompositions(tiles) == ()


def test_invalid_shape_is_not_decomposed() -> None:
    assert enumerate_decompositions([s(1), s(2), s(4), s(5), s(6), s(8), s(9), s(9)]) == ()


def test_four_identical_tiles_are_not_a_four_tile_meld() -> None:
    tiles = [s(1)] * 4 + [s(2), s(3), s(4)] + [s(9)]

    assert enumerate_decompositions(tiles) == ()


def test_four_identical_tiles_can_supply_a_triplet_and_another_use() -> None:
    tiles = [s(1)] * 4 + [s(2), s(3)] + [s(9)] * 2
    decompositions = enumerate_decompositions(tiles)

    assert len(decompositions) == 1
    used = [tile for decomposition in decompositions for meld in decomposition.melds for tile in meld.tiles]
    assert used.count(s(1)) == 4


def test_all_multiple_decompositions_are_returned_without_reusing_tiles() -> None:
    tiles = [s(1)] * 2 + [s(2)] * 2 + [s(3)] * 2 + [s(4)] * 2
    decompositions = enumerate_decompositions(tiles)

    assert len(decompositions) == 2
    assert {decomposition.pair for decomposition in decompositions} == {s(1), s(4)}
    for decomposition in decompositions:
        consumed = [decomposition.pair, decomposition.pair]
        consumed.extend(tile for meld in decomposition.melds for tile in meld.tiles)
        assert sorted(consumed) == sorted(tiles)


def test_decomposition_requires_exactly_eight_tiles() -> None:
    with pytest.raises(ValueError, match="8枚"):
        enumerate_decompositions([s(1)] * 4 + [s(2)] * 3)


def test_four_pairs_decomposition_requires_four_distinct_pair_types() -> None:
    tiles = [s(1)] * 2 + [s(3)] * 2 + [s(5)] * 2 + [s(7)] * 2

    result = find_four_pairs_decomposition(tiles)

    assert result == FourPairsDecomposition((s(1), s(3), s(5), s(7)))


def test_four_pairs_decomposition_rejects_a_quad() -> None:
    tiles = [s(1)] * 4 + [s(3)] * 2 + [s(5)] * 2

    assert find_four_pairs_decomposition(tiles) is None
