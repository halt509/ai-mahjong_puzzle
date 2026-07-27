import pytest

from mahjong_puzzle.tutorial import TUTORIAL_PAGES, TutorialState


def test_tutorial_has_four_short_shared_pages() -> None:
    assert len(TUTORIAL_PAGES) == 4
    assert all(page.title for page in TUTORIAL_PAGES)
    assert all(1 <= len(page.lines) <= 4 for page in TUTORIAL_PAGES)


def test_tutorial_covers_required_beginner_rules() -> None:
    text = "\n".join(
        line
        for page in TUTORIAL_PAGES
        for line in (page.title, *page.lines)
    )

    for required in ("基本和了", "新しい役", "カン", "ドラ", "川", "17"):
        assert required in text


def test_tutorial_state_moves_without_leaving_page_range() -> None:
    tutorial = TutorialState()

    assert tutorial.page_index == 0
    assert not tutorial.previous_page()
    assert tutorial.next_page()
    assert tutorial.page_index == 1

    tutorial.page_index = len(TUTORIAL_PAGES) - 1
    assert not tutorial.next_page()
    assert tutorial.page_index == len(TUTORIAL_PAGES) - 1


def test_tutorial_rejects_invalid_page_index() -> None:
    with pytest.raises(ValueError, match="page_index"):
        TutorialState(page_index=len(TUTORIAL_PAGES))
