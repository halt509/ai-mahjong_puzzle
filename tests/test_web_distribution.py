from pathlib import Path
from zipfile import ZipFile


PROJECT_ROOT = Path(__file__).parents[1]
WEB_APP = PROJECT_ROOT / "web" / "mahjong-puzzle.pyxapp"
MOBILE_WEB_APP = PROJECT_ROOT / "web" / "mahjong-puzzle-mobile.pyxapp"
JAPANESE_FONT = PROJECT_ROOT / "assets" / "fonts" / "umplus_j10r.bdf"


def test_web_app_contains_only_runtime_source() -> None:
    assert WEB_APP.is_file()

    with ZipFile(WEB_APP) as archive:
        names = set(archive.namelist())
        startup = archive.read(
            "mahjong-puzzle/.pyxapp_startup_script"
        ).decode("utf-8")

    assert startup == "web_main.py"
    assert "mahjong-puzzle/web_main.py" in names
    assert "mahjong-puzzle/mahjong_puzzle/app.py" in names
    assert not any("egg-info" in name for name in names)
    assert not any(name.endswith("/sample.py") for name in names)
    assert not any(
        name.startswith(("tests/", "docs/", "assets/", ".git/"))
        for name in names
    )


def test_web_app_does_not_include_development_instructions() -> None:
    with ZipFile(WEB_APP) as archive:
        filenames = {Path(name).name for name in archive.namelist()}

    assert "AGENTS.md" not in filenames
    assert "HANDOFF.md" not in filenames


def test_web_app_contains_mobile_gamepad_bindings() -> None:
    with ZipFile(WEB_APP) as archive:
        app_source = archive.read(
            "mahjong-puzzle/mahjong_puzzle/app.py"
        ).decode("utf-8")

    assert "GAMEPAD1_BUTTON_DPAD_LEFT" in app_source
    assert "GAMEPAD1_BUTTON_A" in app_source
    assert "GAMEPAD1_BUTTON_BACK" in app_source


def test_mobile_web_app_uses_portrait_entry_and_runtime_source() -> None:
    assert MOBILE_WEB_APP.is_file()

    with ZipFile(MOBILE_WEB_APP) as archive:
        names = set(archive.namelist())
        startup = archive.read(
            "mahjong-puzzle-mobile/.pyxapp_startup_script"
        ).decode("utf-8")
        entry_source = archive.read(
            "mahjong-puzzle-mobile/mobile_web_main.py"
        ).decode("utf-8")

    assert startup == "mobile_web_main.py"
    assert "LayoutMode.PORTRAIT" in entry_source
    assert "mahjong-puzzle-mobile/mahjong_puzzle/app.py" in names
    assert not any(
        name.startswith(("tests/", "docs/", "assets/", ".git/"))
        for name in names
    )


def test_japanese_font_is_in_source_and_both_web_apps() -> None:
    assert JAPANESE_FONT.is_file()

    for web_app, root in (
        (WEB_APP, "mahjong-puzzle"),
        (MOBILE_WEB_APP, "mahjong-puzzle-mobile"),
    ):
        with ZipFile(web_app) as archive:
            names = set(archive.namelist())
        assert f"{root}/assets/fonts/umplus_j10r.bdf" in names
        assert f"{root}/assets/fonts/README.md" in names
