"""フェーズ1ルールエンジンの最小実行例。"""

from __future__ import annotations

from mahjong_puzzle.dora import count_dora
from mahjong_puzzle.hand import FourPairsDecomposition
from mahjong_puzzle.scoring import select_best_scored_evaluation
from mahjong_puzzle.state import LineState, TurnState
from mahjong_puzzle.tiles import Suit, TileType
from mahjong_puzzle.yaku import YAKU_DISPLAY_NAMES, evaluate_hand


def _manzu(rank: int) -> TileType:
    return TileType.suited(Suit.MANZU, rank)


def main() -> None:
    """8牌の分解から得点内訳までを順番に表示する。"""

    tiles = [_manzu(1), _manzu(2), _manzu(3)] * 2 + [_manzu(5)] * 2
    indicators = [_manzu(9)]
    evaluations = evaluate_hand(tiles)
    line_state = LineState()
    turn = TurnState().record_turn(winning_line_count=1, kan_count=0)
    dora_count = count_dora(tiles, indicators)
    selected = select_best_scored_evaluation(
        evaluations,
        acquired_yaku=line_state.acquired_yaku,
        dora_count=dora_count,
        previous_line_wins=line_state.win_count,
        consecutive_win_turns=turn.consecutive_win_turns,
        simultaneous_line_count=turn.winning_line_count,
    )
    if selected is None:
        print("役を伴う和了形ではありません。")
        return

    registration = line_state.register_win(selected.evaluation.yaku)
    score = selected.score

    decomposition = selected.evaluation.decomposition
    if isinstance(decomposition, FourPairsDecomposition):
        decomposition_text = " / ".join(
            f"pair: {pair} {pair}" for pair in decomposition.pairs
        )
    else:
        melds = [
            f"{meld.kind.value}: {', '.join(str(tile) for tile in meld.tiles)}"
            for meld in decomposition.melds
        ]
        decomposition_text = (
            f"{' / '.join(melds)} / pair: {decomposition.pair}"
        )
    current_names = [
        YAKU_DISPLAY_NAMES[yaku]
        for yaku in sorted(selected.evaluation.yaku, key=str)
    ]
    new_names = [YAKU_DISPLAY_NAMES[yaku] for yaku in sorted(registration.new_yaku, key=str)]
    print(f"入力牌: {' '.join(str(tile) for tile in tiles)}")
    print(f"分解: {decomposition_text}")
    print(f"成立役: {', '.join(current_names)}")
    print(f"新規役: {', '.join(new_names)}")
    print(f"ドラ枚数: {dora_count}")
    print(
        "得点内訳: "
        f"役={sum(score.yaku_points.values())}, "
        f"ドラ={score.dora_score}, "
        f"複合={score.combination_bonus}, "
        f"同一行={score.line_repeat_bonus}, "
        f"小計={score.subtotal}, "
        f"最終={score.total_score}"
    )


if __name__ == "__main__":
    main()
