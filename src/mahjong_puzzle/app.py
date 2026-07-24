"""フェーズ3までのゲーム進行を確認するPyxel画面。"""

from __future__ import annotations

import argparse

import pyxel

from mahjong_puzzle.board import BOARD_HEIGHT, BOARD_WIDTH, Coordinate
from mahjong_puzzle.game import GameState, TOTAL_TURN_COUNT
from mahjong_puzzle.integration import GameSession
from mahjong_puzzle.tetromino import PositionedCell, Tetromino
from mahjong_puzzle.tiles import Honor, Suit, Tile, TileType

SCREEN_WIDTH = 256
SCREEN_HEIGHT = 176
BOARD_ORIGIN_X = 8
BOARD_ORIGIN_Y = 24
CELL_SIZE = 16
SIDEBAR_X = 144
SIDEBAR_WIDTH = 108
SIDEBAR_HEIGHT = 132
NEXT_LABEL_OFFSET_Y = 80
NEXT_START_OFFSET_Y = 88
NEXT_ITEM_SPACING = 14
NEXT_CELL_STEP = 4
NEXT_CELL_SIZE = 3

_SUIT_COLORS = {
    Suit.MANZU: 8,
    Suit.PINZU: 12,
    Suit.SOUZU: 11,
}
_HONOR_COLOR = 6
_TILE_BACKGROUND = 7
_PREVIEW_BACKGROUND = 10

_HONOR_LABELS = {
    Honor.EAST: "E",
    Honor.SOUTH: "S",
    Honor.WEST: "W",
    Honor.NORTH: "N",
    Honor.WHITE: "P",
    Honor.GREEN: "F",
    Honor.RED: "C",
}


def tile_label(kind: TileType) -> str:
    """Pyxel組み込みフォントで表示できる2文字以内の牌ラベル。"""

    if kind.suit is not None:
        assert kind.rank is not None
        prefix = {
            Suit.MANZU: "m",
            Suit.PINZU: "p",
            Suit.SOUZU: "s",
        }[kind.suit]
        return f"{prefix}{kind.rank}"
    assert kind.honor is not None
    return _HONOR_LABELS[kind.honor]


def tile_color(kind: TileType) -> int:
    """牌種ごとのPyxelパレット色を返す。"""

    if kind.suit is not None:
        return _SUIT_COLORS[kind.suit]
    return _HONOR_COLOR


class MahjongPuzzleApp:
    """GameStateを描画・入力へ接続する薄いPyxelアダプター。"""

    def __init__(self, *, seed: int | None = None) -> None:
        self.seed = seed
        self.session = GameSession.new(seed=seed)
        self.game: GameState = self.session.game

    def run(self) -> None:
        """Pyxelウィンドウを初期化してメインループを開始する。"""

        pyxel.init(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            title="Mahjong Puzzle - Phase 3",
            fps=30,
        )
        pyxel.run(self.update, self.draw)

    def update(self) -> None:
        """1フレーム分の移動・回転・配置入力を処理する。"""

        if pyxel.btnp(pyxel.KEY_ESCAPE):
            pyxel.quit()
            return
        if self.game.is_game_over:
            return
        if pyxel.btnp(pyxel.KEY_LEFT):
            self.game.move_active(-1, 0)
        if pyxel.btnp(pyxel.KEY_RIGHT):
            self.game.move_active(1, 0)
        if pyxel.btnp(pyxel.KEY_UP):
            self.game.move_active(0, -1)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.game.move_active(0, 1)
        if pyxel.btnp(pyxel.KEY_Z):
            self.game.rotate_active(clockwise=False)
        if pyxel.btnp(pyxel.KEY_X):
            self.game.rotate_active(clockwise=True)
        if pyxel.btnp(pyxel.KEY_SPACE) or pyxel.btnp(pyxel.KEY_RETURN):
            self.session.place_active()

    def draw(self) -> None:
        """盤面、配置プレビュー、次3ブロック、進行情報を描画する。"""

        pyxel.cls(1)
        pyxel.text(8, 6, "MAHJONG PUZZLE / PHASE 3", 7)
        self._draw_board()
        self._draw_preview()
        self._draw_sidebar()
        pyxel.text(
            8,
            164,
            "ARROWS:MOVE  Z/X:ROTATE  SPACE/ENTER:PLACE  ESC:QUIT",
            6,
        )
        if self.game.is_game_over:
            self._draw_game_over()

    def _draw_board(self) -> None:
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                tile = self.game.board.tile_at(Coordinate(x, y))
                self._draw_tile(
                    tile,
                    BOARD_ORIGIN_X + x * CELL_SIZE,
                    BOARD_ORIGIN_Y + y * CELL_SIZE,
                    preview=False,
                )

    def _draw_preview(self) -> None:
        for cell in self.game.preview_cells:
            self._draw_positioned_cell(cell)

    def _draw_positioned_cell(self, cell: PositionedCell) -> None:
        self._draw_tile(
            cell.tile,
            BOARD_ORIGIN_X + cell.coordinate.x * CELL_SIZE,
            BOARD_ORIGIN_Y + cell.coordinate.y * CELL_SIZE,
            preview=True,
        )

    @staticmethod
    def _draw_tile(tile: Tile, screen_x: int, screen_y: int, *, preview: bool) -> None:
        background = _PREVIEW_BACKGROUND if preview else _TILE_BACKGROUND
        border = 10 if preview else 5
        pyxel.rect(
            screen_x + 1,
            screen_y + 1,
            CELL_SIZE - 2,
            CELL_SIZE - 2,
            background,
        )
        pyxel.rectb(screen_x, screen_y, CELL_SIZE, CELL_SIZE, border)
        if preview:
            pyxel.rectb(
                screen_x + 1,
                screen_y + 1,
                CELL_SIZE - 2,
                CELL_SIZE - 2,
                7,
            )
        label = tile_label(tile.kind)
        label_x = screen_x + (CELL_SIZE - len(label) * 4) // 2
        pyxel.text(label_x, screen_y + 5, label, tile_color(tile.kind))

    def _draw_sidebar(self) -> None:
        pyxel.rectb(
            SIDEBAR_X - 4,
            BOARD_ORIGIN_Y,
            SIDEBAR_WIDTH,
            SIDEBAR_HEIGHT,
            5,
        )
        pyxel.text(
            SIDEBAR_X,
            BOARD_ORIGIN_Y + 5,
            f"TURN {self.game.turn:02d}/{TOTAL_TURN_COUNT:02d}",
            7,
        )
        pyxel.text(
            SIDEBAR_X,
            BOARD_ORIGIN_Y + 16,
            f"SCORE: {self.session.total_score}",
            10,
        )
        pyxel.text(
            SIDEBAR_X,
            BOARD_ORIGIN_Y + 27,
            f"COMBO: {self.session.turn_state.consecutive_win_turns}",
            7,
        )
        current = self.game.current_block
        current_name = "-" if current is None else current.kind.value
        pyxel.text(SIDEBAR_X, BOARD_ORIGIN_Y + 38, f"CURRENT: {current_name}", 10)
        indicator_labels = " ".join(
            tile_label(indicator.kind)
            for indicator in self.game.visible_dora_indicators
        )
        pyxel.text(
            SIDEBAR_X,
            BOARD_ORIGIN_Y + 49,
            f"DORA: {indicator_labels}",
            7,
        )
        pyxel.text(
            SIDEBAR_X,
            BOARD_ORIGIN_Y + 60,
            f"RIVER: {self.game.river.total_count}",
            7,
        )
        last = self.session.last_turn
        last_counts = (
            "W0 K0"
            if last is None
            else f"W{len(last.wins)} K{len(last.kans)}"
        )
        pyxel.text(
            SIDEBAR_X,
            BOARD_ORIGIN_Y + 71,
            f"LAST: {last_counts}",
            7,
        )
        pyxel.text(
            SIDEBAR_X,
            BOARD_ORIGIN_Y + NEXT_LABEL_OFFSET_Y,
            "NEXT",
            7,
        )
        for index, block in enumerate(self.game.next_blocks):
            self._draw_next_block(
                block,
                x=SIDEBAR_X,
                y=(
                    BOARD_ORIGIN_Y
                    + NEXT_START_OFFSET_Y
                    + index * NEXT_ITEM_SPACING
                ),
            )

    @staticmethod
    def _draw_next_block(block: Tetromino, *, x: int, y: int) -> None:
        pyxel.text(x, y + 2, block.kind.value, 10)
        shape_x = x + 12
        for cell in block.cells:
            cell_x = shape_x + cell.x * NEXT_CELL_STEP
            cell_y = y + cell.y * NEXT_CELL_STEP
            pyxel.rect(
                cell_x,
                cell_y,
                NEXT_CELL_SIZE,
                NEXT_CELL_SIZE,
                tile_color(cell.tile.kind),
            )

    @staticmethod
    def _draw_game_over() -> None:
        width = 104
        height = 28
        x = BOARD_ORIGIN_X + (BOARD_WIDTH * CELL_SIZE - width) // 2
        y = BOARD_ORIGIN_Y + (BOARD_HEIGHT * CELL_SIZE - height) // 2
        pyxel.rect(x, y, width, height, 0)
        pyxel.rectb(x, y, width, height, 7)
        pyxel.text(x + 27, y + 7, "GAME OVER", 10)
        pyxel.text(x + 15, y + 17, "ALL 17 BLOCKS USED", 7)


def main() -> None:
    """コマンドラインからフェーズ2画面を起動する。"""

    parser = argparse.ArgumentParser(description="Mahjong Puzzle Phase 3")
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="random seed for a reproducible game",
    )
    args = parser.parse_args()
    MahjongPuzzleApp(seed=args.seed).run()


if __name__ == "__main__":
    main()
