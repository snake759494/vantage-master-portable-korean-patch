"""Build the Korean dialogue candidate with the preserved font and fixed maps.

The Korean glyph raster is intentionally taken byte-for-byte from the previously
verified CN-base font candidate.  This script changes only the text resources,
the two in-game JIS/Unicode mapping tables, and the two font resource copies
needed to carry that already-built font into a fresh ISO.
"""

from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path

from patch_dialogue_text import (
    BATTLE_CONFIRM_FIELDS,
    BOOT_PATH,
    EBOOT_PATH,
    EVENT_FILES,
    ITEM_DESCRIPTION_FIELDS,
    KANJI_MAP_PATH,
    STATIC_FIELDS,
    make_custom_encoder,
    patch_event_fields,
    patch_static_fields,
    read_iso_file,
    replace_files_in_place,
)
from apply_korean_font_test import load_kanji_map, wansung_syllables
from patch_packed_pspfont import (
    PACK_PSPFONT_RECORD,
    ed7_decompress,
    parse_pack_record,
)


LOOSE_FONT_PATH = "/PSP_GAME/USRDIR/system/pspfont.dat"
PACK_FONT_PATH = "/PSP_GAME/USRDIR/data/pack/init0.dat"
JIS2UTF_PATH = "/PSP_GAME/USRDIR/system/jis2utf.bin"
UTF2JIS_PATH = "/PSP_GAME/USRDIR/system/utf2jis.bin"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch_mapping_tables(
    jis2utf: bytes,
    utf2jis: bytes,
    kanji_map_path: Path,
) -> tuple[bytes, bytes, list[tuple[int, int, str]]]:
    """Assign the first 2,350 JIS slots to the Wansung syllable order."""

    if len(jis2utf) != 0x20000 or len(utf2jis) != 0x20000:
        raise ValueError("the game mapping tables must each contain 65,536 uint16 entries")

    korean = wansung_syllables()
    map_rows = load_kanji_map(kanji_map_path)
    if len(map_rows) < len(korean):
        raise ValueError("the Japanese JIS map has fewer slots than Wansung Hangul")

    patched_jis2utf = bytearray(jis2utf)
    patched_utf2jis = bytearray(utf2jis)
    samples: list[tuple[int, int, str]] = []

    for index, ((_euc_kr, korean_char), row) in enumerate(
        zip(korean, map_rows[: len(korean)])
    ):
        jis_code = int(row["jis_code"], 16)
        unicode_value = ord(korean_char)
        struct.pack_into("<H", patched_jis2utf, jis_code * 2, unicode_value)
        struct.pack_into("<H", patched_utf2jis, unicode_value * 2, jis_code)
        if index in (0, 1, 409, 963, 2349):
            samples.append((jis_code, unicode_value, korean_char))

    # Check the modified associations before the ISO is touched.
    for jis_code, unicode_value in (
        (int(row["jis_code"], 16), ord(korean_char))
        for ((_euc_kr, korean_char), row) in zip(
            korean, map_rows[: len(korean)]
        )
    ):
        actual_unicode = struct.unpack_from("<H", patched_jis2utf, jis_code * 2)[0]
        actual_jis = struct.unpack_from("<H", patched_utf2jis, unicode_value * 2)[0]
        if actual_unicode != unicode_value or actual_jis != jis_code:
            raise ValueError(f"mapping round-trip failed for JIS 0x{jis_code:04X}")

    return bytes(patched_jis2utf), bytes(patched_utf2jis), samples


def verify_preserved_font(
    input_iso: Path,
    loose_font: bytes,
    packed_font: bytes,
) -> tuple[bytes, str]:
    """Verify the supplied packed copy decompresses to the supplied loose copy."""

    original_loose = read_iso_file(input_iso, LOOSE_FONT_PATH)
    original_pack = read_iso_file(input_iso, PACK_FONT_PATH)
    if len(loose_font) != len(original_loose):
        raise ValueError(
            f"loose font size {len(loose_font)} differs from ISO size {len(original_loose)}"
        )
    if len(packed_font) != len(original_pack):
        raise ValueError(
            f"packed font size {len(packed_font)} differs from ISO size {len(original_pack)}"
        )

    name, data_offset, compressed_size, _uncompressed_size, _flags = parse_pack_record(
        packed_font, PACK_PSPFONT_RECORD
    )
    if name != "pspfont.dat":
        raise ValueError(f"packed font record has unexpected name: {name!r}")
    recovered = ed7_decompress(packed_font[data_offset : data_offset + compressed_size])
    if recovered != loose_font:
        raise ValueError("the supplied packed font does not decompress to the supplied loose font")

    return original_loose, sha256(recovered)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, default=Path("Vantage Master Portable (1.01).iso")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("Vantage Master Portable (Korean dialogue mapping fixed).iso"),
    )
    parser.add_argument(
        "--font",
        type=Path,
        default=Path("korean_font_cn_base_test/pspfont_korean_2350_test.dat"),
    )
    parser.add_argument(
        "--packed-font",
        type=Path,
        default=Path("packed_font_cn_base_test/init0_korean.dat"),
    )
    parser.add_argument("--kanji-map", type=Path, default=KANJI_MAP_PATH)
    parser.add_argument(
        "--report-dir", type=Path, default=Path("text_patch_dialogue_mapping_fixed")
    )
    args = parser.parse_args()

    loose_font = args.font.read_bytes()
    packed_font = args.packed_font.read_bytes()
    original_loose, preserved_font_hash = verify_preserved_font(
        args.input, loose_font, packed_font
    )

    encode = make_custom_encoder(args.kanji_map)
    boot_original = read_iso_file(args.input, BOOT_PATH)
    eboot_original = read_iso_file(args.input, EBOOT_PATH)
    patched_boot, static_report = patch_static_fields(boot_original, encode)
    if len(eboot_original) < len(patched_boot):
        raise ValueError("input EBOOT.BIN is smaller than the patched ELF")
    patched_eboot = patched_boot.ljust(len(eboot_original), b"\0")

    replacements: dict[str, bytes] = {
        BOOT_PATH: patched_boot,
        EBOOT_PATH: patched_eboot,
        LOOSE_FONT_PATH: loose_font,
        PACK_FONT_PATH: packed_font,
    }

    event_report: list[str] = []
    for iso_file, specs in EVENT_FILES:
        original = read_iso_file(args.input, iso_file)
        patched, lines = patch_event_fields(original, specs, encode)
        replacements[iso_file] = patched
        event_report.extend([f"{iso_file}: {line}" for line in lines])

    original_jis2utf = read_iso_file(args.input, JIS2UTF_PATH)
    original_utf2jis = read_iso_file(args.input, UTF2JIS_PATH)
    patched_jis2utf, patched_utf2jis, mapping_samples = patch_mapping_tables(
        original_jis2utf, original_utf2jis, args.kanji_map
    )
    replacements[JIS2UTF_PATH] = patched_jis2utf
    replacements[UTF2JIS_PATH] = patched_utf2jis

    args.report_dir.mkdir(parents=True, exist_ok=True)
    (args.report_dir / "BOOT.BIN.patched").write_bytes(patched_boot)
    (args.report_dir / "EBOOT.BIN.patched").write_bytes(patched_eboot)
    (args.report_dir / "jis2utf.bin.patched").write_bytes(patched_jis2utf)
    (args.report_dir / "utf2jis.bin.patched").write_bytes(patched_utf2jis)
    (args.report_dir / "dialogue_patch_report.txt").write_text(
        "Korean dialogue patch with mapping-table fix\n"
        "=============================================\n"
        "Font: preserved byte-for-byte from the verified CN-base Korean candidate\n"
        f"Loose font SHA-256: {sha256(loose_font)}\n"
        f"Packed-font SHA-256: {sha256(packed_font)}\n"
        f"Decompressed packed-font SHA-256: {preserved_font_hash}\n"
        f"Previous original loose-font SHA-256: {sha256(original_loose)}\n"
        "Hangul: 2,350 KS X 1001/Wansung syllables\n"
        "Text encoding: custom Shift-JIS bytes pointing at the first 2,350 JIS slots\n"
        "Mapping resources: jis2utf.bin and utf2jis.bin patched as inverse JIS/Unicode tables\n"
        "Font glyph rasters were not regenerated by this build.\n"
        "Field padding: ASCII spaces; original NUL terminators and field offsets retained\n\n"
        + "Mapping samples\n----------------\n"
        + "\n".join(
            f"JIS 0x{jis:04X} <-> U+{unicode_value:04X} {char}"
            for jis, unicode_value, char in mapping_samples
        )
        + "\n\nStatic fields\n-------------\n"
        + "\n".join(static_report)
        + "\n\nEvent fields\n------------\n"
        + "\n".join(event_report)
        + "\n",
        encoding="utf-8",
    )

    replace_files_in_place(args.input, args.output, replacements)

    for iso_file, expected in replacements.items():
        actual = read_iso_file(args.output, iso_file)
        if actual != expected:
            raise ValueError(f"verification failed for {iso_file}")

    print(f"Built: {args.output} ({args.output.stat().st_size} bytes)")
    print(f"Patched ISO files: {len(replacements)}")
    print(f"Preserved loose font: {sha256(loose_font)}")
    print(f"Patched map hashes: {sha256(patched_jis2utf)} {sha256(patched_utf2jis)}")
    print(f"Report: {args.report_dir / 'dialogue_patch_report.txt'}")


if __name__ == "__main__":
    main()
