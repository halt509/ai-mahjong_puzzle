"""ドラ表示牌の循環とドラ枚数計算。"""

from __future__ import annotations

from collections import Counter
from typing import Iterable

from mahjong_puzzle.tiles import Honor, Tile, TileLike, TileType, normalize_tile_types

MAX_DORA_INDICATORS = 4

_WIND_ORDER = (Honor.EAST, Honor.SOUTH, Honor.WEST, Honor.NORTH)
_DRAGON_ORDER = (Honor.WHITE, Honor.GREEN, Honor.RED)


def dora_from_indicator(indicator: TileLike) -> TileType:
    """表示牌1枚から、循環規則に従って実際のドラを返す。"""

    kind = indicator.kind if isinstance(indicator, Tile) else indicator
    if not isinstance(kind, TileType):
        raise TypeError("ドラ表示牌はTileまたはTileTypeで指定してください")
    if kind.is_suited:
        assert kind.suit is not None and kind.rank is not None
        next_rank = 1 if kind.rank == 9 else kind.rank + 1
        return TileType.suited(kind.suit, next_rank)

    assert kind.honor is not None
    cycle = _WIND_ORDER if kind.honor in _WIND_ORDER else _DRAGON_ORDER
    next_index = (cycle.index(kind.honor) + 1) % len(cycle)
    return TileType.honor_tile(cycle[next_index])


def count_dora(
    tiles: Iterable[TileLike], indicators: Iterable[TileLike]
) -> int:
    """8牌に含まれるドラ枚数を数える。

    同一表示牌が複数ある場合は、同じドラを表示牌の枚数分だけ重複加算する。
    """

    kinds = normalize_tile_types(tiles)
    if len(kinds) != 8:
        raise ValueError(f"ドラ計算には8枚必要です（入力: {len(kinds)}枚）")
    indicator_items = tuple(indicators)
    if len(indicator_items) > MAX_DORA_INDICATORS:
        raise ValueError(f"ドラ表示牌は最大{MAX_DORA_INDICATORS}枚です")
    dora_kinds = tuple(dora_from_indicator(indicator) for indicator in indicator_items)
    hand_counts = Counter(kinds)
    return sum(hand_counts[dora] for dora in dora_kinds)
