"""Render patched strings exactly the way the game resolves them.

Bytes are read straight out of the patched executable, split into glyph codes
the way a Shift-JIS reader would, and looked up through the font's range table
and record table.  Whatever this draws is what the PSP will draw.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

from falcom_font import GLYPH_HEIGHT, FalcomFont

INK = ((255, 255, 255), (176, 176, 176), (92, 92, 92), (16, 16, 16))
BACKGROUND = (24, 32, 56)
LINE_GAP = 4
MARGIN = 10


def split_codes(data: bytes) -> list[int]:
    codes: list[int] = []
    index = 0
    while index < len(data):
        lead = data[index]
        if lead < 0x80 or 0xA0 <= lead <= 0xDF:
            codes.append(lead)
            index += 1
        else:
            codes.append((lead << 8) | data[index + 1])
            index += 2
    return codes


def read_field(data: bytes, offset: int) -> bytes:
    end = data.find(b"\0", offset)
    return data[offset:end]


def draw_line(image: Image.Image, font: FalcomFont, codes: list[int], x: int, y: int) -> int:
    pixels = image.load()
    for code in codes:
        index = font.index_of(code)
        if index is None:
            continue
        record = font.record(index)
        for row_index, row in enumerate(font.read_glyph(index)):
            for column, value in enumerate(row):
                if value:
                    pixels[x + column, y + row_index] = INK[value]
        x += record.width
    return x


def render(font: FalcomFont, raw: bytes) -> Image.Image:
    lines = [split_codes(part) for part in raw.split(b"\n")]
    widths = [
        sum(font.record(font.index_of(code)).width for code in line if font.index_of(code) is not None)
        for line in lines
    ]
    width = max(widths, default=0) + MARGIN * 2
    height = len(lines) * (GLYPH_HEIGHT + LINE_GAP) - LINE_GAP + MARGIN * 2
    image = Image.new("RGB", (max(width, 32), max(height, 32)), BACKGROUND)
    for row, line in enumerate(lines):
        draw_line(image, font, line, MARGIN, MARGIN + row * (GLYPH_HEIGHT + LINE_GAP))
    return image


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boot", type=Path, default=Path("korean_opening_build/BOOT.BIN.patched"))
    parser.add_argument("--font", type=Path, default=Path("korean_font_slotmapped/pspfont_korean.dat"))
    parser.add_argument("--out", type=Path, default=Path("korean_opening_build/preview.png"))
    parser.add_argument("--scale", type=int, default=2)
    args = parser.parse_args()

    font = FalcomFont(args.font.read_bytes())
    boot = args.boot.read_bytes()

    shots = [
        ("클래스 선택", 0x1645F4),
        ("클래스 소개 (비스트)", 0x163980),
        ("마스터 자질", 0x162FD8),
        ("카드 선택", 0x163DC0),
        ("멜렛 등장", 0x164028),
        ("질문", 0x16406C),
        ("소망", 0x16409C),
        ("자기소개 요청", 0x1640EC),
        ("네이티얼 수여", 0x16414C),
        ("출발", 0x164190),
        ("아이템 획득", 0x1642B0),
        ("이동 튜토리얼", 0x15E1FC),
        ("전투 시작 확인", 0x164D04),
        ("모드 선택", 0x161D5C),
        ("시스템 데이터", 0x16275C),
        ("적 사고 타입", 0x16BF60),
        ("제한 시간", 0x16C07C),
        ("획득 아이템", 0x16C40C),
    ]

    panels = [(label, render(font, read_field(boot, offset))) for label, offset in shots]
    gap = 12
    width = max(panel.width for _label, panel in panels)
    height = sum(panel.height for _label, panel in panels) + gap * (len(panels) - 1)
    sheet = Image.new("RGB", (width, height), (10, 12, 20))
    y = 0
    for _label, panel in panels:
        sheet.paste(panel, (0, y))
        y += panel.height + gap

    args.out.parent.mkdir(parents=True, exist_ok=True)
    scaled = sheet.resize((sheet.width * args.scale, sheet.height * args.scale), Image.Resampling.NEAREST)
    scaled.save(args.out)
    print(f"Wrote {args.out} ({scaled.width}x{scaled.height})")
    for label, offset in shots:
        print(f"  {label} @0x{offset:X}")


if __name__ == "__main__":
    main()
