import pytest

from mahjong_puzzle.tiles import Honor, Suit, TileType
from mahjong_puzzle.yaku import Yaku, evaluate_hand


def s(rank: int, suit: Suit = Suit.MANZU) -> TileType:
    return TileType.suited(suit, rank)


def h(honor: Honor) -> TileType:
    return TileType.honor_tile(honor)


@pytest.mark.parametrize(
    ("tiles", "expected"),
    [
        (
            [s(1), s(2), s(3), s(4), s(5), s(6), s(9), s(9)],
            {Yaku.ALL_SEQUENCES, Yaku.CHINITSU},
        ),
        (
            [s(1)] * 3 + [s(9)] * 3 + [h(Honor.EAST)] * 2,
            {Yaku.ALL_TRIPLETS, Yaku.HONITSU, Yaku.HONROUTOU},
        ),
        (
            [s(2), s(3), s(4), s(5), s(6), s(7), s(8), s(8)],
            {Yaku.ALL_SEQUENCES, Yaku.TANYAO, Yaku.CHINITSU},
        ),
        (
            [s(2), s(3), s(4)] * 2 + [s(5)] * 2,
            {Yaku.ALL_SEQUENCES, Yaku.TANYAO, Yaku.IIPEIKOU, Yaku.CHINITSU},
        ),
        (
            [s(1), s(2), s(3), s(7), s(8), s(9)] + [h(Honor.EAST)] * 2,
            {Yaku.ALL_SEQUENCES, Yaku.HONITSU},
        ),
        (
            [s(1)] * 3 + [h(Honor.WHITE)] * 3 + [h(Honor.EAST)] * 2,
            {Yaku.ALL_TRIPLETS, Yaku.HONITSU, Yaku.HONROUTOU, Yaku.YAKUHAI},
        ),
    ],
)
def test_detects_expected_yaku(tiles: list[TileType], expected: set[Yaku]) -> None:
    evaluations = evaluate_hand(tiles)

    assert evaluations
    assert evaluations[0].yaku == frozenset(expected)


@pytest.mark.parametrize(
    ("tiles", "absent"),
    [
        ([s(1), s(2), s(3)] + [s(5)] * 3 + [s(9)] * 2, Yaku.ALL_SEQUENCES),
        ([s(1), s(2), s(3)] + [s(5)] * 3 + [s(9)] * 2, Yaku.ALL_TRIPLETS),
        ([s(1), s(2), s(3), s(4), s(5), s(6), s(9), s(9)], Yaku.TANYAO),
        ([s(1), s(2), s(3), s(4), s(5), s(6), s(9), s(9)], Yaku.IIPEIKOU),
        (
            [s(1), s(2), s(3)] + [s(1, Suit.PINZU), s(2, Suit.PINZU), s(3, Suit.PINZU)] + [h(Honor.EAST)] * 2,
            Yaku.HONITSU,
        ),
        (
            [s(1), s(2), s(3), s(7), s(8), s(9)] + [h(Honor.EAST)] * 2,
            Yaku.CHINITSU,
        ),
        ([s(1)] * 3 + [s(9)] * 3 + [s(2)] * 2, Yaku.HONROUTOU),
        ([s(1)] * 3 + [h(Honor.EAST)] * 3 + [h(Honor.SOUTH)] * 2, Yaku.YAKUHAI),
    ],
)
def test_each_yaku_has_a_non_matching_case(tiles: list[TileType], absent: Yaku) -> None:
    evaluations = evaluate_hand(tiles)

    assert evaluations
    assert absent not in evaluations[0].yaku


def test_basic_shape_without_any_yaku_is_not_a_winning_evaluation() -> None:
    tiles = [
        s(1),
        s(2),
        s(3),
        s(5, Suit.PINZU),
        s(5, Suit.PINZU),
        s(5, Suit.PINZU),
        h(Honor.EAST),
        h(Honor.EAST),
    ]
    evaluation = evaluate_hand(tiles)[0]

    assert evaluation.yaku == frozenset()
    assert not evaluation.is_winning


def test_multiple_decompositions_are_evaluated_separately() -> None:
    tiles = [s(1)] * 2 + [s(2)] * 2 + [s(3)] * 2 + [s(4)] * 2
    evaluations = evaluate_hand(tiles)

    assert len(evaluations) == 2
    assert {evaluation.decomposition.pair for evaluation in evaluations} == {s(1), s(4)}
    assert all(evaluation.yaku == {Yaku.ALL_SEQUENCES, Yaku.IIPEIKOU, Yaku.CHINITSU} for evaluation in evaluations)
