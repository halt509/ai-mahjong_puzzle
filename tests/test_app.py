import pyxel

from mahjong_puzzle.app import (
    BGM_CHANNEL,
    BGM_SOUNDS,
    BOARD_ORIGIN_X,
    BOARD_ORIGIN_Y,
    CONTROL_BINDINGS,
    EFFECT_CHANNELS,
    GAME_TITLE_FRAME_HEIGHT,
    GAME_TITLE_FRAME_WIDTH,
    LANDSCAPE_CONTROLS_DIVIDER_Y,
    LANDSCAPE_CONTROLS_HEIGHT,
    LANDSCAPE_CONTROLS_WIDTH,
    LANDSCAPE_CONTROLS_X,
    LANDSCAPE_CONTROLS_Y,
    LANDSCAPE_MAIN_WIDTH,
    LANDSCAPE_MAIN_X,
    NEXT_CELL_SIZE,
    NEXT_CELL_STEP,
    NEXT_ITEM_SPACING,
    NEXT_START_OFFSET_Y,
    PLACEMENT_KNOCK_SOUND,
    PLACEMENT_RATTLE_SOUND,
    PREPARATION_DURATION_FRAMES,
    PORTRAIT_BOARD_ORIGIN_X,
    PORTRAIT_BOARD_ORIGIN_Y,
    PORTRAIT_PANEL_WIDTH,
    PORTRAIT_PANEL_X,
    PORTRAIT_SCREEN_HEIGHT,
    PORTRAIT_SCREEN_WIDTH,
    SCREEN_HEIGHT,
    SIDEBAR_HEIGHT,
    SIDEBAR_FRAME_X,
    SIDEBAR_WIDTH,
    SIDEBAR_X,
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


def test_bgm_uses_a_channel_reserved_from_effects() -> None:
    assert BGM_CHANNEL == 3
    assert BGM_CHANNEL not in EFFECT_CHANNELS


def test_bgm_is_quiet_and_uses_a_slow_sparse_phrase() -> None:
    for notes, tones, volumes, effects, speed in BGM_SOUNDS:
        assert len(tones) == len(volumes) == len(effects) == 8
        assert notes.count("r") == 4
        assert max(int(volume) for volume in volumes) <= 2
        assert speed >= 18


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
    assert PORTRAIT_PANEL_X == 22
    assert PORTRAIT_PANEL_WIDTH == 132
    assert PORTRAIT_PANEL_X * 2 + PORTRAIT_PANEL_WIDTH == app.screen_width
    assert PORTRAIT_BOARD_ORIGIN_X - PORTRAIT_PANEL_X == 2


def test_portrait_board_frame_matches_mobile_status_width(
    monkeypatch,
) -> None:
    app = MahjongPuzzleApp(seed=20260725, layout=LayoutMode.PORTRAIT)
    rectangles: list[tuple[int, int, int, int]] = []
    monkeypatch.setattr(
        pyxel,
        "rect",
        lambda x, y, width, height, *args: rectangles.append(
            (x, y, width, height)
        ),
    )
    monkeypatch.setattr(pyxel, "rectb", lambda *args: None)
    monkeypatch.setattr(app, "_draw_frame_corners", lambda *args: None)
    monkeypatch.setattr(app, "_draw_tile", lambda *args, **kwargs: None)

    app._draw_board()

    assert rectangles[0] == (
        PORTRAIT_PANEL_X,
        PORTRAIT_BOARD_ORIGIN_Y - 2,
        PORTRAIT_PANEL_WIDTH,
        8 * 16 + 4,
    )


def test_landscape_layout_centers_board_and_sidebar_group() -> None:
    app = MahjongPuzzleApp(seed=20260725)

    assert app.layout is LayoutMode.LANDSCAPE
    assert app.screen_width == 256
    assert app.screen_height == SCREEN_HEIGHT == 192
    assert app.board_origin_x == BOARD_ORIGIN_X == 9
    assert app.board_origin_y == BOARD_ORIGIN_Y == 20
    assert LANDSCAPE_MAIN_X == BOARD_ORIGIN_X - 2 == 7
    assert LANDSCAPE_MAIN_WIDTH == 242
    sidebar_right = SIDEBAR_FRAME_X + SIDEBAR_WIDTH
    assert LANDSCAPE_MAIN_X == app.screen_width - sidebar_right
    assert SIDEBAR_X - SIDEBAR_FRAME_X == 8
    assert LANDSCAPE_CONTROLS_Y - (SIDEBAR_Y + SIDEBAR_HEIGHT) == 2


def test_landscape_game_title_frame_is_horizontally_centered(
    monkeypatch,
) -> None:
    app = MahjongPuzzleApp(seed=20260725)
    panels: list[tuple[int, int, int, int]] = []
    monkeypatch.setattr(
        app,
        "_draw_decorated_panel",
        lambda x, y, width, height, **_kwargs: panels.append(
            (x, y, width, height)
        ),
    )
    monkeypatch.setattr(pyxel, "text", lambda *args: None)

    app._draw_game_title_frame()

    assert panels == [
        (
            (app.screen_width - GAME_TITLE_FRAME_WIDTH) // 2,
            2,
            GAME_TITLE_FRAME_WIDTH,
            GAME_TITLE_FRAME_HEIGHT,
        )
    ]
    title_y = panels[0][1]
    title_bottom = title_y + GAME_TITLE_FRAME_HEIGHT
    board_frame_y = BOARD_ORIGIN_Y - 2
    assert title_y == 2
    assert board_frame_y - title_bottom == 2


def test_portrait_game_uses_mobile_status_instead_of_sidebar(monkeypatch) -> None:
    app = MahjongPuzzleApp(seed=20260725, layout=LayoutMode.PORTRAIT)
    calls: list[str] = []
    monkeypatch.setattr(pyxel, "cls", lambda *args: None)
    monkeypatch.setattr(pyxel, "text", lambda *args: None)
    monkeypatch.setattr(app, "_draw_background", lambda: None)
    monkeypatch.setattr(app, "_draw_game_title_frame", lambda: None)
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
    texts: list[tuple[int, int, str]] = []
    rects: list[tuple[int, int, int, int]] = []
    monkeypatch.setattr(
        pyxel,
        "rect",
        lambda x, y, width, height, *args: rects.append(
            (x, y, width, height)
        ),
    )
    monkeypatch.setattr(pyxel, "rectb", lambda *args: None)
    monkeypatch.setattr(
        pyxel,
        "text",
        lambda x, y, text, *args: texts.append((x, y, text)),
    )

    app._draw_landscape_controls()

    text_x = LANDSCAPE_CONTROLS_X + 8
    assert (text_x, 158, "矢印:移動 Z/X:回転") in texts
    assert (
        text_x,
        170,
        "SPACE:確定 TAB:川 Y:役 H:遊び方",
    ) in texts
    assert LANDSCAPE_CONTROLS_X == BOARD_ORIGIN_X - 2
    assert LANDSCAPE_CONTROLS_WIDTH == LANDSCAPE_MAIN_WIDTH
    assert LANDSCAPE_CONTROLS_HEIGHT == 35
    assert text_x - LANDSCAPE_CONTROLS_X == 8
    assert 158 - LANDSCAPE_CONTROLS_Y == 6
    assert (
        LANDSCAPE_CONTROLS_Y + LANDSCAPE_CONTROLS_HEIGHT - (170 + 10)
        == 7
    )
    assert (
        LANDSCAPE_CONTROLS_X,
        LANDSCAPE_CONTROLS_Y,
        LANDSCAPE_CONTROLS_WIDTH,
        LANDSCAPE_CONTROLS_HEIGHT,
    ) in rects

    divider_y = LANDSCAPE_CONTROLS_DIVIDER_Y
    left_line = next(rect for rect in rects if rect == (92, divider_y, 32, 1))
    right_line = next(rect for rect in rects if rect == (132, divider_y, 32, 1))
    assert 128 - (left_line[0] + left_line[2]) == right_line[0] - 128
    assert LANDSCAPE_CONTROLS_Y + LANDSCAPE_CONTROLS_HEIGHT < divider_y
    assert divider_y < SCREEN_HEIGHT


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
    next_positions: list[tuple[int, int]] = []
    monkeypatch.setattr(pyxel, "rect", lambda *args: None)
    monkeypatch.setattr(pyxel, "rectb", lambda *args: None)
    monkeypatch.setattr(
        pyxel,
        "text",
        lambda x, y, text, *args: calls.append((x, y, text)),
    )
    monkeypatch.setattr(app, "_blt_tile", lambda *args: None)
    monkeypatch.setattr(
        app,
        "_draw_next_block",
        lambda _block, *, x, y: next_positions.append((x, y)),
    )

    app._draw_mobile_status()

    score = next(call for call in calls if call[2].startswith("SCORE"))
    combo = next(call for call in calls if call[2].startswith("COMBO"))
    left_labels = {
        text: x
        for x, _, text in calls
        if text.startswith(("TURN", "SCORE")) or text in {"DORA", "NEXT"}
    }
    labels = {text for _, _, text in calls}
    assert score[1] == combo[1]
    assert set(left_labels.values()) == {PORTRAIT_PANEL_X + 5}
    assert next_positions == [
        (PORTRAIT_PANEL_X + 27 + index * 39, 199)
        for index in range(3)
    ]
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
    assert navigation[2] == "←→:ページ  START・B:閉じる"
    assert navigation[1] + japanese_font_height < inner_frame_bottom


def test_portrait_river_navigation_is_centered_above_inner_frame(
    monkeypatch,
) -> None:
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

    app._draw_river_overlay()

    navigation = next(call for call in calls if call[2] == "BACK・Bで閉じる")
    navigation_width = app._japanese_text_width(navigation[2])
    inner_frame_bottom = 11 + 234 - 1
    japanese_font_height = 10
    assert navigation[0] == (app.screen_width - navigation_width) // 2
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


def test_notice_text_stays_inside_inner_frame_in_both_layouts(
    monkeypatch,
) -> None:
    class FixedWidthFont:
        @staticmethod
        def text_width(text: str) -> int:
            return len(text) * 5

    monkeypatch.setattr(pyxel, "rect", lambda *args: None)

    for layout in LayoutMode:
        app = MahjongPuzzleApp(seed=20260724, layout=layout)
        app._japanese_font = FixedWidthFont()
        app.ui = UiState(screen=ScreenMode.GAME)
        app.ui.queue_notifications(
            (
                Notice(
                    kind=NoticeKind.WIN,
                    title="8行目 和了！",
                    lines=(
                        "基本 +100",
                        "役 SEQ+CHI +1400",
                        "ドラ 10 +1000・合計 +2500",
                    ),
                ),
            ),
            game_over=False,
        )
        frame_calls: list[tuple[int, int, int, int]] = []
        text_calls: list[tuple[int, int, str]] = []
        monkeypatch.setattr(
            pyxel,
            "rectb",
            lambda x, y, width, height, *args: frame_calls.append(
                (x, y, width, height)
            ),
        )
        monkeypatch.setattr(
            pyxel,
            "text",
            lambda x, y, text, *args: text_calls.append((x, y, text)),
        )

        app._draw_notice()

        inner_x, inner_y, inner_width, inner_height = frame_calls[-1]
        inner_right = inner_x + inner_width - 1
        inner_bottom = inner_y + inner_height - 1
        japanese_font_height = 10
        assert all(
            inner_x < text_x
            and text_x + app._japanese_text_width(text) - 1 < inner_right
            and inner_y < text_y
            and text_y + japanese_font_height - 1 < inner_bottom
            for text_x, text_y, text in text_calls
        )


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
    shuffle_calls: list[tuple[int, int]] = []
    bgm_calls: list[tuple[int, bool]] = []
    monkeypatch.setattr(
        pyxel,
        "play",
        lambda channel, sound, *args, **kwargs: shuffle_calls.append(
            (channel, sound)
        ),
    )
    monkeypatch.setattr(
        pyxel,
        "playm",
        lambda music, *args, **kwargs: bgm_calls.append(
            (music, kwargs.get("loop", False))
        ),
    )
    monkeypatch.setattr(pyxel, "stop", lambda *args: None)

    app.update()

    assert app.ui.screen is ScreenMode.PREPARING
    assert app.preparation_frames_remaining == PREPARATION_DURATION_FRAMES
    assert len(shuffle_calls) == 2

    pressed.clear()
    for _ in range(PREPARATION_DURATION_FRAMES):
        app.update()

    assert app.ui.screen is ScreenMode.GAME
    assert bgm_calls == [(0, True)]

    original_x = app.game.active_x
    pressed.add(pyxel.GAMEPAD1_BUTTON_DPAD_LEFT)

    app.update()

    assert app.game.active_x == original_x - 1


def test_gamepad_a_places_active_block(monkeypatch) -> None:
    app = MahjongPuzzleApp(seed=20260725)
    app.ui = UiState(screen=ScreenMode.GAME)
    played_channels: list[int] = []
    monkeypatch.setattr(
        pyxel,
        "btnp",
        lambda key: key == pyxel.GAMEPAD1_BUTTON_A,
    )
    monkeypatch.setattr(
        pyxel,
        "play",
        lambda channel, *args, **kwargs: played_channels.append(channel),
    )

    app.update()

    assert app.game.turn == 1
    assert played_channels
    assert set(played_channels) <= EFFECT_CHANNELS


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


def test_place_button_toggles_bgm_without_closing_river(monkeypatch) -> None:
    app = MahjongPuzzleApp(seed=20260725)
    app.ui = UiState(screen=ScreenMode.GAME)
    app._bgm_playing = True
    app.ui.open_overlay(ScreenMode.RIVER)
    pressed = {pyxel.GAMEPAD1_BUTTON_A}
    monkeypatch.setattr(pyxel, "btnp", lambda key: key in pressed)
    stopped: list[int] = []
    started: list[tuple[int, bool]] = []
    monkeypatch.setattr(pyxel, "stop", lambda channel: stopped.append(channel))
    monkeypatch.setattr(
        pyxel,
        "playm",
        lambda music, *args, **kwargs: started.append(
            (music, kwargs.get("loop", False))
        ),
    )

    app.update()

    assert app.ui.screen is ScreenMode.RIVER
    assert app.bgm_muted
    assert stopped == [BGM_CHANNEL]

    app.update()

    assert app.ui.screen is ScreenMode.RIVER
    assert not app.bgm_muted
    assert started == [(0, True)]


def test_river_draws_bgm_control_in_both_layouts(monkeypatch) -> None:
    for layout, expected in (
        (LayoutMode.LANDSCAPE, "SPACE/A:BGM ON"),
        (LayoutMode.PORTRAIT, "A:BGM ON"),
    ):
        app = MahjongPuzzleApp(seed=20260725, layout=layout)
        app._japanese_font = object()
        texts: list[str] = []
        monkeypatch.setattr(pyxel, "cls", lambda *args: None)
        monkeypatch.setattr(pyxel, "rect", lambda *args: None)
        monkeypatch.setattr(pyxel, "rectb", lambda *args: None)
        monkeypatch.setattr(
            pyxel,
            "text",
            lambda _x, _y, text, *args: texts.append(text),
        )

        app._draw_river_overlay()

        assert expected in texts


def test_gamepad_a_restarts_from_result(monkeypatch) -> None:
    app = MahjongPuzzleApp(seed=20260725)
    app.ui = UiState(screen=ScreenMode.RESULT)
    previous_session = app.session
    monkeypatch.setattr(
        pyxel,
        "btnp",
        lambda key: key == pyxel.GAMEPAD1_BUTTON_A,
    )
    monkeypatch.setattr(pyxel, "play", lambda *args, **kwargs: None)
    monkeypatch.setattr(pyxel, "stop", lambda *args: None)

    app.update()

    assert app.ui.screen is ScreenMode.PREPARING
    assert app.preparation_is_restart
    assert app.session is not previous_session


def test_restart_preparation_draws_clear_transition_message(
    monkeypatch,
) -> None:
    app = MahjongPuzzleApp(seed=20260725)
    app._japanese_font = object()
    app.ui = UiState(screen=ScreenMode.RESULT)
    monkeypatch.setattr(pyxel, "play", lambda *args, **kwargs: None)
    monkeypatch.setattr(pyxel, "stop", lambda *args: None)
    app._begin_game_preparation(restart=True)
    texts: list[str] = []
    monkeypatch.setattr(pyxel, "cls", lambda *args: None)
    monkeypatch.setattr(pyxel, "rect", lambda *args: None)
    monkeypatch.setattr(pyxel, "rectb", lambda *args: None)
    monkeypatch.setattr(
        pyxel,
        "text",
        lambda _x, _y, text, *args: texts.append(text),
    )

    app.draw()

    assert "雀卓清掃中" in texts
    assert "新しい対局へ切り替えます" in texts


def test_help_toggles_bgm_without_assigning_gamepad_y(monkeypatch) -> None:
    app = MahjongPuzzleApp(seed=20260725)
    app.ui = UiState(screen=ScreenMode.GAME)
    app._bgm_playing = True
    app._open_help()
    monkeypatch.setattr(pyxel, "btnp", lambda key: key == pyxel.KEY_M)
    stopped: list[int] = []
    started: list[tuple[int, bool]] = []
    monkeypatch.setattr(pyxel, "stop", lambda channel: stopped.append(channel))
    monkeypatch.setattr(
        pyxel,
        "playm",
        lambda music, *args, **kwargs: started.append(
            (music, kwargs.get("loop", False))
        ),
    )

    app.update()

    assert app.bgm_muted
    assert stopped == [BGM_CHANNEL]

    app.update()

    assert not app.bgm_muted
    assert started == [(0, True)]
    assert pyxel.GAMEPAD1_BUTTON_Y not in CONTROL_BINDINGS[
        ControlAction.TOGGLE_BGM
    ]


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
    assert screenshot[3:5] == (BOARD_ORIGIN_X, BOARD_ORIGIN_Y)
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
