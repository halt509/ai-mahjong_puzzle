from pathlib import Path
from zipfile import ZipFile


PROJECT_ROOT = Path(__file__).parents[1]
WEB_APP = PROJECT_ROOT / "web" / "mahjong-puzzle.pyxapp"


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
