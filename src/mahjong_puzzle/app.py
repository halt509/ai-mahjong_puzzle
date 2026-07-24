"""フェーズ4の画面・通知・音をルール状態へ接続するPyxelアプリ。"""

from __future__ import annotations

import argparse

import pyxel

from mahjong_puzzle.board import BOARD_HEIGHT, BOARD_WIDTH, Coordinate
from mahjong_puzzle.game import GameState, TOTAL_TURN_COUNT
from mahjong_puzzle.integration import GameSession
from mahjong_puzzle.persistence import (
    HighScoreError,
    HighScoreStore,
    default_high_score_path,
)
from mahjong_puzzle.scoring import DEFAULT_SCORING_CONFIG
from mahjong_puzzle.sprites import (
    TILE_IMAGE_BANK,
    TILE_SPRITE_SIZE,
    TILE_TRANSPARENT_COLOR,
    build_placeholder_tile_atlas,
    tile_sprite_uv,
)
from mahjong_puzzle.tetromino import PositionedCell, Tetromino
from mahjong_puzzle.tiles import Honor, Suit, Tile, TileType
from mahjong_puzzle.ui import GameSummary, NoticeKind, ScreenMode, UiState
from mahjong_puzzle.yaku import Yaku

SCREEN_WIDTH = 256
SCREEN_HEIGHT = 176
TITLE_INNER_Y = 16
TITLE_INNER_HEIGHT = 144
TITLE_TEXT_Y = 34
TITLE_QUIT_Y = 137
BOARD_ORIGIN_X = 8
BOARD_ORIGIN_Y = 24
CELL_SIZE = 16
SIDEBAR_X = 144
SIDEBAR_WIDTH = 108
SIDEBAR_HEIGHT = 136
DORA_TILE_X = SIDEBAR_X + 22
DORA_TILE_Y = BOARD_ORIGIN_Y + 47
NEXT_LABEL_OFFSET_Y = 88
NEXT_START_OFFSET_Y = 96
NEXT_ITEM_SPACING = 12
NEXT_CELL_STEP = 3
NEXT_CELL_SIZE = 3

COLOR_INK = 0
COLOR_PANEL = 1
COLOR_BACKGROUND = 2
COLOR_TABLE = 3
COLOR_MAHOGANY = 4
COLOR_WOOD_EDGE = 5
COLOR_MUTED = 6
COLOR_IVORY = 7
COLOR_VERMILION = 8
COLOR_ORANGE = 9
COLOR_GOLD = 10
COLOR_BAMBOO = 11
COLOR_INDIGO = 12
COLOR_STONE = 13
COLOR_PINK = 14
COLOR_BRIGHT_IVORY = 15

_PALETTE = (
    0x17130F,
    0x153D33,
    0x0C2A24,
    0x176348,
    0x603A24,
    0xA87848,
    0xC2A879,
    0xF1E4C3,
    0xB63A31,
    0xD3782E,
    0xDDB64C,
    0x3F8B56,
    0x3E688B,
    0x988A73,
    0xC85D75,
    0xFFFFFF,
)

PLACEMENT_RATTLE_SOUND = (
    "c4d4b3g3c4e3c3",
    "nnnnnnn",
    "7765432",
    "fffffff",
    2,
)
PLACEMENT_KNOCK_SOUND = (
    "c3g2",
    "pp",
    "53",
    "fn",
    2,
)

_SUIT_COLORS = {
    Suit.MANZU: COLOR_VERMILION,
    Suit.PINZU: COLOR_INDIGO,
    Suit.SOUZU: COLOR_BAMBOO,
}
_HONOR_COLOR = COLOR_INDIGO
_HONOR_LABELS = {
    Honor.EAST: "E",
    Honor.SOUTH: "S",
    Honor.WEST: "W",
    Honor.NORTH: "N",
    Honor.WHITE: "P",
    Honor.GREEN: "F",
    Honor.RED: "C",
}
_YAKU_SCREEN_NAMES = {
    Yaku.ALL_SEQUENCES: "ALL SEQUENCES",
    Yaku.ALL_TRIPLETS: "ALL TRIPLETS",
    Yaku.TANYAO: "TANYAO",
    Yaku.IIPEIKOU: "IIPEIKOU",
    Yaku.HONITSU: "HONITSU",
    Yaku.CHINITSU: "CHINITSU",
    Yaku.HONROUTOU: "HONROUTOU",
    Yaku.YAKUHAI: "YAKUHAI",
}


def centered_text_x(text: str) -> int:
    """Pyxel組み込みフォントの文字列を画面中央へ置くX座標を返す。"""

    if not isinstance(text, str):
        raise TypeError("textには文字列が必要です")
    return (SCREEN_WIDTH - len(text) * 4) // 2


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
    """牌種ごとのテーマ色を返す。"""

    if kind.suit is not None:
        return _SUIT_COLORS[kind.suit]
    if kind.honor is Honor.GREEN:
        return COLOR_BAMBOO
    if kind.honor is Honor.RED:
        return COLOR_VERMILION
    return _HONOR_COLOR


class MahjongPuzzleApp:
    """ゲーム進行とフェーズ4 UIを接続するPyxelアダプター。"""

    def __init__(
        self,
        *,
        seed: int | None = None,
        high_score_store: HighScoreStore | None = None,
    ) -> None:
        self.seed = seed
        self.high_score_store = (
            high_score_store
            if high_score_store is not None
            else HighScoreStore(default_high_score_path())
        )
        self.persistence_error: str | None = None
        try:
            self.high_score = self.high_score_store.load()
        except HighScoreError as error:
            self.high_score = 0
            self.persistence_error = str(error)
        self.ui = UiState()
        self._new_session()

    def _new_session(self) -> None:
        self.session = GameSession.new(seed=self.seed)
        self.game: GameState = self.session.game
        self._result_recorded = False

    def run(self) -> None:
        """Pyxelウィンドウ、麻雀テーマ、仮スプライト、音を初期化する。"""

        pyxel.init(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            title="Mahjong Tile Puzzle",
            fps=30,
        )
        self._configure_palette()
        build_placeholder_tile_atlas(pyxel.images[TILE_IMAGE_BANK])
        self._configure_sounds()
        pyxel.run(self.update, self.draw)

    @staticmethod
    def _configure_palette() -> None:
        for index, color in enumerate(_PALETTE):
            pyxel.colors[index] = color

    @staticmethod
    def _configure_sounds() -> None:
        pyxel.sounds[0].set(*PLACEMENT_RATTLE_SOUND)
        pyxel.sounds[1].set("c3e3g3c4", "tttt", "6677", "nnnn", 4)
        pyxel.sounds[2].set("c3e3g3c4e4", "sssss", "66777", "nnnnn", 4)
        pyxel.sounds[3].set("g3e3c3", "ppp", "655", "fff", 8)
        pyxel.sounds[4].set(*PLACEMENT_KNOCK_SOUND)

    @staticmethod
    def _pressed(*keys: int) -> bool:
        return any(pyxel.btnp(key) for key in keys)

    def _notification_control_pressed(self) -> bool:
        return self._pressed(
            pyxel.KEY_LEFT,
            pyxel.KEY_RIGHT,
            pyxel.KEY_UP,
            pyxel.KEY_DOWN,
            pyxel.KEY_Z,
            pyxel.KEY_X,
            pyxel.KEY_SPACE,
            pyxel.KEY_RETURN,
            pyxel.KEY_TAB,
            pyxel.KEY_Y,
            pyxel.KEY_R,
            pyxel.KEY_ESCAPE,
        )

    def update(self) -> None:
        """画面状態に応じた入力を処理する。"""

        if self.ui.current_notice is not None:
            if self._notification_control_pressed():
                self.ui.dismiss_notice()
                self._record_result_if_needed()
            return

        if self.ui.screen is ScreenMode.TITLE:
            if self._pressed(pyxel.KEY_SPACE, pyxel.KEY_RETURN):
                self.ui.start_game()
            elif pyxel.btnp(pyxel.KEY_ESCAPE):
                pyxel.quit()
            return

        if self.ui.screen is ScreenMode.RIVER:
            if self._pressed(pyxel.KEY_TAB, pyxel.KEY_ESCAPE):
                self.ui.close_overlay()
            return

        if self.ui.screen is ScreenMode.YAKU:
            if self._pressed(pyxel.KEY_Y, pyxel.KEY_ESCAPE):
                self.ui.close_overlay()
            return

        if self.ui.screen is ScreenMode.RESULT:
            if pyxel.btnp(pyxel.KEY_R):
                self._new_session()
                self.ui = UiState(screen=ScreenMode.GAME)
            elif pyxel.btnp(pyxel.KEY_ESCAPE):
                pyxel.quit()
            return

        if pyxel.btnp(pyxel.KEY_ESCAPE):
            pyxel.quit()
            return
        if pyxel.btnp(pyxel.KEY_TAB):
            self.ui.open_overlay(ScreenMode.RIVER)
            return
        if pyxel.btnp(pyxel.KEY_Y):
            self.ui.open_overlay(ScreenMode.YAKU)
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
        if self._pressed(pyxel.KEY_SPACE, pyxel.KEY_RETURN):
            result = self.session.place_active()
            self.ui.accept_turn(result)
            pyxel.play(0, 0)
            pyxel.play(3, 4)
            if result.kans:
                pyxel.play(1, 1)
            if result.wins:
                pyxel.play(2, 2)
            self._record_result_if_needed()

    def _record_result_if_needed(self) -> None:
        if self.ui.screen is not ScreenMode.RESULT or self._result_recorded:
            return
        self._result_recorded = True
        try:
            self.high_score = self.high_score_store.record(self.session.total_score)
            self.persistence_error = None
        except HighScoreError as error:
            self.persistence_error = str(error)
        pyxel.play(3, 3)

    def draw(self) -> None:
        """現在画面と必要なオーバーレイを描画する。"""

        if self.ui.screen is ScreenMode.TITLE:
            self._draw_title()
            return
        if self.ui.screen is ScreenMode.RESULT:
            self._draw_result()
            return

        self._draw_game()
        if self.ui.screen is ScreenMode.RIVER:
            self._draw_river_overlay()
        elif self.ui.screen is ScreenMode.YAKU:
            self._draw_yaku_overlay()
        if self.ui.current_notice is not None:
            self._draw_notice()

    def _draw_title(self) -> None:
        pyxel.cls(COLOR_BACKGROUND)
        pyxel.rect(12, 12, 232, 152, COLOR_PANEL)
        pyxel.rectb(12, 12, 232, 152, COLOR_WOOD_EDGE)
        pyxel.rectb(
            16,
            TITLE_INNER_Y,
            224,
            TITLE_INNER_HEIGHT,
            COLOR_MAHOGANY,
        )
        title = "MAHJONG TILE PUZZLE"
        pyxel.text(centered_text_x(title), TITLE_TEXT_Y, title, COLOR_GOLD)
        sample_types = (
            TileType.honor_tile(Honor.EAST),
            TileType.suited(Suit.PINZU, 5),
            TileType.honor_tile(Honor.RED),
        )
        sample_width = (
            len(sample_types) * TILE_SPRITE_SIZE
            + (len(sample_types) - 1) * 2
        )
        sample_x = (SCREEN_WIDTH - sample_width) // 2
        for index, tile_type in enumerate(sample_types):
            self._blt_tile(sample_x + index * 18, 56, tile_type)
        tagline = "OVERWRITE. BUILD. WIN."
        pyxel.text(centered_text_x(tagline), 86, tagline, COLOR_IVORY)
        start_text = "SPACE / ENTER TO START"
        pyxel.text(
            centered_text_x(start_text),
            104,
            start_text,
            COLOR_BRIGHT_IVORY,
        )
        high_score_text = f"HIGH SCORE {self.high_score}"
        pyxel.text(
            centered_text_x(high_score_text),
            121,
            high_score_text,
            COLOR_GOLD,
        )
        if self.persistence_error is not None:
            error_text = "HIGH SCORE SAVE UNAVAILABLE"
            pyxel.text(
                centered_text_x(error_text),
                129,
                error_text,
                COLOR_VERMILION,
            )
        quit_text = "ESC: QUIT"
        pyxel.text(
            centered_text_x(quit_text),
            TITLE_QUIT_Y,
            quit_text,
            COLOR_MUTED,
        )

    def _draw_game(self) -> None:
        pyxel.cls(COLOR_BACKGROUND)
        pyxel.text(8, 6, "MAHJONG TILE PUZZLE", COLOR_IVORY)
        self._draw_board()
        self._draw_preview()
        self._draw_sidebar()
        pyxel.text(
            8,
            163,
            "ARROWS MOVE  Z/X ROTATE  SPACE PUT",
            COLOR_MUTED,
        )
        pyxel.text(
            8,
            170,
            "TAB RIVER  Y YAKU  ESC QUIT",
            COLOR_MUTED,
        )

    def _draw_board(self) -> None:
        pyxel.rect(
            BOARD_ORIGIN_X - 2,
            BOARD_ORIGIN_Y - 2,
            BOARD_WIDTH * CELL_SIZE + 4,
            BOARD_HEIGHT * CELL_SIZE + 4,
            COLOR_MAHOGANY,
        )
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
    def _blt_tile(screen_x: int, screen_y: int, tile_type: TileType) -> None:
        u, v = tile_sprite_uv(tile_type)
        pyxel.blt(
            screen_x,
            screen_y,
            TILE_IMAGE_BANK,
            u,
            v,
            TILE_SPRITE_SIZE,
            TILE_SPRITE_SIZE,
            TILE_TRANSPARENT_COLOR,
        )

    @classmethod
    def _draw_tile(
        cls, tile: Tile, screen_x: int, screen_y: int, *, preview: bool
    ) -> None:
        cls._blt_tile(screen_x, screen_y, tile.kind)
        if preview:
            pyxel.rectb(
                screen_x,
                screen_y,
                CELL_SIZE,
                CELL_SIZE,
                COLOR_GOLD,
            )
            pyxel.rectb(
                screen_x + 1,
                screen_y + 1,
                CELL_SIZE - 2,
                CELL_SIZE - 2,
                COLOR_VERMILION,
            )

    def _draw_sidebar(self) -> None:
        pyxel.rect(
            SIDEBAR_X - 4,
            BOARD_ORIGIN_Y,
            SIDEBAR_WIDTH,
            SIDEBAR_HEIGHT,
            COLOR_PANEL,
        )
        pyxel.rectb(
            SIDEBAR_X - 4,
            BOARD_ORIGIN_Y,
            SIDEBAR_WIDTH,
            SIDEBAR_HEIGHT,
            COLOR_WOOD_EDGE,
        )
        pyxel.text(
            SIDEBAR_X,
            BOARD_ORIGIN_Y + 5,
            f"TURN {self.game.turn:02d}/{TOTAL_TURN_COUNT:02d}",
            COLOR_IVORY,
        )
        pyxel.text(
            SIDEBAR_X,
            BOARD_ORIGIN_Y + 16,
            f"SCORE {self.session.total_score}",
            COLOR_GOLD,
        )
        pyxel.text(
            SIDEBAR_X,
            BOARD_ORIGIN_Y + 27,
            f"COMBO {self.session.turn_state.consecutive_win_turns}",
            COLOR_IVORY,
        )
        current = self.game.current_block
        current_name = "-" if current is None else current.kind.value
        pyxel.text(
            SIDEBAR_X,
            BOARD_ORIGIN_Y + 38,
            f"CURRENT {current_name}",
            COLOR_GOLD,
        )
        self._draw_dora_indicators()
        recent_labels = "".join(
            f"{tile_label(record.tile.kind):>2}"
            for record in self.game.river.recent(8)
        )
        pyxel.text(
            SIDEBAR_X,
            BOARD_ORIGIN_Y + 67,
            f"R{self.game.river.total_count}:{recent_labels}",
            COLOR_IVORY,
        )
        last = self.session.last_turn
        last_counts = (
            "W0 K0"
            if last is None
            else f"W{len(last.wins)} K{len(last.kans)}"
        )
        pyxel.text(
            SIDEBAR_X,
            BOARD_ORIGIN_Y + 78,
            f"LAST {last_counts}",
            COLOR_MUTED,
        )
        pyxel.text(
            SIDEBAR_X,
            BOARD_ORIGIN_Y + NEXT_LABEL_OFFSET_Y,
            "NEXT",
            COLOR_IVORY,
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

    def _draw_dora_indicators(self) -> None:
        pyxel.text(
            SIDEBAR_X,
            DORA_TILE_Y + 5,
            "DORA",
            COLOR_IVORY,
        )
        for index, indicator in enumerate(
            self.game.visible_dora_indicators
        ):
            self._blt_tile(
                DORA_TILE_X + index * (TILE_SPRITE_SIZE + 1),
                DORA_TILE_Y,
                indicator.kind,
            )

    @staticmethod
    def _draw_next_block(block: Tetromino, *, x: int, y: int) -> None:
        pyxel.text(x, y + 2, block.kind.value, COLOR_GOLD)
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

    def _draw_notice(self) -> None:
        notice = self.ui.current_notice
        if notice is None:
            return
        x, y, width, height = 42, 50, 172, 76
        pyxel.rect(x, y, width, height, COLOR_INK)
        pyxel.rectb(x, y, width, height, COLOR_WOOD_EDGE)
        accent = (
            COLOR_VERMILION
            if notice.kind is NoticeKind.KAN
            else COLOR_GOLD
        )
        pyxel.rectb(x + 2, y + 2, width - 4, height - 4, accent)
        title_x = x + (width - len(notice.title) * 4) // 2
        pyxel.text(title_x, y + 10, notice.title, accent)
        for index, line in enumerate(notice.lines):
            line_x = x + (width - len(line) * 4) // 2
            pyxel.text(line_x, y + 25 + index * 10, line, COLOR_IVORY)
        pyxel.text(x + 34, y + 64, "ANY CONTROL TO CONTINUE", COLOR_MUTED)

    def _draw_river_overlay(self) -> None:
        self._draw_overlay_panel("RIVER / FULL HISTORY")
        pyxel.text(
            12,
            25,
            f"TOTAL {self.game.river.total_count}  EACH COLUMN = ONE TURN",
            COLOR_IVORY,
        )
        for index, record in enumerate(self.game.river.records):
            turn_column = index // 4
            slot = index % 4
            x = 10 + turn_column * 14
            y = 38 + slot * 23
            pyxel.rect(x, y, 12, 16, COLOR_IVORY)
            pyxel.rectb(x, y, 12, 16, COLOR_WOOD_EDGE)
            label = tile_label(record.tile.kind)
            label_x = x + (12 - len(label) * 4) // 2
            pyxel.text(label_x, y + 5, label, tile_color(record.tile.kind))
        pyxel.text(88, 153, "TAB / ESC CLOSE", COLOR_MUTED)

    def _draw_yaku_overlay(self) -> None:
        self._draw_overlay_panel("YAKU LIST")
        acquired = {
            yaku
            for state in self.session.line_states
            for yaku in state.acquired_yaku
        }
        for index, yaku in enumerate(Yaku):
            y = 31 + index * 14
            marker = "*" if yaku in acquired else "-"
            points = DEFAULT_SCORING_CONFIG.yaku_points[yaku]
            pyxel.text(18, y, marker, COLOR_GOLD if marker == "*" else COLOR_MUTED)
            pyxel.text(30, y, _YAKU_SCREEN_NAMES[yaku], COLOR_IVORY)
            pyxel.text(190, y, f"{points:>3}", COLOR_GOLD)
        pyxel.text(14, 146, "* ACQUIRED ON AT LEAST ONE ROW", COLOR_MUTED)
        pyxel.text(94, 158, "Y / ESC CLOSE", COLOR_MUTED)

    @staticmethod
    def _draw_overlay_panel(title: str) -> None:
        pyxel.rect(5, 8, 246, 160, COLOR_INK)
        pyxel.rectb(5, 8, 246, 160, COLOR_WOOD_EDGE)
        pyxel.rectb(8, 11, 240, 154, COLOR_MAHOGANY)
        pyxel.text(12, 16, title, COLOR_GOLD)

    def _draw_result(self) -> None:
        pyxel.cls(COLOR_BACKGROUND)
        summary = GameSummary.from_session(self.session)
        pyxel.rect(28, 14, 200, 148, COLOR_PANEL)
        pyxel.rectb(28, 14, 200, 148, COLOR_WOOD_EDGE)
        pyxel.rectb(31, 17, 194, 142, COLOR_MAHOGANY)
        pyxel.text(96, 28, "GAME RESULT", COLOR_GOLD)
        pyxel.text(68, 49, f"FINAL SCORE  {summary.total_score}", COLOR_IVORY)
        pyxel.text(68, 62, f"HIGH SCORE   {self.high_score}", COLOR_GOLD)
        pyxel.text(68, 79, f"TURNS        {summary.turns}", COLOR_IVORY)
        pyxel.text(68, 90, f"WINS         {summary.win_count}", COLOR_IVORY)
        pyxel.text(68, 101, f"KANS         {summary.kan_count}", COLOR_IVORY)
        pyxel.text(
            68,
            112,
            f"YAKU TYPES   {len(summary.acquired_yaku)}",
            COLOR_IVORY,
        )
        pyxel.text(68, 123, f"RIVER TILES  {summary.river_count}", COLOR_IVORY)
        pyxel.text(78, 141, "R RESTART   ESC QUIT", COLOR_BRIGHT_IVORY)
        if self.persistence_error is not None:
            pyxel.text(64, 151, "HIGH SCORE SAVE FAILED", COLOR_VERMILION)


def main() -> None:
    """コマンドラインからゲームを起動する。"""

    parser = argparse.ArgumentParser(description="Mahjong Tile Puzzle")
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
