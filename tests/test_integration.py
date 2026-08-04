from __future__ import annotations

from collections import deque
from fractions import Fraction

import pytest

from mahjong_puzzle.board import BOARD_HEIGHT, BOARD_WIDTH, Board, Coordinate
from mahjong_puzzle.game import BLOCK_COUNT, GameState
from mahjong_puzzle.hand import FourPairsDecomposition
from mahjong_puzzle.integration import GameSession
from mahjong_puzzle.river import River
from mahjong_puzzle.state import LineState, TurnState
from mahjong_puzzle.tetromino import Tetromino, TetrominoKind
from mahjong_puzzle.tiles import (
    Honor,
    Suit,
    Tile,
    TileType,
    all_tile_types,
    create_full_tile_set,
)
from mahjong_puzzle.yaku import Yaku
from mahjong_puzzle.ui import notices_from_turn


def s(rank: int, suit: Suit = Suit.MANZU) -> TileType:
    return TileType.suited(suit, rank)


def h(honor: Honor) -> TileType:
    return TileType.honor_tile(honor)


_INVALID_ROW_2 = [
    h(Honor.EAST),
    s(2, Suit.SOUZU),
    s(4, Suit.SOUZU),
    s(6, Suit.SOUZU),
    s(8, Suit.SOUZU),
    h(Honor.NORTH),
    h(Honor.WEST),
    s(9),
]
_INVALID_ROW_3 = [
    h(Honor.SOUTH),
    s(1, Suit.SOUZU),
    s(3, Suit.SOUZU),
    s(5, Suit.SOUZU),
    s(7, Suit.SOUZU),
    s(9, Suit.SOUZU),
    h(Honor.RED),
    h(Honor.GREEN),
]


def _build_session(
    *,
    row_specs: dict[int, list[TileType]],
    block_types: tuple[TileType, TileType, TileType, TileType],
    block_kind: TetrominoKind,
    rotation: int,
    origin_x: int,
    origin_y: int,
    dora_types: tuple[TileType, TileType, TileType, TileType],
    revealed_dora_count: int = 1,
    line_states: tuple[LineState, ...] | None = None,
    turn_state: TurnState | None = None,
) -> GameSession:
    pools = {
        kind: deque(
            tile for tile in create_full_tile_set() if tile.kind == kind
        )
        for kind in all_tile_types()
    }

    def take(kind: TileType) -> Tile:
        if not pools[kind]:
            raise AssertionError(f"テスト牌が不足しています: {kind}")
        return pools[kind].popleft()

    def take_any() -> Tile:
        for kind in all_tile_types():
            if pools[kind]:
                return pools[kind].popleft()
        raise AssertionError("テスト牌が不足しています")

    block_tiles = tuple(take(kind) for kind in block_types)
    first_block = Tetromino(
        block_id=1,
        kind=block_kind,
        tiles=block_tiles,
    )
    rotated = first_block.with_rotation(rotation)
    positioned = rotated.positioned_cells(origin_x=origin_x, origin_y=origin_y)
    affected = {cell.coordinate: cell.tile.kind for cell in positioned}

    desired_board: dict[Coordinate, Tile] = {}
    for y, kinds in row_specs.items():
        assert len(kinds) == BOARD_WIDTH
        for x, kind in enumerate(kinds):
            coordinate = Coordinate(x, y)
            if coordinate in affected:
                assert affected[coordinate] == kind
            else:
                desired_board[coordinate] = take(kind)

    dora_tiles = tuple(take(kind) for kind in dora_types)
    board_tiles: list[Tile] = []
    for y in range(BOARD_HEIGHT):
        for x in range(BOARD_WIDTH):
            coordinate = Coordinate(x, y)
            board_tiles.append(
                desired_board[coordinate]
                if coordinate in desired_board
                else take_any()
            )

    remaining = tuple(tile for kind in all_tile_types() for tile in pools[kind])
    assert len(remaining) == 64
    future_blocks = tuple(
        Tetromino(
            block_id=index + 2,
            kind=tuple(TetrominoKind)[index % len(TetrominoKind)],
            tiles=remaining[index * 4 : index * 4 + 4],
        )
        for index in range(BLOCK_COUNT - 1)
    )
    game = GameState(
        board=Board.from_tiles(board_tiles),
        dora_indicator_tiles=dora_tiles,
        blocks=(first_block,) + future_blocks,
        river=River(),
        active_x=origin_x,
        active_y=origin_y,
        active_rotation=rotation,
        revealed_dora_count=revealed_dora_count,
    )
    return GameSession(
        game=game,
        line_states=line_states
        if line_states is not None
        else tuple(LineState() for _ in range(BOARD_HEIGHT)),
        turn_state=turn_state if turn_state is not None else TurnState(),
    )


def test_new_kan_defers_that_row_and_reveals_dora() -> None:
    kan_kind = s(1)
    session = _build_session(
        row_specs={
            0: [kan_kind] * 4 + [s(2), s(3), s(4), s(5)],
        },
        block_types=(kan_kind,) * 4,
        block_kind=TetrominoKind.I,
        rotation=0,
        origin_x=0,
        origin_y=0,
        dora_types=(s(9, Suit.SOUZU), s(9, Suit.PINZU), h(Honor.NORTH), h(Honor.WHITE)),
    )

    result = session.place_active()

    assert len(result.kans) == 1
    assert result.kans[0].row == 0
    assert result.kans[0].tile_type == kan_kind
    assert result.kans[0].revealed_indicator == session.game.dora_indicator_tiles[1]
    assert result.wins == ()
    assert kan_kind in session.line_states[0].completed_kans
    assert len(session.game.visible_dora_indicators) == 2


def test_new_kan_dora_scores_on_another_changed_row_in_same_turn() -> None:
    kan_kind = s(1)
    winning_row = [
        s(1, Suit.PINZU),
        s(1, Suit.PINZU),
        s(2, Suit.PINZU),
        s(2, Suit.PINZU),
        s(3, Suit.PINZU),
        s(3, Suit.PINZU),
        s(5, Suit.PINZU),
        s(5, Suit.PINZU),
    ]
    session = _build_session(
        row_specs={
            0: [kan_kind] * 4 + [s(2), s(3), s(4), s(5)],
            1: winning_row,
            2: _INVALID_ROW_2,
            3: _INVALID_ROW_3,
        },
        block_types=(
            kan_kind,
            s(1, Suit.PINZU),
            h(Honor.EAST),
            h(Honor.SOUTH),
        ),
        block_kind=TetrominoKind.I,
        rotation=1,
        origin_x=0,
        origin_y=0,
        dora_types=(
            s(9, Suit.SOUZU),
            s(9, Suit.PINZU),
            h(Honor.NORTH),
            h(Honor.WHITE),
        ),
    )

    result = session.place_active()

    assert [event.row for event in result.kans] == [0]
    assert [event.row for event in result.wins] == [1]
    assert result.wins[0].dora_count == 2
    assert result.wins[0].score.dora_score == 1000
    assert result.consecutive_win_turns == 1


def test_completed_kan_does_not_defer_a_later_win_on_same_line() -> None:
    kan_kind = s(1)
    row = [kan_kind] * 4 + [s(2), s(3), s(5), s(5)]
    line_states = tuple(LineState() for _ in range(BOARD_HEIGHT))
    line_states[0].completed_kans.add(kan_kind)
    session = _build_session(
        row_specs={0: row},
        block_types=(kan_kind,) * 4,
        block_kind=TetrominoKind.I,
        rotation=0,
        origin_x=0,
        origin_y=0,
        dora_types=(
            s(9, Suit.SOUZU),
            s(9, Suit.PINZU),
            h(Honor.NORTH),
            h(Honor.WHITE),
        ),
        line_states=line_states,
    )

    result = session.place_active()

    assert result.kans == ()
    assert [event.row for event in result.wins] == [0]
    assert Yaku.CHINITSU in result.wins[0].current_yaku


def test_two_changed_rows_win_with_simultaneous_multiplier() -> None:
    row_zero = [s(1), s(1), s(2), s(2), s(3), s(3), s(5), s(5)]
    row_one = [
        s(2, Suit.PINZU),
        s(2, Suit.PINZU),
        s(3, Suit.PINZU),
        s(3, Suit.PINZU),
        s(4, Suit.PINZU),
        s(4, Suit.PINZU),
        s(6, Suit.PINZU),
        s(6, Suit.PINZU),
    ]
    session = _build_session(
        row_specs={
            0: row_zero,
            1: row_one,
            2: _INVALID_ROW_2,
            3: _INVALID_ROW_3,
        },
        block_types=(
            s(1),
            s(2, Suit.PINZU),
            h(Honor.EAST),
            h(Honor.SOUTH),
        ),
        block_kind=TetrominoKind.I,
        rotation=1,
        origin_x=0,
        origin_y=0,
        dora_types=(
            s(9, Suit.SOUZU),
            h(Honor.NORTH),
            h(Honor.WHITE),
            h(Honor.RED),
        ),
    )

    result = session.place_active()

    assert [event.row for event in result.wins] == [0, 1]
    assert all(
        event.score.simultaneous_multiplier == Fraction(3, 2)
        for event in result.wins
    )
    assert result.turn_score == sum(event.score.total_score for event in result.wins)
    assert result.total_score == result.turn_score


def test_rewin_scores_only_new_yaku_and_updates_line_history() -> None:
    row = [s(1), s(2), s(3), s(1), s(2), s(3), s(5), s(5)]
    line_states = tuple(LineState() for _ in range(BOARD_HEIGHT))
    line_states[0].acquired_yaku.update(
        {Yaku.ALL_SEQUENCES, Yaku.CHINITSU, Yaku.FOUR_PAIRS}
    )
    line_states[0].win_count = 1
    line_states[0].has_won = True
    session = _build_session(
        row_specs={0: row},
        block_types=(s(1), s(2), s(3), s(1)),
        block_kind=TetrominoKind.I,
        rotation=0,
        origin_x=0,
        origin_y=0,
        dora_types=(
            s(9, Suit.SOUZU),
            h(Honor.NORTH),
            h(Honor.WHITE),
            h(Honor.RED),
        ),
        line_states=line_states,
    )

    result = session.place_active()

    assert len(result.wins) == 1
    win = result.wins[0]
    assert win.new_yaku == frozenset({Yaku.IIPEIKOU})
    assert set(win.score.yaku_points) == {Yaku.IIPEIKOU}
    assert session.line_states[0].acquired_yaku == {
        Yaku.ALL_SEQUENCES,
        Yaku.CHINITSU,
        Yaku.FOUR_PAIRS,
        Yaku.IIPEIKOU,
    }
    assert session.line_states[0].win_count == 2


def test_multiple_kans_record_history_past_dora_limit_and_keep_combo() -> None:
    one = s(1)
    two = s(2)
    session = _build_session(
        row_specs={0: [one] * 4 + [two] * 4},
        block_types=(one,) * 4,
        block_kind=TetrominoKind.I,
        rotation=0,
        origin_x=0,
        origin_y=0,
        dora_types=(
            s(9, Suit.SOUZU),
            s(9, Suit.PINZU),
            h(Honor.NORTH),
            h(Honor.WHITE),
        ),
        revealed_dora_count=3,
        turn_state=TurnState(consecutive_win_turns=2),
    )

    result = session.place_active()

    assert [event.tile_type for event in result.kans] == [one, two]
    assert result.kans[0].revealed_indicator == session.game.dora_indicator_tiles[3]
    assert result.kans[1].revealed_indicator is None
    assert session.line_states[0].completed_kans == {one, two}
    assert len(session.game.visible_dora_indicators) == 4
    assert result.consecutive_win_turns == 2


def test_turn_without_win_or_kan_resets_combo() -> None:
    invalid_row = [
        s(1),
        s(2),
        s(4),
        s(5),
        s(7),
        s(8),
        h(Honor.EAST),
        h(Honor.SOUTH),
    ]
    session = _build_session(
        row_specs={0: invalid_row},
        block_types=(s(1), s(2), s(4), s(5)),
        block_kind=TetrominoKind.I,
        rotation=0,
        origin_x=0,
        origin_y=0,
        dora_types=(
            s(9, Suit.SOUZU),
            s(9, Suit.PINZU),
            h(Honor.NORTH),
            h(Honor.WHITE),
        ),
        turn_state=TurnState(consecutive_win_turns=3),
    )

    result = session.place_active()

    assert result.kans == ()
    assert result.wins == ()
    assert result.consecutive_win_turns == 0


def test_roleless_basic_shape_wins_first_time_with_base_and_dora_score() -> None:
    row = [
        s(1),
        s(2),
        s(3),
        h(Honor.EAST),
        h(Honor.EAST),
        h(Honor.EAST),
        s(5, Suit.PINZU),
        s(5, Suit.PINZU),
    ]
    session = _build_session(
        row_specs={0: row},
        block_types=tuple(row[:4]),
        block_kind=TetrominoKind.I,
        rotation=0,
        origin_x=0,
        origin_y=0,
        dora_types=(
            s(4, Suit.PINZU),
            s(9, Suit.SOUZU),
            h(Honor.NORTH),
            h(Honor.WHITE),
        ),
    )

    result = session.place_active()

    assert len(result.wins) == 1
    win = result.wins[0]
    assert win.current_yaku == frozenset()
    assert win.new_yaku == frozenset()
    assert win.score.base_win_score == 500
    assert win.dora_count == 2
    assert win.score.dora_score == 1000
    assert win.score.total_score == 1500
    assert session.line_states[0].has_won
    assert session.line_states[0].win_count == 1
    notice = notices_from_turn(result)[0]
    assert "基本 +500" in notice.lines
    assert "役 NONE +0" in notice.lines
    assert "ドラ 2 +1000・合計 +1500" in notice.lines


@pytest.mark.parametrize(
    "row",
    [
        [s(1), s(2), s(3), s(4), s(5), s(6), h(Honor.EAST), h(Honor.EAST)],
        [
            s(1),
            s(2),
            s(3),
            h(Honor.EAST),
            h(Honor.EAST),
            h(Honor.EAST),
            s(5, Suit.PINZU),
            s(5, Suit.PINZU),
        ],
        [
            s(1),
            s(1),
            s(1),
            s(2, Suit.PINZU),
            s(2, Suit.PINZU),
            s(2, Suit.PINZU),
            h(Honor.EAST),
            h(Honor.EAST),
        ],
    ],
    ids=("sequence-sequence-pair", "sequence-triplet-pair", "triplet-triplet-pair"),
)
def test_each_normal_shape_type_gets_an_initial_basic_win(
    row: list[TileType],
) -> None:
    session = _build_session(
        row_specs={0: row},
        block_types=tuple(row[:4]),
        block_kind=TetrominoKind.I,
        rotation=0,
        origin_x=0,
        origin_y=0,
        dora_types=(
            s(9, Suit.SOUZU),
            s(9, Suit.PINZU),
            h(Honor.NORTH),
            h(Honor.WHITE),
        ),
    )

    result = session.place_active()

    assert len(result.wins) == 1
    assert result.wins[0].score.base_win_score == 500


def test_roleless_basic_shape_cannot_rewin_without_new_yaku() -> None:
    row = [
        s(1),
        s(2),
        s(3),
        h(Honor.EAST),
        h(Honor.EAST),
        h(Honor.EAST),
        s(5, Suit.PINZU),
        s(5, Suit.PINZU),
    ]
    line_states = tuple(LineState() for _ in range(BOARD_HEIGHT))
    line_states[0].has_won = True
    line_states[0].win_count = 1
    session = _build_session(
        row_specs={0: row},
        block_types=tuple(row[:4]),
        block_kind=TetrominoKind.I,
        rotation=0,
        origin_x=0,
        origin_y=0,
        dora_types=(
            s(9, Suit.SOUZU),
            s(9, Suit.PINZU),
            h(Honor.NORTH),
            h(Honor.WHITE),
        ),
        line_states=line_states,
    )

    result = session.place_active()

    assert result.wins == ()
    assert session.line_states[0].has_won
    assert session.line_states[0].win_count == 1


def test_new_yaku_after_roleless_win_can_rewin_and_gets_base_score() -> None:
    row = [s(1), s(2), s(3), s(1), s(2), s(3), s(5), s(5)]
    line_states = tuple(LineState() for _ in range(BOARD_HEIGHT))
    line_states[0].has_won = True
    line_states[0].win_count = 1
    session = _build_session(
        row_specs={0: row},
        block_types=tuple(row[:4]),
        block_kind=TetrominoKind.I,
        rotation=0,
        origin_x=0,
        origin_y=0,
        dora_types=(
            s(9, Suit.SOUZU),
            s(9, Suit.PINZU),
            h(Honor.NORTH),
            h(Honor.WHITE),
        ),
        line_states=line_states,
    )

    result = session.place_active()

    assert len(result.wins) == 1
    win = result.wins[0]
    assert win.new_yaku
    assert win.score.base_win_score == 500
    assert session.line_states[0].has_won
    assert session.line_states[0].win_count == 2


def test_new_kan_defers_a_roleless_basic_win_on_that_row() -> None:
    quad = s(1)
    row = [
        quad,
        quad,
        quad,
        quad,
        s(2),
        s(3),
        s(5, Suit.PINZU),
        s(5, Suit.PINZU),
    ]
    session = _build_session(
        row_specs={0: row},
        block_types=(quad,) * 4,
        block_kind=TetrominoKind.I,
        rotation=0,
        origin_x=0,
        origin_y=0,
        dora_types=(
            s(9, Suit.SOUZU),
            s(9, Suit.PINZU),
            h(Honor.NORTH),
            h(Honor.WHITE),
        ),
    )

    result = session.place_active()

    assert [event.tile_type for event in result.kans] == [quad]
    assert result.wins == ()
    assert not session.line_states[0].has_won


def test_four_pairs_wins_without_a_normal_decomposition() -> None:
    row = (
        [s(2)] * 2
        + [s(5)] * 2
        + [s(3, Suit.PINZU)] * 2
        + [h(Honor.WHITE)] * 2
    )
    session = _build_session(
        row_specs={0: row},
        block_types=tuple(row[:4]),
        block_kind=TetrominoKind.I,
        rotation=0,
        origin_x=0,
        origin_y=0,
        dora_types=(
            s(9, Suit.SOUZU),
            s(9, Suit.PINZU),
            h(Honor.NORTH),
            h(Honor.RED),
        ),
    )

    result = session.place_active()

    assert len(result.wins) == 1
    win = result.wins[0]
    assert isinstance(win.evaluation.decomposition, FourPairsDecomposition)
    assert win.new_yaku == {Yaku.FOUR_PAIRS}
    assert win.score.yaku_points == {Yaku.FOUR_PAIRS: 4000}
    assert win.score.base_win_score == 500


def test_new_kan_still_takes_priority_over_four_pairs_evaluation() -> None:
    quad = s(2)
    row = [quad] * 4 + [s(3, Suit.PINZU)] * 2 + [h(Honor.WHITE)] * 2
    session = _build_session(
        row_specs={0: row},
        block_types=(quad,) * 4,
        block_kind=TetrominoKind.I,
        rotation=0,
        origin_x=0,
        origin_y=0,
        dora_types=(
            s(9, Suit.SOUZU),
            s(9, Suit.PINZU),
            h(Honor.NORTH),
            h(Honor.RED),
        ),
    )

    result = session.place_active()

    assert [event.tile_type for event in result.kans] == [quad]
    assert result.wins == ()


def test_rewin_scores_only_a_new_phase5_yaku() -> None:
    row = [s(1), s(2), s(3)] + [
        s(4, Suit.PINZU),
        s(5, Suit.PINZU),
        s(6, Suit.PINZU),
    ] + [h(Honor.EAST)] * 2
    line_states = tuple(LineState() for _ in range(BOARD_HEIGHT))
    line_states[0].acquired_yaku.add(Yaku.ALL_SEQUENCES)
    line_states[0].win_count = 1
    line_states[0].has_won = True
    session = _build_session(
        row_specs={0: row},
        block_types=tuple(row[:4]),
        block_kind=TetrominoKind.I,
        rotation=0,
        origin_x=0,
        origin_y=0,
        dora_types=(
            s(9, Suit.SOUZU),
            s(9, Suit.PINZU),
            h(Honor.NORTH),
            h(Honor.RED),
        ),
        line_states=line_states,
    )

    result = session.place_active()

    assert len(result.wins) == 1
    win = result.wins[0]
    assert win.new_yaku == {Yaku.HONOR_PAIR}
    assert win.score.yaku_points == {Yaku.HONOR_PAIR: 1000}


def test_acquired_phase5_yaku_alone_does_not_rewin() -> None:
    row = [s(1), s(2), s(3)] + [
        s(4, Suit.PINZU),
        s(5, Suit.PINZU),
        s(6, Suit.PINZU),
    ] + [h(Honor.EAST)] * 2
    line_states = tuple(LineState() for _ in range(BOARD_HEIGHT))
    line_states[0].acquired_yaku.update(
        {Yaku.ALL_SEQUENCES, Yaku.HONOR_PAIR}
    )
    line_states[0].win_count = 1
    line_states[0].has_won = True
    session = _build_session(
        row_specs={0: row},
        block_types=tuple(row[:4]),
        block_kind=TetrominoKind.I,
        rotation=0,
        origin_x=0,
        origin_y=0,
        dora_types=(
            s(9, Suit.SOUZU),
            s(9, Suit.PINZU),
            h(Honor.NORTH),
            h(Honor.RED),
        ),
        line_states=line_states,
    )

    result = session.place_active()

    assert result.wins == ()
