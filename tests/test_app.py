from mahjong_puzzle.app import (
    BOARD_ORIGIN_Y,
    NEXT_CELL_SIZE,
    NEXT_CELL_STEP,
    NEXT_ITEM_SPACING,
    NEXT_START_OFFSET_Y,
    SIDEBAR_HEIGHT,
    MahjongPuzzleApp,
    tile_label,
)
from mahjong_puzzle.tetromino import Tetromino, TetrominoKind
from mahjong_puzzle.tiles import Honor, Suit, TileType, create_full_tile_set


def test_ascii_tile_labels_cover_suits_and_honors() -> None:
    assert tile_label(TileType.suited(Suit.MANZU, 1)) == "m1"
    assert tile_label(TileType.suited(Suit.PINZU, 9)) == "p9"
    assert tile_label(TileType.suited(Suit.SOUZU, 5)) == "s5"
    assert tile_label(TileType.honor_tile(Honor.EAST)) == "E"
    assert tile_label(TileType.honor_tile(Honor.WHITE)) == "P"
    assert tile_label(TileType.honor_tile(Honor.GREEN)) == "F"
    assert tile_label(TileType.honor_tile(Honor.RED)) == "C"


def test_app_construction_does_not_start_pyxel_loop() -> None:
    app = MahjongPuzzleApp(seed=20260724)

    assert app.session.game is app.game
    assert app.game.turn == 0
    assert not app.game.is_game_over


def test_all_three_next_previews_fit_inside_sidebar() -> None:
    tiles = create_full_tile_set()
    sidebar_bottom = BOARD_ORIGIN_Y + SIDEBAR_HEIGHT - 1

    for kind in TetrominoKind:
        block = Tetromino(block_id=1, kind=kind, tiles=tiles[:4])
        third_preview_y = (
            BOARD_ORIGIN_Y
            + NEXT_START_OFFSET_Y
            + 2 * NEXT_ITEM_SPACING
        )
        preview_bottom = (
            third_preview_y
            + (block.height - 1) * NEXT_CELL_STEP
            + NEXT_CELL_SIZE
            - 1
        )
        assert preview_bottom <= sidebar_bottom
