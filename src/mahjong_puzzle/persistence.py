"""最高得点と初回説明進捗を独立した保存先へ安全に記録する。"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class HighScoreError(RuntimeError):
    """最高得点ファイルの読み書きに失敗した。"""


class TutorialProgressError(RuntimeError):
    """チュートリアル進捗の読み書きに失敗した。"""


class HighScoreBackend(Protocol):
    """デスクトップとWebで共通利用する最高得点保存境界。"""

    def load(self) -> int: ...

    def record(self, score: int) -> int: ...


class TutorialProgressBackend(Protocol):
    """デスクトップとWebで共通利用する初回説明の保存境界。"""

    def load(self) -> bool: ...

    def mark_seen(self) -> None: ...


class WebStorage(Protocol):
    """Web Storage APIのうち最高得点保存に必要な操作。"""

    def getItem(self, key: str) -> object | None: ...

    def setItem(self, key: str, value: str) -> None: ...


def _validate_score(score: int) -> None:
    if not isinstance(score, int) or isinstance(score, bool) or score < 0:
        raise ValueError("得点は0以上の整数でなければなりません")


def _score_from_payload(payload: object, *, location: str) -> int:
    if not isinstance(payload, dict):
        raise HighScoreError(f"最高得点データが不正です: {location}")
    score = payload.get("high_score")
    if not isinstance(score, int) or isinstance(score, bool) or score < 0:
        raise HighScoreError(f"最高得点データが不正です: {location}")
    return score


def default_high_score_path() -> Path:
    """OS標準に近いユーザーデータ領域の保存先を返す。"""

    local_app_data = os.environ.get("LOCALAPPDATA")
    base = Path(local_app_data) if local_app_data else Path.home() / ".local" / "share"
    return base / "ai_mahjong_puzzle" / "highscore.json"


def default_tutorial_progress_path() -> Path:
    """初回説明の進捗を最高得点と同じユーザーデータ領域へ置く。"""

    return default_high_score_path().with_name("tutorial.json")


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
        return _score_from_payload(payload, location=str(self.path))

    def record(self, score: int) -> int:
        """現在値より高い場合だけ原子的に保存し、最高得点を返す。"""

        _validate_score(score)
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


@dataclass(frozen=True)
class LocalStorageHighScoreStore:
    """ブラウザのlocalStorageへ最高得点だけを保存する。"""

    storage: WebStorage
    key: str = "ai_mahjong_puzzle.high_score"
    storage_error_types: tuple[type[BaseException], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.key, str) or not self.key:
            raise ValueError("localStorageのキーは空でない文字列が必要です")
        if not all(
            isinstance(error_type, type)
            and issubclass(error_type, BaseException)
            for error_type in self.storage_error_types
        ):
            raise TypeError("storage_error_typesには例外型を指定してください")

    def load(self) -> int:
        """保存がなければ0を、あれば検証済みの最高得点を返す。"""

        try:
            raw_value = self.storage.getItem(self.key)
        except self.storage_error_types as error:
            raise HighScoreError("ブラウザの最高得点を読み込めません") from error
        if raw_value is None:
            return 0
        try:
            payload = json.loads(str(raw_value))
        except json.JSONDecodeError as error:
            raise HighScoreError("ブラウザの最高得点データが不正です") from error
        return _score_from_payload(payload, location="ブラウザlocalStorage")

    def record(self, score: int) -> int:
        """現在値より高い場合だけlocalStorageへ保存する。"""

        _validate_score(score)
        current = self.load()
        if score <= current:
            return current
        value = json.dumps({"high_score": score}, ensure_ascii=False)
        try:
            self.storage.setItem(self.key, value)
        except self.storage_error_types as error:
            raise HighScoreError("ブラウザへ最高得点を保存できません") from error
        return score


def _tutorial_seen_from_payload(payload: object, *, location: str) -> bool:
    if not isinstance(payload, dict) or not isinstance(payload.get("seen"), bool):
        raise TutorialProgressError(
            f"チュートリアル進捗データが不正です: {location}"
        )
    return payload["seen"]


@dataclass(frozen=True)
class TutorialProgressStore:
    """初回説明を見たかだけを独立したJSONへ保存する。"""

    path: Path

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", Path(self.path))

    def load(self) -> bool:
        if not self.path.exists():
            return False
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise TutorialProgressError(
                f"チュートリアル進捗を読み込めません: {self.path}"
            ) from error
        return _tutorial_seen_from_payload(payload, location=str(self.path))

    def mark_seen(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(self.path.suffix + ".tmp")
            temporary.write_text(
                json.dumps({"seen": True}, ensure_ascii=False),
                encoding="utf-8",
            )
            temporary.replace(self.path)
        except OSError as error:
            raise TutorialProgressError(
                f"チュートリアル進捗を保存できません: {self.path}"
            ) from error


@dataclass(frozen=True)
class LocalStorageTutorialProgressStore:
    """ブラウザのlocalStorageへ初回説明の進捗を保存する。"""

    storage: WebStorage
    key: str = "ai_mahjong_puzzle.tutorial_seen"
    storage_error_types: tuple[type[BaseException], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.key, str) or not self.key:
            raise ValueError("localStorageのキーは空でない文字列が必要です")
        if not all(
            isinstance(error_type, type)
            and issubclass(error_type, BaseException)
            for error_type in self.storage_error_types
        ):
            raise TypeError("storage_error_typesには例外型を指定してください")

    def load(self) -> bool:
        try:
            raw_value = self.storage.getItem(self.key)
        except self.storage_error_types as error:
            raise TutorialProgressError(
                "ブラウザのチュートリアル進捗を読み込めません"
            ) from error
        if raw_value is None:
            return False
        try:
            payload = json.loads(str(raw_value))
        except json.JSONDecodeError as error:
            raise TutorialProgressError(
                "ブラウザのチュートリアル進捗データが不正です"
            ) from error
        return _tutorial_seen_from_payload(
            payload,
            location="ブラウザlocalStorage",
        )

    def mark_seen(self) -> None:
        value = json.dumps({"seen": True}, ensure_ascii=False)
        try:
            self.storage.setItem(self.key, value)
        except self.storage_error_types as error:
            raise TutorialProgressError(
                "ブラウザへチュートリアル進捗を保存できません"
            ) from error


def create_default_high_score_store(
    *,
    platform: str | None = None,
    web_storage: WebStorage | None = None,
    web_error_types: tuple[type[BaseException], ...] = (),
) -> HighScoreBackend:
    """実行環境に応じてファイルまたはlocalStorage保存を選ぶ。"""

    runtime_platform = sys.platform if platform is None else platform
    if runtime_platform != "emscripten":
        return HighScoreStore(default_high_score_path())

    if web_storage is None:
        try:
            from js import localStorage
            from pyodide.ffi import JsException
        except (ImportError, ModuleNotFoundError) as error:
            raise HighScoreError("ブラウザの保存領域を初期化できません") from error
        web_storage = localStorage
        web_error_types = (JsException,)

    return LocalStorageHighScoreStore(
        web_storage,
        storage_error_types=web_error_types,
    )


def create_default_tutorial_progress_store(
    *,
    platform: str | None = None,
    web_storage: WebStorage | None = None,
    web_error_types: tuple[type[BaseException], ...] = (),
) -> TutorialProgressBackend:
    """実行環境に応じて初回説明のファイルまたはlocalStorage保存を選ぶ。"""

    runtime_platform = sys.platform if platform is None else platform
    if runtime_platform != "emscripten":
        return TutorialProgressStore(default_tutorial_progress_path())

    if web_storage is None:
        try:
            from js import localStorage
            from pyodide.ffi import JsException
        except (ImportError, ModuleNotFoundError) as error:
            raise TutorialProgressError(
                "ブラウザの保存領域を初期化できません"
            ) from error
        web_storage = localStorage
        web_error_types = (JsException,)

    return LocalStorageTutorialProgressStore(
        web_storage,
        storage_error_types=web_error_types,
    )
