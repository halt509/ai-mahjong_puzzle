"""最初の3ブロックを使った、初期盤面の軽量な交換距離評価。"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from itertools import combinations, combinations_with_replacement
from typing import Iterable, Sequence

from mahjong_puzzle.board import BOARD_HEIGHT, BOARD_WIDTH, Board
from mahjong_puzzle.tetromino import Tetromino
from mahjong_puzzle.tiles import (
    Suit,
    TileLike,
    TileType,
    all_tile_types,
    normalize_tile_types,
)

INITIAL_DEAL_MAX_CLOSE_DISTANCE = 2
INITIAL_DEAL_REQUIRED_CLOSE_ROWS = 1
INITIAL_DEAL_MAX_PLAYABLE_DISTANCE = 3
INITIAL_DEAL_REQUIRED_PLAYABLE_ROWS = 3
INITIAL_DEAL_MAX_ATTEMPTS = 100
INITIAL_BLOCK_EVALUATION_COUNT = 3
INITIAL_CANDIDATE_TILE_COUNT = INITIAL_BLOCK_EVALUATION_COUNT * 4


@dataclass(frozen=True)
class InitialDealConfig:
    """初期配牌の合格しきい値と再生成上限。"""

    max_close_distance: int = INITIAL_DEAL_MAX_CLOSE_DISTANCE
    required_close_rows: int = INITIAL_DEAL_REQUIRED_CLOSE_ROWS
    max_playable_distance: int = INITIAL_DEAL_MAX_PLAYABLE_DISTANCE
    required_playable_rows: int = INITIAL_DEAL_REQUIRED_PLAYABLE_ROWS
    max_attempts: int = INITIAL_DEAL_MAX_ATTEMPTS

    def __post_init__(self) -> None:
        for name, value in (
            ("近距離の最大交換枚数", self.max_close_distance),
            ("近距離の必要行数", self.required_close_rows),
            ("到達可能距離の最大交換枚数", self.max_playable_distance),
            ("到達可能距離の必要行数", self.required_playable_rows),
        ):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= BOARD_WIDTH
            ):
                raise ValueError(f"{name}は0から{BOARD_WIDTH}でなければなりません")
        if self.max_playable_distance < self.max_close_distance:
            raise ValueError("到達可能距離は近距離以上でなければなりません")
        if (
            not isinstance(self.max_attempts, int)
            or isinstance(self.max_attempts, bool)
            or self.max_attempts < 1
        ):
            raise ValueError("初期配牌の最大試行回数は1以上でなければなりません")


DEFAULT_INITIAL_DEAL_CONFIG = InitialDealConfig()


@dataclass(frozen=True)
class InitialDealEvaluation:
    """8行の交換距離と合否、フォールバック比較用の集計。"""

    row_distances: tuple[int | None, ...]
    close_row_count: int
    playable_row_count: int
    average_distance: float
    passed: bool

    @property
    def quality_key(self) -> tuple[int, int, float]:
        """大きいほどフォールバック候補として良い比較キー。"""

        return (
            self.close_row_count,
            self.playable_row_count,
            -self.average_distance,
        )


@dataclass(frozen=True)
class InitialDealDebug:
    """通常画面へ混在させない、採用初期状態の再現情報。"""

    seed: int
    attempt_count: int
    row_distances: tuple[int | None, ...]
    passed: bool
    used_fallback: bool


def _validate_available_tiles(
    row: tuple[TileType, ...],
    candidates: tuple[TileType, ...],
) -> Counter[TileType]:
    if len(row) != BOARD_WIDTH:
        raise ValueError(f"初期配牌評価の行は{BOARD_WIDTH}枚必要です")
    if len(candidates) != INITIAL_CANDIDATE_TILE_COUNT:
        raise ValueError(
            "初期配牌評価には最初の3ブロックの12牌が必要です"
        )
    available = Counter(row)
    available.update(candidates)
    if any(count > 4 for count in available.values()):
        raise ValueError("初期配牌評価の牌種は合計4枚を超えられません")
    return available


def _possible_melds(
    available: Counter[TileType],
) -> tuple[tuple[TileType, TileType, TileType], ...]:
    melds: list[tuple[TileType, TileType, TileType]] = []
    for tile_type in all_tile_types():
        if available[tile_type] >= 3:
            melds.append((tile_type, tile_type, tile_type))
    for suit in Suit:
        for first_rank in range(1, 8):
            sequence = tuple(
                TileType.suited(suit, rank)
                for rank in range(first_rank, first_rank + 3)
            )
            if all(available[tile_type] >= 1 for tile_type in sequence):
                melds.append(sequence)
    return tuple(melds)


def _replacement_distance(
    target: Counter[TileType],
    row: Counter[TileType],
    candidates: Counter[TileType],
) -> int | None:
    additions = {
        tile_type: max(0, target_count - row[tile_type])
        for tile_type, target_count in target.items()
    }
    if any(
        count > candidates[tile_type]
        for tile_type, count in additions.items()
    ):
        return None
    return sum(additions.values())


def minimum_replacement_distance(
    row_tiles: Iterable[TileLike],
    candidate_tiles: Iterable[TileLike],
) -> int | None:
    """候補12牌の枚数制限内で和了形へ届く最小交換枚数を返す。

    テトリミノの座標は考慮せず、通常形「3＋3＋2」と四対子を対象にする。
    """

    row = normalize_tile_types(row_tiles)
    candidates = normalize_tile_types(candidate_tiles)
    available = _validate_available_tiles(row, candidates)
    row_counts = Counter(row)
    candidate_counts = Counter(candidates)
    best: int | None = None

    melds = _possible_melds(available)
    pair_types = tuple(
        tile_type
        for tile_type in all_tile_types()
        if available[tile_type] >= 2
    )
    for first_meld, second_meld in combinations_with_replacement(melds, 2):
        meld_counts = Counter(first_meld + second_meld)
        for pair in pair_types:
            target = meld_counts.copy()
            target[pair] += 2
            if any(count > 4 or count > available[tile_type] for tile_type, count in target.items()):
                continue
            distance = _replacement_distance(
                target,
                row_counts,
                candidate_counts,
            )
            if distance is not None and (best is None or distance < best):
                best = distance
                if best == 0:
                    return 0

    four_pair_types = tuple(
        tile_type
        for tile_type in all_tile_types()
        if available[tile_type] >= 2
    )
    for pairs in combinations(four_pair_types, 4):
        target = Counter({pair: 2 for pair in pairs})
        distance = _replacement_distance(
            target,
            row_counts,
            candidate_counts,
        )
        if distance is not None and (best is None or distance < best):
            best = distance
            if best == 0:
                return 0
    return best


def assess_initial_deal_distances(
    row_distances: Sequence[int | None],
    config: InitialDealConfig = DEFAULT_INITIAL_DEAL_CONFIG,
) -> InitialDealEvaluation:
    """8行の最小距離から合否とフォールバック比較値を計算する。"""

    distances = tuple(row_distances)
    if len(distances) != BOARD_HEIGHT:
        raise ValueError(f"初期配牌評価には{BOARD_HEIGHT}行分の距離が必要です")
    if not all(
        distance is None
        or (
            isinstance(distance, int)
            and not isinstance(distance, bool)
            and 0 <= distance <= BOARD_WIDTH
        )
        for distance in distances
    ):
        raise ValueError("交換距離は0から8の整数またはNoneでなければなりません")
    if not isinstance(config, InitialDealConfig):
        raise TypeError("configにはInitialDealConfigが必要です")

    close_count = sum(
        1
        for distance in distances
        if distance is not None and 1 <= distance <= config.max_close_distance
    )
    playable_count = sum(
        1
        for distance in distances
        if distance is not None
        and 1 <= distance <= config.max_playable_distance
    )
    unreachable_distance = BOARD_WIDTH + 1
    average = sum(
        unreachable_distance if distance is None else distance
        for distance in distances
    ) / BOARD_HEIGHT
    return InitialDealEvaluation(
        row_distances=distances,
        close_row_count=close_count,
        playable_row_count=playable_count,
        average_distance=average,
        passed=(
            close_count >= config.required_close_rows
            and playable_count >= config.required_playable_rows
        ),
    )


def evaluate_initial_deal(
    board: Board,
    blocks: Sequence[Tetromino],
    config: InitialDealConfig = DEFAULT_INITIAL_DEAL_CONFIG,
) -> InitialDealEvaluation:
    """盤面8行を、最初の3ブロックに含まれる12牌で評価する。"""

    if not isinstance(board, Board):
        raise TypeError("boardにはBoardが必要です")
    if len(blocks) < INITIAL_BLOCK_EVALUATION_COUNT:
        raise ValueError("初期配牌評価には3個以上のブロックが必要です")
    first_blocks = tuple(blocks[:INITIAL_BLOCK_EVALUATION_COUNT])
    if not all(isinstance(block, Tetromino) for block in first_blocks):
        raise TypeError("blocksにはTetrominoが必要です")
    candidate_tiles = tuple(
        tile
        for block in first_blocks
        for tile in block.tiles
    )
    distances = tuple(
        minimum_replacement_distance(board.row(row), candidate_tiles)
        for row in range(BOARD_HEIGHT)
    )
    return assess_initial_deal_distances(distances, config)
