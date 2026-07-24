"""盤面から上書きされた牌の全履歴。"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable

from mahjong_puzzle.board import Coordinate
from mahjong_puzzle.tiles import Tile, TileType


@dataclass(frozen=True)
class DiscardRecord:
    """捨てられた牌、ターン、元座標、配置ID。"""

    tile: Tile
    turn: int
    coordinate: Coordinate
    placement_id: int

    def __post_init__(self) -> None:
        if not isinstance(self.tile, Tile):
            raise TypeError("捨て牌にはTile個体が必要です")
        for name, value in (("turn", self.turn), ("placement_id", self.placement_id)):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value < 1
            ):
                raise ValueError(f"{name}は1以上の整数でなければなりません")
        if not isinstance(self.coordinate, Coordinate):
            raise TypeError("元座標にはCoordinateが必要です")


@dataclass
class River:
    """捨て牌を発生順に保持する。"""

    _records: list[DiscardRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        original = tuple(self._records)
        self._records = []
        self.extend(original)

    @property
    def records(self) -> tuple[DiscardRecord, ...]:
        return tuple(self._records)

    @property
    def total_count(self) -> int:
        return len(self._records)

    def extend(self, records: Iterable[DiscardRecord]) -> None:
        """複数の捨て牌記録を入力順のまま追加する。"""

        additions = tuple(records)
        if not all(isinstance(record, DiscardRecord) for record in additions):
            raise TypeError("川にはDiscardRecordだけを追加できます")
        existing_ids = {record.tile.tile_id for record in self._records}
        new_ids = [record.tile.tile_id for record in additions]
        if len(new_ids) != len(set(new_ids)) or existing_ids & set(new_ids):
            raise ValueError("川で同じ牌個体IDを複数回記録できません")
        self._records.extend(additions)

    def recent(self, count: int) -> tuple[DiscardRecord, ...]:
        """直近の指定件数を古い順で返す。"""

        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            raise ValueError("取得件数は0以上の整数でなければなりません")
        if count == 0:
            return ()
        return tuple(self._records[-count:])

    def counts_by_kind(self) -> Counter[TileType]:
        """川の牌種別枚数を返す。"""

        return Counter(record.tile.kind for record in self._records)
