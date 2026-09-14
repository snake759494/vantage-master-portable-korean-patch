"""Decode the older Falcom ITP texture format used by the PSP assets.

This is intentionally a small reader for the 1005/Indexed2/Bz_1/Pfp_1
variant found in this game's ascii.itp file.  It is used for investigation
and does not modify the ISO.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


class Reader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def read(self, size: int) -> bytes:
        if size < 0 or self.pos + size > len(self.data):
            raise ValueError(f"read beyond end at 0x{self.pos:X}, size {size}")
        result = self.data[self.pos : self.pos + size]
        self.pos += size
        return result

    def u8(self) -> int:
        return self.read(1)[0]

    def u16(self) -> int:
        return int.from_bytes(self.read(2), "little")

    def u32(self) -> int:
        return int.from_bytes(self.read(4), "little")

    def remaining(self) -> bytes:
        return self.data[self.pos :]


def repeat_backref(out: bytearray, count: int, offset: int) -> None:
    if offset <= 0 or offset > len(out):
        raise ValueError(f"invalid back-reference offset {offset} at output {len(out)}")
    for _ in range(count):
        out.append(out[-offset])


def bzip_mode1(data: bytes) -> bytes:
    reader = Reader(data)
    out = bytearray()
    last_offset = 0
    while reader.pos < len(data):
        value = reader.u8()
        if value & 0xC0 == 0x00:  # 00xnnnnn: literal bytes
            extended = (value >> 5) & 1
            count = value & 0x1F
            if extended:
                count = (count << 8) | reader.u8()
            out.extend(reader.read(count))
        elif value & 0xE0 == 0x40:  # 010xnnnn: constant run
            extended = (value >> 4) & 1
            count = value & 0x0F
            if extended:
                count = (count << 8) | reader.u8()
            out.extend(bytes([reader.u8()]) * (4 + count))
        elif value & 0xE0 == 0x60:  # 011nnnnn: repeat last offset
            repeat_backref(out, value & 0x1F, last_offset)
        else:  # 1nnooooo: set offset, then repeat
            count = (value >> 5) & 0x03
            offset = ((value & 0x1F) << 8) | reader.u8()
            last_offset = offset
            repeat_backref(out, 4 + count, last_offset)
    return bytes(out)


class BitReader:
    def __init__(self, reader: Reader):
        self.reader = reader
        self.bits = 0
        self.next_bit = 0

    def renew(self) -> None:
        self.bits = self.reader.u16()
        self.next_bit = 1

    def bit(self) -> int:
        if self.next_bit == 0:
            self.renew()
        result = 1 if self.bits & self.next_bit else 0
        self.next_bit = (self.next_bit << 1) & 0xFFFF
        return result

    def bits_n(self, count: int) -> int:
        result = 0
        for _ in range(count % 8):
            result = (result << 1) | self.bit()
        for _ in range(count // 8):
            result = (result << 8) | self.reader.u8()
        return result

    def count(self) -> int:
        if self.bit():
            return 2
        if self.bit():
            return 3
        if self.bit():
            return 4
        if self.bit():
            return 5
        if self.bit():
            return 6 + self.bits_n(3)
        return 14 + self.bits_n(8)


def bzip_mode2(data: bytes) -> bytes:
    reader = Reader(data)
    bits = BitReader(reader)
    bits.renew()
    bits.next_bit <<= 8
    out = bytearray()
    while True:
        if not bits.bit():
            out.extend(reader.read(1))
        elif not bits.bit():
            offset = bits.bits_n(8)
            repeat_backref(out, bits.count(), offset)
        else:
            offset = bits.bits_n(13)
            if offset == 0:
                break
            if offset == 1:
                count = bits.bits_n(12) if bits.bit() else bits.bits_n(4)
                out.extend(bytes([reader.u8()]) * (14 + count))
            else:
                repeat_backref(out, bits.count(), offset)
    return bytes(out)


def bzip_decompress(data: bytes) -> bytes:
    if not data:
        raise ValueError("empty Bz_1 chunk")
    return bzip_mode2(data) if data[0] == 0 else bzip_mode1(data)


def freadp(reader: Reader) -> bytes:
    """Read one Falcom FREADP/ED7 stream and return its uncompressed bytes."""

    flags = int.from_bytes(reader.remaining()[:4], "little")
    if flags & 0x80000000:
        raise NotImplementedError("high-bit C77 FREADP stream is not needed here")

    in_size = reader.u32()
    in_size_start = reader.pos
    out_size = reader.u32()
    chunk_count = reader.u32()
    out = bytearray()
    for index in range(chunk_count):
        chunk_size = reader.u16()
        chunk = reader.read(chunk_size - 2)
        out.extend(bzip_decompress(chunk))
        continuation = reader.u8()
        expected = 1 if index < chunk_count - 1 else 0
        if continuation != expected:
            raise ValueError(
                f"unexpected FREADP continuation {continuation} at chunk {index}"
            )
    if reader.pos != in_size_start + in_size:
        raise ValueError(
            f"FREADP input size mismatch: expected end 0x{in_size_start + in_size:X}, "
            f"got 0x{reader.pos:X}"
        )
    if len(out) == out_size + 1:
        # Falcom's writer commonly emits one dummy byte in the final chunk.
        out.pop()
    if len(out) != out_size:
        raise ValueError(f"FREADP output size mismatch: expected {out_size}, got {len(out)}")
    return bytes(out)


def unswizzle_pfp1(data: bytes, width: int, height: int) -> bytes:
    if len(data) != width * height or width % 16 or height % 8:
        raise ValueError("Pfp_1 dimensions/data length are not block-aligned")
    # Inverse of Falcom's iter_swizzle(height/8, width/16, 8, 16).
    permutation: list[int] = []
    for y0 in range(height // 8):
        for x0 in range(width // 16):
            for y1 in range(8):
                for x1 in range(16):
                    permutation.append(
                        y0 * 8 * width + x0 * 16 + y1 * width + x1
                    )
    if len(permutation) != len(data) or len(set(permutation)) != len(data):
        raise AssertionError("invalid Pfp_1 permutation")
    result = bytearray(len(data))
    for source_index, destination_index in enumerate(permutation):
        result[destination_index] = data[source_index]
    return bytes(result)


def read_nibbles(reader: Reader, count: int) -> list[int]:
    result: list[int] = []
    for _ in range((count + 1) // 2):
        value = reader.u8()
        result.append(value >> 4)
        if len(result) < count:
            result.append(value & 0x0F)
    return result


def decode_indexed2(data: bytes, width: int, height: int) -> tuple[bytes, list[tuple[int, int, int, int]]]:
    reader = Reader(data)
    block_count = (height // 8) * (width // 16)
    ncolors = read_nibbles(reader, block_count)
    ncolors = [value + 1 if value else 0 for value in ncolors]
    local_palette = reader.read(sum(ncolors))
    mode = reader.u8()
    if mode != 0:
        raise NotImplementedError(f"AFastMode2 subformat {mode} is not implemented")

    pixels = bytearray()
    palette_pos = 0
    for count in ncolors:
        chunk = bytearray(8 * 16)
        if count:
            colors = local_palette[palette_pos : palette_pos + count]
            palette_pos += count
            indices = read_nibbles(reader, len(chunk))
            if any(index >= count for index in indices):
                raise ValueError("AFastMode2 local palette index is out of range")
            chunk[:] = bytes(colors[index] for index in indices)
        pixels.extend(chunk)
    if reader.pos != len(data):
        raise ValueError(f"unexpected AFastMode2 trailing data at 0x{reader.pos:X}")
    return unswizzle_pfp1(bytes(pixels), width, height), []


def decode_itp(path: Path) -> tuple[int, int, list[tuple[int, int, int, int]], bytes]:
    data = path.read_bytes()
    reader = Reader(data)
    header = reader.u32()
    if header != 1005:
        raise ValueError(f"expected ITP head 1005, got {header}")
    width = reader.u32()
    height = reader.u32()
    palette_size = reader.u32()
    compressed_palette = freadp(reader)
    if len(compressed_palette) != palette_size * 4:
        raise ValueError("unexpected palette size")
    palette: list[tuple[int, int, int, int]] = []
    for offset in range(0, len(compressed_palette), 4):
        red, green, blue, alpha = compressed_palette[offset : offset + 4]
        palette.append((blue, green, red, alpha))

    expected_size = reader.u32()
    compressed_pixels = freadp(reader)
    if len(compressed_pixels) != expected_size:
        raise ValueError("unexpected indexed pixel stream size")
    pixels, _unused = decode_indexed2(compressed_pixels, width, height)
    return width, height, palette, pixels


def save_png(width: int, height: int, palette: list[tuple[int, int, int, int]], pixels: bytes, path: Path) -> None:
    image = Image.frombytes("P", (width, height), pixels)
    flat_palette: list[int] = []
    for red, green, blue, _alpha in palette:
        flat_palette.extend((red, green, blue))
    flat_palette.extend([0] * (256 * 3 - len(flat_palette)))
    image.putpalette(flat_palette)
    if any(alpha != 255 for _red, _green, _blue, alpha in palette):
        image.info["transparency"] = bytes(alpha for _red, _green, _blue, alpha in palette)
    image.save(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    width, height, palette, pixels = decode_itp(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    save_png(width, height, palette, pixels, args.output)
    print(f"Decoded {args.input}: {width}x{height}, palette={len(palette)}")
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
