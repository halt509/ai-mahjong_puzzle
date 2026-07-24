"""8×8盤面と、牌を上書きする純粋なデータ操作。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from mahjong_puzzle.tiles import Tile

BOARD_WIDTH = 8
BOARD_HEIGHT = 8


@dataclass(frozen=True, order=True)
class Coordinate:
    """盤面上の0始まり座標。"""

    x: int
    y: int

    def __post_init__(self) -> None:
        if (
            not isinstance(self.x, int)
            or isinstance(self.x, bool)
            or not isinstance(self.y, int)
            or isinstance(self.y, bool)
        ):
            raise ValueError("座標は整数でなければなりません")


@dataclass(frozen=True)
class TileReplacement:
    """上書きされた座標と、その前後の物理牌。"""

    coordinate: Coordinate
    old_tile: Tile
    new_tile: Tile


class Board:
    """全64マスが常に物理牌で埋まっている8×8盤面。"""

    def __init__(self, rows: Iterable[Iterable[Tile]]) -> None:
        materialized = tuple(tuple(row) for row in rows)
        if len(materialized) != BOARD_HEIGHT or any(
            len(row) != BOARD_WIDTH for row in materialized
        ):
            raise ValueError(
                f"盤面は{BOARD_WIDTH}×{BOARD_HEIGHT}でなければなりません"
            )
        tiles = tuple(tile for row in materialized for tile in row)
        if not all(isinstance(tile, Tile) for tile in tiles):
            raise TypeError("盤面にはTile個体が必要です")
        tile_ids = [tile.tile_id for tile in tiles]
        if len(tile_ids) != len(set(tile_ids)):
            raise ValueError("盤面で同じ牌個体IDを複数回使用できません")
        self._rows = [list(row) for row in materialized]

    @classmethod
    def from_tiles(cls, tiles: Iterable[Tile]) -> Board:
        """64枚を入力順の行優先で8×8盤面へ配置する。"""

        materialized = tuple(tiles)
        expected = BOARD_WIDTH * BOARD_HEIGHT
        if len(materialized) != expected:
            raise ValueError(f"盤面の初期化には{expected}枚必要です")
        rows = (
            materialized[start : start + BOARD_WIDTH]
            for start in range(0, expected, BOARD_WIDTH)
        )
        return cls(rows)

    @staticmethod
    def contains(coordinate: Coordinate) -> bool:
        """座標が盤面内かを返す。"""

        return (
            0 <= coordinate.x < BOARD_WIDTH
            and 0 <= coordinate.y < BOARD_HEIGHT
        )

    @property
    def rows(self) -> tuple[tuple[Tile, ...], ...]:
        """変更不能な行タプルとして盤面全体を返す。"""

        return tuple(tuple(row) for row in self._rows)

    @property
    def tiles(self) -> tuple[Tile, ...]:
        """行優先順で盤面の64牌を返す。"""

        return tuple(tile for row in self._rows for tile in row)

    def row(self, y: int) -> tuple[Tile, ...]:
        """指定行の8牌を返す。"""

        if not isinstance(y, int) or isinstance(y, bool) or not 0 <= y < BOARD_HEIGHT:
            raise ValueError("行番号が盤面外です")
        return tuple(self._rows[y])

    def tile_at(self, coordinate: Coordinate) -> Tile:
        """指定座標の牌を返す。"""

        if not isinstance(coordinate, Coordinate):
            raise TypeError("座標はCoordinateで指定してください")
        if not self.contains(coordinate):
            raise ValueError(f"座標が盤面外です: ({coordinate.x}, {coordinate.y})")
        return self._rows[coordinate.y][coordinate.x]

    def overwrite(
        self, replacements: Mapping[Coordinate, Tile]
    ) -> tuple[TileReplacement, ...]:
        """指定座標を物理牌で原子的に上書きし、前後の対応を返す。"""

        items = tuple(replacements.items())
        if not items:
            raise ValueError("上書き対象がありません")
        if not all(isinstance(coordinate, Coordinate) for coordinate, _ in items):
            raise TypeError("上書き座標はCoordinateで指定してください")
        outside = [coordinate for coordinate, _ in items if not self.contains(coordinate)]
        if outside:
            coordinate = outside[0]
            raise ValueError(f"座標が盤面外です: ({coordinate.x}, {coordinate.y})")
        incoming = tuple(tile for _, tile in items)
        if not all(isinstance(tile, Tile) for tile in incoming):
            raise TypeError("上書きにはTile個体が必要です")
        incoming_ids = [tile.tile_id for tile in incoming]
        if len(incoming_ids) != len(set(incoming_ids)):
            raise ValueError("上書き牌の個体IDが重複しています")
        board_ids = {tile.tile_id for tile in self.tiles}
        overlap = board_ids & set(incoming_ids)
        if overlap:
            raise ValueError("盤面上に既に存在する牌個体IDは配置できません")

        ordered = tuple(sorted(items, key=lambda item: item[0]))
        result = tuple(
            TileReplacement(
                coordinate=coordinate,
                old_tile=self._rows[coordinate.y][coordinate.x],
                new_tile=tile,
            )
            for coordinate, tile in ordered
        )
        for replacement in result:
            coordinate = replacement.coordinate
            self._rows[coordinate.y][coordinate.x] = replacement.new_tile
        return result
