"""牌位置ごと回転する7種類のテトリミノと7バッグ生成。"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from mahjong_puzzle.board import Coordinate
from mahjong_puzzle.tiles import Tile


class TetrominoKind(str, Enum):
    """MVPで使用する7種類のテトリミノ。"""

    I = "I"
    O = "O"
    T = "T"
    S = "S"
    Z = "Z"
    J = "J"
    L = "L"


_BASE_COORDINATES: dict[TetrominoKind, tuple[tuple[int, int], ...]] = {
    TetrominoKind.I: ((0, 0), (1, 0), (2, 0), (3, 0)),
    TetrominoKind.O: ((0, 0), (1, 0), (0, 1), (1, 1)),
    TetrominoKind.T: ((0, 0), (1, 0), (2, 0), (1, 1)),
    TetrominoKind.S: ((1, 0), (2, 0), (0, 1), (1, 1)),
    TetrominoKind.Z: ((0, 0), (1, 0), (1, 1), (2, 1)),
    TetrominoKind.J: ((0, 0), (0, 1), (1, 1), (2, 1)),
    TetrominoKind.L: ((2, 0), (0, 1), (1, 1), (2, 1)),
}


@dataclass(frozen=True)
class BlockCell:
    """テトリミノ原点からの相対座標と物理牌。"""

    x: int
    y: int
    tile: Tile


@dataclass(frozen=True)
class PositionedCell:
    """盤面上へ移したテトリミノの1マス。"""

    coordinate: Coordinate
    tile: Tile


@dataclass(frozen=True)
class Tetromino:
    """形と4枚の物理牌を一体として回転するブロック。"""

    block_id: int
    kind: TetrominoKind
    tiles: tuple[Tile, Tile, Tile, Tile]
    rotation: int = 0

    def __post_init__(self) -> None:
        if (
            not isinstance(self.block_id, int)
            or isinstance(self.block_id, bool)
            or self.block_id < 1
        ):
            raise ValueError("block_idは1以上の整数でなければなりません")
        if not isinstance(self.kind, TetrominoKind):
            raise TypeError("kindにはTetrominoKindが必要です")
        if len(self.tiles) != 4 or not all(
            isinstance(tile, Tile) for tile in self.tiles
        ):
            raise ValueError("テトリミノには4枚のTile個体が必要です")
        ids = [tile.tile_id for tile in self.tiles]
        if len(ids) != len(set(ids)):
            raise ValueError("テトリミノの牌個体IDが重複しています")
        if (
            not isinstance(self.rotation, int)
            or isinstance(self.rotation, bool)
            or not 0 <= self.rotation < 4
        ):
            raise ValueError("rotationは0から3でなければなりません")

    @property
    def cells(self) -> tuple[BlockCell, ...]:
        """現在の回転状態における牌付き相対セルを返す。"""

        coordinates = list(_BASE_COORDINATES[self.kind])
        for _ in range(self.rotation):
            coordinates = [(-y, x) for x, y in coordinates]
            min_x = min(x for x, _ in coordinates)
            min_y = min(y for _, y in coordinates)
            coordinates = [(x - min_x, y - min_y) for x, y in coordinates]
        return tuple(
            BlockCell(x=x, y=y, tile=tile)
            for (x, y), tile in zip(coordinates, self.tiles, strict=True)
        )

    @property
    def width(self) -> int:
        return max(cell.x for cell in self.cells) + 1

    @property
    def height(self) -> int:
        return max(cell.y for cell in self.cells) + 1

    def with_rotation(self, rotation: int) -> Tetromino:
        """指定した90度単位の回転状態を返す。"""

        if not isinstance(rotation, int) or isinstance(rotation, bool):
            raise ValueError("rotationは整数でなければなりません")
        return Tetromino(
            block_id=self.block_id,
            kind=self.kind,
            tiles=self.tiles,
            rotation=rotation % 4,
        )

    def rotated(self, *, clockwise: bool) -> Tetromino:
        """牌の位置を形と一緒に90度回転する。"""

        delta = 1 if clockwise else -1
        return self.with_rotation(self.rotation + delta)

    def positioned_cells(
        self, *, origin_x: int, origin_y: int
    ) -> tuple[PositionedCell, ...]:
        """原点を盤面座標へ移した4セルを返す。"""

        if any(
            not isinstance(value, int) or isinstance(value, bool)
            for value in (origin_x, origin_y)
        ):
            raise ValueError("配置原点は整数でなければなりません")
        return tuple(
            PositionedCell(
                coordinate=Coordinate(origin_x + cell.x, origin_y + cell.y),
                tile=cell.tile,
            )
            for cell in self.cells
        )

    def fits(
        self,
        *,
        origin_x: int,
        origin_y: int,
        board_width: int,
        board_height: int,
    ) -> bool:
        """全4セルが指定サイズ内に収まるかを返す。"""

        return all(
            0 <= cell.coordinate.x < board_width
            and 0 <= cell.coordinate.y < board_height
            for cell in self.positioned_cells(origin_x=origin_x, origin_y=origin_y)
        )


def create_seven_bag_sequence(
    count: int, rng: random.Random
) -> tuple[TetrominoKind, ...]:
    """各7種を1回ずつ含むバッグをシャッフルして必要数返す。"""

    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        raise ValueError("ブロック数は0以上の整数でなければなりません")
    if not isinstance(rng, random.Random):
        raise TypeError("rngにはrandom.Randomが必要です")

    result: list[TetrominoKind] = []
    while len(result) < count:
        bag = list(TetrominoKind)
        rng.shuffle(bag)
        result.extend(bag)
    return tuple(result[:count])


def create_tetrominoes(
    tiles: Iterable[Tile], rng: random.Random
) -> tuple[Tetromino, ...]:
    """4枚ずつの物理牌へ7バッグの形を割り当てる。"""

    materialized = tuple(tiles)
    if len(materialized) % 4 != 0:
        raise ValueError("配置ブロック用の牌数は4の倍数でなければなりません")
    if not all(isinstance(tile, Tile) for tile in materialized):
        raise TypeError("配置ブロックにはTile個体が必要です")
    ids = [tile.tile_id for tile in materialized]
    if len(ids) != len(set(ids)):
        raise ValueError("配置ブロック用の牌個体IDが重複しています")
    block_count = len(materialized) // 4
    kinds = create_seven_bag_sequence(block_count, rng)
    return tuple(
        Tetromino(
            block_id=index + 1,
            kind=kinds[index],
            tiles=materialized[index * 4 : index * 4 + 4],
        )
        for index in range(block_count)
    )
