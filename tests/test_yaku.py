import pytest

from mahjong_puzzle.hand import FourPairsDecomposition, HandDecomposition
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
            {
                Yaku.ALL_SEQUENCES,
                Yaku.CHINITSU,
                Yaku.TERMINAL_PAIR,
            },
        ),
        (
            [s(1)] * 3 + [s(9)] * 3 + [h(Honor.EAST)] * 2,
            {
                Yaku.ALL_TRIPLETS,
                Yaku.HONITSU,
                Yaku.HONROUTOU,
                Yaku.HONOR_PAIR,
            },
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
            {Yaku.ALL_SEQUENCES, Yaku.HONITSU, Yaku.HONOR_PAIR},
        ),
        (
            [s(1)] * 3 + [h(Honor.WHITE)] * 3 + [h(Honor.EAST)] * 2,
            {
                Yaku.ALL_TRIPLETS,
                Yaku.HONITSU,
                Yaku.HONROUTOU,
                Yaku.YAKUHAI,
                Yaku.HONOR_PAIR,
            },
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


def test_basic_shape_without_any_yaku_is_a_winning_evaluation() -> None:
    tiles = [
        s(1),
        s(2),
        s(3),
        h(Honor.EAST),
        h(Honor.EAST),
        h(Honor.EAST),
        s(5, Suit.PINZU),
        s(5, Suit.PINZU),
    ]
    evaluation = evaluate_hand(tiles)[0]

    assert evaluation.yaku == frozenset()
    assert evaluation.is_winning


def test_multiple_decompositions_are_evaluated_separately() -> None:
    tiles = [s(1)] * 2 + [s(2)] * 2 + [s(3)] * 2 + [s(4)] * 2
    evaluations = evaluate_hand(tiles)

    normal = [
        evaluation
        for evaluation in evaluations
        if isinstance(evaluation.decomposition, HandDecomposition)
    ]
    special = [
        evaluation
        for evaluation in evaluations
        if isinstance(evaluation.decomposition, FourPairsDecomposition)
    ]

    assert len(normal) == 2
    assert {evaluation.decomposition.pair for evaluation in normal} == {
        s(1),
        s(4),
    }
    assert len(special) == 1
    assert special[0].yaku == {Yaku.FOUR_PAIRS, Yaku.CHINITSU}


@pytest.mark.parametrize("pair", [h(Honor.EAST), h(Honor.WHITE)])
def test_honor_pair_accepts_winds_and_dragons(pair: TileType) -> None:
    tiles = [s(1), s(2), s(3)] + [
        s(4, Suit.PINZU),
        s(5, Suit.PINZU),
        s(6, Suit.PINZU),
    ] + [pair, pair]

    assert Yaku.HONOR_PAIR in evaluate_hand(tiles)[0].yaku


def test_honor_pair_only_checks_the_normal_shape_pair() -> None:
    honor_in_meld = [h(Honor.EAST)] * 3 + [s(1), s(2), s(3)] + [
        s(5, Suit.PINZU),
        s(5, Suit.PINZU),
    ]
    terminal_pair = [s(2), s(3), s(4)] + [
        s(5, Suit.PINZU),
        s(6, Suit.PINZU),
        s(7, Suit.PINZU),
    ] + [s(1, Suit.SOUZU)] * 2

    assert Yaku.HONOR_PAIR not in evaluate_hand(honor_in_meld)[0].yaku
    assert Yaku.HONOR_PAIR not in evaluate_hand(terminal_pair)[0].yaku


@pytest.mark.parametrize(
    "pair",
    [s(1), s(9, Suit.SOUZU)],
)
def test_terminal_pair_accepts_one_and_nine(pair: TileType) -> None:
    tiles = [s(2), s(3), s(4)] + [
        s(5, Suit.PINZU),
        s(6, Suit.PINZU),
        s(7, Suit.PINZU),
    ] + [pair, pair]

    assert Yaku.TERMINAL_PAIR in evaluate_hand(tiles)[0].yaku


@pytest.mark.parametrize(
    "pair",
    [s(2, Suit.PINZU), h(Honor.SOUTH)],
)
def test_terminal_pair_rejects_simple_tiles_and_honors(
    pair: TileType,
) -> None:
    tiles = [s(2), s(3), s(4)] + [
        s(5, Suit.SOUZU),
        s(6, Suit.SOUZU),
        s(7, Suit.SOUZU),
    ] + [pair, pair]

    assert Yaku.TERMINAL_PAIR not in evaluate_hand(tiles)[0].yaku


@pytest.mark.parametrize("second_suit", [Suit.PINZU, Suit.SOUZU])
def test_two_suit_same_sequence_and_all_sequences_are_combined(
    second_suit: Suit,
) -> None:
    tiles = [s(2), s(3), s(4)] + [
        s(2, second_suit),
        s(3, second_suit),
        s(4, second_suit),
    ] + [h(Honor.WHITE)] * 2
    yaku = evaluate_hand(tiles)[0].yaku

    assert {Yaku.TWO_SUIT_SAME_SEQUENCE, Yaku.ALL_SEQUENCES} <= yaku


@pytest.mark.parametrize(
    "second",
    [
        [s(2), s(3), s(4)],
        [s(3, Suit.PINZU), s(4, Suit.PINZU), s(5, Suit.PINZU)],
    ],
)
def test_two_suit_same_sequence_rejects_same_suit_or_different_ranks(
    second: list[TileType],
) -> None:
    tiles = [s(2), s(3), s(4)] + second + [h(Honor.WHITE)] * 2

    assert Yaku.TWO_SUIT_SAME_SEQUENCE not in evaluate_hand(tiles)[0].yaku


@pytest.mark.parametrize(
    "first,second",
    [
        ([s(1), s(2), s(3)], [s(2), s(3), s(4)]),
        (
            [s(6, Suit.PINZU), s(7, Suit.PINZU), s(8, Suit.PINZU)],
            [s(7, Suit.PINZU), s(8, Suit.PINZU), s(9, Suit.PINZU)],
        ),
    ],
)
def test_stepped_sequences_and_all_sequences_are_combined(
    first: list[TileType],
    second: list[TileType],
) -> None:
    yaku = evaluate_hand(first + second + [h(Honor.RED)] * 2)[0].yaku

    assert {Yaku.STEPPED_SEQUENCES, Yaku.ALL_SEQUENCES} <= yaku


@pytest.mark.parametrize(
    "second",
    [
        [s(3), s(4), s(5)],
        [s(2, Suit.PINZU), s(3, Suit.PINZU), s(4, Suit.PINZU)],
        [s(1), s(2), s(3)],
    ],
)
def test_stepped_sequences_rejects_wrong_gap_suit_or_identical_sequence(
    second: list[TileType],
) -> None:
    tiles = [s(1), s(2), s(3)] + second + [h(Honor.RED)] * 2

    assert Yaku.STEPPED_SEQUENCES not in evaluate_hand(tiles)[0].yaku


def test_three_suits_used_detects_all_numbered_suits() -> None:
    tiles = [s(1), s(2), s(3)] + [s(5, Suit.PINZU)] * 3 + [
        s(7, Suit.SOUZU)
    ] * 2

    assert Yaku.THREE_SUITS_USED in evaluate_hand(tiles)[0].yaku


def test_three_suits_used_rejects_two_numbered_suits() -> None:
    tiles = [s(1), s(2), s(3)] + [s(5, Suit.PINZU)] * 3 + [
        s(7, Suit.PINZU)
    ] * 2

    assert Yaku.THREE_SUITS_USED not in evaluate_hand(tiles)[0].yaku


def test_four_pairs_is_a_special_winning_shape() -> None:
    tiles = [s(2)] * 2 + [s(5)] * 2 + [
        s(3, Suit.PINZU)
    ] * 2 + [h(Honor.WHITE)] * 2

    evaluations = evaluate_hand(tiles)

    assert len(evaluations) == 1
    assert isinstance(evaluations[0].decomposition, FourPairsDecomposition)
    assert evaluations[0].yaku == {Yaku.FOUR_PAIRS}
    assert evaluations[0].is_winning


def test_four_pairs_is_stable_for_shuffled_input() -> None:
    ordered = [s(2)] * 2 + [s(5)] * 2 + [
        s(3, Suit.PINZU)
    ] * 2 + [h(Honor.WHITE)] * 2
    shuffled = [ordered[index] for index in (7, 1, 4, 0, 6, 3, 5, 2)]

    assert evaluate_hand(shuffled) == evaluate_hand(ordered)


@pytest.mark.parametrize(
    "tiles",
    [
        [s(2)] * 2 + [s(5)] * 2 + [s(3, Suit.PINZU)] * 2
        + [h(Honor.WHITE), h(Honor.RED)],
        [s(2)] * 4 + [s(3, Suit.PINZU)] * 2 + [h(Honor.WHITE)] * 2,
    ],
)
def test_four_pairs_rejects_incomplete_pairs_and_quad(
    tiles: list[TileType],
) -> None:
    assert not any(
        Yaku.FOUR_PAIRS in evaluation.yaku
        for evaluation in evaluate_hand(tiles)
    )


def test_four_pairs_combines_only_with_whole_hand_yaku() -> None:
    tiles = [s(2)] * 2 + [s(5)] * 2 + [
        s(3, Suit.PINZU)
    ] * 2 + [s(7, Suit.SOUZU)] * 2
    evaluation = evaluate_hand(tiles)[0]

    assert evaluation.yaku == {
        Yaku.FOUR_PAIRS,
        Yaku.TANYAO,
        Yaku.THREE_SUITS_USED,
    }
    assert Yaku.HONOR_PAIR not in evaluation.yaku
    assert Yaku.TERMINAL_PAIR not in evaluation.yaku
    assert Yaku.ALL_SEQUENCES not in evaluation.yaku
    assert Yaku.ALL_TRIPLETS not in evaluation.yaku
    assert Yaku.IIPEIKOU not in evaluation.yaku
    assert Yaku.TWO_SUIT_SAME_SEQUENCE not in evaluation.yaku
    assert Yaku.STEPPED_SEQUENCES not in evaluation.yaku


def test_four_pairs_can_include_honors_while_using_three_suits() -> None:
    tiles = [s(2)] * 2 + [s(3, Suit.PINZU)] * 2 + [
        s(4, Suit.SOUZU)
    ] * 2 + [h(Honor.EAST)] * 2
    evaluation = evaluate_hand(tiles)[0]

    assert {Yaku.FOUR_PAIRS, Yaku.THREE_SUITS_USED} <= evaluation.yaku
    assert Yaku.HONOR_PAIR not in evaluation.yaku
