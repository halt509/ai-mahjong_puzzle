from mahjong_puzzle.ui import Notice, NoticeKind, ScreenMode, UiState


def notice(title: str) -> Notice:
    return Notice(kind=NoticeKind.WIN, title=title, lines=("detail",))


def test_ui_starts_at_title_and_enters_game() -> None:
    ui = UiState()

    assert ui.screen is ScreenMode.TITLE
    ui.start_game()
    assert ui.screen is ScreenMode.PREPARING
    ui.finish_preparation()
    assert ui.screen is ScreenMode.GAME


def test_notification_input_dismisses_one_notice_at_a_time() -> None:
    ui = UiState(screen=ScreenMode.GAME)
    first = notice("FIRST")
    second = notice("SECOND")
    ui.queue_notifications((first, second), game_over=False)

    assert ui.current_notice == first
    assert ui.dismiss_notice()
    assert ui.current_notice == second
    assert ui.dismiss_notice()
    assert ui.current_notice is None
    assert ui.screen is ScreenMode.GAME


def test_last_notification_moves_to_result_when_game_is_over() -> None:
    ui = UiState(screen=ScreenMode.GAME)
    ui.queue_notifications((notice("FINAL"),), game_over=True)

    ui.dismiss_notice()

    assert ui.current_notice is None
    assert ui.screen is ScreenMode.RESULT


def test_game_over_without_notification_moves_directly_to_result() -> None:
    ui = UiState(screen=ScreenMode.GAME)

    ui.queue_notifications((), game_over=True)

    assert ui.screen is ScreenMode.RESULT


def test_overlays_open_only_from_game_and_close_back_to_game() -> None:
    ui = UiState(screen=ScreenMode.GAME)

    assert ui.open_overlay(ScreenMode.RIVER)
    assert ui.screen is ScreenMode.RIVER
    ui.close_overlay()
    assert ui.screen is ScreenMode.GAME
    assert ui.open_overlay(ScreenMode.YAKU)


def test_overlay_cannot_open_while_notification_is_visible() -> None:
    ui = UiState(screen=ScreenMode.GAME)
    ui.queue_notifications((notice("WIN"),), game_over=False)

    assert not ui.open_overlay(ScreenMode.RIVER)
    assert ui.screen is ScreenMode.GAME


def test_help_returns_to_screen_that_opened_it() -> None:
    ui = UiState(screen=ScreenMode.RESULT)

    assert ui.open_help()
    assert ui.screen is ScreenMode.HELP
    ui.close_help()

    assert ui.screen is ScreenMode.RESULT


def test_help_cannot_open_over_notice() -> None:
    ui = UiState(screen=ScreenMode.GAME)
    ui.queue_notifications((notice("WIN"),), game_over=False)

    assert not ui.open_help()
    assert ui.screen is ScreenMode.GAME
