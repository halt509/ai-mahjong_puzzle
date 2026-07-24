import pytest

from mahjong_puzzle.dora import count_dora, dora_from_indicator
from mahjong_puzzle.tiles import Honor, Suit, TileType


def s(rank: int, suit: Suit = Suit.MANZU) -> TileType:
    return TileType.suited(suit, rank)


def h(honor: Honor) -> TileType:
    return TileType.honor_tile(honor)


@pytest.mark.parametrize(
    ("indicator", "dora"),
    [
        (s(9), s(1)),
        (h(Honor.NORTH), h(Honor.EAST)),
        (h(Honor.RED), h(Honor.WHITE)),
    ],
)
def test_dora_cycles(indicator: TileType, dora: TileType) -> None:
    assert dora_from_indicator(indicator) == dora


def test_counts_multiple_dora_indicators() -> None:
    tiles = [s(1), s(1), s(2), s(3), s(4), s(5), s(6), s(7)]

    assert count_dora(tiles, [s(9), s(1)]) == 3


def test_duplicate_indicators_count_the_same_dora_repeatedly() -> None:
    tiles = [s(1), s(1), s(2), s(3), s(4), s(5), s(6), s(7)]

    assert count_dora(tiles, [s(9), s(9)]) == 4


def test_more_than_four_indicators_is_rejected() -> None:
    with pytest.raises(ValueError, match="4枚"):
        count_dora([s(1)] * 4 + [s(2)] * 4, [s(1)] * 5)
