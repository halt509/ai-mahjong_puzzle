"""フェーズ6の初心者向け説明文とページ状態。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TutorialPage:
    """PC・スマートフォンで共有する説明1ページ。"""

    title: str
    lines: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.title, str) or not self.title:
            raise ValueError("titleには空でない文字列が必要です")
        if not 1 <= len(self.lines) <= 4:
            raise ValueError("linesには1〜4行が必要です")
        if not all(isinstance(line, str) and line for line in self.lines):
            raise ValueError("説明行には空でない文字列が必要です")


TUTORIAL_PAGES = (
    TutorialPage(
        title="牌を置いてみよう",
        lines=(
            "黄色い4牌が置かれる場所",
        ),
    ),
    TutorialPage(
        title="横一列で基本和了",
        lines=(
            "横8牌を3＋3＋2の形にする",
            "または同じ牌2枚を4組そろえる",
            "初回の基本和了は500点",
        ),
    ),
    TutorialPage(
        title="役を作って追加点",
        lines=(
            "役ができると追加点を獲得",
            "同じ行の再和了には新しい役が必要",
            "役一覧で条件を確認できる",
        ),
    ),
    TutorialPage(
        title="カン・ドラ・川",
        lines=(
            "同じ牌4枚でカン",
            "カンするとドラ表示が増える",
            "ドラだけでは和了できない",
            "川を確認・17個で終了",
        ),
    ),
)


@dataclass
class TutorialState:
    """説明ページの範囲を保証する小さな状態。"""

    page_index: int = 0
    initial: bool = False

    def __post_init__(self) -> None:
        if (
            not isinstance(self.page_index, int)
            or isinstance(self.page_index, bool)
            or not 0 <= self.page_index < len(TUTORIAL_PAGES)
        ):
            raise ValueError("page_indexが説明ページの範囲外です")
        if not isinstance(self.initial, bool):
            raise TypeError("initialにはboolが必要です")

    @property
    def page(self) -> TutorialPage:
        return TUTORIAL_PAGES[self.page_index]

    def next_page(self) -> bool:
        """次へ進み、末尾ならFalseを返す。"""

        if self.page_index >= len(TUTORIAL_PAGES) - 1:
            return False
        self.page_index += 1
        return True

    def previous_page(self) -> bool:
        """前へ戻り、先頭ならFalseを返す。"""

        if self.page_index <= 0:
            return False
        self.page_index -= 1
        return True
