from mahjong_puzzle.kan import check_kans, find_kan_candidates
from mahjong_puzzle.tiles import Suit, TileType


def s(rank: int) -> TileType:
    return TileType.suited(Suit.MANZU, rank)


def test_detects_one_new_kan() -> None:
    tiles = [s(1)] * 4 + [s(2), s(3), s(4), s(5)]

    assert find_kan_candidates(tiles) == frozenset({s(1)})
    result = check_kans(tiles, completed_kans=set())
    assert result.new_kans == frozenset({s(1)})
    assert result.should_defer_win


def test_same_line_same_kind_is_not_a_new_kan() -> None:
    tiles = [s(1)] * 4 + [s(2), s(3), s(4), s(5)]

    result = check_kans(tiles, completed_kans={s(1)})

    assert result.candidates == frozenset({s(1)})
    assert result.new_kans == frozenset()
    assert not result.should_defer_win


def test_another_kind_on_same_line_is_new() -> None:
    tiles = [s(1)] * 4 + [s(2)] * 4

    result = check_kans(tiles, completed_kans={s(1)})

    assert result.new_kans == frozenset({s(2)})


def test_two_new_kans_on_one_line_are_both_returned() -> None:
    tiles = [s(1)] * 4 + [s(2)] * 4

    result = check_kans(tiles, completed_kans=set())

    assert result.new_kans == frozenset({s(1), s(2)})


def test_same_kind_can_be_new_on_another_line() -> None:
    tiles = [s(1)] * 4 + [s(2), s(3), s(4), s(5)]

    first_line = check_kans(tiles, completed_kans={s(1)})
    second_line = check_kans(tiles, completed_kans=set())

    assert first_line.new_kans == frozenset()
    assert second_line.new_kans == frozenset({s(1)})
