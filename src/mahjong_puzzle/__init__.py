"""フェーズ1から5までのルール・盤面・ターン統合公開API。"""

from mahjong_puzzle.board import Board, Coordinate
from mahjong_puzzle.dora import count_dora, dora_from_indicator
from mahjong_puzzle.game import GameState, PlacementResult
from mahjong_puzzle.initial_deal import (
    DEFAULT_INITIAL_DEAL_CONFIG,
    INITIAL_DEAL_MAX_ATTEMPTS,
    INITIAL_DEAL_MAX_CLOSE_DISTANCE,
    INITIAL_DEAL_MAX_PLAYABLE_DISTANCE,
    INITIAL_DEAL_REQUIRED_CLOSE_ROWS,
    INITIAL_DEAL_REQUIRED_PLAYABLE_ROWS,
    InitialDealConfig,
    InitialDealDebug,
    InitialDealEvaluation,
    assess_initial_deal_distances,
    evaluate_initial_deal,
    minimum_replacement_distance,
)
from mahjong_puzzle.hand import (
    FourPairsDecomposition,
    HandDecomposition,
    Meld,
    MeldKind,
    enumerate_decompositions,
    find_four_pairs_decomposition,
)
from mahjong_puzzle.integration import (
    GameSession,
    KanEvent,
    ResolvedTurn,
    WinEvent,
)
from mahjong_puzzle.kan import KanCheckResult, check_kans, find_kan_candidates
from mahjong_puzzle.river import DiscardRecord, River
from mahjong_puzzle.scoring import (
    BASE_WIN_SCORE,
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
    "BASE_WIN_SCORE",
    "DEFAULT_INITIAL_DEAL_CONFIG",
    "DEFAULT_SCORING_CONFIG",
    "Board",
    "Coordinate",
    "DiscardRecord",
    "GameState",
    "GameSession",
    "FourPairsDecomposition",
    "HandDecomposition",
    "Honor",
    "INITIAL_DEAL_MAX_ATTEMPTS",
    "INITIAL_DEAL_MAX_CLOSE_DISTANCE",
    "INITIAL_DEAL_MAX_PLAYABLE_DISTANCE",
    "INITIAL_DEAL_REQUIRED_CLOSE_ROWS",
    "INITIAL_DEAL_REQUIRED_PLAYABLE_ROWS",
    "InitialDealConfig",
    "InitialDealDebug",
    "InitialDealEvaluation",
    "KanCheckResult",
    "KanEvent",
    "LineState",
    "Meld",
    "MeldKind",
    "PlacementResult",
    "River",
    "ResolvedTurn",
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
    "WinEvent",
    "assess_initial_deal_distances",
    "calculate_score",
    "check_kans",
    "count_dora",
    "create_full_tile_set",
    "dora_from_indicator",
    "enumerate_decompositions",
    "evaluate_hand",
    "evaluate_initial_deal",
    "find_four_pairs_decomposition",
    "find_kan_candidates",
    "minimum_replacement_distance",
    "score_yaku_evaluations",
    "select_best_scored_evaluation",
]
