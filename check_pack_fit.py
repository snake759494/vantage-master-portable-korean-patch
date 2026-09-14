# -*- coding: utf-8 -*-
"""Check that every translated script still fits its slot in asm.dat.

The loose ``._as`` files are easy: a translation padded with spaces to the
bytes the Japanese used keeps every offset.  The packed copies are the hard
part.  ``data/pack/asm.dat`` stores each script ED7-compressed, back to back,
and ``init0.dat`` carries the whole 92,534-byte file verbatim, so a member that
compresses even one byte larger than the stream it replaces would push
everything after it along.  Korean text compresses a little worse than the
Japanese it replaces, so a few maps come back over and their text has to lose a
handful of syllables.

    python check_pack_fit.py            # every member
    python check_pack_fit.py map017     # one

Each line reports the member, how many bytes over it is, and therefore roughly
how many syllables of Korean have to go (a syllable is two bytes uncompressed,
and buys about one compressed byte).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import patch_scripts as scripts
from falcom_font import FalcomFont
from korean_slots import build_slot_map, make_encoder
import ed7_optimal
from patch_packed_pspfont import (ed7_compress, ed7_decompress,
                                  parse_pack_record, u32)

PACK = Path("itp_work/asm_orig.dat")
FONT = Path("korean_font_slotmapped/pspfont_korean.dat")


def main() -> None:
    wanted = sys.argv[1:]
    encode = make_encoder(build_slot_map(FalcomFont(FONT.read_bytes())))
    korean = scripts.load_korean()
    pack = PACK.read_bytes()
    over = []
    changed = 0
    for index in range(u32(pack, 0)):
        name, offset, compressed, _plainsize, _flags = parse_pack_record(pack, index)
        if wanted and not any(word in name for word in wanted):
            continue
        plain = ed7_decompress(pack[offset : offset + compressed])
        patched, lines, _trouble = scripts.patch_script(plain, korean, encode)
        if not lines:
            continue
        changed += 1
        stream = min(len(ed7_compress(patched)), len(ed7_optimal.compress(patched)))
        if stream > compressed:
            over.append((stream - compressed, name, stream, compressed))
    over.sort(reverse=True)
    for excess, name, stream, room in over:
        print(f"{name}: {excess} bytes over ({stream}/{room}) "
              f"-- cut about {max(1, excess)} syllables of Korean")
    print(f"{changed} members translated, {len(over)} over their slot")

    # A work list for whoever has to shorten them: the member, how much has to
    # go, and every string in it with the Korean as it stands.
    if not wanted:
        work = {}
        for excess, name, _stream, _room in over:
            index = next(i for i in range(u32(pack, 0))
                         if parse_pack_record(pack, i)[0] == name)
            _n, offset, compressed, _u, _f = parse_pack_record(pack, index)
            plain = ed7_decompress(pack[offset : offset + compressed])
            work[name] = {
                "over": excess,
                "strings": [{"japanese": japanese, "korean": korean.get(japanese, ""),
                             "bytes": length}
                            for _o, length, japanese in scripts.runs(plain)
                            if japanese in korean],
            }
        Path("itp_work/todo/pack_over.json").write_text(
            json.dumps(work, ensure_ascii=False, indent=1), encoding="utf-8")
        print("work list: itp_work/todo/pack_over.json")
    sys.exit(1 if over else 0)


if __name__ == "__main__":
    main()
