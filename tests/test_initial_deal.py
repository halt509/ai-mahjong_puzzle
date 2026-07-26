from mahjong_puzzle.initial_deal import (
    DEFAULT_INITIAL_DEAL_CONFIG,
    InitialDealConfig,
    assess_initial_deal_distances,
    minimum_replacement_distance,
)
from mahjong_puzzle.tiles import Honor, Suit, TileType


def s(rank: int, suit: Suit = Suit.MANZU) -> TileType:
    return TileType.suited(suit, rank)


def h(honor: Honor) -> TileType:
    return TileType.honor_tile(honor)


def test_one_available_candidate_tile_makes_a_row_one_away() -> None:
    row = [
        s(1),
        s(2),
        s(4),
        s(5),
        s(6),
        s(9, Suit.PINZU),
        s(9, Suit.PINZU),
        h(Honor.EAST),
    ]
    candidates = (
        [s(3)]
        + [h(Honor.SOUTH)] * 4
        + [h(Honor.WEST)] * 4
        + [h(Honor.NORTH)] * 3
    )

    assert minimum_replacement_distance(row, candidates) == 1


def test_candidate_tile_not_in_first_three_blocks_is_not_used() -> None:
    row = [
        s(1),
        s(2),
        s(4),
        s(5),
        s(6),
        s(9, Suit.PINZU),
        s(9, Suit.PINZU),
        h(Honor.EAST),
    ]
    candidates = (
        [h(Honor.SOUTH)] * 4
        + [h(Honor.WEST)] * 4
        + [h(Honor.NORTH)] * 4
    )

    distance = minimum_replacement_distance(row, candidates)

    assert distance is None or distance > 1


def test_candidate_tile_multiplicity_cannot_be_exceeded() -> None:
    row = [
        s(1),
        s(2),
        s(1),
        s(2),
        s(9, Suit.PINZU),
        s(9, Suit.PINZU),
        h(Honor.EAST),
        h(Honor.SOUTH),
    ]
    unrelated = [
        s(1, Suit.PINZU),
        s(4, Suit.PINZU),
        s(7, Suit.PINZU),
        s(1, Suit.SOUZU),
        s(4, Suit.SOUZU),
        s(7, Suit.SOUZU),
        h(Honor.WEST),
        h(Honor.NORTH),
        h(Honor.WHITE),
        h(Honor.GREEN),
    ]
    two_needed = [s(3)] * 2 + unrelated
    only_one = [s(3)] + unrelated + [h(Honor.RED)]

    assert minimum_replacement_distance(row, two_needed) == 2
    distance = minimum_replacement_distance(row, only_one)
    assert distance is None or distance > 2


def test_four_pairs_is_included_in_distance_evaluation() -> None:
    row = [
        s(1),
        s(1),
        s(2, Suit.PINZU),
        s(2, Suit.PINZU),
        s(3, Suit.SOUZU),
        s(3, Suit.SOUZU),
        h(Honor.EAST),
        h(Honor.SOUTH),
    ]
    candidates = (
        [h(Honor.EAST)]
        + [h(Honor.WEST)] * 4
        + [h(Honor.NORTH)] * 4
        + [h(Honor.WHITE)] * 3
    )

    assert minimum_replacement_distance(row, candidates) == 1


def test_default_acceptance_counts_only_distances_from_one() -> None:
    evaluation = assess_initial_deal_distances(
        (0, 1, 2, 3, 4, 5, None, None),
        DEFAULT_INITIAL_DEAL_CONFIG,
    )

    assert evaluation.close_row_count == 2
    assert evaluation.playable_row_count == 3
    assert evaluation.passed


def test_missing_close_or_playable_rows_rejects_initial_deal() -> None:
    no_close = assess_initial_deal_distances(
        (0, 3, 3, 3, 4, 4, 5, None),
        DEFAULT_INITIAL_DEAL_CONFIG,
    )
    too_few_playable = assess_initial_deal_distances(
        (1, 4, 4, 4, 4, 5, None, None),
        DEFAULT_INITIAL_DEAL_CONFIG,
    )

    assert not no_close.passed
    assert not too_few_playable.passed


def test_initial_deal_config_rejects_invalid_attempt_limit() -> None:
    try:
        InitialDealConfig(max_attempts=0)
    except ValueError as error:
        assert "試行" in str(error)
    else:
        raise AssertionError("最大試行回数0を受理してはいけません")
