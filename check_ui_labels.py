# -*- coding: utf-8 -*-
"""Check every rebuilt UI atlas for Japanese the replacement left behind.

A label box is the bounding rectangle of the art it replaces, and getting that
rectangle a few pixels too small is the one mistake that does not show up in
the build: the Korean is drawn, the atlas still decodes, and a stroke of the
Japanese survives just outside the box.  On screen that is a stray mark beside
the label -- the tip of a bracket, the tail of a long vowel.

The test is whether the original art crosses the box's edge.  A stroke the box
cut through has ink on both sides of that edge -- the half inside was painted
over, the half outside was not -- while art that merely sits nearby, the next
label along or a cell border, stops at the line and is not a leftover.

    python check_ui_labels.py            # every atlas
    python check_ui_labels.py sysmenu    # one
"""

from __future__ import annotations

import argparse
from pathlib import Path

import falcom_itp as itp
import patch_ui_textures as ui
import ui_texture_text as spec
from itp_text import Box

RAW = Path("itp_work/raw")
PATCHED = Path("itp_work/patched")

LEFTOVER = 3    # cut strokes before a box is worth reporting
SOLID = 3       # multiples of the ink gap: a cut stroke is solid, a halo is not


def load_patched(stem: str) -> itp.ItpImage:
    """A rebuilt atlas, unpadded: it is NUL-padded to the ISO slot length and
    the loader rejects trailing bytes, so grow the slice until it parses."""
    raw = PATCHED.joinpath(f"{stem}.itp").read_bytes()
    scratch = PATCHED / "_check.itp"
    for size in range(len(raw.rstrip(bytes(1))), len(raw) + 1):
        scratch.write_bytes(raw[:size])
        try:
            return itp.load(scratch)
        except Exception:
            continue
    raise SystemExit(f"{stem}: itp_work/patched copy will not decode")


def check(stem: str, labels) -> list[str]:
    before = itp.load(RAW / f"{stem}.itp")
    after = load_patched(stem)
    problems = []
    # These atlases pack their labels a few pixels apart, so the margin around
    # one box lands inside the next; a neighbour's own art is not a leftover.
    for x, y, w, h, text in labels:
        box = Box(x, y, w, h)
        # Read the plate for one row past each edge as well: the pixel being
        # tested for a leftover is outside the box, and on a shaded button the
        # row above it is a different colour from the row below.
        view = Box(max(0, x - 1), max(0, y - 1),
                   min(before.width, x + w + 1) - max(0, x - 1),
                   min(before.height, y + h + 1) - max(0, y - 1))
        plate = ui.plate_rows(before, view)

        def ink(column: int, row: int) -> bool:
            """Is this pixel lettering rather than the plate under it?

            Measured against the plate of the row it is on, the way the patcher
            measures it.  Against the plate as a whole a shaded button reads as
            ink from end to end, and every tight box looks like it cut a
            stroke.
            """
            if not (0 <= column < before.width and 0 <= row < before.height):
                return False
            colour = before.palette[before.pixels[row * before.width + column]]
            if colour[3] < 40:
                return False  # the bare atlas around a plate draws nothing
            near, far = plate[min(max(row - view.y, 0), view.h - 1)]
            # Solid ink, not the soft edge of a glyph: every tight box has a
            # pixel of halo just outside it, and that is not a cut stroke.
            return min(ui.distance(colour, before.palette[near]),
                       ui.distance(colour, before.palette[far])) > ui.INK_GAP * SOLID

        # A stroke the box cut through has ink on both sides of the edge: the
        # part inside was painted over and the part outside was not.  Ink that
        # merely sits nearby -- the next label along, a cell border, the dot
        # beside a menu item -- does not cross the line and is not a leftover.
        leftover = sum(
            1
            for row in range(box.y, box.bottom)
            for column, outside in ((box.x, box.x - 1), (box.right - 1, box.right))
            if ink(column, row) and ink(outside, row)
        ) + sum(
            1
            for column in range(box.x, box.right)
            for row, outside in ((box.y, box.y - 1), (box.bottom - 1, box.bottom))
            if ink(column, row) and ink(column, outside)
        )
        if leftover >= LEFTOVER:
            problems.append(f"LEFTOVER {leftover:3d}px  ({x},{y},{w},{h})  {text}")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("atlases", nargs="*", help="default: every atlas")
    args = parser.parse_args()

    names = args.atlases or sorted(spec.PATCHES)
    bad = 0
    for stem in names:
        problems = check(stem, spec.PATCHES[stem])
        if problems:
            bad += 1
            print(f"== {stem}")
            for problem in problems:
                print(f"   {problem}")
    print(f"{len(names) - bad}/{len(names)} atlases clean")


if __name__ == "__main__":
    main()
