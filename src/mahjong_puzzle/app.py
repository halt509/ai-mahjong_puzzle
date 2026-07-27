"""フェーズ6の初心者説明を含む画面・入力・音のPyxelアプリ。"""

from __future__ import annotations

import argparse
from enum import Enum
from pathlib import Path

import pyxel

from mahjong_puzzle.board import BOARD_HEIGHT, BOARD_WIDTH, Coordinate
from mahjong_puzzle.game import GameState, TOTAL_TURN_COUNT
from mahjong_puzzle.integration import GameSession
from mahjong_puzzle.persistence import (
    HighScoreBackend,
    HighScoreError,
    TutorialProgressBackend,
    TutorialProgressError,
    create_default_high_score_store,
    create_default_tutorial_progress_store,
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
from mahjong_puzzle.tutorial import TUTORIAL_PAGES, TutorialState
from mahjong_puzzle.ui import GameSummary, NoticeKind, ScreenMode, UiState
from mahjong_puzzle.yaku import YAKU_DISPLAY_NAMES, Yaku
from mahjong_puzzle.yaku_catalog import YAKU_GUIDE_ENTRIES

SCREEN_WIDTH = 256
SCREEN_HEIGHT = 176
PORTRAIT_SCREEN_WIDTH = 176
PORTRAIT_SCREEN_HEIGHT = 256
TITLE_INNER_Y = 16
TITLE_INNER_HEIGHT = 144
TITLE_TEXT_Y = 34
TITLE_QUIT_Y = 137
BOARD_ORIGIN_X = 8
BOARD_ORIGIN_Y = 24
PORTRAIT_BOARD_ORIGIN_X = 24
PORTRAIT_BOARD_ORIGIN_Y = 18
CELL_SIZE = 16
SIDEBAR_X = 144
SIDEBAR_WIDTH = 108
SIDEBAR_Y = BOARD_ORIGIN_Y - 2
SIDEBAR_HEIGHT = BOARD_HEIGHT * CELL_SIZE + 4
DORA_TILE_X = SIDEBAR_X + 22
DORA_TILE_Y = BOARD_ORIGIN_Y + 40
NEXT_LABEL_OFFSET_Y = 61
NEXT_START_OFFSET_Y = 72
NEXT_ITEM_SPACING = 19
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
JAPANESE_FONT_RELATIVE_PATH = Path("assets/fonts/umplus_j10r.bdf")
TUTORIAL_SCREENSHOT_RELATIVE_PATH = Path(
    "assets/guides/tutorial-gameplay.png"
)
TUTORIAL_IMAGE_BANK = 1
GUIDE_CHARACTER_RELATIVE_PATH = Path(
    "assets/sprites/peacock-guide.png"
)
GUIDE_CHARACTER_IMAGE_BANK = 2


class ControlAction(str, Enum):
    """キーボードとゲームパッドで共有する画面操作。"""

    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    ROTATE_COUNTERCLOCKWISE = "rotate_counterclockwise"
    ROTATE_CLOCKWISE = "rotate_clockwise"
    PLACE = "place"
    TOGGLE_RIVER = "toggle_river"
    TOGGLE_YAKU = "toggle_yaku"
    START_GAME = "start_game"
    RESTART_GAME = "restart_game"
    HELP = "help"
    CANCEL = "cancel"
    QUIT = "quit"


class LayoutMode(str, Enum):
    """端末ごとに選択する画面レイアウト。"""

    LANDSCAPE = "landscape"
    PORTRAIT = "portrait"


CONTROL_BINDINGS: dict[ControlAction, tuple[int, ...]] = {
    ControlAction.MOVE_LEFT: (
        pyxel.KEY_LEFT,
        pyxel.GAMEPAD1_BUTTON_DPAD_LEFT,
    ),
    ControlAction.MOVE_RIGHT: (
        pyxel.KEY_RIGHT,
        pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT,
    ),
    ControlAction.MOVE_UP: (
        pyxel.KEY_UP,
        pyxel.GAMEPAD1_BUTTON_DPAD_UP,
    ),
    ControlAction.MOVE_DOWN: (
        pyxel.KEY_DOWN,
        pyxel.GAMEPAD1_BUTTON_DPAD_DOWN,
    ),
    ControlAction.ROTATE_COUNTERCLOCKWISE: (
        pyxel.KEY_Z,
        pyxel.GAMEPAD1_BUTTON_X,
    ),
    ControlAction.ROTATE_CLOCKWISE: (
        pyxel.KEY_X,
        pyxel.GAMEPAD1_BUTTON_B,
    ),
    ControlAction.PLACE: (
        pyxel.KEY_SPACE,
        pyxel.KEY_RETURN,
        pyxel.GAMEPAD1_BUTTON_A,
    ),
    ControlAction.TOGGLE_RIVER: (
        pyxel.KEY_TAB,
        pyxel.GAMEPAD1_BUTTON_BACK,
    ),
    ControlAction.TOGGLE_YAKU: (
        pyxel.KEY_Y,
        pyxel.GAMEPAD1_BUTTON_START,
    ),
    ControlAction.START_GAME: (
        pyxel.KEY_SPACE,
        pyxel.KEY_RETURN,
        pyxel.GAMEPAD1_BUTTON_A,
    ),
    ControlAction.RESTART_GAME: (
        pyxel.KEY_R,
        pyxel.GAMEPAD1_BUTTON_A,
    ),
    ControlAction.HELP: (
        pyxel.KEY_H,
        pyxel.GAMEPAD1_BUTTON_START,
    ),
    ControlAction.CANCEL: (
        pyxel.KEY_ESCAPE,
        pyxel.GAMEPAD1_BUTTON_B,
    ),
    ControlAction.QUIT: (pyxel.KEY_ESCAPE,),
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
    """ゲーム進行とフェーズ6 UIを接続するPyxelアダプター。"""

    def __init__(
        self,
        *,
        seed: int | None = None,
        high_score_store: HighScoreBackend | None = None,
        tutorial_progress_store: TutorialProgressBackend | None = None,
        layout: LayoutMode = LayoutMode.LANDSCAPE,
    ) -> None:
        if not isinstance(layout, LayoutMode):
            raise TypeError("layoutにはLayoutModeが必要です")
        self.seed = seed
        self.layout = layout
        self._japanese_font: pyxel.Font | None = None
        self._yaku_page = 0
        self.tutorial = TutorialState()
        self.high_score_store = (
            high_score_store
            if high_score_store is not None
            else create_default_high_score_store()
        )
        self.persistence_error: str | None = None
        try:
            self.high_score = self.high_score_store.load()
        except HighScoreError as error:
            self.high_score = 0
            self.persistence_error = str(error)
        self.tutorial_progress_store = (
            tutorial_progress_store
            if tutorial_progress_store is not None
            else create_default_tutorial_progress_store()
        )
        self.tutorial_persistence_error: str | None = None
        try:
            self._tutorial_seen = self.tutorial_progress_store.load()
        except TutorialProgressError as error:
            self._tutorial_seen = False
            self.tutorial_persistence_error = str(error)
        self.ui = UiState()
        self._new_session()

    @property
    def screen_width(self) -> int:
        """選択中レイアウトの論理画面幅を返す。"""

        if self.layout is LayoutMode.PORTRAIT:
            return PORTRAIT_SCREEN_WIDTH
        return SCREEN_WIDTH

    @property
    def screen_height(self) -> int:
        """選択中レイアウトの論理画面高を返す。"""

        if self.layout is LayoutMode.PORTRAIT:
            return PORTRAIT_SCREEN_HEIGHT
        return SCREEN_HEIGHT

    @property
    def board_origin_x(self) -> int:
        """選択中レイアウトの盤面左端を返す。"""

        if self.layout is LayoutMode.PORTRAIT:
            return PORTRAIT_BOARD_ORIGIN_X
        return BOARD_ORIGIN_X

    @property
    def board_origin_y(self) -> int:
        """選択中レイアウトの盤面上端を返す。"""

        if self.layout is LayoutMode.PORTRAIT:
            return PORTRAIT_BOARD_ORIGIN_Y
        return BOARD_ORIGIN_Y

    def _centered_text_x(self, text: str) -> int:
        return (self.screen_width - len(text) * 4) // 2

    def _japanese_text_width(self, text: str) -> int:
        if self._japanese_font is None:
            raise RuntimeError("日本語フォントが初期化されていません")
        text_width = getattr(self._japanese_font, "text_width", None)
        if callable(text_width):
            return int(text_width(text))
        return len(text) * 10

    def _centered_japanese_x(self, text: str) -> int:
        return (self.screen_width - self._japanese_text_width(text)) // 2

    @property
    def yaku_page(self) -> int:
        """役一覧で現在表示している0始まりページを返す。"""

        return self._yaku_page

    @property
    def tutorial_page(self) -> int:
        """説明で現在表示している0始まりページを返す。"""

        return self.tutorial.page_index

    def _new_session(self) -> None:
        self.session = GameSession.new(seed=self.seed)
        self.game: GameState = self.session.game
        self._result_recorded = False

    def run(self) -> None:
        """Pyxelウィンドウ、麻雀テーマ、仮スプライト、音を初期化する。"""

        pyxel.init(
            self.screen_width,
            self.screen_height,
            title="Mahjong Tile Puzzle",
            fps=30,
        )
        self._japanese_font = pyxel.Font(self._resolve_japanese_font_path())
        self._configure_palette()
        build_placeholder_tile_atlas(pyxel.images[TILE_IMAGE_BANK])
        pyxel.images[TUTORIAL_IMAGE_BANK].load(
            0,
            0,
            self._resolve_runtime_asset_path(
                TUTORIAL_SCREENSHOT_RELATIVE_PATH
            ),
        )
        pyxel.images[GUIDE_CHARACTER_IMAGE_BANK].load(
            0,
            0,
            self._resolve_runtime_asset_path(
                GUIDE_CHARACTER_RELATIVE_PATH
            ),
        )
        self._configure_sounds()
        self._show_initial_tutorial_if_needed()
        pyxel.run(self.update, self.draw)

    def _show_initial_tutorial_if_needed(self) -> None:
        """未読ならPyxelループ開始前に初回説明を開く。"""

        if self._tutorial_seen:
            return
        self.tutorial = TutorialState(initial=True)
        self.ui.open_help()

    @staticmethod
    def _resolve_japanese_font_path() -> str:
        return MahjongPuzzleApp._resolve_runtime_asset_path(
            JAPANESE_FONT_RELATIVE_PATH
        )

    @staticmethod
    def _resolve_runtime_asset_path(relative_path: Path) -> str:
        source_root = Path(__file__).resolve().parents[2]
        packaged_root = Path(__file__).resolve().parents[1]
        candidates = (
            source_root / relative_path,
            packaged_root / relative_path,
            Path.cwd() / relative_path,
        )
        for candidate in candidates:
            if candidate.is_file():
                return str(candidate)
        raise FileNotFoundError(
            f"実行用アセットが見つかりません: {relative_path}"
        )

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

    def _action_pressed(self, action: ControlAction) -> bool:
        return self._pressed(*CONTROL_BINDINGS[action])

    def _notification_control_pressed(self) -> bool:
        return any(self._action_pressed(action) for action in ControlAction)

    def update(self) -> None:
        """画面状態に応じた入力を処理する。"""

        if self.ui.current_notice is not None:
            if self._notification_control_pressed():
                self.ui.dismiss_notice()
                self._record_result_if_needed()
            return

        if self.ui.screen is ScreenMode.TITLE:
            if self._action_pressed(ControlAction.HELP):
                self._open_help()
            elif self._action_pressed(ControlAction.START_GAME):
                self.ui.start_game()
            elif self._action_pressed(ControlAction.QUIT):
                pyxel.quit()
            return

        if self.ui.screen is ScreenMode.HELP:
            if self._action_pressed(ControlAction.MOVE_LEFT):
                self.tutorial.previous_page()
            elif self._action_pressed(ControlAction.MOVE_RIGHT):
                self.tutorial.next_page()
            elif self._action_pressed(ControlAction.PLACE):
                if not self.tutorial.next_page():
                    self._close_help()
            elif self._action_pressed(
                ControlAction.CANCEL
            ) or self._action_pressed(ControlAction.HELP):
                self._close_help()
            return

        if self.ui.screen is ScreenMode.RIVER:
            if self._action_pressed(
                ControlAction.TOGGLE_RIVER
            ) or self._action_pressed(ControlAction.CANCEL):
                self.ui.close_overlay()
            return

        if self.ui.screen is ScreenMode.YAKU:
            if self._action_pressed(ControlAction.MOVE_LEFT):
                self._yaku_page = (
                    self._yaku_page - 1
                ) % len(YAKU_GUIDE_ENTRIES)
            elif self._action_pressed(ControlAction.MOVE_RIGHT):
                self._yaku_page = (
                    self._yaku_page + 1
                ) % len(YAKU_GUIDE_ENTRIES)
            elif self._action_pressed(
                ControlAction.TOGGLE_YAKU
            ) or self._action_pressed(ControlAction.CANCEL):
                self.ui.close_overlay()
            return

        if self.ui.screen is ScreenMode.RESULT:
            if self._action_pressed(ControlAction.HELP):
                self._open_help()
            elif self._action_pressed(ControlAction.RESTART_GAME):
                self._new_session()
                self.ui = UiState(screen=ScreenMode.GAME)
            elif self._action_pressed(ControlAction.QUIT):
                pyxel.quit()
            return

        if self._action_pressed(ControlAction.QUIT):
            pyxel.quit()
            return
        if self._action_pressed(ControlAction.TOGGLE_RIVER):
            self.ui.open_overlay(ScreenMode.RIVER)
            return
        if self._action_pressed(ControlAction.TOGGLE_YAKU):
            self._yaku_page = 0
            self.ui.open_overlay(ScreenMode.YAKU)
            return
        if self._pressed(pyxel.KEY_H):
            self._open_help()
            return
        if self._action_pressed(ControlAction.MOVE_LEFT):
            self.game.move_active(-1, 0)
        if self._action_pressed(ControlAction.MOVE_RIGHT):
            self.game.move_active(1, 0)
        if self._action_pressed(ControlAction.MOVE_UP):
            self.game.move_active(0, -1)
        if self._action_pressed(ControlAction.MOVE_DOWN):
            self.game.move_active(0, 1)
        if self._action_pressed(ControlAction.ROTATE_COUNTERCLOCKWISE):
            self.game.rotate_active(clockwise=False)
        if self._action_pressed(ControlAction.ROTATE_CLOCKWISE):
            self.game.rotate_active(clockwise=True)
        if self._action_pressed(ControlAction.PLACE):
            result = self.session.place_active()
            self.ui.accept_turn(result)
            pyxel.play(0, 0)
            pyxel.play(3, 4)
            if result.kans:
                pyxel.play(1, 1)
            if result.wins:
                pyxel.play(2, 2)
            self._record_result_if_needed()

    def _open_help(self) -> None:
        if self.ui.open_help():
            self.tutorial = TutorialState()

    def _close_help(self) -> None:
        was_initial = self.tutorial.initial
        self.ui.close_help()
        if not was_initial:
            return
        self._tutorial_seen = True
        try:
            self.tutorial_progress_store.mark_seen()
            self.tutorial_persistence_error = None
        except TutorialProgressError as error:
            self.tutorial_persistence_error = str(error)

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
        if self.ui.screen is ScreenMode.HELP:
            self._draw_help()
            return

        self._draw_game()
        if self.ui.screen is ScreenMode.RIVER:
            self._draw_river_overlay()
        elif self.ui.screen is ScreenMode.YAKU:
            self._draw_yaku_overlay()
        if self.ui.current_notice is not None:
            self._draw_notice()

    def _draw_help(self) -> None:
        """共通内容を横・縦それぞれの説明画面へ収めて描く。"""

        if self._japanese_font is None:
            raise RuntimeError("日本語フォントが初期化されていません")
        page = self.tutorial.page
        pyxel.cls(COLOR_BACKGROUND)
        if self.layout is LayoutMode.PORTRAIT:
            panel = (5, 8, 166, 240)
            bird_x, bird_y = 14, 28
            bubble = (10, 68, 156, 126)
            title_y, line_y, line_step = 78, 99, 18
            max_chars = 14
            footer_y = 218
        else:
            panel = (5, 8, 246, 160)
            bird_x, bird_y = 10, 34
            bubble = (54, 25, 188, 116)
            title_y, line_y, line_step = 35, 55, 17
            max_chars = 18
            footer_y = 153
        x, y, width, height = panel
        pyxel.rect(x, y, width, height, COLOR_PANEL)
        pyxel.rectb(x, y, width, height, COLOR_WOOD_EDGE)
        pyxel.rectb(x + 3, y + 3, width - 6, height - 6, COLOR_MAHOGANY)
        pyxel.text(
            12,
            16,
            "遊び方",
            COLOR_GOLD,
            self._japanese_font,
        )
        page_label = f"{self.tutorial_page + 1}/{len(TUTORIAL_PAGES)}"
        pyxel.text(
            self.screen_width - len(page_label) * 4 - 12,
            18,
            page_label,
            COLOR_GOLD,
        )
        self._draw_guide_bird(bird_x, bird_y)
        bubble_x, bubble_y, bubble_width, bubble_height = bubble
        pyxel.rect(
            bubble_x,
            bubble_y,
            bubble_width,
            bubble_height,
            COLOR_IVORY,
        )
        pyxel.rectb(
            bubble_x,
            bubble_y,
            bubble_width,
            bubble_height,
            COLOR_WOOD_EDGE,
        )
        if self.layout is LayoutMode.LANDSCAPE:
            pyxel.tri(
                bubble_x,
                bubble_y + 24,
                bubble_x - 9,
                bubble_y + 16,
                bubble_x,
                bubble_y + 10,
                COLOR_IVORY,
            )
        pyxel.text(
            bubble_x + 8,
            title_y,
            page.title,
            COLOR_VERMILION,
            self._japanese_font,
        )
        if self.tutorial_page == 0:
            first_line_y = (
                line_y
                if self.layout is LayoutMode.PORTRAIT
                else line_y - 5
            )
            pyxel.text(
                bubble_x + 8,
                first_line_y,
                page.lines[0],
                COLOR_INK,
                self._japanese_font,
            )
            screenshot_x = (
                bubble_x + (bubble_width - 128) // 2
            )
            screenshot_y = first_line_y + 14
            pyxel.blt(
                screenshot_x,
                screenshot_y,
                TUTORIAL_IMAGE_BANK,
                8,
                24,
                128,
                64,
            )
            content_line_count = 0
        else:
            wrapped_lines = tuple(
                part
                for line in page.lines
                for part in self._wrap_help_line(line, max_chars=max_chars)
            )
            for index, line in enumerate(wrapped_lines):
                pyxel.text(
                    bubble_x + 8,
                    line_y + index * line_step,
                    line,
                    COLOR_INK,
                    self._japanese_font,
                )
            content_line_count = len(wrapped_lines)
        page_controls = {
            0: (
                "X・B:回転  A:確定"
                if self.layout is LayoutMode.PORTRAIT
                else "Z・X:回転  SPACE・A:確定"
            ),
            2: (
                "START:役一覧"
                if self.layout is LayoutMode.PORTRAIT
                else "Y:役一覧"
            ),
            3: (
                "SELECT・BACK:川"
                if self.layout is LayoutMode.PORTRAIT
                else "TAB:川"
            ),
        }
        controls = page_controls.get(self.tutorial_page)
        if controls is not None:
            if self.tutorial_page == 0:
                controls_y = screenshot_y + 66
            else:
                controls_y = line_y + content_line_count * line_step
            pyxel.text(
                bubble_x + 8,
                controls_y,
                controls,
                COLOR_INDIGO,
                self._japanese_font,
            )
        footer = "←→  B/ESC:閉じる"
        pyxel.text(
            self._centered_japanese_x(footer),
            footer_y if self.layout is LayoutMode.LANDSCAPE else 231,
            footer,
            COLOR_MUTED,
            self._japanese_font,
        )

    @staticmethod
    def _wrap_help_line(text: str, *, max_chars: int) -> tuple[str, ...]:
        if not isinstance(text, str) or not text:
            raise ValueError("textには空でない文字列が必要です")
        if not isinstance(max_chars, int) or max_chars <= 0:
            raise ValueError("max_charsには正の整数が必要です")
        return tuple(
            text[index : index + max_chars]
            for index in range(0, len(text), max_chars)
        )

    @staticmethod
    def _draw_guide_bird(x: int, y: int) -> None:
        """絵文字を参考にしたオリジナルのくじゃく仮スプライト。"""

        pyxel.blt(
            x,
            y,
            GUIDE_CHARACTER_IMAGE_BANK,
            0,
            0,
            40,
            40,
            COLOR_PINK,
        )

    def _draw_title(self) -> None:
        if self.layout is LayoutMode.PORTRAIT:
            self._draw_portrait_title()
            return
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
        tagline = "牌を上書きして役を作ろう"
        pyxel.text(
            self._centered_japanese_x(tagline),
            84,
            tagline,
            COLOR_IVORY,
            self._japanese_font,
        )
        start_text = "SPACE・ENTER・Aで開始"
        pyxel.text(
            self._centered_japanese_x(start_text),
            101,
            start_text,
            COLOR_BRIGHT_IVORY,
            self._japanese_font,
        )
        help_text = "H・STARTで遊び方"
        pyxel.text(
            self._centered_japanese_x(help_text),
            113,
            help_text,
            COLOR_MUTED,
            self._japanese_font,
        )
        high_score_text = f"最高得点 {self.high_score}"
        pyxel.text(
            self._centered_japanese_x(high_score_text),
            125,
            high_score_text,
            COLOR_GOLD,
            self._japanese_font,
        )
        save_error = (
            self.persistence_error is not None
            or self.tutorial_persistence_error is not None
        )
        if save_error:
            error_text = "保存領域を使えません"
            pyxel.text(
                self._centered_japanese_x(error_text),
                137,
                error_text,
                COLOR_VERMILION,
                self._japanese_font,
            )
        else:
            quit_text = "ESC: 終了"
            pyxel.text(
                self._centered_japanese_x(quit_text),
                TITLE_QUIT_Y,
                quit_text,
                COLOR_MUTED,
                self._japanese_font,
            )

    def _draw_portrait_title(self) -> None:
        pyxel.cls(COLOR_BACKGROUND)
        pyxel.rect(8, 10, 160, 236, COLOR_PANEL)
        pyxel.rectb(8, 10, 160, 236, COLOR_WOOD_EDGE)
        pyxel.rectb(12, 14, 152, 228, COLOR_MAHOGANY)
        title = "MAHJONG TILE PUZZLE"
        pyxel.text(self._centered_text_x(title), 42, title, COLOR_GOLD)
        sample_types = (
            TileType.honor_tile(Honor.EAST),
            TileType.suited(Suit.PINZU, 5),
            TileType.honor_tile(Honor.RED),
        )
        sample_width = (
            len(sample_types) * TILE_SPRITE_SIZE
            + (len(sample_types) - 1) * 2
        )
        sample_x = (self.screen_width - sample_width) // 2
        for index, tile_type in enumerate(sample_types):
            self._blt_tile(sample_x + index * 18, 75, tile_type)
        tagline = "牌を上書きして役を作ろう"
        pyxel.text(
            self._centered_japanese_x(tagline),
            111,
            tagline,
            COLOR_IVORY,
            self._japanese_font,
        )
        start_text = "Aでゲーム開始"
        pyxel.text(
            self._centered_japanese_x(start_text),
            142,
            start_text,
            COLOR_BRIGHT_IVORY,
            self._japanese_font,
        )
        help_text = "STARTで遊び方"
        pyxel.text(
            self._centered_japanese_x(help_text),
            160,
            help_text,
            COLOR_MUTED,
            self._japanese_font,
        )
        high_score_text = f"最高得点 {self.high_score}"
        pyxel.text(
            self._centered_japanese_x(high_score_text),
            181,
            high_score_text,
            COLOR_GOLD,
            self._japanese_font,
        )
        if (
            self.persistence_error is not None
            or self.tutorial_persistence_error is not None
        ):
            error_text = "保存領域を使えません"
            pyxel.text(
                self._centered_japanese_x(error_text),
                199,
                error_text,
                COLOR_VERMILION,
                self._japanese_font,
            )
        pyxel.text(
            self._centered_japanese_x("画面下の仮想パッドで操作"),
            218,
            "画面下の仮想パッドで操作",
            COLOR_MUTED,
            self._japanese_font,
        )

    def _draw_game(self) -> None:
        pyxel.cls(COLOR_BACKGROUND)
        if self.layout is LayoutMode.PORTRAIT:
            pyxel.text(
                self._centered_text_x("MAHJONG TILE PUZZLE"),
                4,
                "MAHJONG TILE PUZZLE",
                COLOR_IVORY,
            )
            self._draw_board()
            self._draw_preview()
            self._draw_mobile_status()
            return
        pyxel.text(8, 6, "MAHJONG TILE PUZZLE", COLOR_IVORY)
        self._draw_board()
        self._draw_preview()
        self._draw_sidebar()
        pyxel.text(
            8,
            155,
            "矢印:移動 Z/X:回転",
            COLOR_MUTED,
            self._japanese_font,
        )
        pyxel.text(
            8,
            166,
            "SPACE:確定 TAB:川 Y:役 H:遊び方",
            COLOR_MUTED,
            self._japanese_font,
        )

    def _draw_board(self) -> None:
        pyxel.rect(
            self.board_origin_x - 2,
            self.board_origin_y - 2,
            BOARD_WIDTH * CELL_SIZE + 4,
            BOARD_HEIGHT * CELL_SIZE + 4,
            COLOR_MAHOGANY,
        )
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                tile = self.game.board.tile_at(Coordinate(x, y))
                self._draw_tile(
                    tile,
                    self.board_origin_x + x * CELL_SIZE,
                    self.board_origin_y + y * CELL_SIZE,
                    preview=False,
                )

    def _draw_preview(self) -> None:
        for cell in self.game.preview_cells:
            self._draw_positioned_cell(cell)

    def _draw_positioned_cell(self, cell: PositionedCell) -> None:
        self._draw_tile(
            cell.tile,
            self.board_origin_x + cell.coordinate.x * CELL_SIZE,
            self.board_origin_y + cell.coordinate.y * CELL_SIZE,
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
            SIDEBAR_Y,
            SIDEBAR_WIDTH,
            SIDEBAR_HEIGHT,
            COLOR_PANEL,
        )
        pyxel.rectb(
            SIDEBAR_X - 4,
            SIDEBAR_Y,
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
            BOARD_ORIGIN_Y + 17,
            f"SCORE {self.session.total_score}",
            COLOR_GOLD,
        )
        pyxel.text(
            SIDEBAR_X + 54,
            BOARD_ORIGIN_Y + 17,
            f"COMBO {self.session.turn_state.consecutive_win_turns}",
            COLOR_IVORY,
        )
        current = self.game.current_block
        current_name = "-" if current is None else current.kind.value
        pyxel.text(
            SIDEBAR_X,
            BOARD_ORIGIN_Y + 29,
            f"BLOCK {current_name}",
            COLOR_GOLD,
        )
        self._draw_dora_indicators()
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

    def _draw_mobile_status(self) -> None:
        """縦画面の盤面下へ、プレイ中の情報をコンパクトに描画する。"""

        panel_x, panel_y, panel_width, panel_height = 8, 152, 160, 98
        pyxel.rect(
            panel_x,
            panel_y,
            panel_width,
            panel_height,
            COLOR_PANEL,
        )
        pyxel.rectb(
            panel_x,
            panel_y,
            panel_width,
            panel_height,
            COLOR_WOOD_EDGE,
        )
        pyxel.text(
            13,
            157,
            f"TURN {self.game.turn:02d}/{TOTAL_TURN_COUNT:02d}",
            COLOR_IVORY,
        )
        pyxel.text(
            108,
            157,
            (
                "-"
                if self.game.current_block is None
                else f"BLOCK {self.game.current_block.kind.value}"
            ),
            COLOR_GOLD,
        )
        pyxel.text(
            13,
            170,
            f"得点 {self.session.total_score}",
            COLOR_GOLD,
            self._japanese_font,
        )
        pyxel.text(
            92,
            170,
            f"連続 {self.session.turn_state.consecutive_win_turns}",
            COLOR_IVORY,
            self._japanese_font,
        )

        pyxel.text(13, 184, "DORA", COLOR_IVORY)
        for index, indicator in enumerate(
            self.game.visible_dora_indicators
        ):
            self._blt_tile(
                34 + index * (TILE_SPRITE_SIZE + 1),
                179,
                indicator.kind,
            )

        pyxel.text(13, 202, "NEXT", COLOR_IVORY)
        for index, block in enumerate(self.game.next_blocks):
            self._draw_next_block(
                block,
                x=43 + index * 39,
                y=199,
            )

        pyxel.text(
            31,
            220,
            "A:確定",
            COLOR_GOLD,
            self._japanese_font,
        )
        pyxel.text(
            101,
            220,
            "X/B:回転",
            COLOR_IVORY,
            self._japanese_font,
        )
        pyxel.text(
            37,
            237,
            "START:役  BACK:川",
            COLOR_MUTED,
            self._japanese_font,
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
        if self.layout is LayoutMode.PORTRAIT:
            x, y, width, height = 6, 83, 164, 84
        else:
            x, y, width, height = 42, 50, 172, 76
        pyxel.rect(x, y, width, height, COLOR_INK)
        pyxel.rectb(x, y, width, height, COLOR_WOOD_EDGE)
        accent = (
            COLOR_VERMILION
            if notice.kind is NoticeKind.KAN
            else COLOR_GOLD
        )
        pyxel.rectb(x + 2, y + 2, width - 4, height - 4, accent)
        title_x = x + (width - self._japanese_text_width(notice.title)) // 2
        pyxel.text(
            title_x,
            y + 10,
            notice.title,
            accent,
            self._japanese_font,
        )
        for index, line in enumerate(notice.lines):
            line_x = x + (width - self._japanese_text_width(line)) // 2
            pyxel.text(
                line_x,
                y + 25 + index * 10,
                line,
                COLOR_IVORY,
                self._japanese_font,
            )
        continuation = "いずれかの操作で続ける"
        continuation_x = (
            x + (width - self._japanese_text_width(continuation)) // 2
        )
        pyxel.text(
            continuation_x,
            y + height - 12,
            continuation,
            COLOR_MUTED,
            self._japanese_font,
        )

    def _draw_river_overlay(self) -> None:
        if self.layout is LayoutMode.PORTRAIT:
            self._draw_portrait_river_overlay()
            return
        self._draw_overlay_panel("川・全履歴")
        pyxel.text(
            12,
            25,
            f"合計 {self.game.river.total_count}牌・縦1列が1手番",
            COLOR_IVORY,
            self._japanese_font,
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
        pyxel.text(
            76,
            153,
            "TAB・BACK・Bで閉じる",
            COLOR_MUTED,
            self._japanese_font,
        )

    def _draw_portrait_river_overlay(self) -> None:
        self._draw_overlay_panel("川・全履歴")
        pyxel.text(
            12,
            27,
            f"合計 {self.game.river.total_count}牌・横1列が1手番",
            COLOR_IVORY,
            self._japanese_font,
        )
        for index, record in enumerate(self.game.river.records):
            turn = index // 4
            slot = index % 4
            column = turn // 9
            row = turn % 9
            x = 10 + column * 82 + slot * 13
            y = 38 + row * 22
            pyxel.rect(x, y, 12, 16, COLOR_IVORY)
            pyxel.rectb(x, y, 12, 16, COLOR_WOOD_EDGE)
            label = tile_label(record.tile.kind)
            label_x = x + (12 - len(label) * 4) // 2
            pyxel.text(label_x, y + 5, label, tile_color(record.tile.kind))
        pyxel.text(
            38,
            235,
            "BACK・Bで閉じる",
            COLOR_MUTED,
            self._japanese_font,
        )

    def _draw_yaku_overlay(self) -> None:
        self._draw_overlay_panel("役一覧")
        if self._japanese_font is None:
            raise RuntimeError("日本語フォントが初期化されていません")
        entry = YAKU_GUIDE_ENTRIES[self._yaku_page]
        acquired = {
            yaku
            for state in self.session.line_states
            for yaku in state.acquired_yaku
        }
        page_label = f"{self._yaku_page + 1}/{len(YAKU_GUIDE_ENTRIES)}"
        if self.layout is LayoutMode.PORTRAIT:
            name_y, reading_y, description_y = 49, 64, 88
            example_label_y, example_y = 109, 124
            acquired_y, navigation_y = 153, 235
            text_x, points_x = 13, 128
        else:
            name_y, reading_y, description_y = 39, 54, 72
            example_label_y, example_y = 87, 101
            acquired_y, navigation_y = 127, 153
            text_x, points_x = 18, 198
        pyxel.text(
            self.screen_width - len(page_label) * 4 - 12,
            16,
            page_label,
            COLOR_GOLD,
        )
        if self.layout is LayoutMode.PORTRAIT:
            pyxel.text(
                text_x,
                24,
                "3＋3＋2で基本和了",
                COLOR_IVORY,
                self._japanese_font,
            )
            pyxel.text(
                text_x,
                35,
                "役があれば追加得点",
                COLOR_MUTED,
                self._japanese_font,
            )
        else:
            pyxel.text(
                text_x,
                24,
                "3＋3＋2で基本和了・役は追加得点",
                COLOR_IVORY,
                self._japanese_font,
            )
        pyxel.text(
            text_x,
            name_y,
            YAKU_DISPLAY_NAMES[entry.yaku],
            COLOR_GOLD,
            self._japanese_font,
        )
        pyxel.text(
            text_x,
            reading_y,
            entry.reading,
            COLOR_MUTED,
            self._japanese_font,
        )
        pyxel.text(
            points_x,
            name_y + 2,
            f"{DEFAULT_SCORING_CONFIG.yaku_points[entry.yaku]}点",
            COLOR_GOLD,
            self._japanese_font,
        )
        pyxel.text(
            text_x,
            description_y,
            entry.description,
            COLOR_IVORY,
            self._japanese_font,
        )
        pyxel.text(
            text_x,
            example_label_y,
            "成立例",
            COLOR_MUTED,
            self._japanese_font,
        )
        example_x = (self.screen_width - 8 * TILE_SPRITE_SIZE) // 2
        for index, tile_type in enumerate(entry.example_tiles):
            self._blt_tile(
                example_x + index * TILE_SPRITE_SIZE,
                example_y,
                tile_type,
            )
        acquired_label = (
            "取得済み" if entry.yaku in acquired else "未取得"
        )
        pyxel.text(
            text_x,
            acquired_y,
            acquired_label,
            COLOR_GOLD if entry.yaku in acquired else COLOR_MUTED,
            self._japanese_font,
        )
        navigation = (
            "←→:ページ  START・B:閉じる"
            if self.layout is LayoutMode.PORTRAIT
            else "←→:ページ  Y・B:閉じる"
        )
        pyxel.text(
            self._centered_japanese_x(navigation),
            navigation_y,
            navigation,
            COLOR_MUTED,
            self._japanese_font,
        )

    def _draw_overlay_panel(self, title: str) -> None:
        pyxel.cls(COLOR_BACKGROUND)
        if self.layout is LayoutMode.PORTRAIT:
            pyxel.rect(5, 8, 166, 240, COLOR_INK)
            pyxel.rectb(5, 8, 166, 240, COLOR_WOOD_EDGE)
            pyxel.rectb(8, 11, 160, 234, COLOR_MAHOGANY)
        else:
            pyxel.rect(5, 8, 246, 160, COLOR_INK)
            pyxel.rectb(5, 8, 246, 160, COLOR_WOOD_EDGE)
            pyxel.rectb(8, 11, 240, 154, COLOR_MAHOGANY)
        pyxel.text(
            12,
            14,
            title,
            COLOR_GOLD,
            self._japanese_font,
        )

    def _draw_result(self) -> None:
        if self.layout is LayoutMode.PORTRAIT:
            self._draw_portrait_result()
            return
        pyxel.cls(COLOR_BACKGROUND)
        summary = GameSummary.from_session(self.session)
        pyxel.rect(28, 14, 200, 148, COLOR_PANEL)
        pyxel.rectb(28, 14, 200, 148, COLOR_WOOD_EDGE)
        pyxel.rectb(31, 17, 194, 142, COLOR_MAHOGANY)
        title = "対局結果"
        pyxel.text(
            self._centered_japanese_x(title),
            27,
            title,
            COLOR_GOLD,
            self._japanese_font,
        )
        result_lines = (
            (f"最終得点  {summary.total_score}", COLOR_IVORY),
            (f"最高得点  {self.high_score}", COLOR_GOLD),
            (f"手番      {summary.turns}", COLOR_IVORY),
            (f"和了      {summary.win_count}", COLOR_IVORY),
            (f"カン      {summary.kan_count}", COLOR_IVORY),
            (f"取得役    {len(summary.acquired_yaku)}種", COLOR_IVORY),
            (f"川の牌    {summary.river_count}枚", COLOR_IVORY),
        )
        for index, (line, color) in enumerate(result_lines):
            pyxel.text(
                68,
                46 + index * 12,
                line,
                color,
                self._japanese_font,
            )
        pyxel.text(
            47,
            134,
            "R・A:もう一度  H・START:遊び方",
            COLOR_BRIGHT_IVORY,
            self._japanese_font,
        )
        if self.persistence_error is None:
            pyxel.text(
                101,
                147,
                "ESC:終了",
                COLOR_MUTED,
                self._japanese_font,
            )
        else:
            error_text = "最高得点を保存できません"
            pyxel.text(
                self._centered_japanese_x(error_text),
                147,
                error_text,
                COLOR_VERMILION,
                self._japanese_font,
            )

    def _draw_portrait_result(self) -> None:
        pyxel.cls(COLOR_BACKGROUND)
        summary = GameSummary.from_session(self.session)
        pyxel.rect(12, 18, 152, 220, COLOR_PANEL)
        pyxel.rectb(12, 18, 152, 220, COLOR_WOOD_EDGE)
        pyxel.rectb(15, 21, 146, 214, COLOR_MAHOGANY)
        title = "対局結果"
        pyxel.text(
            self._centered_japanese_x(title),
            39,
            title,
            COLOR_GOLD,
            self._japanese_font,
        )
        result_lines = (
            (f"最終得点  {summary.total_score}", COLOR_IVORY),
            (f"最高得点  {self.high_score}", COLOR_GOLD),
            (f"手番      {summary.turns}", COLOR_IVORY),
            (f"和了      {summary.win_count}", COLOR_IVORY),
            (f"カン      {summary.kan_count}", COLOR_IVORY),
            (
                f"取得役    {len(summary.acquired_yaku)}種",
                COLOR_IVORY,
            ),
            (f"川の牌    {summary.river_count}枚", COLOR_IVORY),
        )
        for index, (line, color) in enumerate(result_lines):
            pyxel.text(
                39,
                68 + index * 16,
                line,
                color,
                self._japanese_font,
            )
        restart = "A:もう一度"
        pyxel.text(
            self._centered_japanese_x(restart),
            198,
            restart,
            COLOR_BRIGHT_IVORY,
            self._japanese_font,
        )
        help_text = "START:遊び方"
        pyxel.text(
            self._centered_japanese_x(help_text),
            214,
            help_text,
            COLOR_MUTED,
            self._japanese_font,
        )
        if self.persistence_error is not None:
            error_text = "最高得点を保存できません"
            pyxel.text(
                self._centered_japanese_x(error_text),
                226,
                error_text,
                COLOR_VERMILION,
                self._japanese_font,
            )


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
