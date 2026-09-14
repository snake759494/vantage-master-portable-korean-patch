# -*- coding: utf-8 -*-
"""Write the Korean dialogue into the event scripts and their packed copies.

Every line is a NUL-terminated CP932 string inlined in the bytecode of
``data/event/_asm/ev*._as``.  The strings run back to back and the parser walks
them by their terminators, so a shorter Korean line padded with NULs would read
as an empty string and could end the block early -- the way the map-name build
taught us not to guess at a format.  Each translation is therefore padded with
SPACES to the exact byte count of the Japanese it replaces, which leaves every
byte position in the file, and every pack around it, exactly where it was.

226 of the 233 files are carried verbatim as a raw member of a ``data/pack``
archive; the other seven have no packed copy.  Because the replacement is the
same length, the packed copy is spliced in at its own offset and no record
moves.
"""

from __future__ import annotations

import io
import json
import re
from pathlib import Path

import pycdlib

import pack_textures

EVENT_DIR = "/PSP_GAME/USRDIR/data/event/_asm"
KOREAN_DIR = Path("itp_work/event_kr")

JAPANESE = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")


def load_korean(directory: Path = KOREAN_DIR) -> dict[str, str]:
    """Japanese line -> Korean, merged over every chunk file."""
    korean: dict[str, str] = {}
    if not directory.exists():
        return korean
    for path in sorted(directory.glob("*.json")):
        for japanese, text in json.loads(path.read_text(encoding="utf-8")).items():
            korean[japanese] = text
    return korean


def runs(data: bytes) -> list[tuple[int, int, str]]:
    """(offset, length, text) for every NUL-terminated line carrying Japanese."""
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


def patch_script(data: bytes, korean: dict[str, str], encode) -> tuple[bytes, list[str], list[str]]:
    """Rewrite one ``._as`` in place; returns the file, a report and any overruns."""
    result = bytearray(data)
    report: list[str] = []
    over: list[str] = []
    for offset, length, japanese in runs(data):
        text = korean.get(japanese)
        if text is None:
            continue
        encoded = encode(text)
        if len(encoded) > length:
            over.append(f"0x{offset:X}: {len(encoded)} > {length} bytes -- {text!r}")
            continue
        # Space padding, never NUL: the block's byte layout has to survive.
        result[offset : offset + length] = encoded.ljust(length, b" ")
        report.append(f"0x{offset:X} {length}->{len(encoded)}: {japanese} -> {text}")
    return bytes(result), report, over


def read_event_scripts(iso_path: Path) -> dict[str, bytes]:
    with iso_path.open("rb") as handle:
        iso = pycdlib.PyCdlib()
        iso.open_fp(handle)
        try:
            files = {}
            for path, _dirs, names in iso.walk(iso_path=EVENT_DIR):
                for name in names:
                    plain = name.split(";")[0]
                    buffer = io.BytesIO()
                    iso.get_file_from_iso_fp(buffer, iso_path=f"{path.rstrip('/')}/{plain}")
                    files[plain] = buffer.getvalue()
        finally:
            iso.close()
    return files


def build(iso_path: Path, encode, korean: dict[str, str] | None = None):
    """Return {iso path: new bytes} for every script and pack that changes."""
    korean = load_korean() if korean is None else korean
    scripts = read_event_scripts(iso_path)
    patched: dict[str, bytes] = {}
    report: list[str] = []
    over: list[str] = []
    for name, data in sorted(scripts.items()):
        new, lines, bad = patch_script(data, korean, encode)
        over += [f"{name} {line}" for line in bad]
        if new == data:
            continue
        patched[name] = new
        report.append(f"{EVENT_DIR}/{name}: {len(lines)} lines")
        report += [f"    {line}" for line in lines]

    replacements = {f"{EVENT_DIR}/{name}": data for name, data in patched.items()}
    located = pack_textures.find_packs(iso_path, set(patched))
    packs: dict[str, bytes] = {}
    unpacked = sorted(set(patched) - set(located))
    for member, places in sorted(located.items()):
        for pack_name, record in places:
            iso_file = f"{pack_textures.PACK_DIR}/{pack_name}"
            current = packs.get(iso_file)
            if current is None:
                with iso_path.open("rb") as handle:
                    iso = pycdlib.PyCdlib()
                    iso.open_fp(handle)
                    try:
                        buffer = io.BytesIO()
                        iso.get_file_from_iso_fp(buffer, iso_path=iso_file)
                        current = buffer.getvalue()
                    finally:
                        iso.close()
            packs[iso_file] = pack_textures.splice(current, record, patched[member])
    replacements.update(packs)
    report.append(
        f"packed copies spliced: {len(packs)} archives; "
        f"{len(unpacked)} scripts have no packed copy ({', '.join(unpacked)})"
    )
    return replacements, report, over


if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from falcom_font import FalcomFont
    from korean_slots import build_slot_map, make_encoder

    encode = make_encoder(
        build_slot_map(FalcomFont(Path("font_debug/pspfont_orig_from_pack.dat").read_bytes()))
    )
    korean = load_korean()
    reps, report, over = build(Path("Vantage Master Portable (1.01).iso"), encode, korean)
    print(f"translations loaded: {len(korean)}")
    print(f"files to replace: {len(reps)}")
    print(f"lines that do not fit: {len(over)}")
    for line in over[:20]:
        print("  " + line)
