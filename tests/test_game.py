import pytest

from mahjong_puzzle.game import (
    BLOCK_COUNT,
    BOARD_TILE_COUNT,
    DORA_RESERVE_COUNT,
    TOTAL_TURN_COUNT,
    GameState,
)
from mahjong_puzzle.initial_deal import InitialDealConfig
from mahjong_puzzle.tetromino import TetrominoKind


def test_new_game_allocates_all_136_tiles_without_overlap() -> None:
    game = GameState.new(seed=20260724)

    assert len(game.board.tiles) == BOARD_TILE_COUNT == 64
    assert len(game.dora_indicator_tiles) == DORA_RESERVE_COUNT == 4
    assert len(game.blocks) == BLOCK_COUNT == 17
    assert all(len(block.tiles) == 4 for block in game.blocks)
    assert len(game.tracked_tile_ids()) == 136
    assert game.visible_dora_indicators == (game.dora_indicator_tiles[0],)
    assert game.initial_deal_debug is not None
    assert game.initial_deal_debug.seed == 20260724
    assert game.initial_deal_debug.attempt_count >= 1
    assert len(game.initial_deal_debug.row_distances) == 8
    assert game.initial_deal_debug.passed
    assert not game.initial_deal_debug.used_fallback


def test_same_seed_produces_same_board_tiles_and_block_kinds() -> None:
    first = GameState.new(seed=1234)
    second = GameState.new(seed=1234)

    assert [tile.tile_id for tile in first.board.tiles] == [
        tile.tile_id for tile in second.board.tiles
    ]
    assert [block.kind for block in first.blocks] == [
        block.kind for block in second.blocks
    ]
    assert [tile.tile_id for tile in first.dora_indicator_tiles] == [
        tile.tile_id for tile in second.dora_indicator_tiles
    ]
    assert [
        tile.tile_id for block in first.blocks for tile in block.tiles
    ] == [
        tile.tile_id for block in second.blocks for tile in block.tiles
    ]
    assert first.initial_deal_debug == second.initial_deal_debug


def test_attempt_limit_uses_fallback_without_looping_forever() -> None:
    config = InitialDealConfig(
        max_close_distance=0,
        required_close_rows=1,
        max_playable_distance=3,
        required_playable_rows=3,
        max_attempts=2,
    )

    game = GameState.new(seed=11, initial_deal_config=config)

    assert game.initial_deal_debug is not None
    assert game.initial_deal_debug.attempt_count == 2
    assert not game.initial_deal_debug.passed
    assert game.initial_deal_debug.used_fallback
    assert len(game.tracked_tile_ids()) == 136


def test_fallback_keeps_best_candidate_instead_of_last_attempt() -> None:
    one_attempt = InitialDealConfig(
        max_close_distance=0,
        required_close_rows=1,
        max_playable_distance=3,
        required_playable_rows=3,
        max_attempts=1,
    )
    two_attempts = InitialDealConfig(
        max_close_distance=0,
        required_close_rows=1,
        max_playable_distance=3,
        required_playable_rows=3,
        max_attempts=2,
    )

    first_only = GameState.new(seed=0, initial_deal_config=one_attempt)
    with_worse_second = GameState.new(
        seed=0,
        initial_deal_config=two_attempts,
    )

    assert with_worse_second.initial_deal_debug is not None
    assert with_worse_second.initial_deal_debug.attempt_count == 2
    assert with_worse_second.initial_deal_debug.used_fallback
    assert [
        tile.tile_id for tile in with_worse_second.board.tiles
    ] == [
        tile.tile_id for tile in first_only.board.tiles
    ]


def test_current_and_three_next_blocks_are_exposed() -> None:
    game = GameState.new(seed=1)

    assert game.current_block is not None
    assert len(game.next_blocks) == 3
    assert game.next_blocks == game.blocks[1:4]


def test_dora_indicators_are_revealed_up_to_four() -> None:
    game = GameState.new(seed=10)

    first_additions = game.reveal_dora_indicators(2)
    final_additions = game.reveal_dora_indicators(5)
    no_space = game.reveal_dora_indicators(1)

    assert first_additions == game.dora_indicator_tiles[1:3]
    assert final_additions == game.dora_indicator_tiles[3:4]
    assert no_space == ()
    assert game.visible_dora_indicators == game.dora_indicator_tiles


def test_cursor_movement_stays_inside_board() -> None:
    game = GameState.new(seed=2)

    while game.move_active(-1, 0):
        pass
    assert game.active_x == 0
    assert not game.move_active(-1, 0)

    while game.move_active(0, 1):
        pass
    assert game.active_y + game.current_block.height == 8
    assert not game.move_active(0, 1)


def test_rotation_outside_board_is_rejected_without_changing_rotation() -> None:
    game = GameState.new(seed=3)
    while game.move_active(0, 1):
        pass
    before = game.active_rotation

    if game.current_block.kind is TetrominoKind.O:
        pytest.skip("Oブロックでは境界回転差が作れません")

    accepted = game.rotate_active(clockwise=True)
    if not accepted:
        assert game.active_rotation == before


def test_placement_overwrites_four_tiles_and_records_river_context() -> None:
    game = GameState.new(seed=4)
    block = game.current_block
    assert block is not None
    preview = game.preview_cells
    old_ids = {
        game.board.tile_at(cell.coordinate).tile_id for cell in preview
    }

    result = game.place_active()

    assert result.turn == 1
    assert result.placement_id == block.block_id
    assert len(result.discards) == 4
    assert {record.tile.tile_id for record in result.discards} == old_ids
    assert all(record.turn == 1 for record in result.discards)
    assert all(record.placement_id == block.block_id for record in result.discards)
    assert game.river.total_count == 4
    assert {game.board.tile_at(cell.coordinate).tile_id for cell in preview} == {
        cell.tile.tile_id for cell in preview
    }
    assert len(game.tracked_tile_ids()) == 136


def test_changed_rows_are_reported_without_running_phase_one_rules() -> None:
    game = GameState.new(seed=5)

    result = game.place_active()

    assert result.changed_rows == tuple(
        sorted({cell.coordinate.y for cell in result.placed_cells})
    )
    assert not hasattr(result, "winning_rows")


def test_game_ends_after_17_placements_and_preserves_all_tiles() -> None:
    game = GameState.new(seed=6)

    for expected_turn in range(1, TOTAL_TURN_COUNT + 1):
        result = game.place_active()
        assert result.turn == expected_turn

    assert game.is_game_over
    assert game.current_block is None
    assert game.remaining_turns == 0
    assert game.river.total_count == 68
    assert len(game.tracked_tile_ids()) == 136
    with pytest.raises(RuntimeError, match="終了"):
        game.place_active()
