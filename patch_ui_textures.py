"""Draw the Korean label art into the UI atlases.

Each box is analysed before it is touched: the palette entries the Japanese
label used are collected, and the Korean is drawn with those same entries.  A
label with a bright fill and a dark outline is redrawn with an outline; a flat
alpha-mask label is redrawn through an alpha ramp.  Only the ink is cleared --
the plate under it, its gradient, its dither, the icon beside it all keep the
bytes they shipped with -- and nothing outside the box is written at all, so
the atlas keeps working for every other sprite in it.
"""

from __future__ import annotations

import argparse
from collections import Counter, deque
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import falcom_itp as itp
import ui_texture_text as spec
from itp_text import Box

# The atlas art is a heavy gothic; Bold came out visibly thinner than the
# Japanese it replaces, which at 13px and 53% opacity reads as washed out.
# Below ~12px the extra weight closes up the counters, so the smallest labels
# stay on Bold -- and are drawn flat, an outline costing two of the ten pixels
# such a glyph has to work with.
TTF = "NanumSquareNeo-dEb.ttf"
TTF_SMALL = "NanumSquareNeo-cBd.ttf"
# At ten pixels a syllable like 템 or 틀 has counters one pixel wide, and Bold
# closes them into a solid block; Regular is the heaviest face that keeps them
# open at that size.
TTF_TINY = "NanumSquareNeo-bRg.ttf"
SMALL_BOX = 13
TINY_BOX = 12
RAMP_LEVELS = 4      # a 16x8 block may only hold 16 palette entries


def box_pixels(image: itp.ItpImage, box: Box) -> list[int]:
    return [
        image.pixels[y * image.width + x]
        for y in range(box.y, box.bottom)
        for x in range(box.x, box.right)
    ]


def border_indices(image: itp.ItpImage, box: Box) -> list[int]:
    """The palette indices around the rim of a box -- almost always background."""
    ring: list[int] = []
    for x in range(box.x, box.right):
        ring.append(image.pixels[box.y * image.width + x])
        ring.append(image.pixels[(box.bottom - 1) * image.width + x])
    for y in range(box.y, box.bottom):
        ring.append(image.pixels[y * image.width + box.x])
        ring.append(image.pixels[y * image.width + box.right - 1])
    return ring


GREY = 128  # the neutral the atlas is read over when colours are compared


def visible(color: tuple[int, int, int, int]) -> tuple[float, float, float]:
    """What ``color`` looks like laid over a neutral grey.

    A pixel can differ from the plate around it either by colour or by letting
    more of the screen through, and only the composite says how much of a
    difference that is.  Compared as raw RGBA, a colour at alpha 13 looks as
    far from an opaque plate as the glyph itself does, and picking "the ink
    furthest from the plate" then lands on something invisible.
    """
    weight = color[3] / 255
    return tuple(channel * weight + GREY * (1 - weight) for channel in color[:3])


def distance(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> float:
    return sum(abs(p - q) for p, q in zip(visible(a), visible(b)))


PLATE_MARGIN = 2   # columns sampled either side of a box to read its plate
PLATE_SHARE = 0.5   # of the commonest sample, before a colour anchors the plate
PLATE_STEP = 200    # how far a plate may shade away from one of those anchors


def plate_rows(image: itp.ItpImage, box: Box) -> list[tuple[int, int]]:
    """The palette indices of the plate at each end of each row of the box.

    Several of these plates are vertical gradients -- the system menu's cream
    and gold bands, the title menu's lavender-through-white -- so erasing a
    label to one flat colour would leave a stripe where the label was.  A box
    is the ink's bounding rectangle, so the columns just outside it are plate
    by construction and say what the plate is at each row.

    Two things spoil that.  A label whose art fills its plate edge to edge puts
    its own outline in those columns -- but a plate shades by steps, cream to
    gold, one brown to the next, while an outline is a different colour
    altogether, and a plate colour is one the box itself is made of.  And a
    label that fills the plate right to the atlas edge has no columns to read;
    for those the rows above and below the box answer instead, and each row
    falls back to the commonest plate colour it contains.
    """
    palette = image.palette
    left = list(range(max(0, box.x - PLATE_MARGIN), box.x))
    right = list(range(box.right, min(image.width, box.right + PLATE_MARGIN)))
    beside = [[image.pixels[y * image.width + x] for x in left + right]
              for y in range(box.y, box.bottom)]
    around = [
        image.pixels[y * image.width + x]
        for y in (list(range(max(0, box.y - PLATE_MARGIN), box.y))
                  + list(range(box.bottom, min(image.height, box.bottom + PLATE_MARGIN))))
        for x in range(box.x, box.right)
    ]
    held = Counter(box_pixels(image, box))

    def shades(samples: list[int]) -> set[int]:
        seen = Counter(samples)
        if not seen:
            return set()
        anchors = [index for index in seen
                   if seen[index] >= max(seen.values()) * PLATE_SHARE]
        return {
            index for index in seen
            if seen[index] >= 2 and held[index]
            and min(distance(palette[index], palette[anchor]) for anchor in anchors)
            <= PLATE_STEP
        }

    # The columns beside the box are the better witness -- they are level with
    # the row they describe -- so the rows above and below are only consulted
    # when the columns have nothing to say.
    common = shades([index for row in beside for index in row]) or shades(around)

    sides: list[tuple[int, int] | None] = []
    for y in range(box.y, box.bottom):
        inside = Counter(image.pixels[y * image.width + x] for x in range(box.x, box.right))

        def pick(where: list[int]) -> int | None:
            offered = [index for index in where if index in common]
            return max(offered, key=lambda index: inside[index]) if offered else None

        row = beside[y - box.y]
        near = pick(row[:len(left)])
        far = pick(row[len(left):])
        spare = pick(list(inside))
        near, far = near or far or spare, far or near or spare
        sides.append((near, far) if near is not None else None)
    for y in range(len(sides)):
        if sides[y] is None:
            sides[y] = next((sides[o] for o in range(y - 1, -1, -1) if sides[o] is not None),
                            None)
    for y in range(len(sides) - 1, -1, -1):
        if sides[y] is None:
            spare = Counter(border_indices(image, box)).most_common(1)[0][0]
            sides[y] = next((sides[o] for o in range(y + 1, len(sides)) if sides[o] is not None),
                            (spare, spare))
    return sides


INK_GAP = 45      # visible distance from the plate that makes a pixel part of a glyph
OFF_AXIS = 45     # how far off the plate-to-fill line an outline colour sits
BEHIND = -0.15    # ... or how far past the plate, away from the fill, it sits


def beyond(place: tuple[float, float]) -> bool:
    """True when a colour is too far off the plate-to-fill line to be a cover."""
    astray, along = place
    return astray > OFF_AXIS or along < BEHIND
OUTLINE_SHARE = 0.15  # of the ink, before an edge colour counts as an outline
FLOOR_SHARE = 0.06    # ... and before it counts as a colour the label is drawn in
INK_SHADE = 50    # RGB distance within which two entries are one ink at two opacities
SHELTERED = 0.5   # how much of a fill may touch the plate; more than this is anti-aliasing
NEEDS_RIM = 120   # nearer its plate than this, a fill is unreadable without its outline
MIXED = 0.12      # nearest either end of a pair a blend of them is taken to lie
BLEND_SLACK = 30  # RGB distance off that line within which it still counts as one


def off_axis(plate, fill, color) -> tuple[float, float]:
    """Where ``color`` lies relative to the line from the plate to the fill.

    Returns how far off that line it sits and how far along it -- 0 at the
    plate, 1 at the fill.  This is what tells an outline from anti-aliasing.
    A pixel that is merely a partial cover of the glyph lands on the line, part
    of the way along it; the purple rim around the result screen's lettering
    sits off it, and a black rim around white lettering on a transparent field
    sits on it but on the wrong side of the plate.
    """
    plate, fill, color = visible(plate), visible(fill), visible(color)
    axis = [f - p for f, p in zip(fill, plate)]
    span = sum(value * value for value in axis)
    offset = [c - p for c, p in zip(color, plate)]
    if not span:
        return sum(abs(value) for value in offset), 0.0
    along = sum(a * o for a, o in zip(axis, offset)) / span
    return sum(abs(o - along * a) for a, o in zip(axis, offset)), along


def analyse(image: itp.ItpImage, box: Box) -> dict:
    """Work out what the label in ``box`` is drawn with.

    The game's label art comes in two shapes.  Most of it is one colour laid
    down through an alpha ramp -- the button hints, the map names.  The rest is
    pixel lettering: a bright fill inside a second, contrasting outline, which
    has to be drawn the same way or the Korean reads as a flat blob against art
    that is not.

    The fill is the ink the plate does not reach; the outline is the ink that
    rings it.  Anti-aliasing rings a glyph too, so those two are told apart by
    colour: a partial cover of the glyph lands on the line from the plate to
    the fill, and a genuine second colour does not.
    """
    palette = image.palette
    grid = [
        [image.pixels[y * image.width + x] for x in range(box.x, box.right)]
        for y in range(box.y, box.bottom)
    ]
    plate = plate_rows(image, box)
    # For erasing, every row's own plate colour counts.  For deciding what is
    # ink, only a colour that backs a quarter of the box does: a box a row or
    # two taller than its plate ends up with the transparent atlas behind it
    # in the list, and measuring "furthest from the plate" against that picks
    # the outline over the fill.
    backing = Counter(index for pair in plate for index in pair)
    plate_colours = {palette[index] for index, rows in backing.items()
                     if rows >= len(plate) * 0.25}
    # A short box on a smooth gradient can have a different colour behind every
    # row and nothing backing a quarter of it; then all of them count.
    plate_colours = plate_colours or {palette[index] for index in backing}

    # Ink is decided a row at a time, against that row's own plate.  Measured
    # against the plate as a whole it cannot be: the title bar shades from
    # lavender through white and back, so the white its lettering is made of is
    # also the colour the plate wears across its middle.  Compared with every
    # row at once the lettering disappears into its own background and only the
    # purple rim is left to draw with; compared with the row it sits on it is
    # ink everywhere except the two rows where the bar really is white, and
    # there it is invisible anyway.
    inked = [
        [min(distance(palette[index], palette[plate[y][0]]),
             distance(palette[index], palette[plate[y][1]])) > INK_GAP
         for index in row]
        for y, row in enumerate(grid)
    ]
    counts = Counter(grid[y][x] for y in range(box.h) for x in range(box.w) if inked[y][x])
    ink = {index for index in counts if counts[index] > 1}
    if not ink:
        raise ValueError(f"no ink found in {box}")
    # A colour too rare to be a colour of its own is background that strayed
    # over the line, not lettering.
    for y in range(box.h):
        for x in range(box.w):
            if inked[y][x] and grid[y][x] not in ink:
                inked[y][x] = False

    # One colour of ink is spread over a dozen palette entries -- the same
    # purple, the same black, at a dozen opacities -- so entries are grouped
    # before anything is counted.  Left ungrouped, no single entry of an
    # outline carries enough of the box to be recognised as one.
    #
    # Grouped by their own RGB rather than by what they look like over the
    # plate: opacity is exactly what varies within one ink, so a black rim's
    # entries have to fall together however faint the faintest of them is.
    # Each group then stands for its strongest member, not its commonest: the
    # commonest entry of a rim is usually its faintest.  Strength is the
    # colour's own distance from the plate scaled by how much of it is actually
    # laid down, which picks the opaque black out of a black rim's ramp and the
    # brightest cream out of a cream fill's.
    clusters: list[list[int]] = []
    for index in sorted(ink, key=lambda i: -counts[i]):
        for group in clusters:
            if sum(abs(a - b) for a, b in zip(palette[index][:3],
                                              palette[group[0]][:3])) <= INK_SHADE:
                group.append(index)
                break
        else:
            clusters.append([index])
    def strength(index: int) -> float:
        colour = palette[index]
        apart = min(sum(abs(a - b) for a, b in zip(colour[:3], other[:3]))
                    for other in plate_colours)
        return apart * colour[3] / 255

    clusters = [sorted(group, key=lambda index: (-strength(index), -counts[index]))
                for group in clusters]

    edge: Counter = Counter()
    for y, row in enumerate(grid):
        for x, index in enumerate(row):
            if not inked[y][x]:
                continue
            if any(
                not inked[y + dy][x + dx]
                for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                if 0 <= y + dy < box.h and 0 <= x + dx < box.w
            ):
                edge[index] += 1

    def exposure(group: list[int]) -> float:
        """How much of a colour sits against the plate rather than other ink."""
        area = sum(counts[index] for index in group)
        return sum(edge[index] for index in group) / max(1, area)

    # An ink laid over another ink leaves a third colour between them, and at
    # this size that blend can cover more of the box than either of its
    # parents.  It is not a colour the label is drawn in, so it is dropped:
    # a colour that sits on the line between two others, and between them
    # rather than beyond either end, is what those two make where they meet.
    floor = max(4, sum(counts[index] for index in ink) * FLOOR_SHARE)
    sizeable = [group for group in clusters
                if sum(counts[index] for index in group) >= floor] or clusters

    def between(group: list[int]) -> bool:
        here = palette[group[0]][:3]
        ends = [palette[other[0]] for other in sizeable if other is not group]
        for one in ends:
            for other in ends:
                if one is other:
                    continue
                start = one[:3]
                span = [b - a for a, b in zip(start, other[:3])]
                size = sum(v * v for v in span)
                if not size:
                    continue
                along = sum((c - a) * v for c, a, v in zip(here, start, span)) / size
                if not MIXED < along < 1 - MIXED:
                    continue
                if sum(abs(c - (a + along * v))
                       for c, a, v in zip(here, start, span)) <= BLEND_SLACK:
                    return True
        return False

    sizeable = [group for group in sizeable if not between(group)] or sizeable

    # The fill is the colour at the heart of the lettering and the outline is
    # the colour ringing it.  Neither area nor contrast says which is which --
    # at this size a rim covers more than the fill it surrounds, and the rim is
    # darker than the fill on the rank plates but lighter than it on the system
    # menu -- so the question is answered by shape.  Every ink pixel is given
    # its distance from the plate, one for the pixels against it, two for the
    # ring inside those, and so on; the fill is then simply the colour lying
    # deepest on average.
    depth = [[0] * box.w for _ in range(box.h)]
    edge_first: deque = deque()
    for y in range(box.h):
        for x in range(box.w):
            if not inked[y][x]:
                continue
            if any(not (0 <= y + dy < box.h and 0 <= x + dx < box.w)
                   or not inked[y + dy][x + dx]
                   for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1))):
                depth[y][x] = 1
                edge_first.append((y, x))
    while edge_first:
        y, x = edge_first.popleft()
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < box.h and 0 <= nx < box.w and inked[ny][nx] and not depth[ny][nx]:
                depth[ny][nx] = depth[y][x] + 1
                edge_first.append((ny, nx))

    def sunk(group: list[int]) -> float:
        held = set(group)
        deep = [depth[y][x] for y in range(box.h) for x in range(box.w)
                if inked[y][x] and grid[y][x] in held]
        return sum(deep) / len(deep) if deep else 0.0

    body = max(sizeable, key=lambda group: (sunk(group),
                                            sum(counts[index] for index in group)))
    fill = body[0]

    middle = palette[plate[box.h // 2][0]]
    # Measured against the ink the label is actually drawn in.  On a plate that
    # dithers, its own shades come through as ink and shatter into a dozen
    # small colours; counted against all of those together, a real outline
    # never looks like a large enough share of anything to be one.
    total = sum(counts[index] for group in sizeable for index in group)
    # The outline is the other half of the same shape: of the colours the
    # label is really drawn in, the one that runs along the lettering's edges.
    # It has to carry a real share of the lettering to count as one.
    def another(group: list[int]) -> bool:
        """Is this a second ink, or the fill again a shade lighter?"""
        return sum(abs(a - b) for a, b in zip(palette[group[0]][:3],
                                              palette[fill][:3])) > INK_SHADE

    candidates = [group for group in sizeable
                  if group is not body and another(group)
                  and sum(counts[index] for index in group) >= total * OUTLINE_SHARE
                  and beyond(off_axis(middle, palette[fill], palette[group[0]]))]
    if not candidates:
        # On a plate that dithers, its own shades come through as ink and a
        # thin rim can end up looking like a mixture of two of them.  Where the
        # shape test has left nothing to ring the fill with, the rim is looked
        # for again among every colour in the box, by the older reading: the
        # ink that runs along the glyph's edges, off the line that the plate's
        # own anti-aliasing would lie on.
        candidates = [
            group for group in clusters
            if group is not body
            and another(group)
            and sum(counts[index] for index in group) >= total * OUTLINE_SHARE
            and beyond(off_axis(middle, palette[fill], palette[group[0]]))
            and (sum(edge[index] for index in group) >= total * OUTLINE_SHARE
                 or exposure(group) <= SHELTERED)
        ]
        rim = max(candidates, key=lambda g: sum(edge[i] for i in g))[0] if candidates else fill
    else:
        rim = max(candidates, key=lambda g: sum(edge[i] for i in g))[0]
    outlined = rim != fill
    # Under about thirteen pixels a glyph has ten to draw with, and a ring
    # around it eats two of them: the label comes out as a rim with a sliver of
    # fill inside.  Small lettering is drawn flat instead -- unless the rim is
    # the only thing separating it from its plate.  The system menu's buttons
    # are cream lettering on a cream plate, and drawn flat they disappear.
    outlined = outlined and (box.h >= SMALL_BOX
                             or distance(palette[fill], middle) < NEEDS_RIM)

    # A 16x8 block may hold at most 16 palette entries, so the anti-aliasing
    # ramp is capped: pick RAMP_LEVELS entries spread evenly between the plate
    # and the fill.
    target = palette[fill]
    ramp: list[int] = []
    for step in range(1, RAMP_LEVELS + 1):
        want = tuple(b + (t - b) * step / RAMP_LEVELS for b, t in zip(middle, target))
        pick = min(ink, key=lambda index: (
            sum(abs(a - c) for a, c in zip(palette[index], want)), -counts[index]))
        if pick not in ramp:
            ramp.append(pick)
    return {"plate": plate, "fill": fill, "outline": rim, "outlined": outlined,
            "ramp": ramp, "inked": inked}


def render_mask(text: str, box: Box, pad: int, max_size: int | None = None) -> Image.Image:
    """Largest rendering of ``text`` that fits ``box`` minus the outline pad."""
    inner_w = box.w - pad * 2
    inner_h = box.h - pad * 2
    face = (TTF if box.h >= SMALL_BOX
            else TTF_SMALL if box.h >= TINY_BOX else TTF_TINY)
    best = None
    for size in range(min(box.h + 2, max_size or box.h + 2), 5, -1):
        font = ImageFont.truetype(face, size)
        left, top, right, bottom = font.getbbox(text)
        if right - left <= inner_w and bottom - top <= inner_h:
            best = (font, left, top, right - left, bottom - top)
            break
    if best is None:
        font = ImageFont.truetype(face, 6)
        left, top, right, bottom = font.getbbox(text)
        best = (font, left, top, right - left, bottom - top)
    font, left, top, width, height = best

    glyphs = Image.new("L", (max(width, 1), max(height, 1)), 0)
    ImageDraw.Draw(glyphs).text((-left, -top), text, font=font, fill=255)
    if glyphs.width > inner_w or glyphs.height > inner_h:
        scale = min(inner_w / glyphs.width, inner_h / glyphs.height)
        glyphs = glyphs.resize(
            (max(int(glyphs.width * scale), 1), max(int(glyphs.height * scale), 1)),
            Image.Resampling.LANCZOS,
        )

    # The art these replace is a pixel face with hard edges, and a scalable
    # face at twelve or thirteen pixels is mostly edge: left as rendered, a
    # long label never reaches full coverage and comes out a shade of the plate
    # rather than the colour of the lettering.  Stretching the coverage puts a
    # solid core back and keeps a pixel of anti-aliasing around it -- but only
    # above ten pixels or so, below which a dense syllable's counters are one
    # pixel wide and the stretch fills them in, leaving a solid block.
    if box.h >= SMALL_BOX - 1:
        glyphs = glyphs.point(lambda value: min(255, max(0, (value - 30) * 255 // 140)))

    mask = Image.new("L", (box.w, box.h), 0)
    mask.paste(glyphs, ((box.w - glyphs.width) // 2, (box.h - glyphs.height) // 2))
    return mask


def erasure(image: itp.ItpImage, box: Box, style: dict) -> list[list[int]]:
    """What to put where the Japanese was, one palette index per pixel.

    Only the ink is cleared.  Everything else -- the plate's gradient, its
    dither, the frame of a button, the icon beside it -- keeps the byte it
    shipped with, which is the one erase that cannot leave a seam.  An ink
    pixel takes the nearest plate pixel along its own row, so a plate that
    shades across as well as down comes back smooth; a row that is ink from
    end to end falls back to the colour beside the box.

    Anti-aliasing between the lettering and the plate counts as plate here --
    it is too near the plate to be ink -- but it is never copied sideways,
    which would leave bars where the Japanese used to be.
    """
    inked = style["inked"]
    out: list[list[int]] = []
    for y in range(box.h):
        row = [image.pixels[(box.y + y) * image.width + box.x + x] for x in range(box.w)]
        left, right = style["plate"][y]

        def spreadable(x: int) -> bool:
            """May this pixel be copied sideways over the lettering?

            Any pixel that is not ink is the plate, and on a plate with a sheen
            in it -- the gold title bar, the ribbons -- copying the nearest one
            is what keeps that sheen.  Not the pixel beside a glyph, though:
            that one is half glyph, and smeared across the box it leaves a bar
            where the Japanese used to be.
            """
            if inked[y][x]:
                return False
            return not any(inked[y][x + step] for step in (-1, 1)
                           if 0 <= x + step < box.w)

        before: list[tuple[int, int] | None] = []
        seen: tuple[int, int] | None = None
        for x, index in enumerate(row):
            if spreadable(x):
                seen = (index, x)
            before.append(seen)
        after: list[tuple[int, int] | None] = [None] * box.w
        seen = None
        for x in range(box.w - 1, -1, -1):
            if spreadable(x):
                seen = (row[x], x)
            after[x] = seen
        line = []
        for x, index in enumerate(row):
            if not inked[y][x]:
                line.append(index)
                continue
            near = [side for side in (before[x], after[x]) if side is not None]
            if near:
                line.append(min(near, key=lambda side: abs(side[1] - x))[0])
            else:
                line.append(left if x * 2 < box.w else right)
        out.append(line)
    return out


def draw_label(image: itp.ItpImage, box: Box, text: str) -> None:
    style = analyse(image, box)
    plate = erasure(image, box, style)
    mask = render_mask(text, box, pad=1 if style["outlined"] else 0)
    data = mask.load()

    core = [[data[x, y] >= 128 for x in range(box.w)] for y in range(box.h)]
    halo: list[list[bool]] = [[False] * box.w for _ in range(box.h)]
    if style["outlined"]:
        for y in range(box.h):
            for x in range(box.w):
                if core[y][x]:
                    continue
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < box.h and 0 <= nx < box.w and core[ny][nx]:
                            halo[y][x] = True
                            break
                    if halo[y][x]:
                        break

    ramp = style["ramp"]
    for y in range(box.h):
        row = (box.y + y) * image.width + box.x
        for x in range(box.w):
            if style["outlined"]:
                if core[y][x]:
                    value = style["fill"]
                elif halo[y][x]:
                    value = style["outline"]
                else:
                    value = plate[y][x]
            else:
                coverage = data[x, y]
                if coverage < 20:
                    value = plate[y][x]
                else:
                    step = min(len(ramp) - 1, coverage * len(ramp) // 256)
                    value = ramp[step]
            image.pixels[row + x] = value


def patch_texture(
    source: bytes, labels: list[tuple[int, int, int, int, str]], scratch: Path,
) -> tuple[bytes, bytes, itp.ItpImage]:
    """Return (bytes padded to the ISO slot, exact bytes, the patched image)."""
    scratch.write_bytes(source)
    image = itp.load(scratch)
    for x, y, w, h, text in labels:
        draw_label(image, Box(x, y, w, h), text)
    rebuilt = itp.dump(image)
    if len(rebuilt) > len(source):
        raise ValueError(f"patched texture grew from {len(source)} to {len(rebuilt)} bytes")
    return rebuilt.ljust(len(source), b"\0"), rebuilt, image


def preview(before: itp.ItpImage, after: itp.ItpImage, labels, path: Path, scale: int = 4) -> None:
    def strip(image: itp.ItpImage, box: Box) -> Image.Image:
        rgba = bytearray()
        for y in range(box.y, box.bottom):
            for x in range(box.x, box.right):
                rgba.extend(image.palette[image.pixels[y * image.width + x]])
        tile = Image.frombytes("RGBA", (box.w, box.h), bytes(rgba))
        plate = Image.new("RGBA", tile.size, (40, 44, 60, 255))
        return Image.alpha_composite(plate, tile).convert("RGB")

    rows = []
    for x, y, w, h, _text in labels:
        box = Box(x, y, w, h)
        rows.append((strip(before, box), strip(after, box)))
    gap = 6
    width = max(a.width + b.width + gap for a, b in rows) + gap
    height = sum(max(a.height, b.height) + gap for a, b in rows) + gap
    sheet = Image.new("RGB", (width, height), (18, 18, 24))
    y = gap
    for a, b in rows:
        sheet.paste(a, (gap, y))
        sheet.paste(b, (gap + a.width + gap, y))
        y += max(a.height, b.height) + gap
    sheet.resize((sheet.width * scale, sheet.height * scale), Image.Resampling.NEAREST).save(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("itp_work/raw"))
    parser.add_argument("--out", type=Path, default=Path("itp_work/patched"))
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    scratch = args.out / "_scratch.itp"
    for name, labels in spec.PATCHES.items():
        source = (args.raw / f"{name}.itp").read_bytes()
        before = itp.load(args.raw / f"{name}.itp")
        padded, exact, after = patch_texture(source, labels, scratch)
        (args.out / f"{name}.itp").write_bytes(padded)
        scratch.write_bytes(exact)
        # The encoder folds rare colours together when a 16x8 block would need
        # more than 16 palette entries, so a handful of pixels may shift.
        reloaded = itp.load(scratch).pixels
        drift = sum(1 for a, b in zip(reloaded, after.pixels) if a != b)
        if drift > len(after.pixels) // 200:
            raise ValueError(f"{name}: {drift} pixels changed on re-encode, too many")
        preview(before, after, labels, args.out / f"{name}_preview.png")
        print(
            f"{name}: {len(labels)} labels, {len(exact)} bytes "
            f"(slot {len(source)}, zero padding {len(source) - len(exact)}, "
            f"{drift} pixels folded)"
        )
    scratch.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
