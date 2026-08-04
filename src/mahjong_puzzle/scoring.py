"""差し替え可能な得点設定と得点内訳。"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from types import MappingProxyType
from typing import Iterable, Mapping

from mahjong_puzzle.yaku import Yaku, YakuEvaluation

BASE_WIN_SCORE = 500


def _default_yaku_points() -> Mapping[Yaku, int]:
    return MappingProxyType(
        {
            Yaku.ALL_SEQUENCES: 1000,
            Yaku.ALL_TRIPLETS: 2000,
            Yaku.TANYAO: 1000,
            Yaku.IIPEIKOU: 2000,
            Yaku.HONITSU: 3000,
            Yaku.CHINITSU: 5000,
            Yaku.HONROUTOU: 4000,
            Yaku.YAKUHAI: 2000,
            Yaku.HONOR_PAIR: 1000,
            Yaku.TERMINAL_PAIR: 1000,
            Yaku.TWO_SUIT_SAME_SEQUENCE: 2000,
            Yaku.STEPPED_SEQUENCES: 1500,
            Yaku.THREE_SUITS_USED: 1000,
            Yaku.FOUR_PAIRS: 4000,
        }
    )


@dataclass(frozen=True)
class ScoringConfig:
    """役の得点設定。全項目をロジック外から差し替えられる。"""

    yaku_points: Mapping[Yaku, int] = field(default_factory=_default_yaku_points)
    base_win_score: int = BASE_WIN_SCORE
    dora_point: int = 500
    combination_bonus_per_extra_yaku: int = 500
    repeat_win_bonus: int = 1000
    streak_multiplier_step: Fraction = Fraction(1, 4)
    simultaneous_multiplier_step: Fraction = Fraction(1, 2)

    def __post_init__(self) -> None:
        missing = set(Yaku) - set(self.yaku_points)
        if missing:
            names = "、".join(yaku.value for yaku in sorted(missing, key=lambda item: item.value))
            raise ValueError(f"役点設定が不足しています: {names}")
        numeric_values = (
            *self.yaku_points.values(),
            self.base_win_score,
            self.dora_point,
            self.combination_bonus_per_extra_yaku,
            self.repeat_win_bonus,
        )
        if any(not isinstance(value, int) or isinstance(value, bool) or value < 0 for value in numeric_values):
            raise ValueError("点数設定は0以上の整数でなければなりません")
        for name, value in (
            ("連続和了倍率の増分", self.streak_multiplier_step),
            ("同時和了倍率の増分", self.simultaneous_multiplier_step),
        ):
            if not isinstance(value, (int, Fraction)) or isinstance(value, bool):
                raise ValueError(f"{name}は整数またはFractionでなければなりません")
        if self.streak_multiplier_step < 0 or self.simultaneous_multiplier_step < 0:
            raise ValueError("倍率の増分は0以上でなければなりません")
        object.__setattr__(self, "yaku_points", MappingProxyType(dict(self.yaku_points)))
        object.__setattr__(
            self, "streak_multiplier_step", Fraction(self.streak_multiplier_step)
        )
        object.__setattr__(
            self, "simultaneous_multiplier_step", Fraction(self.simultaneous_multiplier_step)
        )


DEFAULT_SCORING_CONFIG = ScoringConfig()


@dataclass(frozen=True)
class ScoreBreakdown:
    """最終得点と、再現可能な計算内訳。"""

    base_win_score: int
    yaku_points: Mapping[Yaku, int]
    dora_count: int
    dora_score: int
    combination_bonus: int
    line_repeat_bonus: int
    subtotal: int
    streak_multiplier: Fraction
    simultaneous_multiplier: Fraction
    total_score: int


@dataclass(frozen=True)
class ScoredYakuEvaluation:
    """1つの分解候補、その新規役、得点内訳。"""

    evaluation: YakuEvaluation
    new_yaku: frozenset[Yaku]
    score: ScoreBreakdown


def _validate_nonnegative_integer(name: str, value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{name}は0以上の整数でなければなりません")


def calculate_score(
    *,
    current_yaku: Iterable[Yaku],
    new_yaku: Iterable[Yaku],
    dora_count: int,
    previous_line_wins: int,
    consecutive_win_turns: int,
    simultaneous_line_count: int,
    config: ScoringConfig = DEFAULT_SCORING_CONFIG,
) -> ScoreBreakdown:
    """新規役だけを基本点にし、設定に従って得点内訳を計算する。

    端数が生じるカスタム設定では、全倍率を掛けた最後に切り捨てる。
    """

    current = frozenset(current_yaku)
    new = frozenset(new_yaku)
    if not all(isinstance(yaku, Yaku) for yaku in current | new):
        raise TypeError("役はYakuで指定してください")
    if not new <= current:
        raise ValueError("新規役は現在役の部分集合でなければなりません")

    _validate_nonnegative_integer("ドラ枚数", dora_count)
    _validate_nonnegative_integer("過去の同一行和了回数", previous_line_wins)
    _validate_nonnegative_integer("連続和了数", consecutive_win_turns)
    _validate_nonnegative_integer("同時和了行数", simultaneous_line_count)
    if consecutive_win_turns < 1:
        raise ValueError("和了ターンの連続和了数は1以上でなければなりません")
    if simultaneous_line_count < 1:
        raise ValueError("同時和了行数は1以上でなければなりません")
    if previous_line_wins > 0 and not new:
        raise ValueError("再和了には1つ以上の新規役が必要です")

    yaku_points = MappingProxyType({yaku: config.yaku_points[yaku] for yaku in new})
    dora_score = dora_count * config.dora_point
    combination_bonus = (
        max(0, len(current) - 1) * config.combination_bonus_per_extra_yaku
    )
    line_repeat_bonus = previous_line_wins * config.repeat_win_bonus
    subtotal = (
        config.base_win_score
        + sum(yaku_points.values())
        + dora_score
        + combination_bonus
        + line_repeat_bonus
    )
    streak_multiplier = 1 + (
        max(0, consecutive_win_turns - 1) * config.streak_multiplier_step
    )
    simultaneous_multiplier = 1 + (
        max(0, simultaneous_line_count - 1) * config.simultaneous_multiplier_step
    )
    total = Fraction(subtotal) * streak_multiplier * simultaneous_multiplier

    return ScoreBreakdown(
        base_win_score=config.base_win_score,
        yaku_points=yaku_points,
        dora_count=dora_count,
        dora_score=dora_score,
        combination_bonus=combination_bonus,
        line_repeat_bonus=line_repeat_bonus,
        subtotal=subtotal,
        streak_multiplier=streak_multiplier,
        simultaneous_multiplier=simultaneous_multiplier,
        total_score=total.numerator // total.denominator,
    )


def score_yaku_evaluations(
    evaluations: Iterable[YakuEvaluation],
    *,
    acquired_yaku: Iterable[Yaku],
    dora_count: int,
    previous_line_wins: int,
    consecutive_win_turns: int,
    simultaneous_line_count: int,
    config: ScoringConfig = DEFAULT_SCORING_CONFIG,
) -> tuple[ScoredYakuEvaluation, ...]:
    """初回基本和了または未取得役がある再和了候補をすべて採点する。"""

    acquired = frozenset(acquired_yaku)
    if not all(isinstance(yaku, Yaku) for yaku in acquired):
        raise TypeError("取得済み役はYakuで指定してください")

    results: list[ScoredYakuEvaluation] = []
    is_first_win = previous_line_wins == 0
    for evaluation in evaluations:
        if not isinstance(evaluation, YakuEvaluation):
            raise TypeError("候補はYakuEvaluationで指定してください")
        new_yaku = evaluation.yaku - acquired
        if not evaluation.is_winning or (not is_first_win and not new_yaku):
            continue
        score = calculate_score(
            current_yaku=evaluation.yaku,
            new_yaku=new_yaku,
            dora_count=dora_count,
            previous_line_wins=previous_line_wins,
            consecutive_win_turns=consecutive_win_turns,
            simultaneous_line_count=simultaneous_line_count,
            config=config,
        )
        results.append(
            ScoredYakuEvaluation(
                evaluation=evaluation,
                new_yaku=frozenset(new_yaku),
                score=score,
            )
        )
    return tuple(results)


def select_best_scored_evaluation(
    evaluations: Iterable[YakuEvaluation],
    *,
    acquired_yaku: Iterable[Yaku],
    dora_count: int,
    previous_line_wins: int,
    consecutive_win_turns: int,
    simultaneous_line_count: int,
    config: ScoringConfig = DEFAULT_SCORING_CONFIG,
) -> ScoredYakuEvaluation | None:
    """有効候補のうち最終得点が最大のものを返す。

    同点では入力順が先の候補を返す。有効候補がなければ``None``を返す。
    """

    scored = score_yaku_evaluations(
        evaluations,
        acquired_yaku=acquired_yaku,
        dora_count=dora_count,
        previous_line_wins=previous_line_wins,
        consecutive_win_turns=consecutive_win_turns,
        simultaneous_line_count=simultaneous_line_count,
        config=config,
    )
    return max(scored, key=lambda candidate: candidate.score.total_score, default=None)
