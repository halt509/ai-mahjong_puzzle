"""画面遷移、14役対応の通知キュー、結果集計。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

from mahjong_puzzle.integration import GameSession, ResolvedTurn
from mahjong_puzzle.yaku import Yaku


class ScreenMode(str, Enum):
    TITLE = "title"
    GAME = "game"
    RIVER = "river"
    YAKU = "yaku"
    RESULT = "result"


class NoticeKind(str, Enum):
    KAN = "kan"
    WIN = "win"


@dataclass(frozen=True)
class Notice:
    """中央通知へ表示する短い構造化メッセージ。"""

    kind: NoticeKind
    title: str
    lines: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.kind, NoticeKind):
            raise TypeError("kindにはNoticeKindが必要です")
        if not isinstance(self.title, str) or not self.title:
            raise ValueError("通知タイトルは空でない文字列が必要です")
        if not all(isinstance(line, str) for line in self.lines):
            raise TypeError("通知行は文字列でなければなりません")


_YAKU_SHORT_NAMES = {
    Yaku.ALL_SEQUENCES: "SEQ",
    Yaku.ALL_TRIPLETS: "TRI",
    Yaku.TANYAO: "TAN",
    Yaku.IIPEIKOU: "IIP",
    Yaku.HONITSU: "HON",
    Yaku.CHINITSU: "CHI",
    Yaku.HONROUTOU: "HRO",
    Yaku.YAKUHAI: "YAK",
    Yaku.HONOR_PAIR: "HPR",
    Yaku.TERMINAL_PAIR: "TPR",
    Yaku.TWO_SUIT_SAME_SEQUENCE: "TSS",
    Yaku.STEPPED_SEQUENCES: "STP",
    Yaku.THREE_SUITS_USED: "TSU",
    Yaku.FOUR_PAIRS: "4PR",
}

if set(_YAKU_SHORT_NAMES) != set(Yaku):
    raise RuntimeError("和了通知の役略称がYaku定義と一致しません")


def notices_from_turn(result: ResolvedTurn) -> tuple[Notice, ...]:
    """ターン結果をカン通知、行別和了通知の順へ変換する。"""

    if not isinstance(result, ResolvedTurn):
        raise TypeError("resultにはResolvedTurnが必要です")
    notices: list[Notice] = []
    for event in result.kans:
        indicator = (
            "DORA LIMIT"
            if event.revealed_indicator is None
            else f"IND {event.revealed_indicator.kind.code.upper()}"
        )
        notices.append(
            Notice(
                kind=NoticeKind.KAN,
                title="KAN!",
                lines=(
                    f"ROW {event.row + 1} / {event.tile_type.code.upper()}",
                    indicator,
                ),
            )
        )
    for event in result.wins:
        new_names = "+".join(
            _YAKU_SHORT_NAMES[yaku]
            for yaku in sorted(event.new_yaku, key=lambda item: item.value)
        )
        notices.append(
            Notice(
                kind=NoticeKind.WIN,
                title=f"WIN! ROW {event.row + 1}",
                lines=(
                    f"NEW {new_names}",
                    f"DORA {event.dora_count}",
                    f"SCORE +{event.score.total_score}",
                ),
            )
        )
    return tuple(notices)


@dataclass(frozen=True)
class GameSummary:
    total_score: int
    turns: int
    win_count: int
    kan_count: int
    acquired_yaku: frozenset[Yaku]
    river_count: int

    @classmethod
    def from_session(cls, session: GameSession) -> GameSummary:
        """現在セッションから結果画面用の集計値を作る。"""

        if not isinstance(session, GameSession):
            raise TypeError("sessionにはGameSessionが必要です")
        return cls(
            total_score=session.total_score,
            turns=session.game.turn,
            win_count=sum(len(result.wins) for result in session.turn_history),
            kan_count=sum(len(result.kans) for result in session.turn_history),
            acquired_yaku=frozenset(
                yaku
                for line_state in session.line_states
                for yaku in line_state.acquired_yaku
            ),
            river_count=session.game.river.total_count,
        )


@dataclass
class UiState:
    """Pyxel入力から独立した画面と通知の状態機械。"""

    screen: ScreenMode = ScreenMode.TITLE
    _notices: list[Notice] = field(default_factory=list)
    _result_pending: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.screen, ScreenMode):
            raise TypeError("screenにはScreenModeが必要です")
        if not all(isinstance(notice, Notice) for notice in self._notices):
            raise TypeError("通知キューにはNoticeだけを指定できます")
        self._notices = list(self._notices)

    @property
    def current_notice(self) -> Notice | None:
        return self._notices[0] if self._notices else None

    def start_game(self) -> None:
        self.screen = ScreenMode.GAME
        self._notices.clear()
        self._result_pending = False

    def queue_notifications(
        self, notices: Iterable[Notice], *, game_over: bool
    ) -> None:
        additions = tuple(notices)
        if not all(isinstance(notice, Notice) for notice in additions):
            raise TypeError("通知キューにはNoticeだけを追加できます")
        self._notices.extend(additions)
        self._result_pending = self._result_pending or game_over
        self._finish_if_ready()

    def accept_turn(self, result: ResolvedTurn) -> None:
        self.queue_notifications(
            notices_from_turn(result),
            game_over=result.placement.is_game_over,
        )

    def dismiss_notice(self) -> bool:
        """現在通知を1件閉じる。入力自体は呼び出し側で消費する。"""

        if not self._notices:
            return False
        self._notices.pop(0)
        self._finish_if_ready()
        return True

    def _finish_if_ready(self) -> None:
        if self._result_pending and not self._notices:
            self.screen = ScreenMode.RESULT

    def open_overlay(self, overlay: ScreenMode) -> bool:
        if overlay not in (ScreenMode.RIVER, ScreenMode.YAKU):
            raise ValueError("オーバーレイはRIVERまたはYAKUで指定してください")
        if self.screen is not ScreenMode.GAME or self.current_notice is not None:
            return False
        self.screen = overlay
        return True

    def close_overlay(self) -> None:
        if self.screen in (ScreenMode.RIVER, ScreenMode.YAKU):
            self.screen = ScreenMode.GAME
