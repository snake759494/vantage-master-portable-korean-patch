# -*- coding: utf-8 -*-
"""Render every gallery page into ``itp_work/patched/galle*.itp``.

Each page is written twice into the ISO -- once as the loose texture and once
inside the pack the loader actually reads -- so the output has to be padded back
to the byte length the original shipped with; ``pack_textures.splice`` will not
move a member.

``galle540`` and ``galle550`` are the locked entries and say only ``??????``, so
they are left alone.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pycdlib

import falcom_itp as itp
import gallery_text
import patch_gallery_textures as gallery
import vmp_system_text

ISO = Path("Vantage Master Portable (1.01).iso")
OUT = Path("itp_work/patched")
SCRATCH = Path("itp_work/tex/_build.itp")


def korean_by_offset() -> dict[int, str]:
    return {offset: text for _label, offset, text in vmp_system_text.SYSTEM_TEXT}


def korean_by_japanese() -> dict[str, str]:
    todo = {entry["off"]: entry for entry in json.loads(
        Path("itp_work/exe_todo.json").read_text(encoding="utf-8"))}
    korean = korean_by_offset()
    out: dict[str, str] = {}
    for offset, entry in todo.items():
        if offset in korean:
            out.setdefault(entry["jp"], korean[offset])
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    SCRATCH.parent.mkdir(parents=True, exist_ok=True)

    with ISO.open("rb") as handle:
        iso = pycdlib.PyCdlib()
        iso.open_fp(handle)
        try:
            buffer = io.BytesIO()
            iso.get_file_from_iso_fp(buffer, iso_path=gallery.BOOT_PATH)
            boot = buffer.getvalue()
            sizes = {}
            for child in iso.list_children(iso_path=gallery.ISO_DIR):
                if child.is_dot() or child.is_dotdot():
                    continue
                name = child.file_identifier().decode().split(";")[0]
                if name.startswith("galle"):
                    sizes[name[:-4]] = child.get_data_length()
        finally:
            iso.close()

    names = dict(gallery.gallery_table(boot))          # stem -> Japanese name
    by_offset = korean_by_offset()
    by_japanese = korean_by_japanese()

    plan: dict[str, tuple[str, list[str]]] = {}
    for stem, japanese in names.items():
        korean_name = by_japanese.get(japanese)
        if korean_name is None:
            raise SystemExit(f"{stem}: no Korean for {japanese!r}")
        if stem in gallery_text.MASTER_SOURCE:
            lines = by_offset[gallery_text.MASTER_SOURCE[stem]].split("\n")
        elif stem in gallery_text.NETIAAL:
            lines = gallery_text.NETIAAL[stem]
        else:
            raise SystemExit(f"{stem}: no description")
        plan[stem] = (korean_name, lines)
        variant = f"galle{int(stem[5:]) + 5:03d}"
        if variant in sizes:
            plan[variant] = (korean_name, lines)

    # Korean usually packs smaller than the kanji it replaces, but on a few
    # pages the repaired background costs more than the text saved.  Those get
    # a flatter repair until the atlas fits the length it must be spliced into.
    LADDER = [(False, 4), (True, 8), (True, 16), (True, 32)]

    written = 0
    coarse: list[str] = []
    for stem, (korean_name, lines) in sorted(plan.items()):
        room = sizes[stem]
        for step, (flat, snap) in enumerate(LADDER):
            image = gallery.read_texture(ISO, stem, SCRATCH)
            gallery.apply(image, korean_name, lines, flat, snap)
            data = itp.dump(image)
            if len(data) <= room:
                if step:
                    coarse.append(f"{stem} (flat, snap {snap})")
                break
        else:
            raise SystemExit(f"{stem}: {len(data)} bytes will not fit {room}")
        (OUT / f"{stem}.itp").write_bytes(data.ljust(room, b"\0"))
        written += 1
    SCRATCH.unlink(missing_ok=True)
    print(f"wrote {written} gallery textures to {OUT}")
    if coarse:
        print(f"  {len(coarse)} needed a flatter repair to fit: " + ", ".join(coarse))


if __name__ == "__main__":
    main()
