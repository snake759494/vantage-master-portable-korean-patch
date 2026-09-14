"""Write the Wansung Hangul rasters into the Japanese pspfont.dat records.

Nothing structural changes: every record keeps its offset and width, so the
patched font is byte-identical in size and can be dropped into the ISO and
re-packed into ``init0.dat`` without moving anything.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from falcom_font import FalcomFont, GLYPH_HEIGHT
from korean_slots import HANGUL_WIDTH, build_slot_map, wansung_syllables

FONT_SIZE = 15
PALETTE_LUMINANCE = (255, 170, 85, 0)
PALETTE = [255, 255, 255, 170, 170, 170, 85, 85, 85, 0, 0, 0] + [0] * (256 * 3 - 12)


def render_rows(char: str, font: ImageFont.FreeTypeFont, width: int) -> list[list[int]]:
    """Rasterize one syllable as ``rows[y][x]`` of 2-bit ink levels."""
    left, top, right, bottom = font.getbbox(char)
    glyph_w, glyph_h = right - left, bottom - top
    if glyph_w > width or glyph_h > GLYPH_HEIGHT:
        raise ValueError(f"{char!r} needs {glyph_w}x{glyph_h}, slot is {width}x{GLYPH_HEIGHT}")

    canvas = Image.new("L", (width, GLYPH_HEIGHT), 255)
    x = (width - glyph_w) // 2 - left
    y = (GLYPH_HEIGHT - glyph_h) // 2 - top
    ImageDraw.Draw(canvas).text((x, y), char, font=font, fill=0)

    pixels = list(canvas.getdata())
    return [
        [
            min(range(4), key=lambda level: abs(pixels[row * width + col] - PALETTE_LUMINANCE[level]))
            for col in range(width)
        ]
        for row in range(GLYPH_HEIGHT)
    ]


def preview_sheet(rasters: list[list[list[int]]], columns: int = 32) -> Image.Image:
    rows = (len(rasters) + columns - 1) // columns
    sheet = Image.new("P", (columns * HANGUL_WIDTH, rows * GLYPH_HEIGHT), 0)
    sheet.putpalette(PALETTE)
    for index, raster in enumerate(rasters):
        tile = Image.new("P", (HANGUL_WIDTH, GLYPH_HEIGHT), 0)
        tile.putpalette(PALETTE)
        tile.putdata([value for row in raster for value in row])
        sheet.paste(tile, ((index % columns) * HANGUL_WIDTH, (index // columns) * GLYPH_HEIGHT))
    return sheet


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font", type=Path, default=Path("pspfont.dat"))
    parser.add_argument("--ttf", type=Path, default=Path("NanumSquareNeo-cBd.ttf"))
    parser.add_argument("--out", type=Path, default=Path("korean_font_slotmapped"))
    args = parser.parse_args()

    source = args.font.read_bytes()
    font = FalcomFont(source)
    slot_map = build_slot_map(font)
    ttf = ImageFont.truetype(str(args.ttf), FONT_SIZE)

    syllables = wansung_syllables()
    rasters = [render_rows(char, ttf, HANGUL_WIDTH) for char in syllables]
    for char, raster in zip(syllables, rasters):
        index = font.index_of(slot_map[char])
        font.write_glyph(index, raster)

    patched = font.to_bytes()
    if len(patched) != len(source):
        raise ValueError("the patched font changed size")

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "pspfont_korean.dat").write_bytes(patched)

    sheet = preview_sheet(rasters)
    sheet.save(args.out / "korean_wansung_2350.png")
    sheet.resize((sheet.width * 4, sheet.height * 4), Image.Resampling.NEAREST).save(
        args.out / "korean_wansung_2350_4x.png"
    )

    with (args.out / "korean_slot_map.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["order", "korean", "unicode", "sjis_code", "replaced_kanji", "glyph_index", "byte_offset"]
        )
        for order, char in enumerate(syllables):
            code = slot_map[char]
            index = font.index_of(code)
            record = font.record(index)
            writer.writerow(
                [
                    order,
                    char,
                    f"U+{ord(char):04X}",
                    f"0x{code:04X}",
                    bytes((code >> 8, code & 0xFF)).decode("cp932"),
                    index,
                    f"0x{font.data_base + record.byte_offset:X}",
                ]
            )

    # Verify every syllable round-trips through the real glyph lookup.
    check = FalcomFont(patched)
    for char, raster in zip(syllables, rasters):
        if check.read_glyph(check.index_of(slot_map[char])) != raster:
            raise ValueError(f"round-trip failed for {char!r}")

    print(f"Wrote {len(syllables)} Hangul glyphs at width {HANGUL_WIDTH}")
    print(f"Font: {args.out / 'pspfont_korean.dat'} sha256={hashlib.sha256(patched).hexdigest()}")


if __name__ == "__main__":
    main()
