"""Patch the early dialogue-box text with the Korean font's custom SJIS slots.

The Japanese PSP executable stores these strings in fixed-size CP932 fields.
Hangul syllables are encoded to the custom Shift-JIS positions whose glyphs
were replaced in the Korean pspfont.dat.  Each field keeps its original size,
terminating NUL, and file offset so the executable layout is unchanged.
"""

from __future__ import annotations

import argparse
import io
import shutil
from pathlib import Path

import pycdlib

from apply_korean_font_test import load_kanji_map, wansung_syllables


BOOT_PATH = "/PSP_GAME/SYSDIR/BOOT.BIN"
EBOOT_PATH = "/PSP_GAME/SYSDIR/EBOOT.BIN"
KANJI_MAP_PATH = Path("font_extraction/japanese_kanji_map.csv")


# The strings below are the fields shown in the user's opening screenshots.
# Offsets are in the decrypted ELF stored as BOOT.BIN and by the Chinese
# reference EBOOT.BIN.  The source text is checked before every replacement.
STATIC_FIELDS: list[tuple[str, int, str, str]] = [
    (
        "card Shade",
        0x163DC0,
        "あなたが選んだのは Shade のカード。\n影、闇、邪なものを意味します。",
        "당신이 고른 것은 Shade 카드.\n그늘과 어둠, 사악함을 뜻합니다.",
    ),
    (
        "card Emblem",
        0x163E54,
        "あなたが選んだのは Emblem のカード。\n名誉、力、忠誠、戦闘を意味します。",
        "당신이 고른 것은 Emblem 카드.\n명예, 힘, 충성, 전투를 뜻합니다.",
    ),
    (
        "card Karma",
        0x163F20,
        "あなたが選んだのは Karma のカード。\n現実、運命を意味します。",
        "당신이 고른 것은 Karma 카드.\n현실과 운명을 뜻합니다.",
    ),
    (
        "card Ego",
        0x163FE8,
        "あなたが選んだのは Ego のカード。\n自我、自己顕示を意味します。",
        "당신이 고른 것은 Ego 카드.\n자아와 자기 과시를 뜻합니다.",
    ),
    (
        "Beast class description",
        0x163980,
        "あなたは幻夢を知らしめる力。\nビーストとしてこの世界に導かれました。",
        "당신은 환몽을 알릴 힘을 지닌\n비스트로서 이 세계에 이끌려 왔습니다.",
    ),
    (
        "Mellett introduction",
        0x164028,
        "私は《紫のメルレット》。\nネイティアルマスターと呼ばれる存在です。",
        "저는 《보랏빛 멜렛》입니다.\n네이티얼 마스터라고 불리는 존재죠.",
    ),
    (
        "question",
        0x16406C,
        "……さて、先ほどの\n質問の答えは決まりましたか？",
        "……그럼, 아까 했던\n질문의 답은 정했나요?",
    ),
    (
        "wish",
        0x16409C,
        "そう、強くなりたい、というのですね。\nあなたのその望み、\nお受けいたしましょう。",
        "그래, 강해지고 싶다는 거군요.\n그 소망,\n받아들이도록 하죠.",
    ),
    (
        "ask about player",
        0x1640EC,
        "まず、\nあなたの事をお聞かせください。",
        "먼저,\n당신에 대해 말씀해 주세요.",
    ),
    (
        "understood",
        0x164114,
        "あなたの事は、大体分かりました。",
        "당신에 대해서는 대략 알겠습니다.",
    ),
    (
        "Beast stats",
        0x162FD8,
        "あなたは攻撃力、魔力と移動力に優れます。\n魔法防御が低いことが欠点ですが\nマスターとしての素質は十分です。",
        "당신은 공격력과 마력, 이동력이 뛰어납니다.\n마법 방어력은 낮지만,\n마스터의 자질은 충분합니다.",
    ),
    (
        "grant four Neatials",
        0x16414C,
        "それでは基本となる、\n４種のネイティアルを\nあなたに授けましょう。",
        "그럼 기본이 되는,\n네 종류의 네이티얼을\n당신에게 주도록 하죠.",
    ),
    (
        "go",
        0x164190,
        "さあ、参りましょうか。\n強くなるために。",
        "자, 가 볼까요.\n강해지기 위해서.",
    ),
    (
        "Koma item",
        0x1642B0,
        "【傀儡の独楽】を手に入れた。\n操り人形の形をしたコマ。",
        "【꼭두각시 팽이】를 손에 넣었다.\n인형 모양의 팽이.",
    ),
    (
        "Koma description",
        0x1642E8,
        "絶妙な均衡を保ちながら回転する様は、\n見る者に安らぎを与える。\n地のネイティアル、パ・ランセルを召喚できる。",
        "절묘한 균형으로 도는 팽이는\n보는 이에게 평온함을 준다.\n땅의 네이티얼, 파・란셀을 소환할 수 있다.",
    ),
    (
        "bottle item",
        0x164354,
        "【瓶入りの船】を手に入れた。\nいかにして入れたのかは不明だが、\n精巧な船の模型が入っている小瓶の置物。",
        "【병 속의 배】를 손에 넣었다.\n어떻게 넣었는지는 알 수 없지만,\n정교한 배 모형이 든 작은 병 장식품.",
    ),
    (
        "bottle description",
        0x1643BC,
        "どのように置いても中の小さな船は沈むことなく、\n常に安定して浮いているという。\n水のネイティアル、レキューを召喚できる。",
        "어떻게 놓아도 안의 작은 배는 가라앉지 않고,\n항상 안정적으로 떠 있다고 한다.\n물의 네이티얼, 레큐를 소환할 수 있다.",
    ),
    (
        "hammer item",
        0x164434,
        "【赤銅の大槌】を手に入れた。\n神話の時代に鍛えられたと言われる赤銅の大槌。",
        "【적동 대망치】를 얻었다.\n신화 시대의 적동 대망치.",
    ),
    (
        "hammer description",
        0x164480,
        "鍛冶の神の力が込められており、\n振るうと鉄をも熔かす高熱を発するという。\n火のネイティアル、ヘピタスを召喚できる。",
        "대장장이 신의 힘이 깃들어,\n휘두르면 쇠도 녹일 고열을 낸다고 한다.\n불의 네이티얼, 헤피타스를 소환할 수 있다.",
    ),
    (
        "sakaki staff item",
        0x1644F4,
        "【榊木の笏杖】を手に入れた。\n神事を行う時に用いる杖。",
        "【사카키 지팡이】를 얻었다.\n신사용 지팡이.",
    ),
    (
        "sakaki staff description",
        0x16452C,
        "本来は魔を払うために使われていたもので、\n振るうと天の使いが現れるといわれている。\n天のネイティアル、ギュネ・フォスを召喚できる。",
        "원래는 마를 물리치는 데 쓰였으며,\n휘두르면 하늘의 사자가 나타난다고 한다.\n하늘의 네이티얼, 규네・포스를 소환할 수 있다.",
    ),
    (
        "class prompt",
        0x1645F4,
        "クラスを選択してください。",
        "클래스를 선택하세요.",
    ),
    (
        "master confirmation",
        0x1646BC,
        "このマスターでよろしいですか？",
        "이 마스터로 괜찮겠습니까?",
    ),
    (
        "movement tutorial",
        0x15E1FC,
        "移動可能な範囲を表示しています。\n目標地点を選んでください。",
        "이동 범위를 표시하고 있습니다.\n목표 지점을 선택하세요.",
    ),
    (
        "wait tutorial",
        0x15ED08,
        "待機して、行動を終了します。",
        "대기하여 행동을 종료합니다.",
    ),
]


BATTLE_CONFIRM_FIELDS: list[tuple[str, int, str, str]] = [
    (
        "battle confirmation",
        0x164D04,
        "戦闘を開始します。よろしいですか？",
        "전투를 시작합니다. 괜찮겠습니까?",
    ),
    (
        "battle confirmation duplicate",
        0x16D090,
        "戦闘を開始します。よろしいですか？",
        "전투를 시작합니다. 괜찮겠습니까?",
    ),
]


# Item-description fields also appear in the item/status screens.  They are
# not needed for the first frame of each item, but patching them prevents the
# same item from switching back to Japanese in the next description screen.
ITEM_DESCRIPTION_FIELDS: list[tuple[str, int, str, str]] = [
    (
        "Koma item/status description",
        0x16664C,
        "操り人形の形をしたコマ。\n絶妙な均衡を保ちながら回転する様は、\n見る者に安らぎを与える。\n地のネイティアル、パ・ランセルを召喚できる。",
        "인형 모양의 팽이.\n절묘한 균형으로 도는 팽이는\n보는 이에게 평온함을 준다.\n땅의 네이티얼, 파・란셀을 소환할 수 있다.",
    ),
    (
        "bottle item/status description",
        0x166ABC,
        "いかにして入れたのかは不明だが、\n精巧な船の模型が入っている小瓶の置物。\nどのように置いても中の小さな船は沈むことなく、\n常に安定して浮いているという。\n水のネイティアル、レキューを召喚できる。",
        "어떻게 넣었는지는 알 수 없지만,\n정교한 배 모형이 든 작은 병 장식품.\n어떻게 놓아도 안의 작은 배는 가라앉지 않고,\n항상 안정적으로 떠 있다고 한다.\n물의 네이티얼, 레큐를 소환할 수 있다.",
    ),
    (
        "hammer item/status description",
        0x166FA0,
        "神話の時代に鍛えられたと言われる赤銅の大槌。\n鍛冶の神の力が込められており、\n振るうと鉄をも熔かす高熱を発するという。\n火のネイティアル、ヘピタスを召喚できる。",
        "신화 시대의 적동 대망치.\n대장장이 신의 힘이 깃들어,\n휘두르면 쇠도 녹일 고열을 낸다고 한다.\n불의 네이티얼, 헤피타스를 소환할 수 있다.",
    ),
    (
        "sakaki staff item/status description",
        0x167628,
        "神事を行う時に用いる杖。\n本来は魔を払うために使われていたもので、\n振るうと天の使いが現れるといわれている。\n天のネイティアル、ギュネ・フォスを召喚できる。",
        "신사를 지낼 때 쓰는 지팡이.\n원래는 마를 물리치는 데 쓰였으며,\n휘두르면 하늘의 사자가 나타난다고 한다.\n하늘의 네이티얼, 규네・포스를 소환할 수 있다.",
    ),
]


EVENT_FILES: list[tuple[str, list[tuple[str, str]]]] = [
    (
        "/PSP_GAME/USRDIR/data/event/_asm/ev00219._as",
        [
            ("私は《紫のメルレット》。", "저는 멜렛입니다."),
            ("ネイティアルマスターと呼ばれる存在です。", "네이티얼 마스터입니다."),
        ],
    ),
    (
        "/PSP_GAME/USRDIR/data/pack/ev00219.dat",
        [
            ("私は《紫のメルレット》。", "저는 멜렛입니다."),
            ("ネイティアルマスターと呼ばれる存在です。", "네이티얼 마스터입니다."),
        ],
    ),
    (
        "/PSP_GAME/USRDIR/data/event/_asm/ev00125._as",
        [
            ("私は《紫のメルレット》。", "저는 멜렛입니다."),
            ("ネイティアルマスターと呼ばれる存在です。", "네이티얼 마스터입니다."),
        ],
    ),
    (
        "/PSP_GAME/USRDIR/data/pack/ev00125.dat",
        [
            ("私は《紫のメルレット》。", "저는 멜렛입니다."),
            ("ネイティアルマスターと呼ばれる存在です。", "네이티얼 마스터입니다."),
        ],
    ),
    (
        "/PSP_GAME/USRDIR/data/event/_asm/ev00521._as",
        [("ふふ、私は《紫のメルレット》。", "후후, 저는 멜렛입니다.")],
    ),
    (
        "/PSP_GAME/USRDIR/data/pack/ev00521.dat",
        [("ふふ、私は《紫のメルレット》。", "후후, 저는 멜렛입니다.")],
    ),
]


def read_iso_file(iso_path: Path, iso_file: str) -> bytes:
    with iso_path.open("rb") as iso_fp:
        iso = pycdlib.PyCdlib()
        iso.open_fp(iso_fp)
        try:
            with iso.open_file_from_iso(iso_path=iso_file) as file_fp:
                return file_fp.read()
        finally:
            iso.close()


def make_custom_encoder(kanji_map_path: Path):
    korean = wansung_syllables()
    map_rows = load_kanji_map(kanji_map_path)
    if len(map_rows) < len(korean):
        raise ValueError("the Japanese JIS map has fewer slots than Wansung Hangul")

    def jis_to_sjis(jis_code: int) -> bytes:
        jis_high = (jis_code >> 8) - 0x21
        jis_low = jis_code & 0xFF
        jis_low += 0x7E if jis_high & 1 else 0x1F
        if 0x7F <= jis_low <= 0x9D:
            jis_low += 1
        sjis_high = (jis_high >> 1) + (0x81 if (jis_high >> 1) <= 0x1E else 0xC1)
        return bytes((sjis_high, jis_low))

    slots = {
        korean_char: jis_to_sjis(int(row["jis_code"], 16))
        for (_euc_kr, korean_char), row in zip(korean, map_rows)
    }

    def encode(text: str) -> bytes:
        result = bytearray()
        for index, char in enumerate(text):
            if char in slots:
                result.extend(slots[char])
            else:
                try:
                    result.extend(char.encode("cp932"))
                except UnicodeEncodeError as exc:
                    raise UnicodeEncodeError(
                        "custom-psp-sjis",
                        text,
                        index,
                        index + 1,
                        f"character {char!r} is neither Wansung Hangul nor CP932",
                    ) from exc
        return bytes(result)

    return encode


def patch_fixed_field(
    data: bytearray,
    offset: int,
    source: str,
    target: str,
    encode,
) -> tuple[int, int]:
    source_bytes = source.encode("cp932")
    if data[offset : offset + len(source_bytes)] != source_bytes:
        actual = data[offset : offset + len(source_bytes)].hex(" ")
        raise ValueError(
            f"source mismatch at 0x{offset:X}: expected {source!r}; bytes={actual}"
        )
    terminator = data.find(0, offset)
    if terminator < 0:
        raise ValueError(f"no NUL terminator after field at 0x{offset:X}")
    capacity = terminator - offset
    target_bytes = encode(target)
    if len(target_bytes) > capacity:
        raise ValueError(
            f"translation too long at 0x{offset:X}: {len(target_bytes)} > {capacity} bytes"
        )
    data[offset:terminator] = target_bytes.ljust(capacity, b" ")
    return capacity, len(target_bytes)


def patch_static_fields(data: bytes, encode) -> tuple[bytes, list[str]]:
    result = bytearray(data)
    report: list[str] = []
    for label, offset, source, target in STATIC_FIELDS + BATTLE_CONFIRM_FIELDS + ITEM_DESCRIPTION_FIELDS:
        capacity, new_length = patch_fixed_field(result, offset, source, target, encode)
        report.append(
            f"{label}: 0x{offset:X}, {capacity} bytes -> {new_length} bytes; {target}"
        )
    return bytes(result), report


def patch_event_fields(data: bytes, specs: list[tuple[str, str]], encode) -> tuple[bytes, list[str]]:
    result = bytearray(data)
    report: list[str] = []
    for source, target in specs:
        source_bytes = source.encode("cp932")
        search_from = 0
        matches = 0
        while True:
            offset = result.find(source_bytes, search_from)
            if offset < 0:
                break
            if offset > 0 and result[offset - 1] != 0:
                search_from = offset + 1
                continue
            terminator = result.find(0, offset)
            if terminator != offset + len(source_bytes):
                search_from = offset + 1
                continue
            capacity = terminator - offset
            target_bytes = encode(target)
            if len(target_bytes) > capacity:
                raise ValueError(
                    f"event translation too long for {source!r}: "
                    f"{len(target_bytes)} > {capacity} bytes"
                )
            result[offset:terminator] = target_bytes.ljust(capacity, b" ")
            matches += 1
            report.append(f"0x{offset:X}: {source} -> {target}")
            search_from = terminator + 1
        if matches == 0:
            raise ValueError(f"event source field not found: {source!r}")
    return bytes(result), report


def replace_files_in_place(
    input_iso: Path, output_iso: Path, replacements: dict[str, bytes]
) -> None:
    if input_iso.resolve() == output_iso.resolve():
        raise ValueError("refusing to modify the input ISO in place")
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
        "--input",
        type=Path,
        default=Path("Vantage Master Portable (Korean CN base packed test).iso"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("Vantage Master Portable (Korean dialogue packed test).iso"),
    )
    parser.add_argument("--report-dir", type=Path, default=Path("text_patch_dialogue_test"))
    parser.add_argument("--kanji-map", type=Path, default=KANJI_MAP_PATH)
    args = parser.parse_args()

    encode = make_custom_encoder(args.kanji_map)
    boot_original = read_iso_file(args.input, BOOT_PATH)
    eboot_original = read_iso_file(args.input, EBOOT_PATH)
    patched_boot, report = patch_static_fields(boot_original, encode)

    # The Japanese retail EBOOT is encrypted and 344 bytes larger than the
    # decrypted ELF.  The Chinese reference image confirms PPSSPP accepts the
    # decrypted ELF in EBOOT.BIN; preserve the ISO directory size by padding
    # only the unused tail.  BOOT.BIN remains the exact ELF size.
    if len(eboot_original) < len(patched_boot):
        raise ValueError("input EBOOT.BIN is smaller than the patched ELF")
    patched_eboot = patched_boot.ljust(len(eboot_original), b"\0")

    replacements: dict[str, bytes] = {
        BOOT_PATH: patched_boot,
        EBOOT_PATH: patched_eboot,
    }
    event_report: list[str] = []
    for iso_file, specs in EVENT_FILES:
        original = read_iso_file(args.input, iso_file)
        patched, lines = patch_event_fields(original, specs, encode)
        replacements[iso_file] = patched
        event_report.extend([f"{iso_file}: {line}" for line in lines])

    args.report_dir.mkdir(parents=True, exist_ok=True)
    (args.report_dir / "BOOT.BIN.patched").write_bytes(patched_boot)
    (args.report_dir / "EBOOT.BIN.patched").write_bytes(patched_eboot)
    (args.report_dir / "dialogue_patch_report.txt").write_text(
        "Korean dialogue patch\n"
        "=====================\n"
        "Hangul: 2,350 KS X 1001/Wansung syllables in the patched pspfont.dat\n"
        "Text encoding: custom Shift-JIS bytes pointing at the first 2,350 JIS slots\n"
        "Field padding: ASCII spaces; original NUL terminators and field offsets retained\n\n"
        + "\n".join(report)
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
    print(f"Report: {args.report_dir / 'dialogue_patch_report.txt'}")


if __name__ == "__main__":
    main()
