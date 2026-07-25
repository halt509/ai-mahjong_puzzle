"""ゲーム内役一覧と日本語ガイドで共有する役説明。"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from mahjong_puzzle.tiles import Honor, Suit, TileType
from mahjong_puzzle.yaku import Yaku


def _suited(suit: Suit, *ranks: int) -> tuple[TileType, ...]:
    return tuple(TileType.suited(suit, rank) for rank in ranks)


def _honors(honor: Honor, count: int) -> tuple[TileType, ...]:
    return tuple(TileType.honor_tile(honor) for _ in range(count))


@dataclass(frozen=True)
class YakuGuideEntry:
    """1役の日本語説明と成立例。"""

    yaku: Yaku
    reading: str
    description: str
    example_tiles: tuple[TileType, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.yaku, Yaku):
            raise TypeError("yakuにはYakuが必要です")
        if not isinstance(self.reading, str) or not self.reading:
            raise ValueError("readingには空でない文字列が必要です")
        if not isinstance(self.description, str) or not self.description:
            raise ValueError("descriptionには空でない文字列が必要です")
        if len(self.example_tiles) != 8 or not all(
            isinstance(tile, TileType) for tile in self.example_tiles
        ):
            raise ValueError("example_tilesには8枚のTileTypeが必要です")


YAKU_GUIDE_ENTRIES = (
    YakuGuideEntry(
        Yaku.ALL_SEQUENCES,
        "ぜんしゅんつ",
        "2つの面子がどちらも順子",
        _suited(Suit.MANZU, 1, 2, 3)
        + _suited(Suit.PINZU, 4, 5, 6)
        + _honors(Honor.EAST, 2),
    ),
    YakuGuideEntry(
        Yaku.ALL_TRIPLETS,
        "ぜんこうつ",
        "2つの面子がどちらも刻子",
        _suited(Suit.MANZU, 1, 1, 1)
        + _suited(Suit.PINZU, 5, 5, 5)
        + _honors(Honor.SOUTH, 2),
    ),
    YakuGuideEntry(
        Yaku.TANYAO,
        "たんやお",
        "8牌すべてが2〜8の数牌",
        _suited(Suit.MANZU, 2, 3, 4)
        + _suited(Suit.PINZU, 5, 6, 7)
        + _suited(Suit.SOUZU, 8, 8),
    ),
    YakuGuideEntry(
        Yaku.IIPEIKOU,
        "いーぺーこー",
        "まったく同じ順子を2組つくる",
        _suited(Suit.MANZU, 2, 3, 4, 2, 3, 4)
        + _suited(Suit.PINZU, 5, 5),
    ),
    YakuGuideEntry(
        Yaku.HONITSU,
        "ほんいつ",
        "1種類の数牌と字牌だけ",
        _suited(Suit.MANZU, 1, 2, 3, 7, 8, 9)
        + _honors(Honor.EAST, 2),
    ),
    YakuGuideEntry(
        Yaku.CHINITSU,
        "ちんいつ",
        "1種類の数牌だけ",
        _suited(Suit.PINZU, 1, 2, 3, 4, 5, 6, 9, 9),
    ),
    YakuGuideEntry(
        Yaku.HONROUTOU,
        "ほんろーとー",
        "8牌すべてが1・9・字牌",
        _suited(Suit.MANZU, 1, 1, 1)
        + _suited(Suit.PINZU, 9, 9, 9)
        + _honors(Honor.NORTH, 2),
    ),
    YakuGuideEntry(
        Yaku.YAKUHAI,
        "やくはい",
        "白・發・中の刻子を含む",
        _honors(Honor.GREEN, 3)
        + _suited(Suit.MANZU, 4, 5, 6)
        + _suited(Suit.PINZU, 9, 9),
    ),
    YakuGuideEntry(
        Yaku.HONOR_PAIR,
        "じはいあたま",
        "字牌の対子を頭にする",
        _suited(Suit.MANZU, 1, 2, 3)
        + _suited(Suit.PINZU, 4, 5, 6)
        + _honors(Honor.WHITE, 2),
    ),
    YakuGuideEntry(
        Yaku.TERMINAL_PAIR,
        "ろーとーあたま",
        "1か9の数牌の対子を頭にする",
        _suited(Suit.MANZU, 2, 3, 4)
        + _suited(Suit.SOUZU, 5, 6, 7)
        + _suited(Suit.PINZU, 9, 9),
    ),
    YakuGuideEntry(
        Yaku.TWO_SUIT_SAME_SEQUENCE,
        "にしょくどうじゅん",
        "別の数牌種で同じ順子を2組",
        _suited(Suit.MANZU, 2, 3, 4)
        + _suited(Suit.PINZU, 2, 3, 4)
        + _honors(Honor.WHITE, 2),
    ),
    YakuGuideEntry(
        Yaku.STEPPED_SEQUENCES,
        "れんぞくしゅんつ",
        "同じ数牌種で1つずれた順子",
        _suited(Suit.MANZU, 2, 3, 4, 3, 4, 5)
        + _honors(Honor.RED, 2),
    ),
    YakuGuideEntry(
        Yaku.THREE_SUITS_USED,
        "さんしょくづかい",
        "萬子・筒子・索子をすべて使う",
        _suited(Suit.MANZU, 1, 2, 3)
        + _suited(Suit.PINZU, 5, 5, 5)
        + _suited(Suit.SOUZU, 7, 7),
    ),
    YakuGuideEntry(
        Yaku.FOUR_PAIRS,
        "よんといつ",
        "4種類の対子でつくる特殊形",
        _suited(Suit.MANZU, 2, 2, 5, 5)
        + _suited(Suit.PINZU, 3, 3)
        + _honors(Honor.WHITE, 2),
    ),
)

YAKU_GUIDE_BY_YAKU: Mapping[Yaku, YakuGuideEntry] = MappingProxyType(
    {entry.yaku: entry for entry in YAKU_GUIDE_ENTRIES}
)
