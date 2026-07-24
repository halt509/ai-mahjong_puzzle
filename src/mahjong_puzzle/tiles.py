"""牌種、牌個体、および136枚セットの生成。"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from functools import total_ordering
from typing import Iterable, TypeAlias


class Suit(Enum):
    """数牌の種類。"""

    MANZU = "manzu"
    PINZU = "pinzu"
    SOUZU = "souzu"


class Honor(Enum):
    """字牌の種類。"""

    EAST = "east"
    SOUTH = "south"
    WEST = "west"
    NORTH = "north"
    WHITE = "white"
    GREEN = "green"
    RED = "red"


_SUIT_ORDER = {suit: index for index, suit in enumerate(Suit)}
_SUIT_DISPLAY = {
    Suit.MANZU: "萬",
    Suit.PINZU: "筒",
    Suit.SOUZU: "索",
}
_SUIT_CODE = {
    Suit.MANZU: "m",
    Suit.PINZU: "p",
    Suit.SOUZU: "s",
}
_HONOR_ORDER = {honor: index for index, honor in enumerate(Honor)}
_HONOR_DISPLAY = {
    Honor.EAST: "東",
    Honor.SOUTH: "南",
    Honor.WEST: "西",
    Honor.NORTH: "北",
    Honor.WHITE: "白",
    Honor.GREEN: "發",
    Honor.RED: "中",
}
_HONOR_CODE = {
    Honor.EAST: "east",
    Honor.SOUTH: "south",
    Honor.WEST: "west",
    Honor.NORTH: "north",
    Honor.WHITE: "white",
    Honor.GREEN: "green",
    Honor.RED: "red",
}


@total_ordering
@dataclass(frozen=True)
class TileType:
    """個体差を除いた牌種。

    数牌では ``suit`` と ``rank`` を、字牌では ``honor`` を保持する。
    """

    suit: Suit | None = None
    rank: int | None = None
    honor: Honor | None = None

    def __post_init__(self) -> None:
        is_suited = self.suit is not None or self.rank is not None
        is_honor = self.honor is not None
        if is_suited == is_honor:
            raise ValueError("牌種は数牌または字牌のどちらか一方でなければなりません")
        if is_suited:
            if not isinstance(self.suit, Suit):
                raise ValueError("数牌には有効なSuitが必要です")
            if not isinstance(self.rank, int) or isinstance(self.rank, bool) or not 1 <= self.rank <= 9:
                raise ValueError("数牌の数字は1から9でなければなりません")
        elif not isinstance(self.honor, Honor):
            raise ValueError("字牌には有効なHonorが必要です")

    @classmethod
    def suited(cls, suit: Suit, rank: int) -> TileType:
        """数牌の牌種を作る。"""

        return cls(suit=suit, rank=rank)

    @classmethod
    def honor_tile(cls, honor: Honor) -> TileType:
        """字牌の牌種を作る。"""

        return cls(honor=honor)

    @property
    def is_suited(self) -> bool:
        return self.suit is not None

    @property
    def is_honor(self) -> bool:
        return self.honor is not None

    @property
    def is_terminal(self) -> bool:
        return self.is_suited and self.rank in (1, 9)

    @property
    def sort_key(self) -> tuple[int, int]:
        """萬子、筒子、索子、字牌の順になる安定ソートキー。"""

        if self.suit is not None:
            assert self.rank is not None
            return (_SUIT_ORDER[self.suit], self.rank)
        assert self.honor is not None
        return (len(Suit), _HONOR_ORDER[self.honor] + 1)

    @property
    def code(self) -> str:
        """個体IDなどに使うASCIIの安定コード。"""

        if self.suit is not None:
            assert self.rank is not None
            return f"{_SUIT_CODE[self.suit]}{self.rank}"
        assert self.honor is not None
        return _HONOR_CODE[self.honor]

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, TileType):
            return NotImplemented
        return self.sort_key < other.sort_key

    def __str__(self) -> str:
        if self.suit is not None:
            assert self.rank is not None
            return f"{self.rank}{_SUIT_DISPLAY[self.suit]}"
        assert self.honor is not None
        return _HONOR_DISPLAY[self.honor]


@dataclass(frozen=True)
class Tile:
    """136枚の山で個体追跡できる物理牌。"""

    kind: TileType
    copy_index: int
    tile_id: str = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.kind, TileType):
            raise ValueError("kindにはTileTypeが必要です")
        if (
            not isinstance(self.copy_index, int)
            or isinstance(self.copy_index, bool)
            or not 0 <= self.copy_index < 4
        ):
            raise ValueError("copy_indexは0から3でなければなりません")
        object.__setattr__(self, "tile_id", f"{self.kind.code}-{self.copy_index + 1}")

    def __str__(self) -> str:
        return str(self.kind)


TileLike: TypeAlias = Tile | TileType


def all_tile_types() -> tuple[TileType, ...]:
    """通常麻雀の34牌種を安定順で返す。"""

    suited = tuple(TileType.suited(suit, rank) for suit in Suit for rank in range(1, 10))
    honors = tuple(TileType.honor_tile(honor) for honor in Honor)
    return suited + honors


def create_full_tile_set() -> tuple[Tile, ...]:
    """重複しない個体IDを持つ通常麻雀136枚を生成する。"""

    return tuple(Tile(kind=kind, copy_index=index) for kind in all_tile_types() for index in range(4))


def normalize_tile_types(tiles: Iterable[TileLike]) -> tuple[TileType, ...]:
    """牌個体または牌種を検証し、牌種のタプルへ変換する。

    同じ物理牌IDの重複と、同一牌種が5枚以上ある不可能な入力を拒否する。
    """

    materialized = tuple(tiles)
    kinds: list[TileType] = []
    physical_ids: list[str] = []
    for tile in materialized:
        if isinstance(tile, Tile):
            kinds.append(tile.kind)
            physical_ids.append(tile.tile_id)
        elif isinstance(tile, TileType):
            kinds.append(tile)
        else:
            raise TypeError("牌はTileまたはTileTypeで指定してください")

    if len(physical_ids) != len(set(physical_ids)):
        raise ValueError("同じ牌個体IDを複数回使用することはできません")

    overfull = [kind for kind, count in Counter(kinds).items() if count > 4]
    if overfull:
        names = "、".join(str(kind) for kind in sorted(overfull))
        raise ValueError(f"同一牌種は4枚までです: {names}")
    return tuple(kinds)
