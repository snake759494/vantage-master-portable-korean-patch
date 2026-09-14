"""Draw the Korean questionnaire into make_7/make_8/make_9.itp.

Paragraphs are redrawn line by line at the original line pitch so the sprite
rectangles the game samples keep their size and position.  The option strips
sit on a 20-pixel grid down the right edge of each atlas and are measured from
the art itself.

All three atlases are drawn in one colour -- white glyphs ringed in black, the
way make_9 already draws its questions and the way the button labels are drawn.
Getting there needs a palette rewrite, not just a different choice of index;
see ``reserve``.
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from PIL import Image

import falcom_itp as itp
import quiz_text
from itp_text import Box
from patch_ui_textures import render_mask


def option_box(image: itp.ItpImage, column: tuple[int, int], pitch: int, index: int) -> Box | None:
    """The drawn extent of one option strip."""
    x0, x1 = column
    top = index * pitch
    field = Counter(image.pixels).most_common(1)[0][0]  # the atlas-wide field
    base = image.palette[field][3]

    def drawn(x: int, y: int) -> bool:
        # Near-transparent noise shares the field's alpha; only real art differs.
        return abs(image.palette[image.pixels[y * image.width + x]][3] - base) > 12

    ys = [y for y in range(top, top + pitch) if any(drawn(x, y) for x in range(x0, x1))]
    if not ys:
        return None

    # The plates are not cut exactly on the 20-pixel grid: the last few rows of
    # a slot can already carry the next label's wider lead-in, and taking the
    # union of every row's extent then drags the box sideways -- make_7's third
    # option came out centred on 432 instead of 440.  The median row is immune.
    spans = []
    for y in ys:
        row = [x for x in range(x0, x1) if drawn(x, y)]
        if row:
            spans.append((min(row), max(row)))
    if not spans:
        return None
    spans.sort()
    left = sorted(span[0] for span in spans)[len(spans) // 2]
    right = sorted(span[1] for span in spans)[len(spans) // 2]
    return Box(left, min(ys), right - left + 1, max(ys) - min(ys) + 1)


NOMINAL_SIZE = 13  # the size the Japanese art in these atlases is drawn at
BOX_PAD_Y = 1      # the detected boxes hug the glyphs; the slot is a little taller

# make_9 does not outline its glyphs, it drops a black shadow straight down
# two pixels: of its solid black pixels 67.8% have a solid white pixel exactly
# two rows above, and 65.4% of body pixels have no black neighbour at all,
# which rules a ring out.  The shadow also degrades far better than a ring
# would if the sprite path ever ignored palette colour -- a glyph plus a
# shifted copy still reads as a glyph, a glyph plus a ring is a blob.
SHADOW_DROP = 2
SHADOW_GAMMA = 0.65  # the shadow is carried heavier than the body's own fringe
RUNGS = 4            # anti-alias steps per ramp; a 16x8 block may hold 16 entries

BODY = (255, 255, 255)   # the option the cursor is on, and every paragraph
DIMMED = (190, 190, 190)  # the option it is not on -- make_9's own ratio, 0.74
SHADOW = (0, 0, 0)


def ramp(colour: tuple[int, int, int]) -> tuple[tuple[int, int, int, int], ...]:
    return tuple(
        colour + (round(255 * (step + 1) / RUNGS),) for step in range(RUNGS)
    )


def outside_index(image: itp.ItpImage, box: Box, sides_only: bool = False) -> int:
    """The index a box sits on, read from just outside its edges.

    A box hugs its glyphs, so its own rim and even its histogram are dominated
    by ink -- sampling those is what filled make_7's paragraphs with the glyph
    colour and left pale text on a bright slab.  The option strips stack with
    no vertical gap, so looking above and below one lands on its neighbour's
    plate rather than on the field; those are sampled from the sides alone.
    """
    margin = 2
    samples: list[int] = []
    for offset in range(1, margin + 1):
        if not sides_only:
            for x in range(box.x, box.right):
                for y in (box.y - offset, box.bottom - 1 + offset):
                    if 0 <= y < image.height:
                        samples.append(image.pixels[y * image.width + x])
        for y in range(box.y, box.bottom):
            for x in (box.x - offset, box.right - 1 + offset):
                if 0 <= x < image.width:
                    samples.append(image.pixels[y * image.width + x])
    return Counter(samples).most_common(1)[0][0]


def reserve(image: itp.ItpImage, colours: tuple[tuple[int, int, int, int], ...]) -> list[int]:
    """Point spare palette entries at the colours the Korean is drawn in.

    All three of these atlases are greyscale, and each carries its own ramp of
    white through black at its own opacities, so no one choice of index draws
    the same colour in all three.  Rather than match them index by index, the
    colours the Korean wants are written into entries none of the pixels use:
    clearing the question boxes frees 255 of make_7's 256 entries and 229 of
    make_8's, which is room enough.  Only the RGBA of an entry changes; the
    block encoding cares about index values alone, so this is free.
    """
    used = set(image.pixels)
    free = [index for index in range(len(image.palette)) if index not in used]
    if len(free) < len(colours):
        raise ValueError(
            f"{len(free)} spare palette entries for {len(colours)} colours"
        )
    chosen = free[-len(colours) :]
    for index, colour in zip(chosen, colours):
        image.palette[index] = colour
    return chosen


def clear(image: itp.ItpImage, box: Box, field: int) -> None:
    for y in range(box.y, box.bottom):
        start = y * image.width + box.x
        image.pixels[start : start + box.w] = bytes([field]) * box.w


def draw_lines(
    image: itp.ItpImage,
    box: Box,
    lines: list[str],
    body: list[int],
    shadow: list[int],
) -> None:
    """Lay the Korean out at the original line pitch, over a cleared box.

    Shadow first and body over it: the body is opaque where it lands, so the
    two layers never have to be blended into their own palette entries, which
    is what keeps a 16-colour block within budget.  The glyph is rasterised two
    pixels shorter than its slot so the shadow has somewhere to fall.
    """
    floor = 255 // (RUNGS * 2)
    pitch = box.h / len(lines)
    for row, text in enumerate(lines):
        if not text.strip():
            continue
        top = box.y + int(row * pitch)
        height = max(int((row + 1) * pitch) - int(row * pitch), 1)
        glyph_box = Box(box.x, top, box.w, max(height - SHADOW_DROP, 1))
        data = render_mask(text, glyph_box, pad=0, max_size=NOMINAL_SIZE).load()

        coverage = [
            [data[x, y] for x in range(glyph_box.w)] for y in range(glyph_box.h)
        ]
        for y, line in enumerate(coverage):
            drop = y + SHADOW_DROP
            if drop >= height:
                break
            base = (top + drop) * image.width + box.x
            for x, value in enumerate(line):
                if value < floor:
                    continue
                weight = (value / 255) ** SHADOW_GAMMA
                image.pixels[base + x] = shadow[min(RUNGS - 1, int(weight * RUNGS))]
        for y, line in enumerate(coverage):
            base = (top + y) * image.width + box.x
            for x, value in enumerate(line):
                if value < floor:
                    continue
                image.pixels[base + x] = body[min(RUNGS - 1, value * RUNGS // 256)]


def preview(before: itp.ItpImage, after: itp.ItpImage, boxes: list[Box], path: Path, scale: int = 2) -> None:
    def strip(image: itp.ItpImage, box: Box) -> Image.Image:
        rgba = bytearray()
        for y in range(box.y, box.bottom):
            for x in range(box.x, box.right):
                rgba.extend(image.palette[image.pixels[y * image.width + x]])
        tile = Image.frombytes("RGBA", (box.w, box.h), bytes(rgba))
        plate = Image.new("RGBA", tile.size, (26, 34, 62, 255))
        return Image.alpha_composite(plate, tile).convert("RGB")

    rows = [(strip(before, box), strip(after, box)) for box in boxes]
    gap = 6
    width = max(max(a.width, b.width) for a, b in rows) + gap * 2
    height = sum(a.height + b.height + gap * 2 for a, b in rows) + gap
    sheet = Image.new("RGB", (width, height), (12, 12, 18))
    y = gap
    for a, b in rows:
        sheet.paste(a, (gap, y))
        y += a.height + 2
        sheet.paste(b, (gap, y))
        y += b.height + gap * 2
    sheet.resize((sheet.width * scale, sheet.height * scale), Image.Resampling.NEAREST).save(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("itp_work/raw"))
    parser.add_argument("--out", type=Path, default=Path("itp_work/patched"))
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    for name, (paragraphs, column, pitch, options) in quiz_text.QUIZ.items():
        source = (args.raw / f"{name}.itp").read_bytes()
        before = itp.load(args.raw / f"{name}.itp")
        image = itp.load(args.raw / f"{name}.itp")

        # Measure every box against the untouched art first: an option strip is
        # found by where the art differs from the field, so clearing one strip
        # before measuring the next would lose it.
        work: list[tuple[Box, list[str], int, bool]] = []
        for x, y, w, h, lines in paragraphs:
            top = max(y - BOX_PAD_Y, 0)
            bottom = min(y + h + BOX_PAD_Y, image.height)
            box = Box(x, top, w, bottom - top)
            work.append((box, lines, outside_index(image, box), True))
        focused = quiz_text.FOCUSED[name]
        strips: list[tuple[Box, Box, list[str], int, bool]] = []
        for index, text in sorted(options.items()):
            box = option_box(image, column, pitch, index)
            if box is None:
                raise ValueError(f"{name}: option strip {index} is empty")
            # The text is centred on the median row, but the whole slot has to
            # be wiped: a label's plate flares wider on its first rows, and
            # clearing only the median width left plate ends and shards of the
            # Japanese behind the Korean.
            slot = Box(column[0], index * pitch, column[1] - column[0], pitch)
            field = outside_index(image, box, sides_only=True)
            strips.append((slot, box, [text], field, index in focused))
            work.append((box, [text], field, index in focused))

        for box, _lines, field, _lit in work[: len(paragraphs)]:
            clear(image, box, field)
        for slot, _box, _lines, field, _lit in strips:
            clear(image, slot, field)
        slots = reserve(image, ramp(BODY) + ramp(DIMMED) + ramp(SHADOW))
        lit, dim, shadow = slots[:RUNGS], slots[RUNGS : RUNGS * 2], slots[RUNGS * 2 :]
        for box, lines, _field, is_lit in work:
            draw_lines(image, box, lines, lit if is_lit else dim, shadow)
        touched = [box for box, _lines, _field, _lit in work]

        # Nothing but the questions lives in these atlases, so the field can be
        # made properly transparent.  make_7 shipped its whole 512x512 at
        # (0,0,0,23) and make_8 half of its at (0,0,0,17): a veil over every
        # line, and the reason its blocks came out at visibly different
        # brightnesses while make_9, whose field is already alpha 0, did not.
        for index in {field for _box, _lines, field, _lit in work}:
            red, green, blue, _alpha = image.palette[index]
            image.palette[index] = (red, green, blue, 0)

        # The one atlas that renders correctly in game is the one stored raw.
        # Same pixels, same palette, same slot -- only the block coder differs,
        # so matching make_9 costs nothing and removes the last structural
        # difference between the three.
        image.revision = 1004

        rebuilt = itp.dump(image)
        if len(rebuilt) > len(source):
            raise ValueError(
                f"{name} grew from {len(source)} to {len(rebuilt)} bytes"
            )
        (args.out / f"{name}.itp").write_bytes(rebuilt.ljust(len(source), b"\0"))
        preview(before, image, touched, args.out / f"{name}_preview.png")
        print(
            f"{name}: {len(paragraphs)} paragraphs + {len(options)} options, "
            f"{len(rebuilt)} bytes (slot {len(source)}, padding {len(source) - len(rebuilt)})"
        )


if __name__ == "__main__":
    main()
