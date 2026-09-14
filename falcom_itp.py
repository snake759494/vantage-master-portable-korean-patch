"""Read and write the Falcom ITP textures this game ships (revisions 1004/1005).

Both revisions share a header::

    u32 revision (1004 or 1005)
    u32 width
    u32 height
    u32 palette colour count
    FREADP stream -> palette, 4 bytes per colour, stored R G B A

Revision 1005 stores that table as differences: every byte is the step from the
previous colour's byte, wrapping at 256.  Read literally such a palette holds no
red at all -- the first byte of each entry is a step, and the steps sum to
exactly 255 across the table because Falcom sorts a palette by red.  Revision
1004 stores the colours outright.

1004 then stores the 8bpp index plane directly as one more FREADP stream.
1005 prefixes the stream with its uncompressed size and stores the indices in
Falcom's "AFastMode2" form: the plane is cut into 16x8 blocks, each block gets
a local palette of at most 16 entries, and its pixels become 4-bit indices into
that local palette.

Both revisions store the blocks in Pfp_1 swizzle order.
"""

from __future__ import annotations

import struct
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from patch_packed_pspfont import bzip_decompress, ed7_compress

BLOCK_W = 16
BLOCK_H = 8
MAX_LOCAL_COLORS = 16


class Reader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0

    def read(self, size: int) -> bytes:
        if size < 0 or self.pos + size > len(self.data):
            raise ValueError(f"read beyond end at 0x{self.pos:X}, size {size}")
        chunk = self.data[self.pos : self.pos + size]
        self.pos += size
        return chunk

    def u8(self) -> int:
        return self.read(1)[0]

    def u16(self) -> int:
        return int.from_bytes(self.read(2), "little")

    def u32(self) -> int:
        return int.from_bytes(self.read(4), "little")


def read_freadp(reader: Reader) -> bytes:
    if int.from_bytes(reader.data[reader.pos : reader.pos + 4], "little") & 0x80000000:
        raise NotImplementedError("C77 FREADP streams are not supported")
    in_size = reader.u32()
    start = reader.pos
    out_size = reader.u32()
    chunk_count = reader.u32()
    out = bytearray()
    for index in range(chunk_count):
        chunk_size = reader.u16()
        out.extend(bzip_decompress(reader.read(chunk_size - 2)))
        continuation = reader.u8()
        if continuation != (1 if index < chunk_count - 1 else 0):
            raise ValueError(f"bad FREADP continuation at chunk {index}")
    if reader.pos != start + in_size:
        raise ValueError("FREADP input size mismatch")
    if len(out) == out_size + 1:
        out.pop()  # Falcom's writer emits one dummy byte in the trailing chunk
    if len(out) != out_size:
        raise ValueError(f"FREADP output size mismatch: {len(out)} != {out_size}")
    return bytes(out)



def read_palette(raw: bytes, revision: int) -> list[tuple[int, int, int, int]]:
    """The colour table, undoing revision 1005's delta coding.

    Read literally, a 1005 palette has no red in it at all -- every first byte
    is under about 25 -- because those bytes are steps, not values, and red is
    the key the table is sorted by, so its steps sum to exactly 255.  The other
    three channels are stepped the same way and wrap round 256 freely; running
    all four up is what turns the atlas from confetti into artwork.
    """
    colors = [tuple(raw[i : i + 4]) for i in range(0, len(raw), 4)]
    if revision != 1005:
        return colors
    out = []
    running = (0, 0, 0, 0)
    for entry in colors:
        running = tuple((a + b) & 0xFF for a, b in zip(running, entry))
        out.append(running)
    return out


def write_palette(palette: list[tuple[int, int, int, int]], revision: int) -> bytes:
    raw = bytearray()
    previous = (0, 0, 0, 0)
    for color in palette:
        if revision == 1005:
            raw.extend((a - b) & 0xFF for a, b in zip(color, previous))
            previous = color
        else:
            raw.extend(color)
    return bytes(raw)


def swizzle_map(width: int, height: int) -> list[int]:
    """Stored position -> linear position, for Falcom's Pfp_1 block order."""
    if width % BLOCK_W or height % BLOCK_H:
        raise ValueError(f"{width}x{height} is not 16x8 block aligned")
    mapping: list[int] = []
    for block_y in range(height // BLOCK_H):
        for block_x in range(width // BLOCK_W):
            for row in range(BLOCK_H):
                base = (block_y * BLOCK_H + row) * width + block_x * BLOCK_W
                mapping.extend(range(base, base + BLOCK_W))
    return mapping


def unswizzle(data: bytes, width: int, height: int) -> bytes:
    out = bytearray(len(data))
    for stored, linear in enumerate(swizzle_map(width, height)):
        out[linear] = data[stored]
    return bytes(out)


def swizzle(data: bytes, width: int, height: int) -> bytes:
    mapping = swizzle_map(width, height)
    return bytes(data[linear] for linear in mapping)


def read_nibbles(data: bytes, pos: int, count: int) -> tuple[list[int], int]:
    values: list[int] = []
    for _ in range((count + 1) // 2):
        byte = data[pos]
        pos += 1
        values.append(byte >> 4)
        if len(values) < count:
            values.append(byte & 0x0F)
    return values, pos


def write_nibbles(out: bytearray, values: list[int]) -> None:
    for index in range(0, len(values), 2):
        high = values[index]
        low = values[index + 1] if index + 1 < len(values) else 0
        out.append((high << 4) | low)


def decode_afastmode2(data: bytes, width: int, height: int) -> bytes:
    block_count = (height // BLOCK_H) * (width // BLOCK_W)
    counts, pos = read_nibbles(data, 0, block_count)
    counts = [value + 1 if value else 0 for value in counts]
    palette_end = pos + sum(counts)
    local_palettes = data[pos:palette_end]
    pos = palette_end
    mode = data[pos]
    pos += 1
    if mode != 0:
        raise NotImplementedError(f"AFastMode2 sub-mode {mode}")

    pixels = bytearray()
    palette_pos = 0
    for count in counts:
        if not count:
            pixels.extend(bytes(BLOCK_W * BLOCK_H))
            continue
        colors = local_palettes[palette_pos : palette_pos + count]
        palette_pos += count
        indices, pos = read_nibbles(data, pos, BLOCK_W * BLOCK_H)
        pixels.extend(bytes(colors[index] for index in indices))
    if pos != len(data):
        raise ValueError(f"AFastMode2 trailing data at 0x{pos:X} of 0x{len(data):X}")
    return bytes(pixels)


def reduce_block_colors(
    chunk: bytes,
    palette: list[tuple[int, int, int, int]],
    histogram: Counter,
) -> bytes:
    """Fold a block's rarest colours into their nearest neighbours.

    A 16x8 block may hold at most 16 palette entries.  A replacement label that
    lands on a block of busy artwork can push it past that; rather than refuse
    the edit, the least-used colours are merged into the closest colour that
    stays, which changes a handful of pixels in one block.
    """
    ordered = sorted(histogram, key=lambda value: (-histogram[value], value))
    keep, drop = ordered[:MAX_LOCAL_COLORS], ordered[MAX_LOCAL_COLORS:]

    def distance(a: int, b: int) -> int:
        return sum((p - q) ** 2 for p, q in zip(palette[a], palette[b]))

    swap = {value: min(keep, key=lambda other: distance(value, other)) for value in drop}
    return bytes(swap.get(value, value) for value in chunk)


def encode_afastmode2(stored: bytes, width: int, height: int, palette=None) -> bytes:
    block_count = (height // BLOCK_H) * (width // BLOCK_W)
    counts: list[int] = []
    local_palettes = bytearray()
    index_stream: list[list[int]] = []

    for block in range(block_count):
        chunk = stored[block * BLOCK_W * BLOCK_H : (block + 1) * BLOCK_W * BLOCK_H]
        # Falcom orders each block's local palette by falling pixel count and,
        # on a tie, by rising global palette index.  Matching that keeps the
        # compressed stream the same size as the original file's.
        histogram = Counter(chunk)
        distinct = sorted(histogram, key=lambda value: (-histogram[value], value))
        if len(distinct) > MAX_LOCAL_COLORS and palette is not None:
            chunk = reduce_block_colors(chunk, palette, histogram)
            histogram = Counter(chunk)
            distinct = sorted(histogram, key=lambda value: (-histogram[value], value))
        if distinct == [0]:
            counts.append(0)
            continue
        if len(distinct) == 1:
            distinct.append(distinct[0])  # the nibble count starts at two
        if len(distinct) > MAX_LOCAL_COLORS:
            raise ValueError(f"block {block} still needs {len(distinct)} colours")
        counts.append(len(distinct) - 1)
        local_palettes.extend(distinct)
        lookup = {value: position for position, value in enumerate(distinct)}
        index_stream.append([lookup[value] for value in chunk])

    out = bytearray()
    write_nibbles(out, counts)
    out.extend(local_palettes)
    out.append(0)
    for indices in index_stream:
        write_nibbles(out, indices)
    return bytes(out)


@dataclass
class ItpImage:
    revision: int
    width: int
    height: int
    palette: list[tuple[int, int, int, int]]  # RGBA
    pixels: bytearray  # linear, row-major palette indices
    ccpi: tuple[int, int, int, int] | None = None  # version, cell w, cell h, flags

    def to_rgba(self) -> bytes:
        flat = bytearray()
        for index in self.pixels:
            flat.extend(self.palette[index])
        return bytes(flat)


def load_ccpi(reader: Reader) -> ItpImage:
    """Revision 1006: a CCPI chunk holding the palette and the cell stream."""
    data_size = reader.u32()
    if reader.read(4) != CCPI_TAG:
        raise ValueError("revision 1006 without a CCPI chunk")
    version = reader.u16()
    color_count = reader.u16()
    cell_w = 1 << reader.u8()
    cell_h = 1 << reader.u8()
    width = reader.u16()
    height = reader.u16()
    flags = reader.u16()
    if version not in (6, 7):
        raise NotImplementedError(f"CCPI version {version}")
    if flags & (1 << 9):
        raise NotImplementedError("CCPI with an external palette")

    payload = read_freadp(reader) if flags & (1 << 15) else reader.read(data_size - 16)
    if len(payload) != data_size - 16:
        raise ValueError("CCPI payload size mismatch")

    palette = [
        tuple(payload[i : i + 4]) for i in range(0, color_count * 4, 4)
    ]
    pos = color_count * 4
    pixels = bytearray(width * height)
    for top in range(0, height, cell_h):
        for left in range(0, width, cell_w):
            this_w = min(cell_w, width - left)
            this_h = min(cell_h, height - top)
            cell, pos = decode_ccpi_cell(payload, pos, this_w * this_h)
            rows = cell_to_rows(cell, this_w, this_h)
            for row in range(this_h):
                start = (top + row) * width + left
                pixels[start : start + this_w] = rows[row * this_w : (row + 1) * this_w]
    if pos != len(payload):
        raise ValueError(f"CCPI trailing data at {pos} of {len(payload)}")
    return ItpImage(1006, width, height, palette, pixels, (version, cell_w, cell_h, flags))


def load(path: Path) -> ItpImage:
    reader = Reader(Path(path).read_bytes())
    revision = reader.u32()
    if revision == 1006:
        image = load_ccpi(reader)
        if reader.pos != len(reader.data):
            raise ValueError(f"trailing bytes at 0x{reader.pos:X}")
        return image
    if revision not in (1004, 1005):
        raise NotImplementedError(f"ITP revision {revision}")
    width = reader.u32()
    height = reader.u32()
    color_count = reader.u32()

    raw_palette = read_freadp(reader)
    if len(raw_palette) != color_count * 4:
        raise ValueError("palette size mismatch")
    palette = read_palette(raw_palette, revision)

    if revision == 1005:
        expected = reader.u32()
        stream = read_freadp(reader)
        if len(stream) != expected:
            raise ValueError("AFastMode2 stream size mismatch")
        stored = decode_afastmode2(stream, width, height)
    else:
        stored = read_freadp(reader)
        if len(stored) != width * height:
            raise ValueError("8bpp plane size mismatch")
    if reader.pos != len(reader.data):
        raise ValueError(f"trailing bytes at 0x{reader.pos:X}")

    return ItpImage(revision, width, height, palette, bytearray(unswizzle(stored, width, height)))


def dump_ccpi(image: ItpImage) -> bytes:
    version, cell_w, cell_h, flags = image.ccpi
    payload = bytearray()
    for color in image.palette:
        payload.extend(color)
    for top in range(0, image.height, cell_h):
        for left in range(0, image.width, cell_w):
            this_w = min(cell_w, image.width - left)
            this_h = min(cell_h, image.height - top)
            rows = bytearray()
            for row in range(this_h):
                start = (top + row) * image.width + left
                rows.extend(image.pixels[start : start + this_w])
            payload.extend(encode_ccpi_cell(rows_to_cell(bytes(rows), this_w, this_h)))

    out = bytearray()
    out.extend(struct.pack("<I", image.revision))
    out.extend(struct.pack("<I", len(payload) + 16))
    out.extend(CCPI_TAG)
    out.extend(
        struct.pack(
            "<HHBBHHH",
            version,
            len(image.palette),
            cell_w.bit_length() - 1,
            cell_h.bit_length() - 1,
            image.width,
            image.height,
            flags,
        )
    )
    out.extend(ed7_compress(bytes(payload)) if flags & (1 << 15) else payload)
    return bytes(out)


def dump(image: ItpImage) -> bytes:
    if image.revision == 1006:
        return dump_ccpi(image)
    out = bytearray()
    out.extend(struct.pack("<4I", image.revision, image.width, image.height, len(image.palette)))
    out.extend(ed7_compress(write_palette(image.palette, image.revision)))

    stored = swizzle(bytes(image.pixels), image.width, image.height)
    if image.revision == 1005:
        stream = encode_afastmode2(stored, image.width, image.height, image.palette)
        out.extend(struct.pack("<I", len(stream)))
        out.extend(ed7_compress(stream))
    else:
        out.extend(ed7_compress(stored))
    return bytes(out)


# --- revision 1006: Falcom's "CCPI" cell format ----------------------------
#
# The plane is cut into cw x ch cells.  Each cell carries a table of up to 256
# 2x2 pixel tiles -- the first n are stored, the rest are derived by flipping
# them -- and its pixels are a run-length stream of indices into that table.
# Algorithm per Aureole-Suite/Cradle (cradle/src/itp/read.rs).

CCPI_TAG = b"CCPI"
CCPI_RUN = 0xFF


def build_tile_table(bases: list[bytes]) -> list[bytes]:
    """The 256-entry tile table a cell addresses: bases, then their flips."""
    count = len(bases)
    table: list[bytes] = [bytes(4)] * 256
    for index in range(count):
        table[index] = bases[index]
    for index in range(count, min(count * 2, 256)):
        a, b, c, d = table[index - count]
        table[index] = bytes((b, a, d, c))  # mirrored left/right
    for index in range(count * 2, min(count * 4, 256)):
        a, b, c, d = table[index - count * 2]
        table[index] = bytes((c, d, a, b))  # mirrored top/bottom
    return table


def decode_ccpi_cell(data: bytes, pos: int, size: int) -> tuple[bytes, int]:
    """Read one cell: returns its 2x2-tile-major pixels and the new offset."""
    count = data[pos]
    pos += 1
    bases = [data[pos + i * 4 : pos + i * 4 + 4] for i in range(count)]
    pos += count * 4
    table = build_tile_table(bases)

    out = bytearray()
    last = 0
    while len(out) < size:
        value = data[pos]
        pos += 1
        if value == CCPI_RUN:
            repeats = data[pos]
            pos += 1
            out.extend(table[last] * repeats)
        else:
            last = value
            out.extend(table[last])
    if len(out) != size:
        raise ValueError(f"CCPI cell overran: {len(out)} != {size}")
    return bytes(out), pos


def cell_to_rows(cell: bytes, width: int, height: int) -> bytes:
    """Lay a cell's 2x2 tiles, stored in raster order, into scanlines."""
    rows = bytearray(width * height)
    index = 0
    for tile_y in range(height // 2):
        for tile_x in range(width // 2):
            a, b, c, d = cell[index : index + 4]
            index += 4
            top = tile_y * 2 * width + tile_x * 2
            rows[top] = a
            rows[top + 1] = b
            rows[top + width] = c
            rows[top + width + 1] = d
    return bytes(rows)


def rows_to_cell(rows: bytes, width: int, height: int) -> bytes:
    out = bytearray()
    for tile_y in range(height // 2):
        for tile_x in range(width // 2):
            top = tile_y * 2 * width + tile_x * 2
            out.extend((rows[top], rows[top + 1], rows[top + width], rows[top + width + 1]))
    return bytes(out)


def encode_ccpi_cell(cell: bytes) -> bytes:
    """Re-encode one cell.  Tiles are stored plainly; only runs are compressed."""
    tiles = [cell[i : i + 4] for i in range(0, len(cell), 4)]
    order: list[bytes] = []
    seen: dict[bytes, int] = {}
    for tile in tiles:
        if tile not in seen:
            seen[tile] = len(order)
            order.append(tile)
    if len(order) > CCPI_RUN:
        raise ValueError(f"cell needs {len(order)} tiles, only {CCPI_RUN} are addressable")

    out = bytearray()
    out.append(len(order))
    for tile in order:
        out.extend(tile)

    index = 0
    last = None
    while index < len(tiles):
        tile = tiles[index]
        run = 1
        while index + run < len(tiles) and tiles[index + run] == tile:
            run += 1
        if tile != last:
            out.append(seen[tile])
            last = tile
            run -= 1
            index += 1
        while run:
            step = min(run, 255)
            out.append(CCPI_RUN)
            out.append(step)
            run -= step
            index += step
    return bytes(out)
