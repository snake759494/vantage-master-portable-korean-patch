# -*- coding: utf-8 -*-
"""Write the Korean into the map, unit and master scripts.

These are the files the event patcher never touched: ``data/map/_asm/mapNNN._as``
carries the map's name and the two paragraphs of advice the HELP box shows on
the map-select screen, ``data/table/_asm/unit._as`` holds the master, class and special-move
names, and ``data/master/_asm/masNNN._as`` the profile of each master.

The ISO carries every one of them twice: loose, and ED7-compressed inside
``data/pack/asm.dat``, which ``data/pack/init0.dat`` in turn stores verbatim as
a 92,534-byte member.  So nothing may move.  A translation is padded with
spaces to exactly the bytes the Japanese occupied, which keeps every offset in
the loose file; and each pack member is required to come back no larger than
the stream it replaces, which keeps every offset in the pack.  That is a real
constraint -- replacing one string of a member and leaving its neighbour in
Japanese costs eleven bytes on map000, because the untouched Japanese loses the
back-references it shared with the text that changed -- but replacing all of
them together comes out at or under the original every time, and the compressor
here reproduces all 449 shipped streams byte for byte, so what it measures is
what the game will read.

An earlier attempt let ``asm.dat`` grow and froze the game.  This one refuses to
grow it at all.
"""

from __future__ import annotations

import json
import re
import struct
from pathlib import Path

import ed7_optimal
from patch_packed_pspfont import (
    PACK_HEADER_SIZE,
    PACK_RECORD_SIZE,
    ed7_compress,
    ed7_decompress,
    parse_pack_record,
    u32,
)

KOREAN_DIR = Path("itp_work/kr_scripts")
JAPANESE = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")
SCRIPT_DIRS = {
    "map": "/PSP_GAME/USRDIR/data/map/_asm",
    "table": "/PSP_GAME/USRDIR/data/table/_asm",
    "master": "/PSP_GAME/USRDIR/data/master/_asm",
}
INIT0_ASM_OFFSET = 847874          # asm.dat is stored raw inside init0.dat
INIT0_ASM_SIZE = 92534


def load_korean(directory: Path = KOREAN_DIR) -> dict[str, str]:
    """Japanese string -> Korean, merged over every file the translators wrote."""
    korean: dict[str, str] = {}
    if not directory.exists():
        return korean
    for path in sorted(directory.glob("*.json")):
        for japanese, text in json.loads(path.read_text(encoding="utf-8")).items():
            korean[japanese] = text
    return korean


def runs(data: bytes) -> list[tuple[int, int, str]]:
    """(offset, length, text) for every NUL-terminated string carrying Japanese."""
    out: list[tuple[int, int, str]] = []
    start = None
    for index, byte in enumerate(data):
        if byte == 0:
            if start is not None and index - start >= 2:
                try:
                    text = data[start:index].decode("cp932")
                except UnicodeDecodeError:
                    text = None
                if text and JAPANESE.search(text):
                    out.append((start, index - start, text))
            start = None
        elif start is None:
            start = index
    return out


def patch_script(data: bytes, korean: dict[str, str], encode) -> tuple[bytes, int, list[str]]:
    """Rewrite one script in place; returns the file, how many lines changed, overruns."""
    result = bytearray(data)
    changed = 0
    over: list[str] = []
    for offset, length, japanese in runs(data):
        text = korean.get(japanese)
        if text is None:
            continue
        encoded = encode(text)
        if len(encoded) > length:
            over.append(f"0x{offset:X}: {len(encoded)} > {length} bytes -- {text[:40]!r}")
            continue
        result[offset : offset + length] = encoded.ljust(length, b" ")
        changed += 1
    return bytes(result), changed, over


def patch_pack(pack: bytes, korean: dict[str, str], encode) -> tuple[bytes, int, list[str]]:
    """Rewrite every member of asm.dat that carries translated text.

    The pack keeps its length and every member keeps its offset: a member whose
    stream would come back longer than it went in is a build error, not
    something to make room for.
    """
    result = bytearray(pack)
    count = u32(pack, 0)
    changed = 0
    trouble: list[str] = []
    for index in range(count):
        name, offset, compressed, uncompressed, _flags = parse_pack_record(pack, index)
        plain = ed7_decompress(pack[offset : offset + compressed])
        patched, lines, over = patch_script(plain, korean, encode)
        trouble += [f"{name} {line}" for line in over]
        if not lines:
            continue
        # Falcom's own parse and the cheapest one, whichever comes out
        # smaller.  Korean compresses worse than the katakana it replaces --
        # every syllable is its own two-byte code where the kana repeat -- and
        # on unit._as the difference between the two parses is the difference
        # between fitting and not.
        stream = min((ed7_compress(patched), ed7_optimal.compress(patched)), key=len)
        if ed7_decompress(stream) != patched:
            raise ValueError(f"{name}: the stream does not decompress to what went in")
        if len(stream) > compressed:
            trouble.append(f"{name}: repacks to {len(stream)} bytes, {compressed} available")
            continue
        result[offset : offset + len(stream)] = stream
        struct.pack_into("<I", result, PACK_HEADER_SIZE + index * PACK_RECORD_SIZE + 20,
                         len(stream))
        changed += 1
    return bytes(result), changed, trouble


def splice_into_init0(init0: bytes, asm: bytes) -> bytes:
    """Put the rebuilt asm.dat back into the pack that stores a copy of it."""
    if len(asm) != INIT0_ASM_SIZE:
        raise ValueError(f"asm.dat is {len(asm)} bytes, not the {INIT0_ASM_SIZE} it must stay")
    name, offset, compressed, uncompressed, _flags = None, None, None, None, None
    count = u32(init0, 0)
    for index in range(count):
        record = parse_pack_record(init0, index)
        if record[0] == "asm.dat":
            name, offset, compressed, uncompressed, _flags = record
            break
    if name is None:
        raise ValueError("init0.dat has no asm.dat member")
    if (offset, compressed) != (INIT0_ASM_OFFSET, INIT0_ASM_SIZE):
        raise ValueError(f"asm.dat sits at {offset}/{compressed} inside init0.dat, not where "
                         f"{INIT0_ASM_OFFSET}/{INIT0_ASM_SIZE} was measured")
    if uncompressed != 0:
        raise ValueError("init0.dat's asm.dat member is compressed, not stored")
    result = bytearray(init0)
    result[offset : offset + len(asm)] = asm
    return bytes(result)


def build(iso_path: Path, encode) -> tuple[dict[str, bytes], bytes, list[str], list[str]]:
    """Every file the script translation touches, and the rebuilt asm.dat.

    Returns ``(replacements, asm, report, trouble)``.  ``trouble`` is empty on a
    clean build; anything in it is a member whose Korean does not fit, which the
    caller should refuse to ship rather than quietly leave in Japanese.
    """
    import pycdlib

    korean = load_korean()
    replacements: dict[str, bytes] = {}
    report: list[str] = []
    trouble: list[str] = []
    if not korean:
        return replacements, b"", report, trouble

    with iso_path.open("rb") as handle:
        iso = pycdlib.PyCdlib()
        iso.open_fp(handle)
        try:
            for kind, directory in SCRIPT_DIRS.items():
                for child in iso.list_children(iso_path=directory):
                    if child is None or child.is_dot() or child.is_dotdot() or child.is_dir():
                        continue
                    name = child.file_identifier().decode("ascii").split(";")[0]
                    full = f"{directory}/{name}"
                    with iso.open_file_from_iso(iso_path=full) as handle_file:
                        plain = handle_file.read()
                    patched, lines, over = patch_script(plain, korean, encode)
                    trouble += [f"{name} {line}" for line in over]
                    if lines:
                        replacements[full] = patched
                        report.append(f"{full}: {lines} strings")
            with iso.open_file_from_iso(iso_path="/PSP_GAME/USRDIR/data/pack/asm.dat") as handle_file:
                pack = handle_file.read()
        finally:
            iso.close()

    asm, members, pack_trouble = patch_pack(pack, korean, encode)
    trouble += pack_trouble
    report.append(f"asm.dat: {members} members rebuilt, {len(asm)} bytes")
    return replacements, asm, report, trouble
