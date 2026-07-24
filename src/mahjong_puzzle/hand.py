"""横1行・8牌の3＋3＋2分解。"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from mahjong_puzzle.tiles import TileLike, TileType, normalize_tile_types


class MeldKind(Enum):
    """3枚面子の種類。"""

    SEQUENCE = "sequence"
    TRIPLET = "triplet"


@dataclass(frozen=True)
class Meld:
    """順子または刻子として使う3牌。"""

    kind: MeldKind
    tiles: tuple[TileType, TileType, TileType]

    def __post_init__(self) -> None:
        if not isinstance(self.kind, MeldKind):
            raise ValueError("kindにはMeldKindが必要です")
        if len(self.tiles) != 3:
            raise ValueError("面子は3枚でなければなりません")
        ordered = tuple(sorted(self.tiles))
        object.__setattr__(self, "tiles", ordered)
        if self.kind is MeldKind.TRIPLET:
            if len(set(ordered)) != 1:
                raise ValueError("刻子は同一牌3枚でなければなりません")
            return
        first, second, third = ordered
        if (
            not all(tile.is_suited for tile in ordered)
            or len({tile.suit for tile in ordered}) != 1
            or first.rank is None
            or second.rank is None
            or third.rank is None
            or (second.rank, third.rank) != (first.rank + 1, first.rank + 2)
        ):
            raise ValueError("順子は同種の連続する数牌3枚でなければなりません")

    @property
    def sort_key(self) -> tuple[str, tuple[tuple[int, int], ...]]:
        return (self.kind.value, tuple(tile.sort_key for tile in self.tiles))


@dataclass(frozen=True)
class HandDecomposition:
    """2面子と1対子による8牌の分解結果。"""

    melds: tuple[Meld, Meld]
    pair: TileType

    def __post_init__(self) -> None:
        if len(self.melds) != 2:
            raise ValueError("和了分解には面子が2組必要です")
        object.__setattr__(self, "melds", tuple(sorted(self.melds, key=lambda meld: meld.sort_key)))
        if not isinstance(self.pair, TileType):
            raise ValueError("pairにはTileTypeが必要です")

    @property
    def sort_key(self) -> tuple[
        tuple[int, int], tuple[tuple[str, tuple[tuple[int, int], ...]], ...]
    ]:
        return (self.pair.sort_key, tuple(meld.sort_key for meld in self.melds))


def _sequence_from_first(first: TileType) -> tuple[TileType, TileType, TileType] | None:
    if not first.is_suited or first.rank is None or first.rank > 7:
        return None
    assert first.suit is not None
    return (
        first,
        TileType.suited(first.suit, first.rank + 1),
        TileType.suited(first.suit, first.rank + 2),
    )


def _enumerate_melds(
    counts: Counter[TileType], remaining_melds: int
) -> tuple[tuple[Meld, ...], ...]:
    remaining_count = sum(counts.values())
    if remaining_melds == 0:
        return ((),) if remaining_count == 0 else ()
    if remaining_count != remaining_melds * 3:
        return ()

    first = min(kind for kind, count in counts.items() if count > 0)
    results: list[tuple[Meld, ...]] = []

    if counts[first] >= 3:
        counts[first] -= 3
        triplet = Meld(MeldKind.TRIPLET, (first, first, first))
        results.extend(
            (triplet,) + tail for tail in _enumerate_melds(counts, remaining_melds - 1)
        )
        counts[first] += 3

    sequence_tiles = _sequence_from_first(first)
    if sequence_tiles is not None and all(counts[tile] > 0 for tile in sequence_tiles):
        for tile in sequence_tiles:
            counts[tile] -= 1
        sequence = Meld(MeldKind.SEQUENCE, sequence_tiles)
        results.extend(
            (sequence,) + tail for tail in _enumerate_melds(counts, remaining_melds - 1)
        )
        for tile in sequence_tiles:
            counts[tile] += 1

    return tuple(results)


def enumerate_decompositions(tiles: Iterable[TileLike]) -> tuple[HandDecomposition, ...]:
    """8牌を2面子＋1対子へ分ける全候補を安定順で返す。"""

    kinds = normalize_tile_types(tiles)
    if len(kinds) != 8:
        raise ValueError(f"和了判定には8枚必要です（入力: {len(kinds)}枚）")

    original_counts = Counter(kinds)
    results: set[HandDecomposition] = set()
    for pair in sorted(kind for kind, count in original_counts.items() if count >= 2):
        counts = original_counts.copy()
        counts[pair] -= 2
        for melds in _enumerate_melds(counts, remaining_melds=2):
            results.add(HandDecomposition(melds=(melds[0], melds[1]), pair=pair))
    return tuple(sorted(results, key=lambda decomposition: decomposition.sort_key))
