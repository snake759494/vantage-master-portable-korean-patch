# -*- coding: utf-8 -*-
"""Check a Korean script translation against the byte budget it has to fit.

The map, unit and master scripts hold their text inline in the bytecode: each
string is NUL-terminated and the binary that follows starts at the next byte,
so a translation may be shorter than the Japanese but never longer.  A Hangul
syllable costs two bytes in the game's font slots, exactly what a kanji or a
kana costs, and ASCII costs one.

    python check_script_fit.py itp_work/kr_scripts/map_help_0.json
    python check_script_fit.py                    # every file there
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

TODO = Path("itp_work/todo")
KR = Path("itp_work/kr_scripts")


def width(text: str) -> int:
    """Bytes the game will store for ``text``."""
    total = 0
    for char in text:
        if char.isascii():
            total += 1
        elif char in "\r\n":
            total += 1
        else:
            total += 2
    return total


def budgets() -> dict[str, int]:
    """Japanese string -> the bytes it occupies, over every todo list."""
    out: dict[str, int] = {}
    for path in TODO.glob("*.json"):
        if path.name.startswith("chunk_"):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        for rows in data.values():
            if not isinstance(rows, list):
                continue
            for row in rows:
                if isinstance(row, list) and len(row) == 3:
                    _offset, length, japanese = row
                    out[japanese] = max(out.get(japanese, 0), length)
    return out


def main() -> None:
    limits = budgets()
    paths = [Path(a) for a in sys.argv[1:]] or sorted(KR.glob("*.json"))
    bad = 0
    checked = 0
    for path in paths:
        pairs = json.loads(path.read_text(encoding="utf-8"))
        for japanese, korean in pairs.items():
            checked += 1
            if japanese not in limits:
                print(f"{path.name}: UNKNOWN SOURCE  {japanese[:40]!r}")
                bad += 1
                continue
            room = limits[japanese]
            used = width(korean)
            if used > room:
                print(f"{path.name}: OVER by {used - room:3d} "
                      f"({used}/{room})  {korean[:50]!r}")
                bad += 1
            if japanese.count("\n") != korean.count("\n"):
                print(f"{path.name}: LINES {japanese.count(chr(10))} -> "
                      f"{korean.count(chr(10))}  {korean[:50]!r}")
                bad += 1
    print(f"{checked} translations checked, {bad} problems")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
