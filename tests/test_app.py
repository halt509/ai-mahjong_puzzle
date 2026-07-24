from mahjong_puzzle.app import MahjongPuzzleApp, tile_label
from mahjong_puzzle.tiles import Honor, Suit, TileType


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

    assert app.game.turn == 0
    assert not app.game.is_game_over
