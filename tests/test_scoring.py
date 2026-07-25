from fractions import Fraction

import pytest

from mahjong_puzzle.hand import enumerate_decompositions
from mahjong_puzzle.scoring import (
    DEFAULT_SCORING_CONFIG,
    calculate_score,
    select_best_scored_evaluation,
)
from mahjong_puzzle.tiles import Suit, TileType
from mahjong_puzzle.yaku import Yaku, YakuEvaluation


def test_only_new_yaku_contribute_yaku_points() -> None:
    result = calculate_score(
        current_yaku={Yaku.CHINITSU, Yaku.ALL_SEQUENCES},
        new_yaku={Yaku.ALL_SEQUENCES},
        dora_count=0,
        previous_line_wins=0,
        consecutive_win_turns=1,
        simultaneous_line_count=1,
    )

    assert result.yaku_points == {Yaku.ALL_SEQUENCES: DEFAULT_SCORING_CONFIG.yaku_points[Yaku.ALL_SEQUENCES]}
    assert result.combination_bonus > 0


def test_dora_and_previous_line_wins_add_to_subtotal() -> None:
    result = calculate_score(
        current_yaku={Yaku.TANYAO},
        new_yaku={Yaku.TANYAO},
        dora_count=2,
        previous_line_wins=3,
        consecutive_win_turns=1,
        simultaneous_line_count=1,
    )

    assert result.dora_score == 2 * DEFAULT_SCORING_CONFIG.dora_point
    assert result.line_repeat_bonus == 3 * DEFAULT_SCORING_CONFIG.repeat_win_bonus
    assert result.subtotal == (
        sum(result.yaku_points.values())
        + result.dora_score
        + result.combination_bonus
        + result.line_repeat_bonus
    )


def test_streak_and_simultaneous_multipliers_are_applied() -> None:
    result = calculate_score(
        current_yaku={Yaku.TANYAO},
        new_yaku={Yaku.TANYAO},
        dora_count=0,
        previous_line_wins=0,
        consecutive_win_turns=3,
        simultaneous_line_count=2,
    )

    assert result.streak_multiplier == Fraction(3, 2)
    assert result.simultaneous_multiplier == Fraction(3, 2)
    assert result.total_score == result.subtotal * 9 // 4


def test_dora_alone_cannot_be_scored_as_a_win() -> None:
    with pytest.raises(ValueError, match="役"):
        calculate_score(
            current_yaku=set(),
            new_yaku=set(),
            dora_count=3,
            previous_line_wins=0,
            consecutive_win_turns=1,
            simultaneous_line_count=1,
        )


def test_acquired_yaku_cannot_be_passed_as_new() -> None:
    with pytest.raises(ValueError, match="部分集合"):
        calculate_score(
            current_yaku={Yaku.TANYAO},
            new_yaku={Yaku.CHINITSU},
            dora_count=0,
            previous_line_wins=0,
            consecutive_win_turns=1,
            simultaneous_line_count=1,
        )


def test_highest_scoring_valid_decomposition_is_selected() -> None:
    s = lambda rank: TileType.suited(Suit.MANZU, rank)
    decomposition = enumerate_decompositions(
        [s(1), s(2), s(3), s(4), s(5), s(6), s(9), s(9)]
    )[0]
    low = YakuEvaluation(decomposition, frozenset({Yaku.ALL_SEQUENCES}))
    high = YakuEvaluation(
        decomposition, frozenset({Yaku.ALL_SEQUENCES, Yaku.CHINITSU})
    )

    selected = select_best_scored_evaluation(
        [low, high],
        acquired_yaku=set(),
        dora_count=0,
        previous_line_wins=0,
        consecutive_win_turns=1,
        simultaneous_line_count=1,
    )

    assert selected is not None
    assert selected.evaluation is high


def test_scoring_candidates_excludes_decomposition_with_only_acquired_yaku() -> None:
    s = lambda rank: TileType.suited(Suit.MANZU, rank)
    decomposition = enumerate_decompositions(
        [s(1), s(2), s(3), s(4), s(5), s(6), s(9), s(9)]
    )[0]
    acquired_only = YakuEvaluation(
        decomposition, frozenset({Yaku.ALL_SEQUENCES, Yaku.CHINITSU})
    )

    selected = select_best_scored_evaluation(
        [acquired_only],
        acquired_yaku={Yaku.ALL_SEQUENCES, Yaku.CHINITSU},
        dora_count=2,
        previous_line_wins=1,
        consecutive_win_turns=1,
        simultaneous_line_count=1,
    )

    assert selected is None


def test_phase5_yaku_points_are_configured() -> None:
    assert DEFAULT_SCORING_CONFIG.yaku_points[Yaku.HONOR_PAIR] == 100
    assert DEFAULT_SCORING_CONFIG.yaku_points[Yaku.TERMINAL_PAIR] == 100
    assert (
        DEFAULT_SCORING_CONFIG.yaku_points[Yaku.TWO_SUIT_SAME_SEQUENCE]
        == 200
    )
    assert DEFAULT_SCORING_CONFIG.yaku_points[Yaku.STEPPED_SEQUENCES] == 150
    assert DEFAULT_SCORING_CONFIG.yaku_points[Yaku.THREE_SUITS_USED] == 100
    assert DEFAULT_SCORING_CONFIG.yaku_points[Yaku.FOUR_PAIRS] == 400
