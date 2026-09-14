# -*- coding: utf-8 -*-
"""Pack an ED7 stream as small as the format allows.

``patch_packed_pspfont.ed7_compress`` reproduces Falcom's own compressor byte
for byte -- all 449 members of ``asm.dat`` come back identical -- which makes it
the right tool for checking that a file is unchanged, and the wrong one for
making room.  Falcom's is greedy: it takes the longest match it can see at every
position, and a greedy parse is not the cheapest one.

This is the cheapest one.  The bit cost of every encoding the format has is
known, so the parse is a shortest-path over the input: at each byte, the cost of
emitting it as a literal against the cost of every back-reference that starts
there, chosen to minimise the total.  The output uses exactly the same encodings
and decompresses to exactly the same bytes -- the game cannot tell -- and it is
about two per cent smaller, which is what pays for Korean being less repetitive
than the katakana it replaces.  On ``unit._as``, where 39 master, class and
special-move names come to 52 bytes more than the slot allows under a greedy
parse, it comes to 26 bytes less.
"""
from __future__ import annotations

import struct
from pathlib import Path

from patch_packed_pspfont import (
    BzipBits,
    Digraphs,
    PACK_PSPFONT_CHUNK_SIZE,
    count_equal,
    ed7_decompress,
    put_u16,
    put_u32,
)

FAR = 13
NEAR = 8


def length_bits(run_len: int) -> int:
    if run_len == 2:
        return 1
    if run_len <= 5:
        return run_len - 1
    if run_len <= 13:
        return 8
    return 13


def candidates(data: bytes) -> list[tuple[int, int, int, int]]:
    """(far length, far position, near length, near position) at each offset."""
    digraphs = Digraphs(data)
    out = []
    for pos in range(len(data)):
        best_len, best_pos = 0, pos
        near_len, near_pos = 0, pos
        if pos + 3 < len(data):
            candidate = digraphs.head[digraphs.digraph(pos)]
            while candidate != 0xFFFF:
                length = count_equal(data[pos + 2 :], data[candidate + 2 :], 267) + 2
                if length >= best_len:
                    best_len, best_pos = length, candidate
                if pos - candidate < 256 and length >= near_len:
                    near_len, near_pos = length, candidate
                candidate = digraphs.next[candidate % len(digraphs.next)]
        out.append((best_len, best_pos, near_len, near_pos))
        digraphs.advance()
    return out


def parse(data: bytes) -> list[tuple[int, int]]:
    """The cheapest sequence of (length, source position) for the whole chunk."""
    table = candidates(data)
    size = len(data)
    cost = [0] * (size + 1)
    take: list[tuple[int, int]] = [(1, 0)] * (size + 1)
    for pos in range(size - 1, -1, -1):
        best = 9 + cost[pos + 1]
        choice = (1, pos)
        run = count_equal(data[pos:], data[pos + 1 :], 0xFFE) + 1
        if run >= 14:
            length = min(run, (1 << 12) - 1 + 14)
            price = 1 + 1 + 13 + 1 + (12 if length - 14 >= 16 else 4) + 8 + cost[pos + length]
            if price < best:
                best, choice = price, (length, pos)
        far_len, far_pos, near_len, near_pos = table[pos]
        for length, source, distance_bits in ((far_len, far_pos, FAR), (near_len, near_pos, NEAR)):
            if length < 2:
                continue
            length = min(length, (1 << 8) - 1 + 14, size - pos)
            for take_len in range(2, length + 1):
                price = (1 + 1 + distance_bits + length_bits(take_len)
                         + cost[pos + take_len])
                if price < best:
                    best, choice = price, (take_len, source)
        cost[pos] = best
        take[pos] = choice
    out = []
    pos = 0
    while pos < size:
        length, source = take[pos]
        out.append((length, source))
        pos += length
    return out


def compress_chunk(data: bytes) -> bytes:
    out = bytearray()
    bits = BzipBits(out)
    pos = 0
    for run_len, run_pos in parse(data):
        if bits.bit(run_len > 1):
            if run_pos == pos:
                bits.bit(True)
                bits.bits(13, 1)
                n = run_len - 14
                if bits.bit(n >= 16):
                    bits.bits(12, n)
                else:
                    bits.bits(4, n)
                bits.byte(data[pos])
            else:
                distance = pos - run_pos
                if bits.bit(distance >= 256):
                    bits.bits(13, distance)
                else:
                    bits.bits(8, distance)
                for threshold in (3, 4, 5, 6):
                    if run_len >= threshold:
                        bits.bit(False)
                if bits.bit(run_len < 14):
                    if run_len >= 6:
                        bits.bits(3, run_len - 6)
                else:
                    bits.bits(8, run_len - 14)
        else:
            bits.byte(data[pos])
        pos += run_len
    bits.bit(True)
    bits.bit(True)
    bits.bits(13, 0)
    return bytes(out)


def compress(data: bytes) -> bytes:
    chunks = [data[i : i + PACK_PSPFONT_CHUNK_SIZE]
              for i in range(0, len(data), PACK_PSPFONT_CHUNK_SIZE)] or [b""]
    out = bytearray(b"\x00\x00\x00\x00")
    put_u32(out, len(data))
    put_u32(out, len(chunks) + 1)
    for chunk in chunks:
        stream = compress_chunk(chunk)
        put_u16(out, len(stream) + 2)
        out.extend(stream)
        out.append(1)
    stream = compress_chunk(chunks[-1][:1])
    put_u16(out, len(stream) + 2)
    out.extend(stream)
    out.append(0)
    struct.pack_into("<I", out, 0, len(out) - 4)
    return bytes(out)
