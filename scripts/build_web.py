"""Pyxel Web Launcher向けの最小pyxappを生成する。"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACKAGE = PROJECT_ROOT / "src" / "mahjong_puzzle"
FONT_ASSETS = PROJECT_ROOT / "assets" / "fonts"
OUTPUT_DIR = PROJECT_ROOT / "web"
WEB_APPS = (
    (
        "mahjong-puzzle",
        PROJECT_ROOT / "src" / "web_main.py",
        OUTPUT_DIR / "mahjong-puzzle.pyxapp",
    ),
    (
        "mahjong-puzzle-mobile",
        PROJECT_ROOT / "src" / "mobile_web_main.py",
        OUTPUT_DIR / "mahjong-puzzle-mobile.pyxapp",
    ),
)


def _build_app(app_name: str, entry: Path, output: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="mahjong-puzzle-web-") as temp:
        app_dir = Path(temp) / app_name
        shutil.copytree(
            SOURCE_PACKAGE,
            app_dir / "mahjong_puzzle",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "sample.py"),
        )
        shutil.copy2(entry, app_dir / entry.name)
        shutil.copytree(FONT_ASSETS, app_dir / "assets" / "fonts")

        subprocess.run(
            [
                sys.executable,
                "-m",
                "pyxel",
                "package",
                str(app_dir),
                str(app_dir / entry.name),
            ],
            cwd=PROJECT_ROOT,
            check=True,
        )

    generated = PROJECT_ROOT / f"{app_name}.pyxapp"
    if not generated.is_file():
        raise RuntimeError("Pyxelアプリが生成されませんでした")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generated.replace(output)
    print(f"generated: {output.relative_to(PROJECT_ROOT)}")


def main() -> None:
    """PC横画面版とスマホ縦画面版のpyxappを出力する。"""

    for app_name, entry, output in WEB_APPS:
        _build_app(app_name, entry, output)


if __name__ == "__main__":
    main()
