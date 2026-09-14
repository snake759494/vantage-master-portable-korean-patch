"""Extract the Japanese kanji raster from Falcom's PSP pspfont.dat.

This game stores the kanji raster as 16x16 tiles in the NGP 2bpp layout
used by CrystalTile2/YY-CHR.  The accompanying jis2utf.bin file supplies
the compact JIS-code-to-Unicode map used to place each tile in the grid.
"""

from __future__ import annotations

import argparse
import csv
import struct
from pathlib import Path

from PIL import Image


TILE_W = 16
TILE_H = 16
TILE_BYTES = 64  # 16 * 16 * 2 bits / 8
KANJI_OFFSET = 0x1CEC4
JIS_FIRST = 0x3021
JIS_LAST = 0x7426

# Palette index 0 is the background, followed by the three 2bpp shades.
# Keeping the output as a four-color indexed PNG makes it safe to edit and
# round-trip without introducing antialiasing colors.
PALETTE = [255, 255, 255, 170, 170, 170, 85, 85, 85, 0, 0, 0] + [0] * (256 * 3 - 12)


def decode_ngp_tile(raw: bytes) -> Image.Image:
    """Decode one 16x16 NGP 2bpp-reverse tile.

    NGP's packed 2bpp format stores four two-bit pixels per byte, but the
    byte/pixel groups are read from right to left.  For a 16-pixel row the
    stored order is therefore ``p12..p15, p8..p11, p4..p7, p0..p3`` and
    each group is least-significant pair first.  The old extractor treated
    the row as a normal left-to-right packed stream and then rotated it;
    that produced a misleading preview and caused newly inserted glyphs to
    be transformed by the game.
    """

    if len(raw) != TILE_BYTES:
        raise ValueError(f"expected {TILE_BYTES} bytes, got {len(raw)}")

    pixels: list[int] = []
    for y in range(TILE_H):
        row = raw[y * 4 : y * 4 + 4]
        for x in range(TILE_W):
            stored_x = TILE_W - 1 - x
            value = row[stored_x // 4]
            pixels.append((value >> ((stored_x & 3) * 2)) & 3)

    tile = Image.new("P", (TILE_W, TILE_H), 0)
    tile.putdata(pixels)
    tile.putpalette(PALETTE)
    return tile.rotate(90, expand=False)


def read_jis2utf(path: Path) -> dict[int, int]:
    data = path.read_bytes()
    if len(data) != 0x20000:
        raise ValueError(f"unexpected jis2utf.bin size: {len(data)} bytes")
    values = struct.unpack("<65536H", data)
    return {code: value for code, value in enumerate(values) if value}


def kanji_entries(jis2utf: dict[int, int]) -> list[tuple[int, int, str]]:
    entries: list[tuple[int, int, str]] = []
    for jis_code in range(JIS_FIRST, JIS_LAST + 1):
        value = jis2utf.get(jis_code, 0)
        if not value:
            continue
        entries.append((jis_code, value, chr(value)))
    return entries


def paste_kanji_sheet(
    source: bytes,
    entries: list[tuple[int, int, str]],
    columns: int,
    rows: int,
) -> Image.Image:
    sheet = Image.new("P", (columns * TILE_W, rows * TILE_H), 0)
    sheet.putpalette(PALETTE)
    for tile_index, (jis_code, _unicode, _char) in enumerate(entries):
        start = KANJI_OFFSET + tile_index * TILE_BYTES
        tile = decode_ngp_tile(source[start : start + TILE_BYTES])
        sheet.paste(tile, ((tile_index % columns) * TILE_W, (tile_index // columns) * TILE_H))
    return sheet


def paste_jis_grid(source: bytes, entries: list[tuple[int, int, str]]) -> Image.Image:
    first_row, last_row = JIS_FIRST >> 8, JIS_LAST >> 8
    first_col, last_col = 0x21, 0x7E
    columns = last_col - first_col + 1
    rows = last_row - first_row + 1
    sheet = Image.new("P", (columns * TILE_W, rows * TILE_H), 0)
    sheet.putpalette(PALETTE)
    for tile_index, (jis_code, _unicode, _char) in enumerate(entries):
        start = KANJI_OFFSET + tile_index * TILE_BYTES
        tile = decode_ngp_tile(source[start : start + TILE_BYTES])
        col = (jis_code & 0xFF) - first_col
        row = (jis_code >> 8) - first_row
        sheet.paste(tile, (col * TILE_W, row * TILE_H))
    return sheet


def save_nearest_scaled(image: Image.Image, path: Path, scale: int) -> None:
    image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST).save(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--font", type=Path, default=Path("pspfont.dat"))
    parser.add_argument("--jis2utf", type=Path, default=Path("jis2utf.bin"))
    parser.add_argument("--out", type=Path, default=Path("font_extraction"))
    args = parser.parse_args()

    source = args.font.read_bytes()
    if len(source) < KANJI_OFFSET + TILE_BYTES:
        raise ValueError("pspfont.dat is shorter than the kanji raster offset")

    mapping = read_jis2utf(args.jis2utf)
    entries = kanji_entries(mapping)
    expected = 6355
    if len(entries) != expected:
        raise ValueError(f"expected {expected} kanji map entries, got {len(entries)}")

    end = KANJI_OFFSET + len(entries) * TILE_BYTES
    if end > len(source):
        raise ValueError("pspfont.dat ends before the complete kanji raster")

    args.out.mkdir(parents=True, exist_ok=True)

    compact_columns = 32
    compact_rows = (len(entries) + compact_columns - 1) // compact_columns
    compact = paste_kanji_sheet(source, entries, compact_columns, compact_rows)
    compact.save(args.out / "japanese_kanji_compact_16x16.png")
    save_nearest_scaled(compact, args.out / "japanese_kanji_compact_4x.png", 4)

    jis_grid = paste_jis_grid(source, entries)
    jis_grid.save(args.out / "japanese_kanji_jis_grid_16x16.png")
    save_nearest_scaled(jis_grid, args.out / "japanese_kanji_jis_grid_4x.png", 4)

    with (args.out / "japanese_kanji_map.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["tile_index", "jis_code", "unicode", "character", "file_offset"])
        for tile_index, (jis_code, unicode_value, char) in enumerate(entries):
            writer.writerow(
                [
                    tile_index,
                    f"0x{jis_code:04X}",
                    f"U+{unicode_value:04X}",
                    char,
                    f"0x{KANJI_OFFSET + tile_index * TILE_BYTES:X}",
                ]
            )

    info = (
        "Vantage Master Portable (1.01) Japanese kanji extraction\n"
        "=========================================================\n"
        f"Source: {args.font}\n"
        f"Raster offset: 0x{KANJI_OFFSET:X}\n"
        f"Raster end (exclusive): 0x{end:X}\n"
        f"Tiles: {len(entries)}\n"
        "Tile size: 16x16 pixels, 64 bytes\n"
        "Encoding: NGP 2bpp-reverse (right-to-left groups, low two-bit pair first)\n"
        "Palette: 4-color grayscale (white, light gray, dark gray, black)\n"
        f"JIS code range represented: 0x{JIS_FIRST:04X}..0x{JIS_LAST:04X} (non-empty kanji entries only)\n"
        "The compact PNG preserves tile order; the JIS-grid PNG places blank cells for unused JIS positions.\n"
    )
    (args.out / "README.txt").write_text(info, encoding="utf-8")

    print(f"Extracted {len(entries)} kanji tiles to {args.out}")
    print(f"Raster bytes: 0x{KANJI_OFFSET:X}..0x{end - 1:X}")


if __name__ == "__main__":
    main()
