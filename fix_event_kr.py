# -*- coding: utf-8 -*-
"""Overwrite single dialogue translations: fix_event_kr.py <chunk> then stdin pairs."""
import json, sys
from pathlib import Path
chunk = Path(sys.argv[1])
d = json.loads(chunk.read_text(encoding="utf-8"))
pairs = json.loads(sys.stdin.read())
todo = json.loads(Path("itp_work/event_todo.json").read_text(encoding="utf-8"))
keys = {e["jp"] for rows in todo.values() for e in rows}
for jp, ko in pairs.items():
    assert jp in keys, jp
    d[jp] = ko
chunk.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"{chunk.name}: {len(pairs)} updated, {len(d)} total")
