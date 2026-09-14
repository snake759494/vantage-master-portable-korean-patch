"""Render the 2,350 KS X 1001 Hangul syllables into the extracted kanji block.

The output keeps the original 16x16 NGP 2bpp tile format.  It creates PNG
preview sheets and a separate patched pspfont.dat copy; the original source
font is never modified.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


TILE_W = 16
TILE_H = 16
TILE_BYTES = 64
KANJI_OFFSET = 0x1CEC4
KANJI_COUNT = 6355
KOREAN_COUNT = 2350
JIS_FIRST_ROW = 0x30
JIS_FIRST_COL = 0x21
JIS_COLUMNS = 94
JIS_ROWS = 69
# 15px keeps every Wansung syllable within the 16x16 tile without clipping.
FONT_SIZE = 15
# The game/NGP font reader applies a clockwise-looking +90-degree transform
# to the stored tile.  Pillow's rotate() uses the opposite sign convention,
# so an upright source glyph must be rotated 270 degrees before packing.
STORED_TILE_ROTATION = 270

# Palette index 0 is white/background; index 3 is black/foreground.
PALETTE = [255, 255, 255, 170, 170, 170, 85, 85, 85, 0, 0, 0] + [
    0
] * (256 * 3 - 12)
PALETTE_LUMINANCE = (255, 170, 85, 0)


def wansung_syllables() -> list[tuple[bytes, str]]:
    """Return the 2,350 KS X 1001 Hangul syllables in EUC-KR byte order."""

    items: list[tuple[bytes, str]] = []
    for codepoint in range(0xAC00, 0xD7A4):
        char = chr(codepoint)
        try:
            encoded = char.encode("euc_kr")
        except UnicodeEncodeError:
            continue
        if (
            len(encoded) == 2
            and 0xB0 <= encoded[0] <= 0xC8
            and 0xA1 <= encoded[1] <= 0xFE
        ):
            items.append((encoded, char))
    items.sort(key=lambda item: item[0])
    if len(items) != KOREAN_COUNT:
        raise ValueError(f"expected {KOREAN_COUNT} Wansung syllables, got {len(items)}")
    return items


def load_kanji_map(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != KANJI_COUNT:
        raise ValueError(f"expected {KANJI_COUNT} kanji map rows, got {len(rows)}")
    return rows


def quantize_luminance(image: Image.Image) -> Image.Image:
    """Convert an antialiased L image to the font's four grayscale indices."""

    if image.mode != "L":
        image = image.convert("L")
    pixels = [
        min(range(4), key=lambda index: abs(value - PALETTE_LUMINANCE[index]))
        for value in image.getdata()
    ]
    result = Image.new("P", image.size, 0)
    result.putdata(pixels)
    result.putpalette(PALETTE)
    return result


def render_glyph(char: str, font: ImageFont.FreeTypeFont) -> Image.Image:
    """Render one centered 16x16 glyph and reduce it to four palette levels."""

    bbox = font.getbbox(char)
    left, top, right, bottom = bbox
    width = right - left
    height = bottom - top
    if width > TILE_W or height > TILE_H:
        raise ValueError(f"glyph {char!r} exceeds {TILE_W}x{TILE_H}: {bbox}")

    canvas = Image.new("L", (TILE_W, TILE_H), 255)
    x = (TILE_W - width) // 2 - left
    y = (TILE_H - height) // 2 - top
    ImageDraw.Draw(canvas).text((x, y), char, font=font, fill=0)
    return quantize_luminance(canvas)


def save_nearest_scaled(image: Image.Image, path: Path, scale: int = 4) -> None:
    scaled = image.resize(
        (image.width * scale, image.height * scale), Image.Resampling.NEAREST
    )
    scaled.save(path)


def new_sheet(width_tiles: int, height_tiles: int) -> Image.Image:
    sheet = Image.new("P", (width_tiles * TILE_W, height_tiles * TILE_H), 0)
    sheet.putpalette(PALETTE)
    return sheet


def make_compact_sheet(glyphs: list[Image.Image], columns: int = 32) -> Image.Image:
    rows = math.ceil(len(glyphs) / columns)
    sheet = new_sheet(columns, rows)
    for index, glyph in enumerate(glyphs):
        sheet.paste(glyph, ((index % columns) * TILE_W, (index // columns) * TILE_H))
    return sheet


def jis_position(jis_code: int) -> tuple[int, int]:
    col = (jis_code & 0xFF) - JIS_FIRST_COL
    row = (jis_code >> 8) - JIS_FIRST_ROW
    if not (0 <= col < JIS_COLUMNS and 0 <= row < JIS_ROWS):
        raise ValueError(f"JIS code is outside the expected grid: 0x{jis_code:04X}")
    return col * TILE_W, row * TILE_H


def make_jis_sheet(
    map_rows: list[dict[str, str]], glyphs: list[Image.Image], base: Image.Image | None = None
) -> Image.Image:
    if base is None:
        sheet = new_sheet(JIS_COLUMNS, JIS_ROWS)
    else:
        sheet = base.convert("P")
        sheet.putpalette(PALETTE)
    for row, glyph in zip(map_rows[: len(glyphs)], glyphs):
        x, y = jis_position(int(row["jis_code"], 16))
        sheet.paste(glyph, (x, y))
    return sheet


def encode_ngp_tile(tile: Image.Image) -> bytes:
    """Encode an upright tile as the on-disk NGP 2bpp-reverse layout.

    The font renderer rotates the decoded tile by +90 degrees.  Applying the
    inverse here makes the glyph upright in-game instead of rotated.
    """

    tile = tile.convert("P").rotate(STORED_TILE_ROTATION, expand=False)

    # NGP stores each row from right to left.  Within each byte the first
    # stored two-bit pair is the least-significant pair.  This is the
    # ``2bpp-reverse`` layout used by tile editors; it is a horizontal
    # reversal, not a 90-degree rotation.
    pixels = list(tile.getdata())
    result = bytearray()
    for y in range(TILE_H):
        row = pixels[y * TILE_W : (y + 1) * TILE_W]
        encoded_row = [0] * (TILE_W // 4)
        for x, value in enumerate(row):
            stored_x = TILE_W - 1 - x
            encoded_row[stored_x // 4] |= (value & 3) << ((stored_x & 3) * 2)
        result.extend(encoded_row)
    if len(result) != TILE_BYTES:
        raise AssertionError("encoded tile has an unexpected size")
    return bytes(result)


def make_patched_font(source: bytes, glyphs: list[Image.Image]) -> bytes:
    result = bytearray(source)
    end = KANJI_OFFSET + len(glyphs) * TILE_BYTES
    if end > len(result):
        raise ValueError("source font ends before the replacement block")
    for index, glyph in enumerate(glyphs):
        start = KANJI_OFFSET + index * TILE_BYTES
        result[start : start + TILE_BYTES] = encode_ngp_tile(glyph)
    return bytes(result)


def write_map(
    path: Path,
    map_rows: list[dict[str, str]],
    korean: list[tuple[bytes, str]],
) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "replacement_index",
                "jis_code",
                "original_unicode",
                "original_character",
                "korean_unicode",
                "korean_character",
                "euc_kr",
                "file_offset",
            ]
        )
        for index, ((encoded, korean_char), row) in enumerate(
            zip(korean, map_rows[:KOREAN_COUNT])
        ):
            writer.writerow(
                [
                    index,
                    row["jis_code"],
                    row["unicode"],
                    row["character"],
                    f"U+{ord(korean_char):04X}",
                    korean_char,
                    encoded.hex(" ").upper(),
                    row["file_offset"],
                ]
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font", type=Path, default=Path("pspfont.dat"))
    parser.add_argument("--ttf", type=Path, default=Path("NanumSquareNeo-cBd.ttf"))
    parser.add_argument(
        "--kanji-map",
        type=Path,
        default=Path("font_extraction/japanese_kanji_map.csv"),
    )
    parser.add_argument(
        "--original-jis-grid",
        type=Path,
        default=Path("font_extraction/japanese_kanji_jis_grid_16x16.png"),
    )
    parser.add_argument(
        "--original-compact",
        type=Path,
        default=Path("font_extraction/japanese_kanji_compact_16x16.png"),
    )
    parser.add_argument("--out", type=Path, default=Path("korean_font_test"))
    args = parser.parse_args()

    source = args.font.read_bytes()
    korean = wansung_syllables()
    map_rows = load_kanji_map(args.kanji_map)
    font = ImageFont.truetype(args.ttf, FONT_SIZE)
    glyphs = [render_glyph(char, font) for _encoded, char in korean]

    args.out.mkdir(parents=True, exist_ok=True)

    korean_compact = make_compact_sheet(glyphs)
    korean_compact.save(args.out / "korean_wansung_2350_compact_16x16.png")
    save_nearest_scaled(
        korean_compact, args.out / "korean_wansung_2350_compact_4x.png"
    )

    korean_jis = make_jis_sheet(map_rows, glyphs)
    korean_jis.save(args.out / "korean_wansung_2350_jis_grid_16x16.png")
    save_nearest_scaled(korean_jis, args.out / "korean_wansung_2350_jis_grid_4x.png")

    original_jis = Image.open(args.original_jis_grid)
    mixed_jis = make_jis_sheet(map_rows, glyphs, original_jis)
    mixed_jis.save(args.out / "korean_wansung_2350_mixed_jis_grid_16x16.png")
    save_nearest_scaled(
        mixed_jis, args.out / "korean_wansung_2350_mixed_jis_grid_4x.png"
    )

    original_compact = Image.open(args.original_compact)
    # Rebuild the full compact atlas with Korean tiles in the first 2,350 slots.
    mixed_compact = original_compact.copy().convert("P")
    mixed_compact.putpalette(PALETTE)
    for index, glyph in enumerate(glyphs):
        mixed_compact.paste(glyph, ((index % 32) * TILE_W, (index // 32) * TILE_H))
    mixed_compact.save(args.out / "korean_wansung_2350_mixed_compact_16x16.png")
    save_nearest_scaled(
        mixed_compact, args.out / "korean_wansung_2350_mixed_compact_4x.png"
    )

    patched = make_patched_font(source, glyphs)
    (args.out / "pspfont_korean_2350_test.dat").write_bytes(patched)
    write_map(args.out / "korean_wansung_2350_map.csv", map_rows, korean)

    end = KANJI_OFFSET + KOREAN_COUNT * TILE_BYTES
    info = (
        "Vantage Master Portable (1.01) Korean font replacement test\n"
        "==============================================================\n"
        f"Source font: {args.font}\n"
        f"Test font copy: pspfont_korean_2350_test.dat\n"
        f"TTF: {args.ttf}\n"
        f"Replacement block: 0x{KANJI_OFFSET:X}..0x{end - 1:X}\n"
        f"Replaced tiles: {KOREAN_COUNT} of {KANJI_COUNT}\n"
        "Korean order: 2,350 KS X 1001/Wansung syllables sorted by EUC-KR bytes\n"
        f"Rasterization: {FONT_SIZE}px, centered in 16x16, antialiased then quantized to 4 colors\n"
        "Tile format: NGP 2bpp-reverse, right-to-left groups, low two-bit pair first; stored inverse rotation 270 degrees\n"
        "The original pspfont.dat is unchanged. The mixed PNGs retain Japanese glyphs after the first 2,350 slots.\n"
    )
    (args.out / "README.txt").write_text(info, encoding="utf-8")

    print(f"Rendered {len(glyphs)} Korean syllables to {args.out}")
    print(f"Patched test copy: {args.out / 'pspfont_korean_2350_test.dat'}")


if __name__ == "__main__":
    main()
