# -*- coding: utf-8 -*-
"""Every proper name, and everywhere it is spelled differently.

The same creature is named in five places -- the executable's field, the
gallery page drawn from it, the master's profile, the unit table and the map
advice -- and each was translated by someone who could not see the others.
This lists the names whose Japanese appears in more than one place and whose
Korean does not agree, and the names that appear only once, which are the
coinages nobody had a chance to check.

    python check_names.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import vmp_opening_text as opening
import vmp_system_text as system

KATAKANA = re.compile(r"[\u30a1-\u30fa][\u30a1-\u30fa\u30fc\u30fb]{2,}")


def executable() -> dict[str, str]:
    out: dict[str, str] = {}
    for label, _offset, korean in system.SYSTEM_TEXT:
        out.setdefault(label, korean)
    for name in dir(opening):
        if not name.isupper():
            continue
        table = getattr(opening, name)
        if not isinstance(table, list):
            continue
        for row in table:
            if (isinstance(row, tuple) and len(row) >= 3
                    and isinstance(row[0], str) and isinstance(row[2], str)):
                out.setdefault(row[0], row[2])
    return out


def folder(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for file in sorted(path.glob("*.json")):
        for japanese, korean in json.loads(file.read_text(encoding="utf-8")).items():
            out.setdefault(japanese, korean)
    return out


def main() -> None:
    sources = {
        "exe": executable(),
        "script": folder(Path("itp_work/kr_scripts")),
        "event": folder(Path("itp_work/event_kr")),
    }
    # A name on its own, not a sentence: those are the entries that name a thing.
    named: dict[str, dict[str, str]] = {}
    for where, table in sources.items():
        for japanese, korean in table.items():
            bare = japanese.strip("@ff&?0 ﾀ?@囮Y")
            if len(bare) > 16 or "\n" in bare or not KATAKANA.fullmatch(bare):
                continue
            spelling = korean.strip("@ff&?0 ﾀ?@囮Y").strip()
            named.setdefault(bare, {})[where] = spelling

    clashes = {name: seen for name, seen in named.items() if len(set(seen.values())) > 1}
    print(f"{len(named)} names, {len(clashes)} spelled more than one way")
    for name, seen in sorted(clashes.items()):
        print(f"  {name}")
        for where, spelling in sorted(seen.items()):
            print(f"      {where:7s} {spelling}")

    # And the same name written into someone else's sentence.  The name has to
    # stand on its own there: ルフィー inside マルフィール is a different word,
    # and so is アルマス inside ネイティアルマスター.
    inside = 0
    for name, seen in sorted(named.items()):
        best = seen.get("exe") or seen.get("event") or next(iter(seen.values()))
        standalone = re.compile(
            r"(?<![ァ-ヺー])" + re.escape(name) + r"(?![ァ-ヺー])")
        for where, table in sources.items():
            for japanese, korean in table.items():
                if japanese.strip("@ff&?0 ﾀ?@囮Y") == name:
                    continue
                if standalone.search(japanese) and best not in korean:
                    print(f"  {name} -> {best!r} not found in {where}: {korean[:44]!r}")
                    inside += 1
    print(f"{inside} sentences spell a name differently from the name entry")
    sys.exit(1 if clashes or inside else 0)


if __name__ == "__main__":
    main()
