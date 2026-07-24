"""フェーズ1ルールとフェーズ2盤面操作の公開API。"""

from mahjong_puzzle.board import Board, Coordinate
from mahjong_puzzle.dora import count_dora, dora_from_indicator
from mahjong_puzzle.game import GameState, PlacementResult
from mahjong_puzzle.hand import HandDecomposition, Meld, MeldKind, enumerate_decompositions
from mahjong_puzzle.kan import KanCheckResult, check_kans, find_kan_candidates
from mahjong_puzzle.river import DiscardRecord, River
from mahjong_puzzle.scoring import (
    DEFAULT_SCORING_CONFIG,
    ScoreBreakdown,
    ScoredYakuEvaluation,
    ScoringConfig,
    calculate_score,
    score_yaku_evaluations,
    select_best_scored_evaluation,
)
from mahjong_puzzle.state import LineState, TurnState
from mahjong_puzzle.tetromino import Tetromino, TetrominoKind
from mahjong_puzzle.tiles import Honor, Suit, Tile, TileType, create_full_tile_set
from mahjong_puzzle.yaku import Yaku, YakuEvaluation, evaluate_hand

__all__ = [
    "DEFAULT_SCORING_CONFIG",
    "Board",
    "Coordinate",
    "DiscardRecord",
    "GameState",
    "HandDecomposition",
    "Honor",
    "KanCheckResult",
    "LineState",
    "Meld",
    "MeldKind",
    "PlacementResult",
    "River",
    "ScoreBreakdown",
    "ScoredYakuEvaluation",
    "ScoringConfig",
    "Suit",
    "Tile",
    "TileType",
    "Tetromino",
    "TetrominoKind",
    "TurnState",
    "Yaku",
    "YakuEvaluation",
    "calculate_score",
    "check_kans",
    "count_dora",
    "create_full_tile_set",
    "dora_from_indicator",
    "enumerate_decompositions",
    "evaluate_hand",
    "find_kan_candidates",
    "score_yaku_evaluations",
    "select_best_scored_evaluation",
]
