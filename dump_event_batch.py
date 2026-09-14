# -*- coding: utf-8 -*-
"""Print the next batch of untranslated dialogue, with each line's byte budget.

``python dump_event_batch.py <count>`` walks the scripts in order and prints the
next ``count`` lines that no chunk under ``itp_work/event_kr`` has yet.
"""
import json, sys
from pathlib import Path

TODO = json.loads(Path("itp_work/event_todo.json").read_text(encoding="utf-8"))
done = set()
for path in sorted(Path("itp_work/event_kr").glob("*.json")):
    done |= set(json.loads(path.read_text(encoding="utf-8")))

want = int(sys.argv[1]) if len(sys.argv) > 1 else 150
seen, shown = set(), 0
for name in sorted(TODO):
    rows = [e for e in TODO[name] if e["jp"] not in done and e["jp"] not in seen]
    if not rows:
        continue
    print(f"### {name}")
    for entry in rows:
        seen.add(entry["jp"])
        shown += 1
        print(f"[{entry['len']}] " + entry["jp"].replace(chr(10), "\n"))
    print()
    if shown >= want:
        break
left = sum(1 for name in TODO for e in TODO[name]
           if e["jp"] not in done and e["jp"] not in seen)
print(f"--- shown {shown}; still untranslated after this batch: {left}")
