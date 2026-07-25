from mahjong_puzzle.yaku import Yaku, evaluate_hand
from mahjong_puzzle.yaku_catalog import YAKU_GUIDE_ENTRIES


def test_catalog_covers_every_yaku_once() -> None:
    catalog_yaku = [entry.yaku for entry in YAKU_GUIDE_ENTRIES]

    assert len(catalog_yaku) == len(Yaku)
    assert set(catalog_yaku) == set(Yaku)


def test_catalog_examples_match_the_current_rule_engine() -> None:
    for entry in YAKU_GUIDE_ENTRIES:
        assert len(entry.example_tiles) == 8
        assert any(
            entry.yaku in evaluation.yaku
            for evaluation in evaluate_hand(entry.example_tiles)
        ), entry.yaku


def test_catalog_has_japanese_readings_and_descriptions() -> None:
    for entry in YAKU_GUIDE_ENTRIES:
        assert entry.reading
        assert entry.description
