from mahjong_puzzle.board import Coordinate
from mahjong_puzzle.river import DiscardRecord, River
from mahjong_puzzle.tiles import create_full_tile_set


def test_river_keeps_full_discard_context_and_recent_order() -> None:
    tiles = create_full_tile_set()
    river = River()
    records = [
        DiscardRecord(
            tile=tiles[index],
            turn=index + 1,
            coordinate=Coordinate(index, 0),
            placement_id=10 + index,
        )
        for index in range(3)
    ]

    river.extend(records)

    assert river.records == tuple(records)
    assert river.recent(2) == tuple(records[-2:])
    assert river.total_count == 3


def test_river_counts_discarded_tile_kinds() -> None:
    tiles = create_full_tile_set()
    river = River()
    river.extend(
        [
            DiscardRecord(tiles[0], 1, Coordinate(0, 0), 1),
            DiscardRecord(tiles[1], 1, Coordinate(1, 0), 1),
            DiscardRecord(tiles[4], 2, Coordinate(2, 0), 2),
        ]
    )

    counts = river.counts_by_kind()

    assert counts[tiles[0].kind] == 2
    assert counts[tiles[4].kind] == 1
