from mahjong_puzzle.state import LineState, TurnState
from mahjong_puzzle.tiles import Suit, TileType
from mahjong_puzzle.yaku import Yaku


def s(rank: int) -> TileType:
    return TileType.suited(Suit.MANZU, rank)


def test_first_win_registers_all_current_yaku() -> None:
    state = LineState()

    result = state.register_win({Yaku.CHINITSU, Yaku.ALL_SEQUENCES})

    assert result.is_new_win
    assert result.new_yaku == {Yaku.CHINITSU, Yaku.ALL_SEQUENCES}
    assert state.acquired_yaku == {Yaku.CHINITSU, Yaku.ALL_SEQUENCES}
    assert state.win_count == 1
    assert state.has_won


def test_first_roleless_basic_win_is_registered() -> None:
    state = LineState()

    result = state.register_win(set())

    assert result.is_new_win
    assert result.new_yaku == frozenset()
    assert state.has_won
    assert state.win_count == 1


def test_only_acquired_yaku_does_not_register_again() -> None:
    state = LineState(acquired_yaku={Yaku.CHINITSU}, win_count=1)

    result = state.register_win({Yaku.CHINITSU})

    assert not result.is_new_win
    assert result.new_yaku == frozenset()
    assert state.win_count == 1


def test_new_yaku_registers_even_with_acquired_yaku_present() -> None:
    state = LineState(acquired_yaku={Yaku.CHINITSU}, win_count=1)

    result = state.register_win({Yaku.CHINITSU, Yaku.IIPEIKOU})

    assert result.is_new_win
    assert result.new_yaku == frozenset({Yaku.IIPEIKOU})
    assert state.acquired_yaku == {Yaku.CHINITSU, Yaku.IIPEIKOU}
    assert result.previous_win_count == 1


def test_roleless_basic_win_cannot_be_registered_twice() -> None:
    state = LineState(has_won=True, win_count=1)

    result = state.register_win(set())

    assert not result.is_new_win
    assert state.has_won
    assert state.win_count == 1


def test_line_kan_history_is_updated_per_line() -> None:
    first_line = LineState()
    second_line = LineState()
    tiles = [s(1)] * 4 + [s(2)] * 4

    first = first_line.check_and_record_kans(tiles)
    again = first_line.check_and_record_kans(tiles)
    other_line = second_line.check_and_record_kans(tiles)

    assert first.new_kans == {s(1), s(2)}
    assert again.new_kans == frozenset()
    assert other_line.new_kans == {s(1), s(2)}


def test_win_turn_increments_combo_and_exposes_simultaneous_lines() -> None:
    state = TurnState(consecutive_win_turns=2)

    result = state.record_turn(winning_line_count=3, kan_count=0)

    assert state.consecutive_win_turns == 3
    assert result.consecutive_win_turns == 3
    assert result.winning_line_count == 3


def test_kan_only_turn_keeps_combo() -> None:
    state = TurnState(consecutive_win_turns=2)

    state.record_turn(winning_line_count=0, kan_count=1)

    assert state.consecutive_win_turns == 2


def test_empty_turn_resets_combo() -> None:
    state = TurnState(consecutive_win_turns=2)

    state.record_turn(winning_line_count=0, kan_count=0)

    assert state.consecutive_win_turns == 0
