"""Survey a texture: list the ink boxes in a region and render them readably."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageOps

import falcom_itp as itp
from itp_text import Box, alpha_of


def ink_boxes(image: itp.ItpImage, region: Box, threshold: int, row_gap: int, col_gap: int) -> list[Box]:
    alpha = [alpha_of(image, index) for index in image.pixels]

    def lit(x: int, y: int) -> bool:
        return alpha[y * image.width + x] > threshold

    bands: list[tuple[int, int]] = []
    start = None
    blank = 0
    for y in range(region.y, region.bottom):
        if any(lit(x, y) for x in range(region.x, region.right)):
            if start is None:
                start = y
            blank = 0
        elif start is not None:
            blank += 1
            if blank > row_gap:
                bands.append((start, y - blank))
                start = None
    if start is not None:
        bands.append((start, region.bottom - 1))

    boxes: list[Box] = []
    for top, bottom in bands:
        run = None
        gap = 0
        for x in range(region.x, region.right):
            if any(lit(x, y) for y in range(top, bottom + 1)):
                if run is None:
                    run = x
                gap = 0
            elif run is not None:
                gap += 1
                if gap > col_gap:
                    boxes.append(Box(run, top, x - gap - run + 1, bottom - top + 1))
                    run = None
        if run is not None:
            boxes.append(Box(run, top, region.right - run, bottom - top + 1))
    return boxes


def contact_sheet(image: itp.ItpImage, boxes: list[Box], scale: int, path: Path) -> None:
    alpha = bytes(alpha_of(image, index) for index in image.pixels)
    plane = Image.frombytes("L", (image.width, image.height), alpha)
    tiles = [
        ImageOps.autocontrast(plane.crop((b.x, b.y, b.right, b.bottom))) for b in boxes
    ]
    width = max((t.width for t in tiles), default=1)
    height = sum(t.height + 4 for t in tiles) or 1
    sheet = Image.new("L", (width, height), 110)
    y = 0
    for tile in tiles:
        sheet.paste(tile, (0, y))
        y += tile.height + 4
    sheet.resize((sheet.width * scale, sheet.height * scale), Image.Resampling.NEAREST).save(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name")
    parser.add_argument("--x", type=int, default=0)
    parser.add_argument("--y", type=int, default=0)
    parser.add_argument("--w", type=int, default=0)
    parser.add_argument("--h", type=int, default=0)
    parser.add_argument("--threshold", type=int, default=20)
    parser.add_argument("--row-gap", type=int, default=1)
    parser.add_argument("--col-gap", type=int, default=10)
    parser.add_argument("--scale", type=int, default=5)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    image = itp.load(Path("itp_work/raw", args.name + ".itp"))
    region = Box(args.x, args.y, args.w or image.width - args.x, args.h or image.height - args.y)
    boxes = ink_boxes(image, region, args.threshold, args.row_gap, args.col_gap)
    for index, box in enumerate(boxes):
        print(f"{index:3d}: x={box.x:3d} y={box.y:3d} w={box.w:3d} h={box.h:2d}")
    out = args.out or Path("itp_work/read", f"{args.name}_survey.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    contact_sheet(image, boxes, args.scale, out)
    print(f"{len(boxes)} boxes -> {out}")


if __name__ == "__main__":
    main()
