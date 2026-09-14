# -*- coding: utf-8 -*-
"""Collect every translatable line in the event scripts, in reading order.

The dialogue lives in ``data/event/_asm/*._as`` as NUL-terminated CP932 strings
inlined in the bytecode, and 226 of the 235 files are carried verbatim inside
``data/pack/ev*.dat`` -- the remaining 7 have no packed copy at all.  Nothing is
compressed, so a line can be rewritten where it lies.

It may not change length, though.  The strings run one after another and the
parser walks them by their terminators, so a shorter Korean line padded with
NULs would read as an empty string and could end the block early.  Translations
are therefore padded with spaces to the exact byte count of the Japanese, which
leaves every byte position in the file untouched.
"""

from __future__ import annotations

import io
import json
import re
from pathlib import Path

import pycdlib

ISO = Path("Vantage Master Portable (1.01).iso")
EVENT_DIR = "/PSP_GAME/USRDIR/data/event/_asm"
OUT = Path("itp_work/event_todo.json")

JAPANESE = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")


def runs(data: bytes) -> list[tuple[int, str]]:
    """Every NUL-terminated CP932 string that carries kana or kanji."""
    out: list[tuple[int, str]] = []
    start = None
    for index, byte in enumerate(data):
        if byte == 0:
            if start is not None and index - start >= 2:
                try:
                    text = data[start:index].decode("cp932")
                except UnicodeDecodeError:
                    text = None
                if text and JAPANESE.search(text):
                    out.append((start, text))
            start = None
        elif start is None:
            start = index
    return out


def main() -> None:
    with ISO.open("rb") as handle:
        iso = pycdlib.PyCdlib()
        iso.open_fp(handle)
        try:
            files = {}
            for path, _dirs, names in iso.walk(iso_path=EVENT_DIR):
                for name in names:
                    full = path.rstrip("/") + "/" + name
                    buffer = io.BytesIO()
                    iso.get_file_from_iso_fp(buffer, iso_path=full)
                    files[name.split(";")[0]] = buffer.getvalue()
        finally:
            iso.close()

    todo = {}
    lines = chars = 0
    for name, data in sorted(files.items()):
        found = runs(data)
        if not found:
            continue
        todo[name] = [
            {"off": offset, "len": len(text.encode("cp932")), "jp": text}
            for offset, text in found
        ]
        lines += len(found)
        chars += sum(len(text.encode("cp932")) for text in (t for _o, t in found))

    OUT.write_text(json.dumps(todo, ensure_ascii=False, indent=1), encoding="utf-8")
    unique = {entry["jp"] for entries in todo.values() for entry in entries}
    print(f"{len(todo)} files, {lines} lines, {chars:,} bytes, {len(unique)} unique")
    sizes = sorted((len(v), k) for k, v in todo.items())
    print(f"lines per file: min {sizes[0][0]} median {sizes[len(sizes)//2][0]} max {sizes[-1][0]}")
    print("biggest files:", ", ".join(f"{k}({n})" for n, k in sizes[-6:]))


if __name__ == "__main__":
    main()
