"""1行8牌のカン候補と新規カン判定。"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from mahjong_puzzle.tiles import TileLike, TileType, normalize_tile_types


@dataclass(frozen=True)
class KanCheckResult:
    """現在の4枚候補と、履歴を除いた新規カン。"""

    candidates: frozenset[TileType]
    new_kans: frozenset[TileType]

    @property
    def should_defer_win(self) -> bool:
        """新規カンがあるため、この行の和了を保留すべきか。"""

        return bool(self.new_kans)


def find_kan_candidates(tiles: Iterable[TileLike]) -> frozenset[TileType]:
    """8牌中ちょうど4枚ある全牌種を返す。"""

    kinds = normalize_tile_types(tiles)
    if len(kinds) != 8:
        raise ValueError(f"カン判定には8枚必要です（入力: {len(kinds)}枚）")
    return frozenset(kind for kind, count in Counter(kinds).items() if count == 4)


def check_kans(
    tiles: Iterable[TileLike], completed_kans: Iterable[TileType]
) -> KanCheckResult:
    """行の履歴と比較し、新規カンだけを抽出する純粋関数。"""

    candidates = find_kan_candidates(tiles)
    completed = frozenset(completed_kans)
    if not all(isinstance(kind, TileType) for kind in completed):
        raise TypeError("カン履歴はTileTypeで指定してください")
    return KanCheckResult(candidates=candidates, new_kans=candidates - completed)
