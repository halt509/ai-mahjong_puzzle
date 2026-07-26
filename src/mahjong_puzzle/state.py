"""行ごとの履歴と、画面非依存のターンコンボ状態。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from mahjong_puzzle.kan import KanCheckResult, check_kans
from mahjong_puzzle.tiles import TileLike, TileType
from mahjong_puzzle.yaku import Yaku


@dataclass(frozen=True)
class WinRegistration:
    """再和了判定と、状態更新前後の情報。"""

    current_yaku: frozenset[Yaku]
    new_yaku: frozenset[Yaku]
    acquired_yaku: frozenset[Yaku]
    previous_win_count: int
    is_new_win: bool


@dataclass
class LineState:
    """1行の取得済み役、和了回数、カン済み牌種。"""

    acquired_yaku: set[Yaku] = field(default_factory=set)
    completed_kans: set[TileType] = field(default_factory=set)
    win_count: int = 0
    has_won: bool = False

    def __post_init__(self) -> None:
        if not all(isinstance(yaku, Yaku) for yaku in self.acquired_yaku):
            raise TypeError("取得済み役はYakuで指定してください")
        if not all(isinstance(kind, TileType) for kind in self.completed_kans):
            raise TypeError("カン履歴はTileTypeで指定してください")
        if not isinstance(self.win_count, int) or isinstance(self.win_count, bool) or self.win_count < 0:
            raise ValueError("和了回数は0以上の整数でなければなりません")
        if not isinstance(self.has_won, bool):
            raise TypeError("has_wonはboolでなければなりません")
        if self.win_count > 0:
            self.has_won = True
        elif self.has_won:
            raise ValueError("has_wonがTrueなら和了回数は1以上必要です")
        self.acquired_yaku = set(self.acquired_yaku)
        self.completed_kans = set(self.completed_kans)

    def register_win(self, current_yaku: Iterable[Yaku]) -> WinRegistration:
        """初回基本和了か、未取得役がある再和了を履歴へ登録する。"""

        current = frozenset(current_yaku)
        if not all(isinstance(yaku, Yaku) for yaku in current):
            raise TypeError("現在役はYakuで指定してください")
        new_yaku = current - self.acquired_yaku
        previous_win_count = self.win_count
        is_new_win = not self.has_won or bool(new_yaku)
        if is_new_win:
            self.acquired_yaku.update(current)
            self.win_count += 1
            self.has_won = True
        return WinRegistration(
            current_yaku=current,
            new_yaku=frozenset(new_yaku),
            acquired_yaku=frozenset(self.acquired_yaku),
            previous_win_count=previous_win_count,
            is_new_win=is_new_win,
        )

    def check_and_record_kans(self, tiles: Iterable[TileLike]) -> KanCheckResult:
        """新規カンを判定して、この行の履歴へ記録する。"""

        result = check_kans(tiles, self.completed_kans)
        self.completed_kans.update(result.new_kans)
        return result


@dataclass(frozen=True)
class TurnResult:
    """ターン後のコンボ数とイベント件数。"""

    consecutive_win_turns: int
    winning_line_count: int
    kan_count: int


@dataclass
class TurnState:
    """連続和了ターン数だけを保持する最小ターン状態。"""

    consecutive_win_turns: int = 0

    def __post_init__(self) -> None:
        if (
            not isinstance(self.consecutive_win_turns, int)
            or isinstance(self.consecutive_win_turns, bool)
            or self.consecutive_win_turns < 0
        ):
            raise ValueError("連続和了数は0以上の整数でなければなりません")

    def record_turn(self, *, winning_line_count: int, kan_count: int) -> TurnResult:
        """和了で増加、カンだけなら維持、何もなければリセットする。"""

        for name, value in (
            ("同時和了行数", winning_line_count),
            ("カン数", kan_count),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{name}は0以上の整数でなければなりません")

        if winning_line_count > 0:
            self.consecutive_win_turns += 1
        elif kan_count == 0:
            self.consecutive_win_turns = 0
        return TurnResult(
            consecutive_win_turns=self.consecutive_win_turns,
            winning_line_count=winning_line_count,
            kan_count=kan_count,
        )
