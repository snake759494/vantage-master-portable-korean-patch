"""Pick the font slots that carry Hangul and encode text into them.

The game finds a glyph with ``index = base + (sjis_code - start)`` over the
four Shift-JIS ranges in the ``pspfont.dat`` header, then reads a variable
width record.  A Hangul raster is therefore only visible if it is written to
the record of the very code the text stream contains -- the earlier builds
wrote fixed 64-byte tiles at a hard-coded raster offset instead, which is why
``저는`` came out as ``젯늠``.

Slots are taken from JIS level 2 first so that the common level-1 kanji keep
their Japanese glyphs in the text that is still untranslated.
"""

from __future__ import annotations

from pathlib import Path

from falcom_font import FalcomFont

KOREAN_COUNT = 2350
HANGUL_WIDTH = 15

# Only JIS level 2 and the IBM/NEC extension blocks: level-1 kanji keep their
# Japanese glyphs, so untranslated Japanese text stays readable.
SLOT_REGIONS: list[tuple[int, int]] = [
    (0x989F, 0x9FFC),  # level 2, first half
    (0xE040, 0xEAA4),  # level 2, second half
    (0xED40, 0xEEFC),  # NEC-selected IBM extended kanji
    (0xFA40, 0xFC4B),  # IBM extended kanji
]


def wansung_syllables() -> list[str]:
    """The 2,350 KS X 1001 Hangul syllables in EUC-KR byte order."""
    items: list[tuple[bytes, str]] = []
    for codepoint in range(0xAC00, 0xD7A4):
        char = chr(codepoint)
        try:
            encoded = char.encode("euc_kr")
        except UnicodeEncodeError:
            continue
        if len(encoded) == 2 and 0xB0 <= encoded[0] <= 0xC8 and 0xA1 <= encoded[1] <= 0xFE:
            items.append((encoded, char))
    items.sort(key=lambda item: item[0])
    if len(items) != KOREAN_COUNT:
        raise ValueError(f"expected {KOREAN_COUNT} Wansung syllables, got {len(items)}")
    return [char for _encoded, char in items]


def is_full_width_code(code: int) -> bool:
    try:
        decoded = bytes((code >> 8, code & 0xFF)).decode("cp932")
    except (UnicodeDecodeError, ValueError):
        return False
    return len(decoded) == 1


def candidate_codes(font: FalcomFont, width: int = HANGUL_WIDTH) -> list[int]:
    """Shift-JIS codes whose glyph record is exactly ``width`` pixels wide."""
    codes: list[int] = []
    for start, end in SLOT_REGIONS:
        for code in range(start, end + 1):
            if not is_full_width_code(code):
                continue
            index = font.index_of(code)
            if index is None or font.record(index).width != width:
                continue
            codes.append(code)
    return codes


def build_slot_map(font: FalcomFont) -> dict[str, int]:
    """Map each Wansung syllable to the Shift-JIS code that will carry it."""
    syllables = wansung_syllables()
    codes = candidate_codes(font)
    if len(codes) < len(syllables):
        raise ValueError(
            f"only {len(codes)} slots of width {HANGUL_WIDTH} are available for "
            f"{len(syllables)} syllables"
        )
    return dict(zip(syllables, codes[: len(syllables)]))


def make_encoder(slot_map: dict[str, int]):
    """Encode a translated string into the game's byte stream."""
    slots = {char: bytes((code >> 8, code & 0xFF)) for char, code in slot_map.items()}

    def encode(text: str) -> bytes:
        result = bytearray()
        for index, char in enumerate(text):
            if char in slots:
                result.extend(slots[char])
                continue
            try:
                result.extend(char.encode("cp932"))
            except UnicodeEncodeError as exc:
                raise UnicodeEncodeError(
                    "vmp-korean",
                    text,
                    index,
                    index + 1,
                    f"character {char!r} is neither Wansung Hangul nor CP932",
                ) from exc
        return bytes(result)

    return encode


def load_slot_map(font_path: Path = Path("pspfont.dat")) -> tuple[FalcomFont, dict[str, int]]:
    font = FalcomFont(font_path.read_bytes())
    return font, build_slot_map(font)
