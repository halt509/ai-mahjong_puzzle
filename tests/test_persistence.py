import json

import pytest

from mahjong_puzzle.persistence import (
    CURRENT_SCORE_UNIT_VERSION,
    HighScoreError,
    HighScoreStore,
    LocalStorageHighScoreStore,
    LocalStorageTutorialProgressStore,
    TutorialProgressError,
    TutorialProgressStore,
    create_default_high_score_store,
    create_default_tutorial_progress_store,
)


class FakeLocalStorage:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.fail_reads = False
        self.fail_writes = False

    def getItem(self, key: str) -> str | None:
        if self.fail_reads:
            raise RuntimeError("read blocked")
        return self.values.get(key)

    def setItem(self, key: str, value: str) -> None:
        if self.fail_writes:
            raise RuntimeError("write blocked")
        self.values[key] = value


def test_missing_high_score_file_loads_as_zero(tmp_path) -> None:
    store = HighScoreStore(tmp_path / "score.json")

    assert store.load() == 0


def test_only_a_higher_score_is_saved(tmp_path) -> None:
    path = tmp_path / "nested" / "score.json"
    store = HighScoreStore(path)

    assert store.record(1200) == 1200
    assert store.record(900) == 1200
    assert store.record(1500) == 1500
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "high_score": 1500,
        "score_unit_version": CURRENT_SCORE_UNIT_VERSION,
    }


def test_legacy_high_score_file_is_migrated_only_once(tmp_path) -> None:
    path = tmp_path / "score.json"
    path.write_text(json.dumps({"high_score": 1200}), encoding="utf-8")
    store = HighScoreStore(path)

    assert store.load() == 12000
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "high_score": 12000,
        "score_unit_version": CURRENT_SCORE_UNIT_VERSION,
    }
    assert store.load() == 12000


def test_current_high_score_file_is_not_migrated(tmp_path) -> None:
    path = tmp_path / "score.json"
    path.write_text(
        json.dumps(
            {
                "high_score": 12000,
                "score_unit_version": CURRENT_SCORE_UNIT_VERSION,
            }
        ),
        encoding="utf-8",
    )

    assert HighScoreStore(path).load() == 12000


def test_corrupt_high_score_file_raises_explicit_error(tmp_path) -> None:
    path = tmp_path / "score.json"
    path.write_text("{broken", encoding="utf-8")

    with pytest.raises(HighScoreError, match="読み込めません"):
        HighScoreStore(path).load()


@pytest.mark.parametrize("score", [-1, True, 1.5])
def test_invalid_score_is_rejected(tmp_path, score: object) -> None:
    with pytest.raises(ValueError, match="0以上の整数"):
        HighScoreStore(tmp_path / "score.json").record(score)  # type: ignore[arg-type]


def test_local_storage_persists_only_the_highest_score() -> None:
    storage = FakeLocalStorage()
    store = LocalStorageHighScoreStore(storage)

    assert store.load() == 0
    assert store.record(1200) == 1200
    assert store.record(900) == 1200
    assert store.record(1500) == 1500
    assert json.loads(storage.values[store.key]) == {
        "high_score": 1500,
        "score_unit_version": CURRENT_SCORE_UNIT_VERSION,
    }


def test_legacy_local_storage_high_score_is_migrated_only_once() -> None:
    storage = FakeLocalStorage()
    store = LocalStorageHighScoreStore(storage)
    storage.values[store.key] = json.dumps({"high_score": 1200})

    assert store.load() == 12000
    assert json.loads(storage.values[store.key]) == {
        "high_score": 12000,
        "score_unit_version": CURRENT_SCORE_UNIT_VERSION,
    }
    assert store.load() == 12000


def test_unknown_score_unit_version_is_rejected() -> None:
    storage = FakeLocalStorage()
    store = LocalStorageHighScoreStore(storage)
    storage.values[store.key] = json.dumps(
        {"high_score": 1200, "score_unit_version": 999}
    )

    with pytest.raises(HighScoreError, match="単位バージョン"):
        store.load()


def test_corrupt_local_storage_raises_explicit_error() -> None:
    storage = FakeLocalStorage()
    store = LocalStorageHighScoreStore(storage)
    storage.values[store.key] = "{broken"

    with pytest.raises(HighScoreError, match="ブラウザ"):
        store.load()


def test_local_storage_access_error_is_not_hidden() -> None:
    storage = FakeLocalStorage()
    storage.fail_reads = True
    store = LocalStorageHighScoreStore(
        storage,
        storage_error_types=(RuntimeError,),
    )

    with pytest.raises(HighScoreError, match="ブラウザ"):
        store.load()


def test_web_runtime_selects_local_storage_backend() -> None:
    storage = FakeLocalStorage()

    store = create_default_high_score_store(
        platform="emscripten",
        web_storage=storage,
        web_error_types=(RuntimeError,),
    )

    assert isinstance(store, LocalStorageHighScoreStore)


def test_missing_tutorial_progress_file_is_unseen(tmp_path) -> None:
    store = TutorialProgressStore(tmp_path / "tutorial.json")

    assert not store.load()


def test_tutorial_progress_file_remembers_completion(tmp_path) -> None:
    path = tmp_path / "nested" / "tutorial.json"
    store = TutorialProgressStore(path)

    store.mark_seen()

    assert store.load()
    assert json.loads(path.read_text(encoding="utf-8")) == {"seen": True}


def test_corrupt_tutorial_progress_file_raises_explicit_error(tmp_path) -> None:
    path = tmp_path / "tutorial.json"
    path.write_text("{broken", encoding="utf-8")

    with pytest.raises(TutorialProgressError, match="読み込めません"):
        TutorialProgressStore(path).load()


def test_local_storage_remembers_tutorial_completion() -> None:
    storage = FakeLocalStorage()
    store = LocalStorageTutorialProgressStore(storage)

    assert not store.load()
    store.mark_seen()

    assert store.load()
    assert json.loads(storage.values[store.key]) == {"seen": True}


def test_web_runtime_selects_tutorial_local_storage_backend() -> None:
    storage = FakeLocalStorage()

    store = create_default_tutorial_progress_store(
        platform="emscripten",
        web_storage=storage,
        web_error_types=(RuntimeError,),
    )

    assert isinstance(store, LocalStorageTutorialProgressStore)
