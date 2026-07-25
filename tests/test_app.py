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
    SIDEBAR_HEIGHT,
    TITLE_INNER_HEIGHT,
    TITLE_INNER_Y,
    TITLE_QUIT_Y,
    TITLE_TEXT_Y,
    ControlAction,
    MahjongPuzzleApp,
    centered_text_x,
    tile_label,
)
from mahjong_puzzle.tetromino import Tetromino, TetrominoKind
from mahjong_puzzle.tiles import Honor, Suit, TileType, create_full_tile_set
from mahjong_puzzle.ui import Notice, NoticeKind, ScreenMode, UiState


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
    assert pyxel.GAMEPAD1_BUTTON_Y in CONTROL_BINDINGS[
        ControlAction.TOGGLE_YAKU
    ]
    assert pyxel.GAMEPAD1_BUTTON_BACK in CONTROL_BINDINGS[
        ControlAction.TOGGLE_RIVER
    ]
    assert pyxel.GAMEPAD1_BUTTON_START in CONTROL_BINDINGS[
        ControlAction.START_GAME
    ]


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
    pressed.add(pyxel.GAMEPAD1_BUTTON_Y)
    app.update()

    assert app.ui.screen is ScreenMode.YAKU


def test_gamepad_start_restarts_from_result(monkeypatch) -> None:
    app = MahjongPuzzleApp(seed=20260725)
    app.ui = UiState(screen=ScreenMode.RESULT)
    previous_session = app.session
    monkeypatch.setattr(
        pyxel,
        "btnp",
        lambda key: key == pyxel.GAMEPAD1_BUTTON_START,
    )

    app.update()

    assert app.ui.screen is ScreenMode.GAME
    assert app.session is not previous_session


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
