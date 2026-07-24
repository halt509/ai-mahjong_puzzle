import pytest

from mahjong_puzzle.board import BOARD_HEIGHT, BOARD_WIDTH, Board, Coordinate
from mahjong_puzzle.tiles import Tile, create_full_tile_set


def make_board() -> tuple[Board, tuple[Tile, ...]]:
    tiles = create_full_tile_set()
    return Board.from_tiles(tiles[: BOARD_WIDTH * BOARD_HEIGHT]), tiles


def test_board_is_filled_row_major_with_64_unique_tiles() -> None:
    board, tiles = make_board()

    assert board.tile_at(Coordinate(0, 0)) == tiles[0]
    assert board.tile_at(Coordinate(7, 7)) == tiles[63]
    assert len(board.tiles) == 64
    assert len({tile.tile_id for tile in board.tiles}) == 64


def test_overwrite_returns_old_tiles_and_updates_board() -> None:
    board, tiles = make_board()
    replacements = {
        Coordinate(1, 2): tiles[64],
        Coordinate(2, 2): tiles[65],
    }

    result = board.overwrite(replacements)

    assert tuple(item.coordinate for item in result) == (
        Coordinate(1, 2),
        Coordinate(2, 2),
    )
    assert tuple(item.old_tile for item in result) == (tiles[17], tiles[18])
    assert board.tile_at(Coordinate(1, 2)) == tiles[64]
    assert board.tile_at(Coordinate(2, 2)) == tiles[65]


def test_invalid_overwrite_is_atomic() -> None:
    board, tiles = make_board()
    before = board.rows

    with pytest.raises(ValueError, match="盤面外"):
        board.overwrite(
            {
                Coordinate(0, 0): tiles[64],
                Coordinate(8, 0): tiles[65],
            }
        )

    assert board.rows == before


def test_board_rejects_duplicate_incoming_physical_tiles() -> None:
    board, tiles = make_board()

    with pytest.raises(ValueError, match="個体ID"):
        board.overwrite(
            {
                Coordinate(0, 0): tiles[64],
                Coordinate(1, 0): tiles[64],
            }
        )
