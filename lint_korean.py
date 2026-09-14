# -*- coding: utf-8 -*-
"""Read every Korean line the patch writes and complain about the mechanical faults.

Not a judge of translation -- a proofreader's eye for the things that are
wrong no matter what the sentence means: a doubled space, a stray kana left in,
a full stop that became a Japanese one, a bracket opened and not closed, a line
that mixes 하십시오체 with 해요체.  What it finds still has to be read by
someone, but it finds it in ten thousand lines instead of ten.

    python lint_korean.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import vmp_opening_text as opening
import vmp_system_text as system

KANA = re.compile(r"[\u3041-\u309f\u30a1-\u30fa]")
LATIN_SENTENCE = re.compile(r"[A-Za-z]{4,}")
PAIRS = (("《", "》"), ("「", "」"), ("『", "』"), ("(", ")"), ("（", "）"), ("[", "]"))


def sources():
    # The label beside each executable field is only the first line of the
    # Japanese, kept for review; the whole field has to be read out of the
    # original executable or a bracket that closes on the second line looks
    # unclosed.
    boot = Path("itp_work/BOOT_orig.bin")
    original = boot.read_bytes() if boot.exists() else b""

    def japanese_at(offset: int, label: str) -> str:
        if not original:
            return label
        end = original.find(bytes(1), offset)
        try:
            return original[offset:end].decode("cp932")
        except UnicodeDecodeError:
            return label

    for label, offset, korean in system.SYSTEM_TEXT:
        yield "vmp_system_text", f"0x{offset:X}", korean, japanese_at(offset, label)
    for name in dir(opening):
        if not name.isupper():
            continue
        table = getattr(opening, name)
        if not isinstance(table, list):
            continue
        for row in table:
            if isinstance(row, tuple) and len(row) >= 3 and isinstance(row[2], str):
                where = f"0x{row[1]:X}" if isinstance(row[1], int) else name
                source = japanese_at(row[1], "") if isinstance(row[1], int) else ""
                yield "vmp_opening_text", where, row[2], source
    for folder in ("itp_work/kr_scripts", "itp_work/event_kr"):
        for path in sorted(Path(folder).glob("*.json")):
            for japanese, korean in json.loads(path.read_text(encoding="utf-8")).items():
                yield path.name, japanese.split("\n")[0][:20], korean, japanese


def faults(text: str, source: str | None = None) -> list[str]:
    out = []
    if KANA.search(text):
        out.append("kana left in: " + "".join(sorted(set(KANA.findall(text)))))
    # Runs of the fullwidth space are how the records screen lines its
    # columns up, so only a doubled ASCII space the Japanese did not have
    # counts as a slip.
    if "  " in text and (source is None or "  " not in source):
        out.append("doubled space")
    if "。" in text or "、" in text:
        out.append("Japanese punctuation")
    for opener, closer in PAIRS:
        # A speech bracket often opens on one line of dialogue and closes on
        # the next, so the test is not whether the Korean balances but whether
        # it balances as well as the Japanese it replaces.
        skew = text.count(opener) - text.count(closer)
        if source is not None:
            skew -= source.count(opener) - source.count(closer)
        if skew:
            out.append(f"unclosed {opener}{closer}")
    # Trailing space is how a couple of fields centre their contents; it is
    # a slip only where the Japanese did not have it.
    if text != text.rstrip() and (source is None or source == source.rstrip()):
        out.append("trailing whitespace")
    return out


def main() -> None:
    lines = 0
    bad = 0
    for row in sources():
        where, key, korean = row[0], row[1], row[2]
        source = row[3] if len(row) > 3 else None
        lines += 1
        for fault in faults(korean, source):
            print(f"{where:22s} {key:22s} {fault}")
            print(f"{'':22s} {'':22s} {korean.replace(chr(10), ' / ')[:88]}")
            bad += 1
    print(f"{lines} lines read, {bad} faults")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
