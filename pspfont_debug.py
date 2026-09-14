from pathlib import Path
from PIL import Image


SOURCE = Path("pspfont.dat")
OUT = Path("font_debug")


def unpack_2bpp(raw: bytes, width: int, reverse_pixels: bool, invert: bool) -> Image.Image:
    """Render a byte stream as a row-major 2bpp image."""
    pixels = []
    for value in raw:
        if reverse_pixels:
            vals = ((value >> 6) & 3, (value >> 4) & 3, (value >> 2) & 3, value & 3)
        else:
            vals = (value & 3, (value >> 2) & 3, (value >> 4) & 3, (value >> 6) & 3)
        if invert:
            vals = tuple(3 - v for v in vals)
        pixels.extend(vals)
    height = (len(pixels) + width - 1) // width
    pixels.extend([0] * (width * height - len(pixels)))
    img = Image.new("L", (width, height))
    img.putdata([255 - p * 85 for p in pixels])
    return img


def decode_linear_tile(raw: bytes, high_first: bool) -> Image.Image:
    """Decode one 16x16 tile where four bytes make one scanline."""
    if len(raw) != 64:
        raise ValueError("a 16x16 2bpp tile must contain 64 bytes")
    out = []
    for y in range(16):
        for value in raw[y * 4 : y * 4 + 4]:
            if high_first:
                out.extend(((value >> 6) & 3, (value >> 4) & 3, (value >> 2) & 3, value & 3))
            else:
                out.extend((value & 3, (value >> 2) & 3, (value >> 4) & 3, (value >> 6) & 3))
    img = Image.new("L", (16, 16))
    img.putdata([255 - p * 85 for p in out])
    return img


def make_tile_sheet(data: bytes, start: int, cols: int, rows: int, high_first: bool, rotate: int) -> Image.Image:
    sheet = Image.new("L", (cols * 16, rows * 16), 255)
    for i in range(cols * rows):
        tile = data[start + i * 64 : start + (i + 1) * 64]
        if len(tile) < 64:
            break
        tile_img = decode_linear_tile(tile, high_first)
        if rotate:
            tile_img = tile_img.rotate(rotate, expand=False)
        sheet.paste(tile_img, ((i % cols) * 16, (i // cols) * 16))
    return sheet


def main() -> None:
    data = SOURCE.read_bytes()
    OUT.mkdir(exist_ok=True)
    # Try the raw font blob and the beginning of the file at likely 2bpp row widths.
    starts = {
        "file": 0,
        "table_end": 0xEEE8,
        "after_indexed_records": 0xEEE8 + 0x23DAF,
        "near_fc00": 0xFC00,
        "near_10000": 0x10000,
    }
    widths = (16, 32, 42, 64, 84, 128, 168, 256, 336, 512)
    for name, start in starts.items():
        raw = data[start : start + 0x8000]
        for width in widths:
            for reverse in (False, True):
                for invert in (False, True):
                    img = unpack_2bpp(raw, width, reverse, invert)
                    # Scale for easier visual inspection, but keep the original dimensions in the name.
                    img = img.resize((img.width * 2, img.height * 2), Image.Resampling.NEAREST)
                    img.save(OUT / f"{name}_w{width}_{'rev' if reverse else 'nat'}_{'inv' if invert else 'raw'}.png")

    tile_start = 0x1CEC4
    for high_first in (False, True):
        for rotate in (0, 90, 270):
            sheet = make_tile_sheet(data, tile_start, 10, 10, high_first, rotate)
            sheet = sheet.resize((sheet.width * 3, sheet.height * 3), Image.Resampling.NEAREST)
            sheet.save(OUT / f"tiles_0x1CEC4_{'hi' if high_first else 'lo'}_rot{rotate}.png")
            for i in range(12):
                tile = data[tile_start + i * 64 : tile_start + (i + 1) * 64]
                if len(tile) == 64:
                    t = decode_linear_tile(tile, high_first).rotate(rotate, expand=False)
                    t.resize((160, 160), Image.Resampling.NEAREST).save(
                        OUT / f"tile_{i:03d}_{'hi' if high_first else 'lo'}_rot{rotate}.png"
                    )
            if high_first is False and rotate == 90:
                for idx in (6348, 6349, 6350, 6351, 6352, 6353, 6354, 6355, 6356, 6357, 6358, 6359):
                    tile = data[tile_start + idx * 64 : tile_start + (idx + 1) * 64]
                    if len(tile) == 64:
                        decode_linear_tile(tile, high_first).rotate(rotate, expand=False).resize(
                            (160, 160), Image.Resampling.NEAREST
                        ).save(OUT / f"tail_tile_{idx:04d}.png")
    for off in (0x1CEC0, 0x1CEC4, 0x20EC4, 0x24EC4, 0x28EC4, 0x2CEC4, 0x30EC4, 0x34EC4, 0x38EC4, 0x40EC4, 0x50EC4, 0x60EC4, 0x70EC4, 0x80EC4, 0x803C4, 0x807C4, 0x80BC4, 0x88EC4, 0x8CEC4, 0x90EC4, 0x94EC4, 0x98EC4, 0x9CEC4):
        sheet = make_tile_sheet(data, off, 16, 8, False, 90)
        sheet = sheet.resize((sheet.width * 2, sheet.height * 2), Image.Resampling.NEAREST)
        sheet.save(OUT / f"tiles_{off:06X}_lo_rot90.png")


if __name__ == "__main__":
    main()
