# -*- coding: utf-8 -*-
"""Report whether Korean translations fit the executable fields they replace.

Two fields in this table turned out not to be strings at all, and each cost a
round of in-game testing.  0x178768 began with FF FF FF FF, an int32 -1
sentinel that CP932 decodes to a private-use character; 0x16C5AE began two
bytes inside the float 1.0 that the world map's setup routine loads as a base
scale, so overwriting it made the map, its icons and its panel vanish.  The two
guards below catch exactly those shapes.

The complete check would be to parse BOOT.BIN's PT_PSPREL segment, recover
every address the code builds from its R_MIPS_32 words and HI16/LO16 pairs, and
require each field to be referenced at its exact start.  That is the right test
and it is what identified 0x16C5AE; it is not implemented here because a
half-correct relocation parser matched only a quarter of the fields that are
known good, and a checker that cries wolf is worse than none.

Each field is written over the Japanese in place, so a translation may not be
longer than the slot: the string's own bytes plus whatever NUL padding follows
it.  Hangul costs two bytes in the patched font's encoding, ASCII and newlines
one, so a Japanese line of kanji buys about the same number of Hangul syllables
and no more.

Usage: python check_fit.py <todo.json> <translations.json> [more.json ...]
``translations.json`` maps a hex or decimal offset to the Korean string.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from falcom_font import FalcomFont
from korean_slots import build_slot_map, make_encoder

FONT = Path("font_debug/pspfont_orig_from_pack.dat")


def encoder():
    return make_encoder(build_slot_map(FalcomFont(FONT.read_bytes())))


def load_translations(paths: list[Path]) -> dict[int, str]:
    out: dict[int, str] = {}
    for path in paths:
        raw = json.loads(path.read_text(encoding="utf-8"))
        items = raw.items() if isinstance(raw, dict) else (
            (entry["off"], entry["korean"]) for entry in raw
        )
        for key, value in items:
            offset = key if isinstance(key, int) else int(str(key), 0)
            out[offset] = value
    return out


def main() -> None:
    todo = {entry["off"]: entry for entry in json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))}
    translations = load_translations([Path(p) for p in sys.argv[2:]])
    encode = encoder()

    missing = [off for off in todo if off not in translations]
    over: list[tuple[int, int, int, str]] = []
    bad: list[tuple[int, str, str]] = []
    for offset, korean in sorted(translations.items()):
        entry = todo.get(offset)
        if entry is None:
            bad.append((offset, korean, "offset is not in the work list"))
            continue
        # The build writes inside the Japanese only; the NUL run behind a string
        # is often the low half of an aligned constant, so it is not ours.
        capacity = entry["len"]
        try:
            size = len(encode(korean))
        except Exception as error:  # noqa: BLE001 - report, do not abort the sweep
            bad.append((offset, korean, str(error)))
            continue
        if size > capacity:
            over.append((offset, size, capacity, korean))
        if any("" <= char <= "" for char in entry["jp"]):
            # CP932 turns 0xFF into U+F8F3, so a record whose name is preceded
            # by an int32 -1 sentinel reads back as a string with four
            # private-use characters in front of it.  Writing Korean over those
            # four bytes is what stopped the scenario world map drawing its
            # map, its icons and its panel: five menu records lost the
            # sentinel.  Start the field after them instead.
            bad.append((offset, korean, "the Japanese carries private-use bytes"))
        raw = entry["jp"].encode("cp932", "replace")[:1]
        if entry["off"] % 4 and raw and not (
            raw[0] < 0x80
            or 0xA1 <= raw[0] <= 0xDF
            or 0x81 <= raw[0] <= 0x9F
            or 0xE0 <= raw[0] <= 0xFC
        ):
            # A field that starts part-way into a four-byte word, on a byte that
            # is not a valid CP932 lead, is not a string: it is the tail of an
            # aligned constant.  0x16C5AE was the top half of the float 1.0 at
            # 0x16C5AC, and overwriting it is what stopped the scenario world
            # map drawing its map, its icons and its panel.  Such a field has to
            # start at the next word boundary instead.
            bad.append((offset, korean, "field starts inside an aligned constant"))
        for mark, name in ((chr(10), "LF"), (chr(13), "CR")):
            # Some fields break their lines with CR, not LF, and that is exactly
            # why 62 of them were missed by the first census.  A Korean line that
            # swaps one separator for the other silently reflows the dialog.
            if korean.count(mark) != entry["jp"].count(mark):
                bad.append(
                    (offset, korean, f"{name} count {korean.count(mark)} != {entry['jp'].count(mark)}")
                )

    print(f"translated {len(translations)}/{len(todo)}  missing {len(missing)}")
    for offset, size, capacity, korean in over:
        print(f"  OVER 0x{offset:06X} {size}>{capacity} bytes: {korean!r}")
    for offset, korean, why in bad:
        print(f"  BAD  0x{offset:06X} {why}: {korean!r}")
    if missing:
        print("  missing offsets:", " ".join(f"0x{o:06X}" for o in sorted(missing)[:40]))
    print("OK" if not (over or bad or missing) else "NOT OK")


if __name__ == "__main__":
    main()
