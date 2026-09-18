"""Patch the pspfont.dat copy packed inside init0.dat.

Vantage Master Portable keeps a loose ``system/pspfont.dat`` file in the ISO,
but the normal resource loader reads the compressed copy in
``data/pack/init0.dat``.  This script round-trips Falcom's ED7/BZip mode-2
container, replaces the packed font with the already-rendered Korean test
font, and updates the pack entry while preserving the original pack size.
"""

from __future__ import annotations

import argparse
import io
import struct
from pathlib import Path

from decode_falcom_itp import bzip_decompress


PACK_MAGIC_COUNT_OFFSET = 0
PACK_HEADER_SIZE = 0x10
PACK_RECORD_SIZE = 0x20
PACK_DATA_ENTRY_NAME = b"pspfont.dat"
PACK_PSPFONT_RECORD = 2
PACK_PSPFONT_DATA_OFFSET = 0x54EA
PACK_PSPFONT_COMPRESSED_SIZE = 0x5F13F
PACK_PSPFONT_UNCOMPRESSED_SIZE = 0x9E5A4
PACK_PSPFONT_CHUNK_SIZE = 0x7FF0


def u32(data: bytes | bytearray, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def put_u16(out: bytearray, value: int) -> None:
    out.extend(struct.pack("<H", value))


def put_u32(out: bytearray, value: int) -> None:
    out.extend(struct.pack("<I", value))


def count_equal(a: bytes, b: bytes, limit: int) -> int:
    count = min(limit, len(a), len(b))
    i = 0
    while i < count and a[i] == b[i]:
        i += 1
    return i


class Digraphs:
    """The bounded digraph index used by Falcom's mode-2 compressor."""

    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
        self.head = [0xFFFF] * 0x10000
        self.next = [0xFFFF] * 0x2000
        self.tail = [0xFFFF] * 0x10000

    def digraph(self, pos: int) -> int:
        first = self.data[pos]
        second = self.data[pos + 1] if pos + 1 < len(self.data) else 0
        return first | (second << 8)

    def advance(self) -> None:
        if self.pos >= 0x1FFF:
            previous = self.pos - 0x1FFF
            self.head[self.digraph(previous)] = self.next[previous % len(self.next)]

        digraph = self.digraph(self.pos)
        if self.head[digraph] == 0xFFFF:
            self.head[digraph] = self.pos
        else:
            self.next[self.tail[digraph]] = self.pos
        self.tail[digraph] = self.pos % len(self.next)
        self.next[self.pos % len(self.next)] = 0xFFFF
        self.pos += 1

    def get(self, run_len: int, run_pos: int) -> tuple[int, int]:
        candidate = self.head[self.digraph(self.pos)]
        while candidate != 0xFFFF:
            length = count_equal(
                self.data[self.pos + 2 :], self.data[candidate + 2 :], 267
            ) + 2
            if length >= run_len:
                run_len, run_pos = length, candidate
            candidate = self.next[candidate % len(self.next)]
        return run_len, run_pos


class BzipBits:
    def __init__(self, out: bytearray):
        self.out = out
        self.bit_mask = 0x0080
        self.bit_pos = len(out)
        self.out.extend((0, 0))

    def bit(self, value: bool) -> bool:
        self.bit_mask <<= 1
        if self.bit_mask == 0x10000:
            self.bit_pos = len(self.out)
            self.out.extend((0, 0))
            self.bit_mask = 1
        if value:
            if self.bit_mask < 256:
                self.out[self.bit_pos] |= self.bit_mask
            else:
                self.out[self.bit_pos + 1] |= self.bit_mask >> 8
        return value

    def bits(self, count: int, value: int) -> None:
        for bit in reversed(range((count // 8) * 8, count)):
            self.bit((value >> bit) & 1 != 0)
        for byte_index in reversed(range(count // 8)):
            self.out.append((value >> (byte_index * 8)) & 0xFF)

    def byte(self, value: int) -> None:
        self.out.append(value)


def bzip_mode2_compress(data: bytes) -> bytes:
    """Compress one BZip mode-2 chunk (Falcom's non-bzip2 algorithm)."""

    if len(data) >= 0xFFFF:
        raise ValueError("mode-2 BZip chunks must be shorter than 0xFFFF bytes")

    out = bytearray()
    bits = BzipBits(out)
    digraphs = Digraphs(data)
    input_pos = 0

    while input_pos < len(data):
        run_len = count_equal(data[input_pos:], data[input_pos + 1 :], 0xFFE) + 1
        if run_len < 14:
            run_len = 1
        run_pos = input_pos

        if run_len < 64 and input_pos + 3 < len(data):
            run_len, run_pos = digraphs.get(run_len, run_pos)
        if run_len <= 0:
            raise AssertionError("compressor produced an empty run")

        if bits.bit(run_len > 1):
            if run_pos == input_pos:
                run_len = min(run_len, (1 << 12) - 1 + 14)
                bits.bit(True)
                bits.bits(13, 1)
                n = run_len - 14
                if bits.bit(n >= 16):
                    bits.bits(12, n)
                else:
                    bits.bits(4, n)
                bits.byte(data[input_pos])
            else:
                run_len = min(run_len, (1 << 8) - 1 + 14)
                distance = input_pos - run_pos
                if bits.bit(distance >= 256):
                    bits.bits(13, distance)
                else:
                    bits.bits(8, distance)
                if run_len >= 3:
                    bits.bit(False)
                if run_len >= 4:
                    bits.bit(False)
                if run_len >= 5:
                    bits.bit(False)
                if run_len >= 6:
                    bits.bit(False)
                if bits.bit(run_len < 14):
                    if run_len >= 6:
                        bits.bits(3, run_len - 6)
                else:
                    bits.bits(8, run_len - 14)
        else:
            bits.byte(data[input_pos])

        for _ in range(run_len):
            input_pos += 1
            digraphs.advance()

    bits.bit(True)
    bits.bit(True)
    bits.bits(13, 0)
    return bytes(out)


def read_compressed_chunk(reader: io.BytesIO) -> tuple[bytes, int]:
    size_raw = reader.read(2)
    if len(size_raw) != 2:
        raise ValueError("missing compressed chunk size")
    size = struct.unpack("<H", size_raw)[0]
    compressed = reader.read(size - 2)
    if len(compressed) != size - 2:
        raise ValueError("compressed chunk runs past ED7 stream")
    return compressed, size


def ed7_decompress(data: bytes) -> bytes:
    reader = io.BytesIO(data)
    input_size = u32(data, 0)
    output_size = u32(data, 4)
    chunk_count = u32(data, 8)
    out = bytearray()
    reader.seek(12)

    for index in range(chunk_count):
        compressed, _size = read_compressed_chunk(reader)
        chunk = bzip_decompress(compressed)
        out.extend(chunk)
        continuation = reader.read(1)
        if len(continuation) != 1 or continuation[0] != (1 if index < chunk_count - 1 else 0):
            raise ValueError("invalid ED7 continuation byte")

    if reader.tell() != 4 + input_size:
        raise ValueError(
            f"ED7 input size mismatch: expected {4 + input_size:#x}, got {reader.tell():#x}"
        )
    if len(out) == output_size + 1:
        out.pop()
    if len(out) != output_size:
        raise ValueError(f"ED7 output size mismatch: expected {output_size}, got {len(out)}")
    return bytes(out)


def write_compressed_chunk(out: bytearray, data: bytes) -> None:
    compressed = bzip_mode2_compress(data)
    if len(compressed) + 2 > 0xFFFF:
        raise ValueError("compressed chunk does not fit in a 16-bit length")
    put_u16(out, len(compressed) + 2)
    out.extend(compressed)


def ed7_compress(data: bytes) -> bytes:
    chunks = [data[i : i + PACK_PSPFONT_CHUNK_SIZE] for i in range(0, len(data), PACK_PSPFONT_CHUNK_SIZE)]
    if not chunks:
        chunks = [b""]

    out = bytearray(b"\x00\x00\x00\x00")
    put_u32(out, len(data))
    put_u32(out, len(chunks) + 1)
    for chunk in chunks:
        write_compressed_chunk(out, chunk)
        out.append(1)
    write_compressed_chunk(out, chunks[-1][:1])
    out.append(0)
    struct.pack_into("<I", out, 0, len(out) - 4)
    return bytes(out)


def parse_pack_record(pack: bytes, index: int) -> tuple[str, int, int, int, int]:
    offset = PACK_HEADER_SIZE + index * PACK_RECORD_SIZE
    name = pack[offset : offset + 16].split(b"\0", 1)[0].decode("ascii")
    values = struct.unpack_from("<4I", pack, offset + 16)
    return name, *values


def verify_pack_layout(pack: bytes) -> None:
    count = u32(pack, PACK_MAGIC_COUNT_OFFSET)
    if not (0 < count < 10000):
        raise ValueError(f"invalid init0.dat record count: {count}")
    previous_end = PACK_HEADER_SIZE + count * PACK_RECORD_SIZE
    for index in range(count):
        name, data_offset, compressed_size, _uncompressed_size, _flags = parse_pack_record(pack, index)
        if data_offset < previous_end:
            raise ValueError(f"overlapping init0.dat record {index}: {name}")
        if data_offset + compressed_size > len(pack):
            raise ValueError(f"record {index} runs past init0.dat: {name}")
        previous_end = data_offset + compressed_size


def patch_pack(pack: bytes, replacement: bytes) -> tuple[bytes, bytes, bytes]:
    verify_pack_layout(pack)
    name, data_offset, compressed_size, uncompressed_size, flags = parse_pack_record(
        pack, PACK_PSPFONT_RECORD
    )
    if name != PACK_DATA_ENTRY_NAME.decode("ascii"):
        raise ValueError(f"record {PACK_PSPFONT_RECORD} is {name!r}, not pspfont.dat")
    if (
        data_offset != PACK_PSPFONT_DATA_OFFSET
        or compressed_size != PACK_PSPFONT_COMPRESSED_SIZE
        or uncompressed_size != PACK_PSPFONT_UNCOMPRESSED_SIZE
        or flags != 0
    ):
        raise ValueError(
            "unexpected original pspfont record: "
            f"offset={data_offset:#x}, compressed={compressed_size:#x}, "
            f"uncompressed={uncompressed_size:#x}, flags={flags:#x}"
        )
    original_compressed = pack[data_offset : data_offset + compressed_size]
    original_uncompressed = ed7_decompress(original_compressed)
    if len(original_uncompressed) != PACK_PSPFONT_UNCOMPRESSED_SIZE:
        raise ValueError("unexpected decompressed pspfont size")

    stream = ed7_compress(replacement)
    if len(stream) > compressed_size:
        raise ValueError(
            f"new packed font is larger than the original slot: {len(stream):#x} > {compressed_size:#x}"
        )
    slot = stream + b"\0" * (compressed_size - len(stream))

    result = bytearray(pack)
    result[data_offset : data_offset + compressed_size] = slot
    return bytes(result), original_uncompressed, stream


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pack",
        type=Path,
        default=Path("itp_work/init0_orig.dat"),
        help="data/pack/init0.dat exactly as the original ISO ships it",
    )
    parser.add_argument(
        "--original-loose",
        type=Path,
        default=Path("pspfont.dat"),
        help="original loose pspfont.dat used to verify the packed copy",
    )
    parser.add_argument(
        "--replacement",
        type=Path,
        default=Path("korean_font_slotmapped/pspfont_korean.dat"),
    )
    parser.add_argument("--out", type=Path, default=Path("korean_font_slotmapped/init0_korean.dat"))
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    pack = args.pack.read_bytes()
    replacement = args.replacement.read_bytes()
    if len(replacement) != PACK_PSPFONT_UNCOMPRESSED_SIZE:
        raise ValueError(f"replacement size {len(replacement)} is not 0x{PACK_PSPFONT_UNCOMPRESSED_SIZE:X}")

    patched, original_uncompressed, compressed = patch_pack(pack, replacement)
    if original_uncompressed != args.original_loose.read_bytes():
        raise ValueError("packed original pspfont differs from loose system/pspfont.dat")
    recovered = ed7_decompress(compressed)
    if recovered != replacement:
        raise ValueError("compressed replacement did not round-trip")
    if not args.verify_only:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(patched)
        print(f"Wrote {args.out} ({len(patched)} bytes)")
    print(
        f"Verified pspfont.dat: loose={len(replacement)} bytes, "
        f"packed stream={len(compressed)} bytes, slot={PACK_PSPFONT_COMPRESSED_SIZE} bytes"
    )


if __name__ == "__main__":
    main()
