import json

import pytest

from mahjong_puzzle.persistence import HighScoreError, HighScoreStore


def test_missing_high_score_file_loads_as_zero(tmp_path) -> None:
    store = HighScoreStore(tmp_path / "score.json")

    assert store.load() == 0


def test_only_a_higher_score_is_saved(tmp_path) -> None:
    path = tmp_path / "nested" / "score.json"
    store = HighScoreStore(path)

    assert store.record(1200) == 1200
    assert store.record(900) == 1200
    assert store.record(1500) == 1500
    assert json.loads(path.read_text(encoding="utf-8")) == {"high_score": 1500}


def test_corrupt_high_score_file_raises_explicit_error(tmp_path) -> None:
    path = tmp_path / "score.json"
    path.write_text("{broken", encoding="utf-8")

    with pytest.raises(HighScoreError, match="読み込めません"):
        HighScoreStore(path).load()


@pytest.mark.parametrize("score", [-1, True, 1.5])
def test_invalid_score_is_rejected(tmp_path, score: object) -> None:
    with pytest.raises(ValueError, match="0以上の整数"):
        HighScoreStore(tmp_path / "score.json").record(score)  # type: ignore[arg-type]
