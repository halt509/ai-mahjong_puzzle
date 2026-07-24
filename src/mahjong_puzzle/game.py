"""フェーズ2の盤面、配置、川、ターン進行をまとめるゲーム状態。"""

from __future__ import annotations

import random
from dataclasses import dataclass

from mahjong_puzzle.board import (
    BOARD_HEIGHT,
    BOARD_WIDTH,
    Board,
)
from mahjong_puzzle.river import DiscardRecord, River
from mahjong_puzzle.tetromino import (
    PositionedCell,
    Tetromino,
    TetrominoKind,
    create_tetrominoes,
)
from mahjong_puzzle.tiles import Tile, create_full_tile_set

BOARD_TILE_COUNT = BOARD_WIDTH * BOARD_HEIGHT
DORA_RESERVE_COUNT = 4
BLOCK_TILE_COUNT = 68
BLOCK_COUNT = BLOCK_TILE_COUNT // 4
TOTAL_TURN_COUNT = BLOCK_COUNT
NEXT_BLOCK_DISPLAY_COUNT = 3
TOTAL_TILE_COUNT = BOARD_TILE_COUNT + DORA_RESERVE_COUNT + BLOCK_TILE_COUNT


@dataclass(frozen=True)
class PlacementResult:
    """1回の配置による盤面変更と川記録。"""

    turn: int
    placement_id: int
    kind: TetrominoKind
    placed_cells: tuple[PositionedCell, ...]
    discards: tuple[DiscardRecord, ...]
    changed_rows: tuple[int, ...]
    is_game_over: bool


@dataclass
class GameState:
    """Pyxelに依存しないフェーズ2のゲーム進行状態。"""

    board: Board
    dora_indicator_tiles: tuple[Tile, ...]
    blocks: tuple[Tetromino, ...]
    river: River
    turn: int = 0
    active_index: int = 0
    active_x: int = 0
    active_y: int = 0
    active_rotation: int = 0
    next_display_count: int = NEXT_BLOCK_DISPLAY_COUNT

    def __post_init__(self) -> None:
        if not isinstance(self.board, Board):
            raise TypeError("boardにはBoardが必要です")
        if len(self.dora_indicator_tiles) != DORA_RESERVE_COUNT:
            raise ValueError(f"ドラ表示牌用の予約は{DORA_RESERVE_COUNT}枚必要です")
        if not all(isinstance(tile, Tile) for tile in self.dora_indicator_tiles):
            raise TypeError("ドラ表示牌用の予約にはTile個体が必要です")
        if len(self.blocks) != BLOCK_COUNT:
            raise ValueError(f"配置ブロックは{BLOCK_COUNT}個必要です")
        if not all(isinstance(block, Tetromino) for block in self.blocks):
            raise TypeError("配置ブロックにはTetrominoが必要です")
        block_ids = [block.block_id for block in self.blocks]
        if len(block_ids) != len(set(block_ids)):
            raise ValueError("配置ブロックのblock_idが重複しています")
        if not isinstance(self.river, River):
            raise TypeError("riverにはRiverが必要です")
        for name, value in (
            ("turn", self.turn),
            ("active_index", self.active_index),
            ("active_x", self.active_x),
            ("active_y", self.active_y),
            ("active_rotation", self.active_rotation),
            ("next_display_count", self.next_display_count),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{name}は0以上の整数でなければなりません")
        self._validate_progress()
        self.validate_tile_conservation()
        if not self.is_game_over:
            current = self.current_block
            assert current is not None
            if not current.fits(
                origin_x=self.active_x,
                origin_y=self.active_y,
                board_width=BOARD_WIDTH,
                board_height=BOARD_HEIGHT,
            ):
                raise ValueError("現在ブロックの位置が盤面外です")

    @classmethod
    def new(cls, *, seed: int | None = None) -> GameState:
        """136枚を64＋4＋68へ配分し、再現可能な新規ゲームを作る。"""

        if seed is not None and (
            not isinstance(seed, int) or isinstance(seed, bool)
        ):
            raise ValueError("seedは整数またはNoneでなければなりません")
        rng = random.Random(seed)
        tiles = list(create_full_tile_set())
        rng.shuffle(tiles)
        board_end = BOARD_TILE_COUNT
        dora_end = board_end + DORA_RESERVE_COUNT
        board = Board.from_tiles(tiles[:board_end])
        dora_tiles = tuple(tiles[board_end:dora_end])
        blocks = create_tetrominoes(tiles[dora_end:], rng)
        game = cls(
            board=board,
            dora_indicator_tiles=dora_tiles,
            blocks=blocks,
            river=River(),
        )
        game._reset_active_position()
        game.validate_tile_conservation()
        return game

    def _validate_progress(self) -> None:
        if self.turn != self.active_index:
            raise ValueError("turnとactive_indexが一致していません")
        if not 0 <= self.active_index <= len(self.blocks):
            raise ValueError("active_indexがブロック範囲外です")
        if not 0 <= self.active_rotation < 4:
            raise ValueError("active_rotationは0から3でなければなりません")
        if self.river.total_count != self.turn * 4:
            raise ValueError("ターン数と川の牌数が一致していません")

    def _reset_active_position(self) -> None:
        self.active_rotation = 0
        self.active_y = 0
        block = self.current_block
        self.active_x = 0 if block is None else (BOARD_WIDTH - block.width) // 2

    @property
    def visible_dora_indicators(self) -> tuple[Tile, ...]:
        """フェーズ2ではゲーム開始時の1枚だけを公開する。"""

        return self.dora_indicator_tiles[:1]

    @property
    def current_block(self) -> Tetromino | None:
        if self.is_game_over:
            return None
        return self.blocks[self.active_index].with_rotation(self.active_rotation)

    @property
    def next_blocks(self) -> tuple[Tetromino, ...]:
        start = self.active_index + 1
        end = start + self.next_display_count
        return self.blocks[start:end]

    @property
    def preview_cells(self) -> tuple[PositionedCell, ...]:
        block = self.current_block
        if block is None:
            return ()
        return block.positioned_cells(
            origin_x=self.active_x,
            origin_y=self.active_y,
        )

    @property
    def is_game_over(self) -> bool:
        return self.active_index >= len(self.blocks)

    @property
    def remaining_turns(self) -> int:
        return len(self.blocks) - self.active_index

    def move_active(self, dx: int, dy: int) -> bool:
        """ブロックが盤面内に収まる場合だけ原点を移動する。"""

        if any(
            not isinstance(value, int) or isinstance(value, bool)
            for value in (dx, dy)
        ):
            raise ValueError("移動量は整数でなければなりません")
        block = self.current_block
        if block is None:
            return False
        next_x = self.active_x + dx
        next_y = self.active_y + dy
        if not block.fits(
            origin_x=next_x,
            origin_y=next_y,
            board_width=BOARD_WIDTH,
            board_height=BOARD_HEIGHT,
        ):
            return False
        self.active_x = next_x
        self.active_y = next_y
        return True

    def rotate_active(self, *, clockwise: bool) -> bool:
        """壁蹴りなしで、盤面内に収まる場合だけ90度回転する。"""

        block = self.current_block
        if block is None:
            return False
        candidate = block.rotated(clockwise=clockwise)
        if not candidate.fits(
            origin_x=self.active_x,
            origin_y=self.active_y,
            board_width=BOARD_WIDTH,
            board_height=BOARD_HEIGHT,
        ):
            return False
        self.active_rotation = candidate.rotation
        return True

    def place_active(self) -> PlacementResult:
        """現在ブロックを配置し、4枚を川へ記録して次ターンへ進む。"""

        block = self.current_block
        if block is None:
            raise RuntimeError("ゲームは終了しています")
        placed_cells = self.preview_cells
        replacements = self.board.overwrite(
            {cell.coordinate: cell.tile for cell in placed_cells}
        )
        next_turn = self.turn + 1
        discards = tuple(
            DiscardRecord(
                tile=replacement.old_tile,
                turn=next_turn,
                coordinate=replacement.coordinate,
                placement_id=block.block_id,
            )
            for replacement in replacements
        )
        self.river.extend(discards)
        self.turn = next_turn
        self.active_index += 1
        self._reset_active_position()
        self._validate_progress()
        self.validate_tile_conservation()
        return PlacementResult(
            turn=self.turn,
            placement_id=block.block_id,
            kind=block.kind,
            placed_cells=placed_cells,
            discards=discards,
            changed_rows=tuple(
                sorted({cell.coordinate.y for cell in placed_cells})
            ),
            is_game_over=self.is_game_over,
        )

    def _tracked_tiles(self) -> tuple[Tile, ...]:
        future_block_tiles = tuple(
            tile
            for block in self.blocks[self.active_index :]
            for tile in block.tiles
        )
        return (
            self.board.tiles
            + tuple(record.tile for record in self.river.records)
            + self.dora_indicator_tiles
            + future_block_tiles
        )

    def validate_tile_conservation(self) -> None:
        """全状態にある牌が重複・不足なく136枚か検証する。"""

        tiles = self._tracked_tiles()
        tile_ids = [tile.tile_id for tile in tiles]
        if len(tiles) != TOTAL_TILE_COUNT or len(tile_ids) != len(set(tile_ids)):
            raise RuntimeError("ゲーム状態の136枚に重複または不足があります")

    def tracked_tile_ids(self) -> frozenset[str]:
        """検証済みの全136個体IDを返す。"""

        self.validate_tile_conservation()
        return frozenset(tile.tile_id for tile in self._tracked_tiles())
