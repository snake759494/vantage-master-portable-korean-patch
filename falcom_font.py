"""Reader/writer for Falcom's PSP `pspfont.dat` proportional font.

Layout
------
0x00  uint32[4]  range start codes (Shift-JIS / CP932, half-width codes as-is)
0x40  uint32[4]  range end codes (inclusive)
0x80  uint32[4]  glyph index of each range's first code
0xC0  uint32     total glyph count (15240 in the Japanese build)
0xC4  record[N]  uint24 offset, uint8 width -- both counted in 4-byte columns
      uint32     total data length in bytes
0xEEE8 ...       glyph rasters

A glyph is 16 pixels tall and ``width`` pixels wide, stored column-major:
one column is 16 pixels x 2bpp = 4 bytes, so a record occupies ``width * 4``
bytes at ``data_base + offset * 4``.  Reading those bytes row-major is what
made every earlier preview look rotated by 90 degrees.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

GLYPH_HEIGHT = 16
BYTES_PER_COLUMN = 4  # 16 pixels * 2bpp


@dataclass(frozen=True)
class Record:
    index: int
    offset: int  # in 4-byte columns, relative to the data base
    width: int  # in pixels == in columns

    @property
    def byte_offset(self) -> int:
        return self.offset * BYTES_PER_COLUMN

    @property
    def byte_size(self) -> int:
        return self.width * BYTES_PER_COLUMN


class FalcomFont:
    def __init__(self, data: bytes) -> None:
        self.data = bytearray(data)
        self.range_starts = list(struct.unpack_from("<4I", data, 0x00))
        self.range_ends = list(struct.unpack_from("<4I", data, 0x40))
        self.range_bases = list(struct.unpack_from("<4I", data, 0x80))
        self.glyph_count = struct.unpack_from("<I", data, 0xC0)[0]
        self.record_table = 0xC4
        self.data_base = self.record_table + self.glyph_count * 4 + 4
        self.data_length = struct.unpack_from("<I", data, self.data_base - 4)[0]
        if self.data_base + self.data_length != len(data):
            raise ValueError(
                f"data length {self.data_length} does not reach the end of the {len(data)}-byte file"
            )

    # -- code <-> glyph index -------------------------------------------------

    def index_of(self, code: int) -> int | None:
        """Return the glyph slot the game uses for a Shift-JIS code."""
        for start, end, base in zip(self.range_starts, self.range_ends, self.range_bases):
            if start <= code <= end:
                return base + (code - start)
        return None

    def code_of(self, index: int) -> int | None:
        for start, end, base in zip(self.range_starts, self.range_ends, self.range_bases):
            count = end - start + 1
            if base <= index < base + count:
                return start + (index - base)
        return None

    # -- records --------------------------------------------------------------

    def record(self, index: int) -> Record:
        if not 0 <= index < self.glyph_count:
            raise IndexError(index)
        pos = self.record_table + index * 4
        raw = self.data
        offset = raw[pos] | (raw[pos + 1] << 8) | (raw[pos + 2] << 16)
        return Record(index, offset, raw[pos + 3])

    def records(self) -> list[Record]:
        return [self.record(i) for i in range(self.glyph_count)]

    # -- rasters --------------------------------------------------------------

    def read_glyph(self, index: int) -> list[list[int]]:
        """Return the glyph as ``rows[y][x]`` of 2-bit values."""
        rec = self.record(index)
        start = self.data_base + rec.byte_offset
        blob = self.data[start : start + rec.byte_size]
        rows = [[0] * rec.width for _ in range(GLYPH_HEIGHT)]
        for x in range(rec.width):
            column = blob[x * BYTES_PER_COLUMN : (x + 1) * BYTES_PER_COLUMN]
            for y in range(GLYPH_HEIGHT):
                byte = column[y >> 2]
                rows[y][x] = (byte >> ((y & 3) * 2)) & 3
        return rows

    def write_glyph(self, index: int, rows: list[list[int]]) -> None:
        """Overwrite a glyph in place; the pixel width must match the record."""
        rec = self.record(index)
        if len(rows) != GLYPH_HEIGHT or any(len(r) != rec.width for r in rows):
            raise ValueError(
                f"glyph {index} is {rec.width}x{GLYPH_HEIGHT}, got "
                f"{len(rows[0]) if rows else 0}x{len(rows)}"
            )
        start = self.data_base + rec.byte_offset
        for x in range(rec.width):
            column = bytearray(BYTES_PER_COLUMN)
            for y in range(GLYPH_HEIGHT):
                column[y >> 2] |= (rows[y][x] & 3) << ((y & 3) * 2)
            self.data[start + x * BYTES_PER_COLUMN : start + (x + 1) * BYTES_PER_COLUMN] = column

    def to_bytes(self) -> bytes:
        return bytes(self.data)
