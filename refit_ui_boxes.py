# -*- coding: utf-8 -*-
"""Re-measure every label box against the art it replaces.

The patcher centres the Korean in the box it is given, so the box has to be the
bounding rectangle of the Japanese and nothing more.  Where it is wider the
Korean drifts sideways -- the map list was the worst of it, a 128-pixel box
around 68 pixels of lettering, which pushed every name thirty pixels right of
where it belongs.

The measurement marks ink the same way the patcher does, each pixel against its
own row of the plate, and takes the bounding rectangle of what it finds.  It
only ever shrinks a box: what lies just outside one is as often the plate's own
border or the frame of a button as it is a cut stroke, and growing into that
would erase the art the label sits on.  Boxes that really do cut a stroke are
what ``check_ui_labels.py`` reports, and those are measured by hand.

    python refit_ui_boxes.py                 # report the drift
    python refit_ui_boxes.py --write         # rewrite ui_texture_text.py
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import falcom_itp as itp
import patch_ui_textures as ui
import ui_texture_text as spec
from itp_text import Box

TABLE = Path("ui_texture_text.py")

# Boxes set by hand and left alone.  Korean needs more room than Japanese for
# the same word -- three syllables where four kana fit -- and the item and
# magic tabs have a ruled frame with clear space inside it, so these four are
# opened out to the frame rather than closed down onto the katakana.
KEEP = {
    (4, 80, 28, 13), (196, 80, 27, 13),
    (4, 209, 28, 13), (196, 209, 27, 13),
    (293, 37, 106, 12),
}

# The map list's boxes are not written out one by one; they live in
# ``ui_texture_text.INFO3_BOXES``, measured by this same code.  Asking again
# only unsettles them: a box that already takes in its halo has nothing left
# outside it to grow into, so the second answer is the solid lettering alone.
GENERATED = {"info3"}


WEAK = 12    # visible distance at which a pixel is still the glyph's soft edge
HALO = 3     # pixels of soft edge a box may take in beyond the solid lettering
SOLID = 0.95 # share of a row that must be ink before it counts as a rule, not art


def spread(image: itp.ItpImage, box: Box, gap: int) -> list[list[bool]]:
    """Which pixels of the box stand ``gap`` away from their own row's plate."""
    palette = image.palette
    plate = ui.plate_rows(image, box)
    out = []
    for y in range(box.h):
        near, far = palette[plate[y][0]], palette[plate[y][1]]
        row = []
        for x in range(box.w):
            colour = palette[image.pixels[(box.y + y) * image.width + box.x + x]]
            row.append(min(ui.distance(colour, near), ui.distance(colour, far)) > gap)
        out.append(row)
    return out


def measure(image: itp.ItpImage, box: Box) -> Box | None:
    """The tight rectangle of the lettering, never larger than ``box``.

    Solid ink alone is not the whole label: a glyph fades into its background
    over a pixel or two, and on the map list -- whose plate is the bare
    transparent sheet -- that halo is plainly visible where it is left behind.
    So the rectangle is taken twice, once at the distance that says "this is
    the glyph" and once at the distance that says "this is not the plate", and
    the softer one is allowed to widen the harder one by a few pixels.  Any
    more than that and it is not a halo but the plate's own dither, which on a
    shaded plate runs the length of the box.
    """
    strong = spread(image, box, ui.INK_GAP)
    rows = [y for y in range(box.h) if any(strong[y])]
    columns = [x for x in range(box.w) if any(strong[y][x] for y in range(box.h))]
    if not rows:
        return None
    top, bottom = min(rows), max(rows)
    left, right = min(columns), max(columns)

    weak = spread(image, box, WEAK)
    for _ in range(HALO):
        if top > 0 and any(weak[top - 1][x] for x in range(left, right + 1)):
            top -= 1
        if bottom < box.h - 1 and any(weak[bottom + 1][x] for x in range(left, right + 1)):
            bottom += 1
        if left > 0 and any(weak[y][left - 1] for y in range(top, bottom + 1)):
            left -= 1
        if right < box.w - 1 and any(weak[y][right + 1] for y in range(top, bottom + 1)):
            right += 1
    # A row or column that is ink from end to end is not lettering: lettering
    # has gaps in it.  It is the rule the plate is drawn with -- the line under
    # the system menu's buttons, the frame of a tab -- and taking it into the
    # box costs the label its colours, because sixty pixels of one shade
    # outweigh the glyph they sit beside.
    def solid_row(y: int) -> bool:
        return sum(strong[y][x] for x in range(left, right + 1)) >= (right - left + 1) * SOLID

    def solid_column(x: int) -> bool:
        return sum(strong[y][x] for y in range(top, bottom + 1)) >= (bottom - top + 1) * SOLID

    while top < bottom and solid_row(top):
        top += 1
    while bottom > top and solid_row(bottom):
        bottom -= 1
    while left < right and solid_column(left):
        left += 1
    while right > left and solid_column(right):
        right -= 1

    return Box(box.x + left, box.y + top, right - left + 1, bottom - top + 1)


def refit() -> dict[str, list]:
    out: dict[str, list] = {}
    for name, labels in spec.PATCHES.items():
        if name in GENERATED:
            continue
        image = itp.load(Path(f"itp_work/raw/{name}.itp"))
        out[name] = [((x, y, w, h),
                      None if (x, y, w, h) in KEEP else measure(image, Box(x, y, w, h)),
                      text)
                     for x, y, w, h, text in labels]
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="rewrite ui_texture_text.py")
    parser.add_argument("--quiet", action="store_true", help="only count, do not list")
    args = parser.parse_args()

    moved: dict[tuple[int, int, int, int], tuple[int, int, int, int]] = {}
    for name, rows in refit().items():
        report = []
        for old, tight, text in rows:
            if tight is None:
                if old not in KEEP:
                    report.append(f"   NO INK  {old}  {text}")
                continue
            new = (tight.x, tight.y, tight.w, tight.h)
            if new == old:
                continue
            drift = ((new[0] + new[2] / 2) - (old[0] + old[2] / 2),
                     (new[1] + new[3] / 2) - (old[1] + old[3] / 2))
            moved[old] = new
            report.append("   {0} -> {1}  centre {2:+.1f},{3:+.1f}  {4}"
                          .format(old, new, drift[0], drift[1], text))
        if report and not args.quiet:
            print(f"== {name}  ({len(report)}/{len(rows)})")
            print("\n".join(report))
    print(f"{len(moved)} boxes move")

    if not args.write:
        return
    source = TABLE.read_text(encoding="utf-8")
    changed = 0
    for old, new in moved.items():
        pattern = re.compile(r"\(\s*%d,\s*%d,\s*%d,\s*%d,\s*(\"|')" % old)
        source, count = pattern.subn(
            "(%d, %d, %d, %d, " % new + chr(92) + "g<1>", source)
        changed += count
    TABLE.write_text(source, encoding="utf-8")
    print(f"{changed} entries rewritten in {TABLE}")


if __name__ == "__main__":
    main()
