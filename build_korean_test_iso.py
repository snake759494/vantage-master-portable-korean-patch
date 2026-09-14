"""Create a test ISO with the Korean pspfont.dat replacement in place."""

from __future__ import annotations

import argparse
import io
import shutil
from pathlib import Path

import pycdlib


ISO_FONT_PATH = "/PSP_GAME/USRDIR/system/pspfont.dat"


def replace_iso_file(input_iso: Path, output_iso: Path, replacement: bytes) -> None:
    input_resolved = input_iso.resolve()
    output_resolved = output_iso.resolve()
    if input_resolved == output_resolved:
        raise ValueError("refusing to modify the original ISO in place")
    if output_iso.exists():
        raise FileExistsError(f"output already exists: {output_iso}")

    shutil.copy2(input_iso, output_iso)
    try:
        with output_iso.open("r+b") as iso_fp:
            iso = pycdlib.PyCdlib()
            iso.open_fp(iso_fp)
            try:
                iso.modify_file_in_place(
                    io.BytesIO(replacement), len(replacement), iso_path=ISO_FONT_PATH
                )
            finally:
                iso.close()
            iso_fp.flush()
    except Exception:
        # Keep a failed build from looking like a valid test image.
        output_iso.unlink(missing_ok=True)
        raise


def read_iso_file(iso_path: Path) -> bytes:
    with iso_path.open("rb") as iso_fp:
        iso = pycdlib.PyCdlib()
        iso.open_fp(iso_fp)
        try:
            with iso.open_file_from_iso(iso_path=ISO_FONT_PATH) as file_fp:
                return file_fp.read()
        finally:
            iso.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("Vantage Master Portable (1.01).iso"),
    )
    parser.add_argument(
        "--replacement",
        type=Path,
        default=Path("korean_font_test/pspfont_korean_2350_test.dat"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("Vantage Master Portable (Korean font test).iso"),
    )
    args = parser.parse_args()

    original_font = read_iso_file(args.input)
    replacement = args.replacement.read_bytes()
    if len(original_font) != len(replacement):
        raise ValueError(
            f"replacement size {len(replacement)} differs from ISO font size {len(original_font)}"
        )

    replace_iso_file(args.input, args.output, replacement)
    verified = read_iso_file(args.output)
    if verified != replacement:
        raise ValueError("ISO verification failed: embedded pspfont.dat differs")

    print(f"Built: {args.output}")
    print(f"Embedded file: {ISO_FONT_PATH}")
    print(f"Verified bytes: {len(verified)}")


if __name__ == "__main__":
    main()
