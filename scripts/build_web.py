"""Pyxel Web Launcher向けの最小pyxappを生成する。"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_PACKAGE = PROJECT_ROOT / "src" / "mahjong_puzzle"
WEB_ENTRY = PROJECT_ROOT / "src" / "web_main.py"
OUTPUT_DIR = PROJECT_ROOT / "web"
OUTPUT_APP = OUTPUT_DIR / "mahjong-puzzle.pyxapp"


def main() -> None:
    """実行コードだけを一時領域へ集め、pyxappとして出力する。"""

    with tempfile.TemporaryDirectory(prefix="mahjong-puzzle-web-") as temp:
        app_dir = Path(temp) / "mahjong-puzzle"
        shutil.copytree(
            SOURCE_PACKAGE,
            app_dir / "mahjong_puzzle",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "sample.py"),
        )
        shutil.copy2(WEB_ENTRY, app_dir / "web_main.py")

        subprocess.run(
            [
                sys.executable,
                "-m",
                "pyxel",
                "package",
                str(app_dir),
                str(app_dir / "web_main.py"),
            ],
            cwd=PROJECT_ROOT,
            check=True,
        )

    generated = PROJECT_ROOT / "mahjong-puzzle.pyxapp"
    if not generated.is_file():
        raise RuntimeError("Pyxelアプリが生成されませんでした")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    generated.replace(OUTPUT_APP)
    print(f"generated: {OUTPUT_APP.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
