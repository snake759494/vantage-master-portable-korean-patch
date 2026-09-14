"""Build a same-size ISO with both pspfont copies patched."""

from __future__ import annotations

import argparse
import io
import shutil
from pathlib import Path

import pycdlib


LOOSE_ISO_PATH = "/PSP_GAME/USRDIR/system/pspfont.dat"
PACK_ISO_PATH = "/PSP_GAME/USRDIR/data/pack/init0.dat"


def read_iso_file(iso_path: Path, iso_file: str) -> bytes:
    with iso_path.open("rb") as iso_fp:
        iso = pycdlib.PyCdlib()
        iso.open_fp(iso_fp)
        try:
            with iso.open_file_from_iso(iso_path=iso_file) as file_fp:
                return file_fp.read()
        finally:
            iso.close()


def replace_files_in_place(input_iso: Path, output_iso: Path, replacements: dict[str, bytes]) -> None:
    if input_iso.resolve() == output_iso.resolve():
        raise ValueError("refusing to modify the original ISO in place")
    if output_iso.exists():
        raise FileExistsError(f"output already exists: {output_iso}")

    shutil.copy2(input_iso, output_iso)
    try:
        with output_iso.open("r+b") as iso_fp:
            iso = pycdlib.PyCdlib()
            iso.open_fp(iso_fp)
            try:
                for iso_file, replacement in replacements.items():
                    with iso.open_file_from_iso(iso_path=iso_file) as file_fp:
                        original = file_fp.read()
                    if len(original) != len(replacement):
                        raise ValueError(
                            f"{iso_file}: replacement size {len(replacement)} "
                            f"does not match original size {len(original)}"
                        )
                    iso.modify_file_in_place(
                        io.BytesIO(replacement), len(replacement), iso_path=iso_file
                    )
            finally:
                iso.close()
            iso_fp.flush()
    except Exception:
        output_iso.unlink(missing_ok=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, default=Path("Vantage Master Portable (1.01).iso")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("Vantage Master Portable (Korean packed font test).iso"),
    )
    parser.add_argument(
        "--replacement",
        type=Path,
        default=Path("korean_font_test/pspfont_korean_2350_test.dat"),
        help="replacement loose pspfont.dat",
    )
    parser.add_argument(
        "--packed-replacement",
        type=Path,
        default=Path("packed_font_test/init0_korean.dat"),
        help="replacement packed init0.dat",
    )
    args = parser.parse_args()

    replacements = {
        LOOSE_ISO_PATH: args.replacement.read_bytes(),
        PACK_ISO_PATH: args.packed_replacement.read_bytes(),
    }
    replace_files_in_place(args.input, args.output, replacements)

    for iso_file, expected in replacements.items():
        actual = read_iso_file(args.output, iso_file)
        if actual != expected:
            raise ValueError(f"verification failed for {iso_file}")
        print(f"Verified {iso_file}: {len(actual)} bytes")
    print(f"Built: {args.output} ({args.output.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
