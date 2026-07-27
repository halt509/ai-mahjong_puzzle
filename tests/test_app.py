import pyxel

from mahjong_puzzle.app import (
    BOARD_ORIGIN_Y,
    CONTROL_BINDINGS,
    NEXT_CELL_SIZE,
    NEXT_CELL_STEP,
    NEXT_ITEM_SPACING,
    NEXT_START_OFFSET_Y,
    PLACEMENT_KNOCK_SOUND,
    PLACEMENT_RATTLE_SOUND,
    PORTRAIT_BOARD_ORIGIN_X,
    PORTRAIT_BOARD_ORIGIN_Y,
    PORTRAIT_SCREEN_HEIGHT,
    PORTRAIT_SCREEN_WIDTH,
    SIDEBAR_HEIGHT,
    SIDEBAR_Y,
    TITLE_INNER_HEIGHT,
    TITLE_INNER_Y,
    TITLE_QUIT_Y,
    TITLE_TEXT_Y,
    ControlAction,
    LayoutMode,
    MahjongPuzzleApp,
    centered_text_x,
    tile_label,
)
from mahjong_puzzle.tetromino import Tetromino, TetrominoKind
from mahjong_puzzle.tiles import Honor, Suit, TileType, create_full_tile_set
from mahjong_puzzle.tutorial import TUTORIAL_PAGES, TutorialState
from mahjong_puzzle.ui import Notice, NoticeKind, ScreenMode, UiState
from mahjong_puzzle.yaku import YAKU_DISPLAY_NAMES
from mahjong_puzzle.yaku_catalog import YAKU_GUIDE_ENTRIES


def test_ascii_tile_labels_cover_suits_and_honors() -> None:
    assert tile_label(TileType.suited(Suit.MANZU, 1)) == "m1"
    assert tile_label(TileType.suited(Suit.PINZU, 9)) == "p9"
    assert tile_label(TileType.suited(Suit.SOUZU, 5)) == "s5"
    assert tile_label(TileType.honor_tile(Honor.EAST)) == "E"
    assert tile_label(TileType.honor_tile(Honor.WHITE)) == "P"
    assert tile_label(TileType.honor_tile(Honor.GREEN)) == "F"
    assert tile_label(TileType.honor_tile(Honor.RED)) == "C"


def test_title_text_positions_are_calculated_from_screen_center() -> None:
    assert centered_text_x("MAHJONG TILE PUZZLE") == 90
    assert centered_text_x("ESC: QUIT") == 110


def test_title_content_has_matching_top_and_bottom_margins() -> None:
    title_top_margin = TITLE_TEXT_Y - TITLE_INNER_Y
    inner_bottom = TITLE_INNER_Y + TITLE_INNER_HEIGHT - 1
    quit_bottom_margin = inner_bottom - (TITLE_QUIT_Y + 4)

    assert title_top_margin == quit_bottom_margin


def test_placement_sound_layers_short_noise_and_tile_knock() -> None:
    notes, tones, volumes, effects, speed = PLACEMENT_RATTLE_SOUND

    assert len(notes) // 2 == len(tones) == len(volumes) == len(effects)
    assert len(tones) >= 6
    assert set(tones) == {"n"}
    assert speed <= 2

    _, knock_tones, _, _, _ = PLACEMENT_KNOCK_SOUND
    assert set(knock_tones) == {"p"}


def test_app_construction_does_not_start_pyxel_loop() -> None:
    app = MahjongPuzzleApp(seed=20260724)

    assert app.session.game is app.game
    assert app.game.turn == 0
    assert not app.game.is_game_over


def test_portrait_layout_uses_mobile_screen_and_centered_board() -> None:
    app = MahjongPuzzleApp(seed=20260725, layout=LayoutMode.PORTRAIT)

    assert app.screen_width == PORTRAIT_SCREEN_WIDTH == 176
    assert app.screen_height == PORTRAIT_SCREEN_HEIGHT == 256
    assert app.board_origin_x == PORTRAIT_BOARD_ORIGIN_X == 24
    assert app.board_origin_y == PORTRAIT_BOARD_ORIGIN_Y == 18
    assert PORTRAIT_BOARD_ORIGIN_X * 2 + 8 * 16 == PORTRAIT_SCREEN_WIDTH


def test_landscape_layout_keeps_existing_dimensions_and_board_origin() -> None:
    app = MahjongPuzzleApp(seed=20260725)

    assert app.layout is LayoutMode.LANDSCAPE
    assert app.screen_width == 256
    assert app.screen_height == 176
    assert app.board_origin_x == 8
    assert app.board_origin_y == 24


def test_portrait_game_uses_mobile_status_instead_of_sidebar(monkeypatch) -> None:
    app = MahjongPuzzleApp(seed=20260725, layout=LayoutMode.PORTRAIT)
    calls: list[str] = []
    monkeypatch.setattr(pyxel, "cls", lambda *args: None)
    monkeypatch.setattr(pyxel, "text", lambda *args: None)
    monkeypatch.setattr(app, "_draw_board", lambda: calls.append("board"))
    monkeypatch.setattr(app, "_draw_preview", lambda: calls.append("preview"))
    monkeypatch.setattr(
        app,
        "_draw_mobile_status",
        lambda: calls.append("mobile_status"),
    )
    monkeypatch.setattr(
        app,
        "_draw_sidebar",
        lambda: calls.append("sidebar"),
    )

    app._draw_game()

    assert calls == ["board", "preview", "mobile_status"]


def test_mobile_status_always_shows_essential_controls(monkeypatch) -> None:
    app = MahjongPuzzleApp(seed=20260725, layout=LayoutMode.PORTRAIT)
    app._japanese_font = object()
    texts: list[str] = []
    monkeypatch.setattr(pyxel, "rect", lambda *args: None)
    monkeypatch.setattr(pyxel, "rectb", lambda *args: None)
    monkeypatch.setattr(pyxel, "tri", lambda *args: None)
    monkeypatch.setattr(
        pyxel,
        "text",
        lambda _x, _y, text, _color, *args: texts.append(text),
    )
    monkeypatch.setattr(app, "_blt_tile", lambda *args: None)

    app._draw_mobile_status()

    assert "A:確定" in texts
    assert "X/B:回転" in texts


def test_landscape_bottom_controls_are_japanese(monkeypatch) -> None:
    app = MahjongPuzzleApp(seed=20260725)
    app._japanese_font = object()
    texts: list[tuple[int, str]] = []
    monkeypatch.setattr(pyxel, "cls", lambda *args: None)
    monkeypatch.setattr(
        pyxel,
        "text",
        lambda _x, y, text, *args: texts.append((y, text)),
    )
    monkeypatch.setattr(app, "_draw_board", lambda: None)
    monkeypatch.setattr(app, "_draw_preview", lambda: None)
    monkeypatch.setattr(app, "_draw_sidebar", lambda: None)

    app._draw_game()

    assert (155, "矢印:移動 Z/X:回転") in texts
    assert (166, "SPACE:確定 TAB:川 Y:役 H:遊び方") in texts


def test_desktop_status_groups_score_and_combo_without_river_or_last(
    monkeypatch,
) -> None:
    app = MahjongPuzzleApp(seed=20260725)
    calls: list[tuple[int, int, str]] = []
    monkeypatch.setattr(pyxel, "rect", lambda *args: None)
    monkeypatch.setattr(pyxel, "rectb", lambda *args: None)
    monkeypatch.setattr(
        pyxel,
        "text",
        lambda x, y, text, *args: calls.append((x, y, text)),
    )
    monkeypatch.setattr(app, "_blt_tile", lambda *args: None)
    monkeypatch.setattr(app, "_draw_next_block", lambda *args, **kwargs: None)

    app._draw_sidebar()

    score = next(call for call in calls if call[2].startswith("SCORE"))
    combo = next(call for call in calls if call[2].startswith("COMBO"))
    labels = {text for _, _, text in calls}
    assert score[1] == combo[1]
    assert "NEXT" in labels
    assert not any(
        label.startswith(("RIVER", "LAST", "川", "直前"))
        for label in labels
    )


def test_mobile_status_groups_score_and_combo_without_recent_river(
    monkeypatch,
) -> None:
    app = MahjongPuzzleApp(seed=20260725, layout=LayoutMode.PORTRAIT)
    app._japanese_font = object()
    calls: list[tuple[int, int, str]] = []
    monkeypatch.setattr(pyxel, "rect", lambda *args: None)
    monkeypatch.setattr(pyxel, "rectb", lambda *args: None)
    monkeypatch.setattr(
        pyxel,
        "text",
        lambda x, y, text, *args: calls.append((x, y, text)),
    )
    monkeypatch.setattr(app, "_blt_tile", lambda *args: None)
    monkeypatch.setattr(app, "_draw_next_block", lambda *args, **kwargs: None)

    app._draw_mobile_status()

    score = next(call for call in calls if call[2].startswith("SCORE"))
    combo = next(call for call in calls if call[2].startswith("COMBO"))
    labels = {text for _, _, text in calls}
    assert score[1] == combo[1]
    assert "NEXT" in labels
    assert not any(label.startswith(("得点", "連続")) for label in labels)
    assert not any(
        label.startswith(("RIVER", "LAST", "川 ", "直前"))
        for label in labels
    )


def test_yaku_overlay_changes_page_with_left_and_right(monkeypatch) -> None:
    app = MahjongPuzzleApp(seed=20260725)
    app.ui = UiState(screen=ScreenMode.YAKU)
    pressed = {pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT}
    monkeypatch.setattr(pyxel, "btnp", lambda key: key in pressed)

    app.update()

    assert app.yaku_page == 1

    pressed.clear()
    pressed.add(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT)
    app.update()

    assert app.yaku_page == 0


def test_yaku_overlay_draws_japanese_details_and_tile_example(
    monkeypatch,
) -> None:
    app = MahjongPuzzleApp(seed=20260725)
    app._japanese_font = object()
    texts: list[str] = []
    tiles: list[TileType] = []
    monkeypatch.setattr(pyxel, "cls", lambda *args: None)
    monkeypatch.setattr(pyxel, "rect", lambda *args: None)
    monkeypatch.setattr(pyxel, "rectb", lambda *args: None)
    monkeypatch.setattr(
        pyxel,
        "text",
        lambda _x, _y, text, _color, *args: texts.append(text),
    )
    monkeypatch.setattr(
        app,
        "_blt_tile",
        lambda _x, _y, tile_type: tiles.append(tile_type),
    )

    app._draw_yaku_overlay()

    entry = YAKU_GUIDE_ENTRIES[0]
    assert YAKU_DISPLAY_NAMES[entry.yaku] in texts
    assert entry.reading in texts
    assert entry.description in texts
    assert "3＋3＋2で基本和了・役は追加得点" in texts
    assert tiles == list(entry.example_tiles)


def test_portrait_yaku_navigation_fits_above_inner_frame(monkeypatch) -> None:
    app = MahjongPuzzleApp(seed=20260725, layout=LayoutMode.PORTRAIT)

    class FixedWidthFont:
        @staticmethod
        def text_width(text: str) -> int:
            return len(text) * 5

    app._japanese_font = FixedWidthFont()
    calls: list[tuple[int, int, str]] = []
    monkeypatch.setattr(pyxel, "cls", lambda *args: None)
    monkeypatch.setattr(pyxel, "rect", lambda *args: None)
    monkeypatch.setattr(pyxel, "rectb", lambda *args: None)
    monkeypatch.setattr(
        pyxel,
        "text",
        lambda x, y, text, *args: calls.append((x, y, text)),
    )
    monkeypatch.setattr(app, "_blt_tile", lambda *args: None)

    app._draw_yaku_overlay()

    navigation = next(call for call in calls if call[2].startswith("←→"))
    inner_frame_bottom = 11 + 234 - 1
    japanese_font_height = 10
    assert navigation[1] + japanese_font_height < inner_frame_bottom


def test_all_three_next_previews_fit_inside_sidebar() -> None:
    tiles = create_full_tile_set()
    sidebar_bottom = SIDEBAR_Y + SIDEBAR_HEIGHT - 1

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


def test_sidebar_frame_matches_board_frame_height() -> None:
    board_frame_top = BOARD_ORIGIN_Y - 2
    board_frame_height = 8 * 16 + 4

    assert SIDEBAR_Y == board_frame_top
    assert SIDEBAR_HEIGHT == board_frame_height


def test_control_dismisses_notice_without_moving_block(monkeypatch) -> None:
    app = MahjongPuzzleApp(seed=20260724)
    app.ui = UiState(screen=ScreenMode.GAME)
    app.ui.queue_notifications(
        (
            Notice(
                kind=NoticeKind.WIN,
                title="WIN!",
                lines=("TOTAL +100",),
            ),
        ),
        game_over=False,
    )
    original_x = app.game.active_x
    monkeypatch.setattr(
        pyxel,
        "btnp",
        lambda key: key == pyxel.GAMEPAD1_BUTTON_A,
    )

    app.update()

    assert app.ui.current_notice is None
    assert app.ui.screen is ScreenMode.GAME
    assert app.game.active_x == original_x


def test_gamepad_buttons_are_bound_to_mobile_controls() -> None:
    assert pyxel.GAMEPAD1_BUTTON_DPAD_LEFT in CONTROL_BINDINGS[
        ControlAction.MOVE_LEFT
    ]
    assert pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT in CONTROL_BINDINGS[
        ControlAction.MOVE_RIGHT
    ]
    assert pyxel.GAMEPAD1_BUTTON_DPAD_UP in CONTROL_BINDINGS[
        ControlAction.MOVE_UP
    ]
    assert pyxel.GAMEPAD1_BUTTON_DPAD_DOWN in CONTROL_BINDINGS[
        ControlAction.MOVE_DOWN
    ]
    assert pyxel.GAMEPAD1_BUTTON_X in CONTROL_BINDINGS[
        ControlAction.ROTATE_COUNTERCLOCKWISE
    ]
    assert pyxel.GAMEPAD1_BUTTON_B in CONTROL_BINDINGS[
        ControlAction.ROTATE_CLOCKWISE
    ]
    assert pyxel.GAMEPAD1_BUTTON_A in CONTROL_BINDINGS[ControlAction.PLACE]
    assert pyxel.GAMEPAD1_BUTTON_START in CONTROL_BINDINGS[
        ControlAction.TOGGLE_YAKU
    ]
    assert pyxel.GAMEPAD1_BUTTON_BACK in CONTROL_BINDINGS[
        ControlAction.TOGGLE_RIVER
    ]
    assert pyxel.GAMEPAD1_BUTTON_A in CONTROL_BINDINGS[
        ControlAction.START_GAME
    ]
    assert all(
        pyxel.GAMEPAD1_BUTTON_Y not in bindings
        for bindings in CONTROL_BINDINGS.values()
    )


def test_gamepad_starts_game_and_moves_active_block(monkeypatch) -> None:
    app = MahjongPuzzleApp(seed=20260725)
    pressed = {pyxel.GAMEPAD1_BUTTON_A}
    monkeypatch.setattr(pyxel, "btnp", lambda key: key in pressed)

    app.update()

    assert app.ui.screen is ScreenMode.GAME

    original_x = app.game.active_x
    pressed.clear()
    pressed.add(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT)

    app.update()

    assert app.game.active_x == original_x - 1


def test_gamepad_a_places_active_block(monkeypatch) -> None:
    app = MahjongPuzzleApp(seed=20260725)
    app.ui = UiState(screen=ScreenMode.GAME)
    monkeypatch.setattr(
        pyxel,
        "btnp",
        lambda key: key == pyxel.GAMEPAD1_BUTTON_A,
    )
    monkeypatch.setattr(pyxel, "play", lambda *args, **kwargs: None)

    app.update()

    assert app.game.turn == 1


def test_gamepad_opens_and_closes_overlays(monkeypatch) -> None:
    app = MahjongPuzzleApp(seed=20260725)
    app.ui = UiState(screen=ScreenMode.GAME)
    pressed = {pyxel.GAMEPAD1_BUTTON_BACK}
    monkeypatch.setattr(pyxel, "btnp", lambda key: key in pressed)

    app.update()

    assert app.ui.screen is ScreenMode.RIVER

    pressed.clear()
    pressed.add(pyxel.GAMEPAD1_BUTTON_B)
    app.update()

    assert app.ui.screen is ScreenMode.GAME

    pressed.clear()
    pressed.add(pyxel.GAMEPAD1_BUTTON_START)
    app.update()

    assert app.ui.screen is ScreenMode.YAKU


def test_gamepad_a_restarts_from_result(monkeypatch) -> None:
    app = MahjongPuzzleApp(seed=20260725)
    app.ui = UiState(screen=ScreenMode.RESULT)
    previous_session = app.session
    monkeypatch.setattr(
        pyxel,
        "btnp",
        lambda key: key == pyxel.GAMEPAD1_BUTTON_A,
    )

    app.update()

    assert app.ui.screen is ScreenMode.GAME
    assert app.session is not previous_session


def test_gamepad_start_opens_help_from_title(monkeypatch) -> None:
    app = MahjongPuzzleApp(seed=20260725)
    monkeypatch.setattr(
        pyxel,
        "btnp",
        lambda key: key == pyxel.GAMEPAD1_BUTTON_START,
    )

    app.update()

    assert app.ui.screen is ScreenMode.HELP


def test_gamepad_start_opens_help_from_result(monkeypatch) -> None:
    app = MahjongPuzzleApp(seed=20260725)
    app.ui = UiState(screen=ScreenMode.RESULT)
    previous_session = app.session
    monkeypatch.setattr(
        pyxel,
        "btnp",
        lambda key: key == pyxel.GAMEPAD1_BUTTON_START,
    )

    app.update()

    assert app.ui.screen is ScreenMode.HELP
    assert app.session is previous_session


def test_keyboard_h_opens_help_without_changing_game(monkeypatch) -> None:
    app = MahjongPuzzleApp(seed=20260725)
    app.ui = UiState(screen=ScreenMode.GAME)
    previous_session = app.session
    monkeypatch.setattr(pyxel, "btnp", lambda key: key == pyxel.KEY_H)

    app.update()

    assert app.ui.screen is ScreenMode.HELP
    assert app.session is previous_session


def test_first_launch_opens_tutorial_and_skip_marks_seen(monkeypatch) -> None:
    class FakeTutorialProgress:
        def __init__(self) -> None:
            self.seen = False

        def load(self) -> bool:
            return self.seen

        def mark_seen(self) -> None:
            self.seen = True

    progress = FakeTutorialProgress()
    app = MahjongPuzzleApp(
        seed=20260725,
        tutorial_progress_store=progress,
    )

    app._show_initial_tutorial_if_needed()
    assert app.ui.screen is ScreenMode.HELP
    assert app.tutorial_page == 0

    monkeypatch.setattr(
        pyxel,
        "btnp",
        lambda key: key == pyxel.GAMEPAD1_BUTTON_B,
    )
    app.update()

    assert app.ui.screen is ScreenMode.TITLE
    assert progress.seen


def test_tutorial_a_advances_and_finishes_on_last_page(monkeypatch) -> None:
    class FakeTutorialProgress:
        def load(self) -> bool:
            return False

        def mark_seen(self) -> None:
            self.seen = True

    progress = FakeTutorialProgress()
    app = MahjongPuzzleApp(
        seed=20260725,
        tutorial_progress_store=progress,
    )
    app._show_initial_tutorial_if_needed()
    monkeypatch.setattr(
        pyxel,
        "btnp",
        lambda key: key == pyxel.GAMEPAD1_BUTTON_A,
    )

    for expected_page in range(1, len(TUTORIAL_PAGES)):
        app.update()
        assert app.tutorial_page == expected_page
        assert app.ui.screen is ScreenMode.HELP

    app.update()

    assert app.ui.screen is ScreenMode.TITLE
    assert progress.seen


def test_help_draws_japanese_content_and_bird(monkeypatch) -> None:
    app = MahjongPuzzleApp(seed=20260725)
    app._japanese_font = object()
    texts: list[str] = []
    bird_calls: list[tuple[int, int]] = []
    monkeypatch.setattr(pyxel, "cls", lambda *args: None)
    monkeypatch.setattr(pyxel, "rect", lambda *args: None)
    monkeypatch.setattr(pyxel, "rectb", lambda *args: None)
    monkeypatch.setattr(pyxel, "tri", lambda *args: None)
    screenshot_calls: list[tuple[object, ...]] = []
    monkeypatch.setattr(
        pyxel,
        "blt",
        lambda *args: screenshot_calls.append(args),
    )
    monkeypatch.setattr(
        pyxel,
        "text",
        lambda _x, _y, text, _color, *args: texts.append(text),
    )
    monkeypatch.setattr(
        app,
        "_draw_guide_bird",
        lambda x, y: bird_calls.append((x, y)),
    )

    app._draw_help()

    assert TUTORIAL_PAGES[0].title in texts
    assert TUTORIAL_PAGES[0].lines[0] in texts
    assert bird_calls
    assert screenshot_calls
    screenshot = screenshot_calls[0]
    assert screenshot[5:7] == (128, 64)
    assert not any("A:次へ" in text for text in texts)


def test_all_help_text_fits_inside_both_screen_widths(monkeypatch) -> None:
    class FixedWidthFont:
        @staticmethod
        def text_width(text: str) -> int:
            return len(text) * 10

    monkeypatch.setattr(pyxel, "cls", lambda *args: None)
    monkeypatch.setattr(pyxel, "rect", lambda *args: None)
    monkeypatch.setattr(pyxel, "rectb", lambda *args: None)
    monkeypatch.setattr(pyxel, "tri", lambda *args: None)
    monkeypatch.setattr(pyxel, "blt", lambda *args: None)

    for layout in LayoutMode:
        app = MahjongPuzzleApp(seed=20260725, layout=layout)
        app._japanese_font = FixedWidthFont()
        monkeypatch.setattr(app, "_draw_guide_bird", lambda *args: None)
        for page_index in range(len(TUTORIAL_PAGES)):
            calls: list[tuple[int, str]] = []
            monkeypatch.setattr(
                pyxel,
                "text",
                lambda x, _y, text, *args: calls.append((x, text)),
            )
            app.tutorial = TutorialState(page_index=page_index)

            app._draw_help()

            assert all(
                x >= 0
                and x + app._japanese_text_width(text) <= app.screen_width
                for x, text in calls
                if any(ord(character) > 127 for character in text)
            )


def test_sidebar_draws_visible_dora_indicators_as_tile_sprites(
    monkeypatch,
) -> None:
    app = MahjongPuzzleApp(seed=20260724)
    calls: list[tuple[int, int, TileType]] = []
    monkeypatch.setattr(
        "mahjong_puzzle.app.pyxel.text",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        app,
        "_blt_tile",
        lambda x, y, tile_type: calls.append((x, y, tile_type)),
    )

    app._draw_dora_indicators()

    assert [tile_type for _, _, tile_type in calls] == [
        tile.kind for tile in app.game.visible_dora_indicators
    ]
