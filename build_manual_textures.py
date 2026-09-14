# -*- coding: utf-8 -*-
"""Render every rulebook page into ``itp_work/patched/{manual,histor}*.itp``.

These atlases are in no pack -- the game loads them straight out of
``data/system`` -- but the ISO is rebuilt in place, so each one still has to
come back no longer than it shipped and is padded to exactly that length.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pycdlib

import falcom_itp as itp
import manual_text
import patch_manual_textures as manual

ISO = Path("Vantage Master Portable (1.01).iso")
OUT = Path("itp_work/patched")
SCRATCH = Path("itp_work/tex/_manual.itp")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    SCRATCH.parent.mkdir(parents=True, exist_ok=True)

    with ISO.open("rb") as handle:
        iso = pycdlib.PyCdlib()
        iso.open_fp(handle)
        try:
            sizes = {}
            for child in iso.list_children(iso_path=manual.ISO_DIR):
                if child.is_dot() or child.is_dotdot():
                    continue
                name = child.file_identifier().decode().split(";")[0]
                if name.endswith(".itp"):
                    sizes[name[:-4]] = child.get_data_length()
        finally:
            iso.close()

    written, tight, coarse = 0, [], []
    only = set(sys.argv[1:])
    for stem, lines in sorted(manual_text.PAGES.items()):
        if only and stem not in only:
            continue
        room = sizes[stem]
        # A repaired page usually packs smaller than the kanji it replaces, but
        # a page that is mostly table rules costs more than the text saved.  A
        # coarser repair makes longer horizontal runs, which is what the ED7
        # stream packs, so those pages step down until they fit.
        for snap in (4, 8, 16, 32):
            image = manual.read_texture(ISO, stem, SCRATCH)
            manual.apply(image, lines, snap=snap)
            data = itp.dump(image)
            if len(data) <= room:
                if snap != 4:
                    coarse.append(f"{stem} (snap {snap})")
                break
        else:
            raise SystemExit(f"{stem}: {len(data)} bytes will not fit {room}")
        if len(data) > room * 0.97:
            tight.append(f"{stem} {len(data)}/{room}")
        (OUT / f"{stem}.itp").write_bytes(data.ljust(room, b"\0"))
        written += 1
    SCRATCH.unlink(missing_ok=True)
    print(f"wrote {written} rulebook pages to {OUT}")
    if coarse:
        print(f"  {len(coarse)} needed a coarser repair to fit: " + ", ".join(coarse))
    if tight:
        print("  close to the budget: " + ", ".join(tight))


if __name__ == "__main__":
    main()
