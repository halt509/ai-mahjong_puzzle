import random

import pytest

from mahjong_puzzle.tetromino import (
    Tetromino,
    TetrominoKind,
    create_seven_bag_sequence,
)
from mahjong_puzzle.tiles import Tile, create_full_tile_set


def make_block(kind: TetrominoKind = TetrominoKind.T) -> Tetromino:
    return Tetromino(block_id=1, kind=kind, tiles=create_full_tile_set()[:4])


@pytest.mark.parametrize("kind", list(TetrominoKind))
def test_each_tetromino_has_four_distinct_normalized_cells(
    kind: TetrominoKind,
) -> None:
    block = make_block(kind)

    for rotation in range(4):
        rotated = block.with_rotation(rotation)
        coordinates = {(cell.x, cell.y) for cell in rotated.cells}
        assert len(coordinates) == 4
        assert min(x for x, _ in coordinates) == 0
        assert min(y for _, y in coordinates) == 0


@pytest.mark.parametrize("kind", list(TetrominoKind))
def test_four_rotations_restore_shape_and_tile_positions(kind: TetrominoKind) -> None:
    block = make_block(kind)
    rotated = block
    for _ in range(4):
        rotated = rotated.rotated(clockwise=True)

    assert rotated.rotation == block.rotation
    assert rotated.cells == block.cells


def test_rotation_moves_shape_and_tiles_together() -> None:
    block = make_block(TetrominoKind.I)
    original_by_id = {cell.tile.tile_id: (cell.x, cell.y) for cell in block.cells}
    rotated_by_id = {
        cell.tile.tile_id: (cell.x, cell.y)
        for cell in block.rotated(clockwise=True).cells
    }

    assert original_by_id[block.tiles[1].tile_id] == (1, 0)
    assert rotated_by_id[block.tiles[1].tile_id] == (0, 1)


def test_placement_coordinates_are_offset_from_origin() -> None:
    block = make_block(TetrominoKind.O)

    cells = block.positioned_cells(origin_x=3, origin_y=4)

    assert {(cell.coordinate.x, cell.coordinate.y) for cell in cells} == {
        (3, 4),
        (4, 4),
        (3, 5),
        (4, 5),
    }


def test_fit_check_only_accepts_positions_inside_board() -> None:
    block = make_block(TetrominoKind.I)

    assert block.fits(origin_x=4, origin_y=7, board_width=8, board_height=8)
    assert not block.fits(origin_x=5, origin_y=7, board_width=8, board_height=8)
    assert not block.fits(origin_x=-1, origin_y=0, board_width=8, board_height=8)


def test_seven_bag_contains_each_kind_once_per_complete_bag() -> None:
    sequence = create_seven_bag_sequence(17, random.Random(20260724))

    assert set(sequence[:7]) == set(TetrominoKind)
    assert set(sequence[7:14]) == set(TetrominoKind)
    assert len(set(sequence[14:])) == 3


def test_tetromino_rejects_duplicate_physical_tiles() -> None:
    tile: Tile = create_full_tile_set()[0]

    with pytest.raises(ValueError, match="個体ID"):
        Tetromino(block_id=1, kind=TetrominoKind.I, tiles=(tile,) * 4)
