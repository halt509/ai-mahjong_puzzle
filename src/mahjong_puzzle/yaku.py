"""8牌ルールの初期採用役判定。"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from mahjong_puzzle.hand import (
    FourPairsDecomposition,
    HandDecomposition,
    MeldKind,
    WinningDecomposition,
    enumerate_decompositions,
    find_four_pairs_decomposition,
)
from mahjong_puzzle.tiles import (
    Honor,
    Suit,
    TileLike,
    TileType,
    normalize_tile_types,
)


class Yaku(str, Enum):
    """フェーズ5で認識する14役の内部ID。"""

    ALL_SEQUENCES = "all_sequences"
    ALL_TRIPLETS = "all_triplets"
    TANYAO = "tanyao"
    IIPEIKOU = "iipeikou"
    HONITSU = "honitsu"
    CHINITSU = "chinitsu"
    HONROUTOU = "honroutou"
    YAKUHAI = "yakuhai"
    HONOR_PAIR = "honor_pair"
    TERMINAL_PAIR = "terminal_pair"
    TWO_SUIT_SAME_SEQUENCE = "two_suit_same_sequence"
    STEPPED_SEQUENCES = "stepped_sequences"
    THREE_SUITS_USED = "three_suits_used"
    FOUR_PAIRS = "four_pairs"


YAKU_DISPLAY_NAMES: dict[Yaku, str] = {
    Yaku.ALL_SEQUENCES: "全順子",
    Yaku.ALL_TRIPLETS: "全刻子",
    Yaku.TANYAO: "断么九",
    Yaku.IIPEIKOU: "一盃口",
    Yaku.HONITSU: "混一色",
    Yaku.CHINITSU: "清一色",
    Yaku.HONROUTOU: "混老頭",
    Yaku.YAKUHAI: "役牌",
    Yaku.HONOR_PAIR: "字牌頭",
    Yaku.TERMINAL_PAIR: "老頭頭",
    Yaku.TWO_SUIT_SAME_SEQUENCE: "二色同順",
    Yaku.STEPPED_SEQUENCES: "連続順子",
    Yaku.THREE_SUITS_USED: "三色使い",
    Yaku.FOUR_PAIRS: "四対子",
}

_DRAGONS = {Honor.WHITE, Honor.GREEN, Honor.RED}


@dataclass(frozen=True)
class YakuEvaluation:
    """1つの分解候補と、その候補で成立する役。"""

    decomposition: WinningDecomposition
    yaku: frozenset[Yaku]

    @property
    def is_winning(self) -> bool:
        """基本形に加え1役以上ある場合だけ真になる。"""

        return bool(self.yaku)


def _validate_decomposition_matches(
    kinds: tuple[TileType, ...], decomposition: HandDecomposition
) -> None:
    consumed = [decomposition.pair, decomposition.pair]
    consumed.extend(tile for meld in decomposition.melds for tile in meld.tiles)
    if Counter(consumed) != Counter(kinds):
        raise ValueError("分解候補は入力された8牌と一致しません")


def evaluate_decomposition(
    tiles: Iterable[TileLike], decomposition: HandDecomposition
) -> frozenset[Yaku]:
    """指定した有効分解について成立役を返す。"""

    kinds = normalize_tile_types(tiles)
    if len(kinds) != 8:
        raise ValueError(f"役判定には8枚必要です（入力: {len(kinds)}枚）")
    _validate_decomposition_matches(kinds, decomposition)

    result: set[Yaku] = set()
    meld_kinds = tuple(meld.kind for meld in decomposition.melds)
    if all(kind is MeldKind.SEQUENCE for kind in meld_kinds):
        result.add(Yaku.ALL_SEQUENCES)
    if all(kind is MeldKind.TRIPLET for kind in meld_kinds):
        result.add(Yaku.ALL_TRIPLETS)

    sequence_melds = [
        meld for meld in decomposition.melds if meld.kind is MeldKind.SEQUENCE
    ]
    if len(sequence_melds) == 2 and sequence_melds[0].tiles == sequence_melds[1].tiles:
        result.add(Yaku.IIPEIKOU)
    if len(sequence_melds) == 2:
        first, second = sequence_melds
        first_ranks = tuple(tile.rank for tile in first.tiles)
        second_ranks = tuple(tile.rank for tile in second.tiles)
        first_suit = first.tiles[0].suit
        second_suit = second.tiles[0].suit
        if first_suit is not second_suit and first_ranks == second_ranks:
            result.add(Yaku.TWO_SUIT_SAME_SEQUENCE)
        first_start = first.tiles[0].rank
        second_start = second.tiles[0].rank
        assert first_start is not None and second_start is not None
        if (
            first_suit is second_suit
            and abs(first_start - second_start) == 1
        ):
            result.add(Yaku.STEPPED_SEQUENCES)

    result.update(_evaluate_whole_hand_yaku(kinds))

    if any(
        meld.kind is MeldKind.TRIPLET
        and meld.tiles[0].honor in _DRAGONS
        for meld in decomposition.melds
    ):
        result.add(Yaku.YAKUHAI)

    if decomposition.pair.is_honor:
        result.add(Yaku.HONOR_PAIR)
    elif decomposition.pair.is_terminal:
        result.add(Yaku.TERMINAL_PAIR)

    return frozenset(result)


def _evaluate_whole_hand_yaku(
    kinds: tuple[TileType, ...],
) -> frozenset[Yaku]:
    result: set[Yaku] = set()
    if all(
        tile.is_suited
        and tile.rank is not None
        and 2 <= tile.rank <= 8
        for tile in kinds
    ):
        result.add(Yaku.TANYAO)

    numbered_suits = {tile.suit for tile in kinds if tile.is_suited}
    has_honor = any(tile.is_honor for tile in kinds)
    if len(numbered_suits) == 1:
        if has_honor:
            result.add(Yaku.HONITSU)
        else:
            result.add(Yaku.CHINITSU)

    if all(tile.is_honor or tile.is_terminal for tile in kinds):
        result.add(Yaku.HONROUTOU)

    if numbered_suits == set(Suit):
        result.add(Yaku.THREE_SUITS_USED)
    return frozenset(result)


def evaluate_four_pairs(
    tiles: Iterable[TileLike],
    decomposition: FourPairsDecomposition,
) -> frozenset[Yaku]:
    """四対子と、8牌全体だけを見る複合役を返す。"""

    kinds = normalize_tile_types(tiles)
    if len(kinds) != 8:
        raise ValueError(f"役判定には8枚必要です（入力: {len(kinds)}枚）")
    expected = Counter(
        pair
        for pair in decomposition.pairs
        for _ in range(2)
    )
    if expected != Counter(kinds):
        raise ValueError("四対子分解は入力された8牌と一致しません")
    return frozenset(
        {Yaku.FOUR_PAIRS} | set(_evaluate_whole_hand_yaku(kinds))
    )


def evaluate_hand(tiles: Iterable[TileLike]) -> tuple[YakuEvaluation, ...]:
    """通常形と四対子の全候補を個別に役判定する。

    基本形だが役なしの候補も返し、``YakuEvaluation.is_winning`` で和了可否を
    判別できる。不成立形では空タプルを返す。
    """

    kinds = normalize_tile_types(tiles)
    decompositions = enumerate_decompositions(kinds)
    evaluations = [
        YakuEvaluation(
            decomposition=decomposition,
            yaku=evaluate_decomposition(kinds, decomposition),
        )
        for decomposition in decompositions
    ]
    four_pairs = find_four_pairs_decomposition(kinds)
    if four_pairs is not None:
        evaluations.append(
            YakuEvaluation(
                decomposition=four_pairs,
                yaku=evaluate_four_pairs(kinds, four_pairs),
            )
        )
    return tuple(evaluations)
