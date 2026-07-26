"""配置後のカン、ドラ、和了、得点を仕様順に統合する。"""

from __future__ import annotations

from dataclasses import dataclass, field

from mahjong_puzzle.board import BOARD_HEIGHT
from mahjong_puzzle.dora import count_dora
from mahjong_puzzle.game import GameState, PlacementResult
from mahjong_puzzle.scoring import (
    DEFAULT_SCORING_CONFIG,
    ScoreBreakdown,
    ScoringConfig,
    select_best_scored_evaluation,
)
from mahjong_puzzle.state import LineState, TurnState
from mahjong_puzzle.tiles import Tile, TileType
from mahjong_puzzle.yaku import Yaku, YakuEvaluation, evaluate_hand


@dataclass(frozen=True)
class KanEvent:
    """1種類の新規カンと、それに対応して公開できた表示牌。"""

    row: int
    tile_type: TileType
    revealed_indicator: Tile | None


@dataclass(frozen=True)
class WinEvent:
    """1行の採用分解、役、ドラ、得点内訳。"""

    row: int
    evaluation: YakuEvaluation
    current_yaku: frozenset[Yaku]
    new_yaku: frozenset[Yaku]
    dora_count: int
    score: ScoreBreakdown


@dataclass(frozen=True)
class ResolvedTurn:
    """1回の配置から確定した全イベントと累計得点。"""

    placement: PlacementResult
    kans: tuple[KanEvent, ...]
    revealed_indicators: tuple[Tile, ...]
    wins: tuple[WinEvent, ...]
    consecutive_win_turns: int
    turn_score: int
    total_score: int

    @property
    def kan_rows(self) -> tuple[int, ...]:
        return tuple(sorted({event.row for event in self.kans}))

    @property
    def winning_rows(self) -> tuple[int, ...]:
        return tuple(event.row for event in self.wins)


def _default_line_states() -> tuple[LineState, ...]:
    return tuple(LineState() for _ in range(BOARD_HEIGHT))


@dataclass
class GameSession:
    """GameStateへ行履歴、コンボ、得点を重ねるフェーズ3状態。"""

    game: GameState
    line_states: tuple[LineState, ...] = field(default_factory=_default_line_states)
    turn_state: TurnState = field(default_factory=TurnState)
    scoring_config: ScoringConfig = DEFAULT_SCORING_CONFIG
    total_score: int = 0
    turn_history: list[ResolvedTurn] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.game, GameState):
            raise TypeError("gameにはGameStateが必要です")
        if len(self.line_states) != BOARD_HEIGHT or not all(
            isinstance(state, LineState) for state in self.line_states
        ):
            raise ValueError(f"line_statesには{BOARD_HEIGHT}行分のLineStateが必要です")
        self.line_states = tuple(self.line_states)
        if not isinstance(self.turn_state, TurnState):
            raise TypeError("turn_stateにはTurnStateが必要です")
        if not isinstance(self.scoring_config, ScoringConfig):
            raise TypeError("scoring_configにはScoringConfigが必要です")
        if (
            not isinstance(self.total_score, int)
            or isinstance(self.total_score, bool)
            or self.total_score < 0
        ):
            raise ValueError("累計得点は0以上の整数でなければなりません")
        if not all(isinstance(result, ResolvedTurn) for result in self.turn_history):
            raise TypeError("turn_historyにはResolvedTurnだけを指定できます")
        self.turn_history = list(self.turn_history)

    @classmethod
    def new(
        cls,
        *,
        seed: int | None = None,
        scoring_config: ScoringConfig = DEFAULT_SCORING_CONFIG,
    ) -> GameSession:
        """新しい盤面と空の行履歴からセッションを作る。"""

        return cls(
            game=GameState.new(seed=seed),
            scoring_config=scoring_config,
        )

    @property
    def last_turn(self) -> ResolvedTurn | None:
        return self.turn_history[-1] if self.turn_history else None

    def place_active(self) -> ResolvedTurn:
        """現在ブロックを配置し、フェーズ3の全ルールを順番に解決する。"""

        placement = self.game.place_active()
        kan_specs: list[tuple[int, TileType]] = []
        for row in placement.changed_rows:
            check = self.line_states[row].check_and_record_kans(
                self.game.board.row(row)
            )
            kan_specs.extend(
                (row, tile_type)
                for tile_type in sorted(check.new_kans)
            )

        revealed = self.game.reveal_dora_indicators(len(kan_specs))
        kan_events = tuple(
            KanEvent(
                row=row,
                tile_type=tile_type,
                revealed_indicator=revealed[index]
                if index < len(revealed)
                else None,
            )
            for index, (row, tile_type) in enumerate(kan_specs)
        )
        kan_rows = {event.row for event in kan_events}

        winning_evaluations: list[tuple[int, tuple[YakuEvaluation, ...]]] = []
        for row in placement.changed_rows:
            if row in kan_rows:
                continue
            evaluations = evaluate_hand(self.game.board.row(row))
            line_state = self.line_states[row]
            acquired = line_state.acquired_yaku
            if any(
                evaluation.is_winning
                and (
                    not line_state.has_won
                    or bool(evaluation.yaku - acquired)
                )
                for evaluation in evaluations
            ):
                winning_evaluations.append((row, evaluations))

        winning_line_count = len(winning_evaluations)
        turn_state = self.turn_state.record_turn(
            winning_line_count=winning_line_count,
            kan_count=len(kan_events),
        )

        win_events: list[WinEvent] = []
        for row, evaluations in winning_evaluations:
            line_state = self.line_states[row]
            row_tiles = self.game.board.row(row)
            row_dora_count = count_dora(
                row_tiles,
                self.game.visible_dora_indicators,
            )
            selected = select_best_scored_evaluation(
                evaluations,
                acquired_yaku=line_state.acquired_yaku,
                dora_count=row_dora_count,
                previous_line_wins=line_state.win_count,
                consecutive_win_turns=turn_state.consecutive_win_turns,
                simultaneous_line_count=winning_line_count,
                config=self.scoring_config,
            )
            if selected is None:
                raise RuntimeError("和了候補の採点結果が見つかりません")
            registration = line_state.register_win(
                selected.evaluation.yaku
            )
            if registration.new_yaku != selected.new_yaku:
                raise RuntimeError("和了候補と行履歴の新規役が一致しません")
            win_events.append(
                WinEvent(
                    row=row,
                    evaluation=selected.evaluation,
                    current_yaku=registration.current_yaku,
                    new_yaku=registration.new_yaku,
                    dora_count=row_dora_count,
                    score=selected.score,
                )
            )

        turn_score = sum(event.score.total_score for event in win_events)
        self.total_score += turn_score
        result = ResolvedTurn(
            placement=placement,
            kans=kan_events,
            revealed_indicators=revealed,
            wins=tuple(win_events),
            consecutive_win_turns=turn_state.consecutive_win_turns,
            turn_score=turn_score,
            total_score=self.total_score,
        )
        self.turn_history.append(result)
        return result
