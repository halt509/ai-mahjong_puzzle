"""実際の牌アトラスから初心者向け日本語ガイドPNGを生成する。"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mahjong_puzzle.scoring import DEFAULT_SCORING_CONFIG
from mahjong_puzzle.sprites import TILE_SPRITE_SIZE, tile_sprite_uv
from mahjong_puzzle.tiles import Honor, Suit, TileType
from mahjong_puzzle.yaku import YAKU_DISPLAY_NAMES, Yaku, evaluate_hand
from mahjong_puzzle.yaku_catalog import (
    YAKU_GUIDE_ENTRIES,
    YakuGuideEntry,
)

WIDTH = 1600
HEIGHT = 3300
MARGIN = 64
CARD_GAP = 28
OUTPUT_PATH = ROOT / "assets" / "guides" / "beginner-guide-ja.png"
ATLAS_PATH = ROOT / "assets" / "sprites" / "mahjong-tiles-placeholder.png"

INK = "#17130f"
PANEL = "#153d33"
BACKGROUND = "#0c2a24"
TABLE = "#176348"
MAHOGANY = "#603a24"
WOOD_EDGE = "#a87848"
MUTED = "#c2a879"
IVORY = "#f1e4c3"
VERMILION = "#b63a31"
GOLD = "#ddb64c"
BAMBOO = "#3f8b56"
INDIGO = "#3e688b"
WHITE = "#ffffff"
TRANSPARENT_RGB = (200, 93, 117)


def suited(suit: Suit, *ranks: int) -> tuple[TileType, ...]:
    return tuple(TileType.suited(suit, rank) for rank in ranks)


def honors(honor: Honor, count: int) -> tuple[TileType, ...]:
    return tuple(TileType.honor_tile(honor) for _ in range(count))


YakuCard = YakuGuideEntry
YAKU_CARDS = YAKU_GUIDE_ENTRIES


def _font_path(*, bold: bool) -> Path:
    names = (
        (
            Path("C:/Windows/Fonts/BIZ-UDGothicB.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
            Path("/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"),
        )
        if bold
        else (
            Path("C:/Windows/Fonts/BIZ-UDGothicR.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"),
        )
    )
    for path in names:
        if path.exists():
            return path
    raise FileNotFoundError(
        "日本語フォントが見つかりません。BIZ UDゴシックまたはNoto Sans CJKを"
        "インストールしてください。"
    )


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(_font_path(bold=bold)), size=size)


def text_center(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    selected_font: ImageFont.ImageFont,
    fill: str,
) -> None:
    draw.text(xy, text, font=selected_font, fill=fill, anchor="mm")


def rounded_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    fill: str = PANEL,
    outline: str = WOOD_EDGE,
    width: int = 5,
    radius: int = 20,
) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(
        (x1 + 8, y1 + 10, x2 + 8, y2 + 10),
        radius=radius,
        fill=MAHOGANY,
    )
    draw.rounded_rectangle(
        box,
        radius=radius,
        fill=fill,
        outline=outline,
        width=width,
    )


def load_tile_sprite(atlas: Image.Image, kind: TileType, scale: int) -> Image.Image:
    u, v = tile_sprite_uv(kind)
    sprite = atlas.crop((u, v, u + TILE_SPRITE_SIZE, v + TILE_SPRITE_SIZE)).convert(
        "RGBA"
    )
    pixels = sprite.load()
    for y in range(sprite.height):
        for x in range(sprite.width):
            if pixels[x, y][:3] == TRANSPARENT_RGB:
                pixels[x, y] = (*TRANSPARENT_RGB, 0)
    return sprite.resize(
        (TILE_SPRITE_SIZE * scale, TILE_SPRITE_SIZE * scale),
        Image.Resampling.NEAREST,
    )


def draw_tiles(
    canvas: Image.Image,
    atlas: Image.Image,
    tiles: Iterable[TileType],
    *,
    x: int,
    y: int,
    scale: int,
    gap: int = 4,
) -> None:
    tile_size = TILE_SPRITE_SIZE * scale
    for index, kind in enumerate(tiles):
        sprite = load_tile_sprite(atlas, kind, scale)
        canvas.alpha_composite(sprite, (x + index * (tile_size + gap), y))


def validate_examples() -> None:
    for card in YAKU_CARDS:
        if len(card.example_tiles) != 8:
            raise ValueError(f"{YAKU_DISPLAY_NAMES[card.yaku]}の例は8牌必要です")
        evaluations = evaluate_hand(card.example_tiles)
        if not evaluations or not any(card.yaku in item.yaku for item in evaluations):
            raise ValueError(
                f"{YAKU_DISPLAY_NAMES[card.yaku]}の例が実際の判定で成立しません"
            )


def draw_header(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    atlas: Image.Image,
) -> None:
    rounded_panel(draw, (MARGIN, 54, WIDTH - MARGIN, 286), fill=PANEL)
    draw.text(
        (104, 92),
        "麻雀牌パズル",
        font=font(70, bold=True),
        fill=GOLD,
    )
    draw.text(
        (108, 178),
        "はじめての遊び方 ＆ 役一覧",
        font=font(36, bold=True),
        fill=IVORY,
    )
    draw.text(
        (110, 230),
        "8牌でつくる、オリジナル麻雀パズル",
        font=font(25),
        fill=MUTED,
    )
    decoration = (
        TileType.honor_tile(Honor.EAST),
        TileType.suited(Suit.PINZU, 5),
        TileType.honor_tile(Honor.RED),
    )
    draw_tiles(canvas, atlas, decoration, x=1230, y=94, scale=7, gap=10)


def draw_quick_start(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    atlas: Image.Image,
) -> None:
    y1, y2 = 320, 690
    rounded_panel(draw, (MARGIN, y1, WIDTH - MARGIN, y2), fill=TABLE)
    draw.text((94, y1 + 34), "まずはこれだけ！", font=font(39, bold=True), fill=GOLD)

    steps = (
        ("1", "黄色い4牌を\n移動・回転"),
        ("2", "好きな位置へ\n上書き配置"),
        ("3", "横1列の8牌で\n3＋3＋2を作る"),
        ("4", "形ができれば和了！\n役は追加得点"),
    )
    step_width = 350
    for index, (number, label) in enumerate(steps):
        cx = 116 + index * step_width
        cy = y1 + 130
        draw.ellipse((cx, cy, cx + 62, cy + 62), fill=GOLD, outline=IVORY, width=3)
        text_center(
            draw,
            (cx + 31, cy + 31),
            number,
            selected_font=font(32, bold=True),
            fill=INK,
        )
        draw.multiline_text(
            (cx + 78, cy - 1),
            label,
            font=font(25, bold=True),
            fill=IVORY,
            spacing=8,
        )

    example_tiles = (
        suited(Suit.MANZU, 1, 2, 3)
        + suited(Suit.PINZU, 4, 5, 6)
        + honors(Honor.EAST, 2)
    )
    tile_scale = 5
    tile_gap = 5
    tile_width = 8 * TILE_SPRITE_SIZE * tile_scale + 7 * tile_gap
    tile_x = (WIDTH - tile_width) // 2
    tile_y = y1 + 236
    draw_tiles(
        canvas,
        atlas,
        example_tiles,
        x=tile_x,
        y=tile_y,
        scale=tile_scale,
        gap=tile_gap,
    )
    label_y = tile_y + TILE_SPRITE_SIZE * tile_scale + 26
    text_center(
        draw,
        (tile_x + 120, label_y),
        "3枚組",
        selected_font=font(23, bold=True),
        fill=IVORY,
    )
    text_center(
        draw,
        (tile_x + 383, label_y),
        "3枚組",
        selected_font=font(23, bold=True),
        fill=IVORY,
    )
    text_center(
        draw,
        (tile_x + 597, label_y),
        "2枚組（対子）",
        selected_font=font(23, bold=True),
        fill=IVORY,
    )


def draw_yaku_card(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    atlas: Image.Image,
    card: YakuCard,
    box: tuple[int, int, int, int],
) -> None:
    x1, y1, x2, y2 = box
    rounded_panel(draw, box, fill=PANEL, width=4, radius=16)
    name = YAKU_DISPLAY_NAMES[card.yaku]
    points = DEFAULT_SCORING_CONFIG.yaku_points[card.yaku]
    draw.text((x1 + 28, y1 + 23), name, font=font(34, bold=True), fill=GOLD)
    draw.text(
        (x1 + 28, y1 + 68),
        f"（{card.reading}）",
        font=font(20),
        fill=MUTED,
    )
    badge = (x2 - 138, y1 + 23, x2 - 22, y1 + 68)
    draw.rounded_rectangle(badge, radius=10, fill=MAHOGANY, outline=GOLD, width=2)
    text_center(
        draw,
        ((badge[0] + badge[2]) // 2, (badge[1] + badge[3]) // 2),
        f"{points}点",
        selected_font=font(23, bold=True),
        fill=IVORY,
    )
    draw.text(
        (x1 + 28, y1 + 111),
        card.description,
        font=font(22, bold=True),
        fill=IVORY,
    )
    draw_tiles(
        canvas,
        atlas,
        card.example_tiles,
        x=x1 + 29,
        y=y1 + 158,
        scale=4,
        gap=4,
    )


def draw_yaku_list(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    atlas: Image.Image,
) -> None:
    draw.text(
        (MARGIN, 732),
        f"このゲームの役 {len(YAKU_CARDS)}種類",
        font=font(43, bold=True),
        fill=GOLD,
    )
    draw.text(
        (MARGIN + 475, 747),
        "※例では、ほかの役も同時に成立することがあります",
        font=font(22),
        fill=MUTED,
    )

    top = 798
    card_width = (WIDTH - MARGIN * 2 - CARD_GAP) // 2
    card_height = 256
    row_gap = 24
    for index, card in enumerate(YAKU_CARDS):
        column = index % 2
        row = index // 2
        x1 = MARGIN + column * (card_width + CARD_GAP)
        y1 = top + row * (card_height + row_gap)
        draw_yaku_card(
            canvas,
            draw,
            atlas,
            card,
            (x1, y1, x1 + card_width, y1 + card_height),
        )


def draw_footer(draw: ImageDraw.ImageDraw) -> None:
    panel_y1 = 2770
    rounded_panel(draw, (MARGIN, panel_y1, WIDTH - MARGIN, 3240), fill=TABLE)
    divider_x = 1000
    draw.line((divider_x, panel_y1 + 36, divider_x, 3202), fill=WOOD_EDGE, width=4)

    draw.text(
        (96, panel_y1 + 34),
        "覚えておきたいルール",
        font=font(34, bold=True),
        fill=GOLD,
    )
    rules = (
        "● 「3＋3＋2」または四対子で基本和了（50点）",
        "● 同じ行は、新しい役を作ればもう一度和了できる",
        "● 同じ牌4枚でカン。ドラ表示牌が増える",
        "● ドラは加点だけ。ドラだけでは和了できない",
        "● 17個のブロックを置いたらゲーム終了",
    )
    for index, rule in enumerate(rules):
        draw.text(
            (102, panel_y1 + 92 + index * 48),
            rule,
            font=font(23, bold=True),
            fill=IVORY,
        )

    draw.text(
        (1030, panel_y1 + 34),
        "操作（PC / スマホ）",
        font=font(34, bold=True),
        fill=GOLD,
    )
    controls = (
        ("矢印 / 十字", "移動"),
        ("Z / Xボタン", "左回転"),
        ("X / Bボタン", "右回転"),
        ("Space / A", "配置"),
        ("Tab / BACK", "川を見る"),
        ("Y / Yボタン", "役一覧"),
    )
    for index, (key, action) in enumerate(controls):
        y = panel_y1 + 88 + index * 41
        draw.rounded_rectangle(
            (1030, y, 1265, y + 33),
            radius=8,
            fill=MAHOGANY,
            outline=WOOD_EDGE,
            width=2,
        )
        text_center(
            draw,
            (1147, y + 16),
            key,
            selected_font=font(19, bold=True),
            fill=IVORY,
        )
        draw.text((1290, y + 3), action, font=font(21, bold=True), fill=IVORY)

    draw.text(
        (MARGIN, 3160),
        "※一般的な麻雀を8牌向けにアレンジした独自ルールです。点数は現在の仮設定です。",
        font=font(21),
        fill=MUTED,
    )
    draw.text(
        (WIDTH - MARGIN, 3192),
        "更新: 2026-07-26 / AI: GPT-5",
        font=font(17),
        fill=MUTED,
        anchor="ra",
    )


def build_guide(output_path: Path = OUTPUT_PATH) -> Path:
    validate_examples()
    if not ATLAS_PATH.exists():
        raise FileNotFoundError(f"牌アトラスが見つかりません: {ATLAS_PATH}")

    atlas = Image.open(ATLAS_PATH).convert("RGB")
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(canvas)

    draw_header(canvas, draw, atlas)
    draw_quick_start(canvas, draw, atlas)
    draw_yaku_list(canvas, draw, atlas)
    draw_footer(draw)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output_path, optimize=True)
    return output_path


def main() -> None:
    output = build_guide()
    print(f"初心者向けガイドを生成しました: {output}")


if __name__ == "__main__":
    main()
