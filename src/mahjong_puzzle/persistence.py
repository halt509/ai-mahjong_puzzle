"""ローカルの最高得点をJSONで安全に保存する。"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


class HighScoreError(RuntimeError):
    """最高得点ファイルの読み書きに失敗した。"""


def default_high_score_path() -> Path:
    """OS標準に近いユーザーデータ領域の保存先を返す。"""

    local_app_data = os.environ.get("LOCALAPPDATA")
    base = Path(local_app_data) if local_app_data else Path.home() / ".local" / "share"
    return base / "ai_mahjong_puzzle" / "highscore.json"


@dataclass(frozen=True)
class HighScoreStore:
    path: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", Path(self.path))

    def load(self) -> int:
        """保存がなければ0を、あれば検証済みの最高得点を返す。"""

        if not self.path.exists():
            return 0
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise HighScoreError(f"最高得点を読み込めません: {self.path}") from error
        if not isinstance(payload, dict):
            raise HighScoreError(f"最高得点データが不正です: {self.path}")
        score = payload.get("high_score")
        if not isinstance(score, int) or isinstance(score, bool) or score < 0:
            raise HighScoreError(f"最高得点データが不正です: {self.path}")
        return score

    def record(self, score: int) -> int:
        """現在値より高い場合だけ原子的に保存し、最高得点を返す。"""

        if not isinstance(score, int) or isinstance(score, bool) or score < 0:
            raise ValueError("得点は0以上の整数でなければなりません")
        current = self.load()
        if score <= current:
            return current
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(self.path.suffix + ".tmp")
            temporary.write_text(
                json.dumps({"high_score": score}, ensure_ascii=False),
                encoding="utf-8",
            )
            temporary.replace(self.path)
        except OSError as error:
            raise HighScoreError(f"最高得点を保存できません: {self.path}") from error
        return score
