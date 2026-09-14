# -*- coding: utf-8 -*-
"""Write the Korean map names into every copy the ISO carries.

A map's name is the first string in ``mapNNN._as``, and the ISO holds that file
three times: loose under ``data/map/_asm``, compressed inside the ``asm.dat``
pack, and again inside the copy of ``asm.dat`` that ``init0.dat`` bundles.  The
name is followed immediately by binary script data, so it may not grow -- but
the ED7 stream around it does: replacing Japanese bytes with Korean breaks the
back-references the compressor had found, and 35 of the 52 members come out
1-16 bytes larger, 208 bytes in total.  Shortening the names does not help;
even a one-syllable name grows twelve of them, so the cost is the edit itself
and not the length.

``asm.dat`` therefore has to grow, and ``init0.dat`` -- which carries a copy of
it -- has to be repacked around the bigger member, which it can afford because
its ``pspfont.dat`` member is padded with 27,447 spare bytes.

BUT THAT BUILD FROZE.  Reclaiming the font's padding moves 88 of init0.dat's 91
members 27,444 bytes earlier, and the longer asm.dat pushes ``unit._as`` past
the 92,534 bytes the file shipped with.  The scenario map list -- the first
screen that loads map and unit scripts -- hung on it, and the map names showed
as Japanese, so the game had not read the patched copies either.  Every pack
member still decompressed to its declared size and every pack layout verified,
so the damage is not in the data: something reads these two files at offsets
or lengths it does not take from the record table.

This module is therefore off by default; ``build_korean_opening_iso.py`` only
calls it under ``--map-names``.  Making the names safe means finding a way to
edit them that moves nothing -- the whole point of the earlier attempts to keep
every replacement the same size.
"""

from __future__ import annotations

import struct

from patch_packed_pspfont import (
    PACK_HEADER_SIZE,
    PACK_RECORD_SIZE,
    ed7_compress,
    ed7_decompress,
    parse_pack_record,
    u32,
)

import map_names

NUL = bytes(1)

MAP_MEMBER = "map{:03d}._as"


def members(pack: bytes) -> list[tuple[str, int, int, int, int]]:
    return [parse_pack_record(pack, index) for index in range(u32(pack, 0))]


def trim(body: bytes, uncompressed: int) -> bytes:
    """Drop a compressed member's trailing NUL padding, if it has any.

    ``init0.dat`` reserves 389,439 bytes for a font that compresses to 361,995
    and pads the rest with NULs; reclaiming that is what lets a bigger asm.dat
    in without moving anything in the ISO.  The trim is only kept when the
    shorter stream still decompresses to its declared size, so a stream that
    genuinely ends in NUL bytes is left alone.
    """
    if not uncompressed:
        return body
    stripped = body.rstrip(NUL)
    if len(stripped) == len(body):
        return body
    # A stream can legitimately end in NUL bytes, so put them back one at a
    # time and keep the shortest prefix that still decompresses whole.
    for extra in range(9):
        candidate = stripped + NUL * extra
        if len(candidate) > len(body):
            break
        try:
            if len(ed7_decompress(candidate)) == uncompressed:
                return candidate
        except Exception:  # noqa: BLE001 - not a valid cut, try one more byte
            continue
    return body


def rebuild(pack: bytes, payloads: dict[str, bytes], pad_to: int | None = None) -> bytes:
    """Repack with new member bodies, recomputing every offset."""
    records = members(pack)
    out = bytearray(pack[: PACK_HEADER_SIZE + len(records) * PACK_RECORD_SIZE])
    cursor = len(out)
    for index, (name, offset, stored, uncompressed, flags) in enumerate(records):
        body = payloads.get(name) or trim(pack[offset : offset + stored], uncompressed)
        table = PACK_HEADER_SIZE + index * PACK_RECORD_SIZE
        struct.pack_into("<4I", out, table + 16, cursor, len(body), uncompressed, flags)
        out.extend(body)
        cursor += len(body)
    if pad_to is not None:
        if len(out) > pad_to:
            raise ValueError(f"repacked to {len(out)} bytes, over the {pad_to}-byte slot")
        out.extend(b"\0" * (pad_to - len(out)))
    return bytes(out)


def rename(plain: bytes, korean: bytes) -> bytes:
    """Overwrite the leading name of a map script, keeping its terminator."""
    capacity = plain.index(0)
    if len(korean) > capacity:
        raise ValueError(f"{korean!r} needs {len(korean)} of {capacity} bytes")
    return korean.ljust(capacity, b"\0") + plain[capacity:]


def patch_asm(asm: bytes, encode) -> tuple[bytes, dict[str, bytes]]:
    """Return the repacked asm.dat and the loose ``_as`` files to match."""
    payloads: dict[str, bytes] = {}
    loose: dict[str, bytes] = {}
    for name, offset, stored, uncompressed, _flags in members(asm):
        index = None
        for number in map_names.NAMES:
            if name == MAP_MEMBER.format(number):
                index = number
                break
        if index is None:
            continue
        plain = rename(ed7_decompress(asm[offset : offset + stored]), encode(map_names.NAMES[index]))
        loose[name] = plain
        payloads[name] = ed7_compress(plain) if uncompressed else plain
    return rebuild(asm, payloads), loose


def patch_init0(init0: bytes, asm: bytes) -> bytes:
    """Put the new asm.dat into init0.dat, reclaiming the font member's padding."""
    return rebuild(init0, {"asm.dat": asm}, pad_to=len(init0))


def find_record(iso: bytes, extent: int, length: int, name: str) -> int:
    """Offset of the ISO9660 directory record for a file, found by its extent.

    ``asm.dat`` comes out 203 bytes bigger than it went in, which pycdlib will
    not write: ``modify_file_in_place`` insists on the exact original length.
    The file still fits -- 92,737 bytes inside a 94,208-byte allocation -- so
    only the length in its directory record has to change, and the record is
    identified by the extent pycdlib already reported for it.
    """
    ident = name.encode("ascii")
    wanted = struct.pack("<I", extent) + struct.pack(">I", extent)
    start = 0
    while True:
        at = iso.find(wanted, start)
        if at < 0:
            raise ValueError(f"no directory record for {name} at extent {extent}")
        record = at - 2
        if (
            record > 0
            and iso[record + 10 : record + 18]
            == struct.pack("<I", length) + struct.pack(">I", length)
            and ident in iso[record : record + iso[record]]
        ):
            return record
        start = at + 1


def grow_in_place(iso: bytearray, extent: int, length: int, name: str, data: bytes) -> None:
    """Write a longer file into the sectors it already owns."""
    allocated = -(-length // 2048) * 2048
    if len(data) > allocated:
        raise ValueError(f"{name}: {len(data)} bytes will not fit {allocated} allocated")
    record = find_record(bytes(iso), extent, length, name)
    iso[record + 10 : record + 18] = struct.pack("<I", len(data)) + struct.pack(">I", len(data))
    start = extent * 2048
    iso[start : start + allocated] = data.ljust(allocated, b"\0")
