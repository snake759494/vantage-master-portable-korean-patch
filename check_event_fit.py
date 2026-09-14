# -*- coding: utf-8 -*-
"""Check every Korean dialogue line against the field it replaces.

A key that matches nothing is the dangerous case: it looks translated in the
chunk file and silently never reaches the ISO, so it is reported as an error
rather than skipped.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, ".")
from falcom_font import FalcomFont
from korean_slots import build_slot_map, make_encoder
from patch_event_scripts import load_korean

todo = json.loads(Path("itp_work/event_todo.json").read_text(encoding="utf-8"))
budget = {e["jp"]: e["len"] for rows in todo.values() for e in rows}
korean = load_korean()
encode = make_encoder(build_slot_map(FalcomFont(Path("font_debug/pspfont_orig_from_pack.dat").read_bytes())))

unknown, over, bad = [], [], []
for japanese, text in sorted(korean.items()):
    if japanese not in budget:
        unknown.append(japanese); continue
    try:
        size = len(encode(text))
    except Exception as error:  # noqa: BLE001
        bad.append((japanese, str(error))); continue
    if size > budget[japanese]:
        over.append((japanese, text, size, budget[japanese]))
    if text.count("\n") != japanese.count("\n"):
        bad.append((japanese, f"line count {text.count(chr(10))} != {japanese.count(chr(10))}"))

print(f"translated {len(korean)}/{len(budget)} unique lines  ({len(korean)*100//max(len(budget),1)}%)")
for j in unknown[:10]:
    print(f"  KEY NOT IN ANY SCRIPT: {j!r}")
for j, t, s, c in over[:10]:
    print(f"  OVER {s}>{c}: {j} -> {t}")
for j, why in bad[:10]:
    print(f"  BAD {why}: {j}")
print("OK" if not (unknown or over or bad) else f"NOT OK ({len(unknown)} unknown, {len(over)} over, {len(bad)} bad)")
