# -*- coding: utf-8 -*-
"""Check a rebuilt ISO against the one it was made from.

Four things have to hold, and each of them has broken at least once:
the executable must be the same length; the five int32 -1 sentinels and the two
float constants in it must be intact (a Korean string that ran a byte long over
one of those froze the world map); every data/system texture must still be the
length its ISO slot holds; and every texture that changed must still decode.
"""

from __future__ import annotations

import argparse
import io
import re
import struct
from pathlib import Path

import pycdlib

import falcom_itp as itp

BOOT = "/PSP_GAME/SYSDIR/BOOT.BIN"
SYSTEM = "/PSP_GAME/USRDIR/data/system"
SENTINELS = (0x178768, 0x17877C, 0x178790, 0x1787A4, 0x1787B8)
FLOATS = ((0x15F26C, 0.5), (0x16C5AC, 1.0))
SCRATCH = Path("itp_work/tex/_verify.itp")


def read(path: Path):
    with path.open("rb") as handle:
        iso = pycdlib.PyCdlib()
        iso.open_fp(handle)
        try:
            buffer = io.BytesIO()
            iso.get_file_from_iso_fp(buffer, iso_path=BOOT)
            boot = buffer.getvalue()
            textures = {}
            for child in iso.list_children(iso_path=SYSTEM):
                if child.is_dot() or child.is_dotdot():
                    continue
                name = child.file_identifier().decode().split(";")[0]
                member = io.BytesIO()
                iso.get_file_from_iso_fp(member, iso_path=f"{SYSTEM}/{name}")
                textures[name] = member.getvalue()
        finally:
            iso.close()
    return boot, textures


def decodes(data: bytes) -> bool:
    SCRATCH.parent.mkdir(parents=True, exist_ok=True)
    for size in range(len(data.rstrip(bytes(1))), len(data) + 1):
        SCRATCH.write_bytes(data[:size])
        try:
            itp.load(SCRATCH)
            return True
        except Exception:
            continue
    return False


def read_file(path: Path, iso_file: str) -> bytes:
    with path.open("rb") as handle:
        iso = pycdlib.PyCdlib()
        iso.open_fp(handle)
        try:
            buffer = io.BytesIO()
            iso.get_file_from_iso_fp(buffer, iso_path=iso_file)
            return buffer.getvalue()
        finally:
            iso.close()


def pack_report(original: Path, built: Path) -> list[str]:
    """Whether asm.dat and init0.dat still hold what the loader expects."""
    from patch_packed_pspfont import ed7_decompress, parse_pack_record, u32

    lines = []
    for iso_file in ("/PSP_GAME/USRDIR/data/pack/asm.dat",
                     "/PSP_GAME/USRDIR/data/pack/init0.dat"):
        was = read_file(original, iso_file)
        now = read_file(built, iso_file)
        name = iso_file.rsplit("/", 1)[1]
        if len(was) != len(now):
            lines.append(f"{name} length {len(was)} -> {len(now)}  BROKEN")
            continue
        moved = []
        short = []
        for index in range(u32(now, 0)):
            member, offset, compressed, plain, _flags = parse_pack_record(now, index)
            old_member = parse_pack_record(was, index)
            if member != old_member[0] or offset != old_member[1]:
                moved.append(member)
                continue
            if plain and len(ed7_decompress(now[offset : offset + compressed])) != plain:
                short.append(member)
        if moved or short:
            lines.append(f"{name}: {len(moved)} members moved, {len(short)} decompress "
                         f"to the wrong size  BROKEN {(moved + short)[:6]}")
        else:
            lines.append(f"{name}: {u32(now, 0)} members, none moved, all decompress")
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("built", type=Path)
    parser.add_argument("--original", type=Path,
                        default=Path("Vantage Master Portable (1.01).iso"))
    args = parser.parse_args()

    if args.built.stat().st_size != args.original.stat().st_size:
        raise SystemExit("ISO size changed")
    print(f"ISO size equal: {args.built.stat().st_size} bytes")

    before_boot, before = read(args.original)
    after_boot, after = read(args.built)

    print(f"BOOT.BIN length equal: {len(before_boot) == len(after_boot)}")
    bad = [f"0x{off:X}" for off in SENTINELS
           if struct.unpack_from("<i", after_boot, off)[0] != -1]
    print(f"int32 -1 sentinels intact: {not bad}" + (f"  BROKEN {bad}" if bad else ""))
    bad = [f"0x{off:X}" for off, want in FLOATS
           if struct.unpack_from("<f", after_boot, off)[0] != want]
    print(f"float constants intact: {not bad}" + (f"  BROKEN {bad}" if bad else ""))

    print(f"same data/system file set: {set(before) == set(after)}")
    lengths = [n for n in before if len(before[n]) != len(after.get(n, b""))]
    print(f"textures whose length changed: {lengths or 'none'}")

    changed = sorted(n for n in before if before[n] != after[n])
    groups: dict[str, int] = {}
    for name in changed:
        groups[re.sub(r"\d+\.itp$", "", name) or name] = \
            groups.get(re.sub(r"\d+\.itp$", "", name) or name, 0) + 1
    print(f"textures changed: {len(changed)}  " +
          ", ".join(f"{k} x{v}" for k, v in sorted(groups.items())))
    broken = [n for n in changed if n.endswith(".itp") and not decodes(after[n])]
    print(f"changed textures that no longer decode: {broken or 'none'}")

    # The script packs.  Nothing in these may move: the map, unit and master
    # translations are written over the Japanese at the same length, and every
    # member of asm.dat has to come back no larger than the stream it replaced,
    # because init0.dat stores the whole file verbatim.
    packs = pack_report(args.original, args.built)
    for line in packs:
        print(line)
    if bad or lengths or broken or any("BROKEN" in line for line in packs):
        raise SystemExit("verification FAILED")
    print("OK")


if __name__ == "__main__":
    main()
