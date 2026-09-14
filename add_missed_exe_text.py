# -*- coding: utf-8 -*-
"""Translate the executable strings the first census missed.

They were missed for one reason: these fields break their lines with CR (0x0D),
not LF, and the filter that pulled strings out of BOOT.BIN only allowed LF.  The
confirmation dialogs the game shows before returning to the title -- the ones
that still read Japanese on screen -- are all in this group.

Each Korean line is joined with the separator the Japanese itself uses, so the
line structure of a field can never drift from the original.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, ".")

MISSED = Path("itp_work/exe_missed.json")
TODO = Path("itp_work/exe_todo.json")
OUT = Path("itp_work/kr/zz_missed.json")

KOREAN: dict[int, list[str]] = {
    0x160614: ["시간"],
    0x161CA0: ["OpenMessage - 문자열 초과!"],
    0x1620F4: ["오토세이브를 ＯＮ하면,", "전적과 커스터마이즈 설정이 자동 갱신됩니다."],
    0x162140: ["전적과 커스터마이즈 설정을 저장하려면", "타이틀 화면에서 시스템 데이터를", "수동 저장해야 합니다."],
    0x1621C4: ["오토세이브를 ＯＦＦ합니다.", "전적과 커스터마이즈 설정이", "자동 갱신되지 않게 되는데 괜찮습니까?"],
    0x16222C: ["전적과 커스터마이즈 설정을 읽지 못했지만,", "이대로 게임을 시작할까요?"],
    0x162278: ["시스템 데이터 생성이 끝나지 않았지만,", "이대로 게임을 시작할까요?"],
    0x1623C0: ["Vantage Master PORTABLE의 시스템 데이터를", "저장하려면 공간이 １２８ＫＢ 이상 필요합니다."],
    0x16241C: ["새로 만들지 못했습니다.", "손상된 시스템 데이터를 지워야 합니다."],
    0x1624A0: ["접근 중 오류가 발생해,", "시스템 데이터 생성에 실패했습니다."],
    0x1624E8: ["슬립 모드로 전환되어,", "시스템 데이터 생성에 실패했습니다."],
    0x1625B0: ["Vantage Master PORTABLE의 시스템 데이터를", "만들려면 공간이 １２８ＫＢ 이상 필요합니다."],
    0x16260C: ["시스템 데이터가 손상되어,", "전적과 커스터마이즈 설정을 잃었습니다."],
    0x162654: ["접근 중 오류가 발생해,", "시스템 데이터 로드에 실패했습니다."],
    0x1626A0: ["슬립 모드로 전환되어,", "시스템 데이터 로드에 실패했습니다."],
    0x165F44: ["통상"],
    0x165F4C: ["주간"],
    0x165F54: ["야간"],
    0x165F94: ["인접"],
    0x165FB4: ["직선"],
    0x165FBC: ["발생"],
    0x165FC4: ["목표"],
    0x165FFC: ["전체"],
    0x166004: ["속성"],
    0x16600C: ["특성"],
    0x166050: ["거리"],
    0x166058: ["종류"],
    0x166060: ["범위"],
    0x166074: ["없음"],
    0x1660AC: ["박명"],
    0x16C658: ["NetErrorSaveWork:미지의 오류"],
    0x16CCD0: ["NetworkProgram : 메모리 누수?"],
    0x16CD28: ["결정"],
    0x16CD3C: ["승낙"],
    0x16CD44: ["거부"],
    0x16CD4C: ["중지"],
    0x16CD54: ["뒤로"],
    0x16D738: [
        "시스템 데이터 저장이 끝나지 않았습니다.",
        "전투 도중 경과가 저장되지 않는데,",
        "세이브를 중지해도 괜찮습니까?",
    ],
    0x16D7A8: [
        "시스템 데이터 저장이 끝나지 않았습니다.",
        "커스터마이즈 설정이",
        "저장되지 않는데 괜찮습니까?",
    ],
    0x16D808: [
        "시스템 데이터 저장이 끝나지 않았습니다.",
        "전적이 저장되지 않는데 괜찮습니까?",
    ],
    0x16D858: [
        "시스템 데이터 저장이 끝나지 않았습니다.",
        "전적과 커스터마이즈 설정이",
        "저장되지 않는데 괜찮습니까?",
    ],
    0x16D8BC: ["중단 데이터를 저장하려면 시스템 데이터를", "만들어야 합니다."],
    0x16D920: ["시스템 데이터를 만들어", "중단 데이터를 저장할까요?"],
    0x16D954: [
        "커스터마이즈 설정을 저장하려면",
        "시스템 데이터가 필요합니다.",
        "시스템 데이터를 만들까요?",
    ],
    0x16D9B4: ["전적을 저장하려면 시스템 데이터가 필요합니다.", "시스템 데이터를 만들까요?"],
    0x16DA08: [
        "전적과 커스터마이즈 설정을 저장하려면",
        "시스템 데이터가 필요합니다.",
        "시스템 데이터를 만들까요?",
    ],
    0x16DA94: ["커스터마이즈 설정이", "저장되지 않는데 괜찮습니까?"],
    0x16DAF0: ["전적과 커스터마이즈 설정이", "저장되지 않는데 괜찮습니까?"],
    0x16DB2C: ["중단 데이터는 저장되지 않는데", "타이틀로 돌아갈까요?"],
    0x16DB64: ["오토세이브를 ＯＮ하면", "전적과 커스터마이즈 설정이 자동 갱신됩니다."],
    0x16DBD0: [
        "전적과 커스터마이즈 설정을 저장하려면",
        "타이틀 화면에서 시스템 데이터를",
        "수동 저장해야 합니다.",
    ],
    0x16DC34: [
        "오토세이브를 ＯＦＦ합니다.",
        "전적과 커스터마이즈 설정이",
        "자동 갱신되지 않게 되는데 괜찮습니까?",
    ],
    0x16DCF4: [
        "Vantage Master PORTABLE의 시스템 데이터를",
        "저장하려면 공간이 １２８ＫＢ 이상 필요합니다.",
    ],
    0x16DDCC: [
        "Vantage Master PORTABLE의 시스템 데이터를",
        "만들려면 공간이 １２８ＫＢ 이상 필요합니다.",
    ],
    0x16DED8: ["세이브에 실패했습니다.", "%s"],
    0x16E7A0: ["", "덮어써도 괜찮습니까?"],
    0x16E7C0: ["중단 데이터를 저장하고", "타이틀로 돌아갈까요?"],
    0x16E7F0: ["오토세이브를 ＯＮ하면", "전적과 커스터마이즈 설정이 자동 갱신됩니다."],
    0x16E83C: [
        "전적과 커스터마이즈 설정을 저장하려면",
        "타이틀 화면에서 시스템 데이터를",
        "수동 저장해야 합니다.",
    ],
    0x16ED64: [
        "오토세이브를 ＯＦＦ합니다.",
        "전적과 커스터마이즈 설정이",
        "자동 갱신되지 않게 되는데 괜찮습니까?",
    ],
    0x16EE08: [
        "타이틀 화면으로 돌아가면 게임 도중 경과는",
        "저장되지 않습니다. 괜찮습니까?",
    ],
    0x1795FC: ["이동"],
}


def main() -> None:
    missed = {entry["off"]: entry for entry in json.loads(MISSED.read_text(encoding="utf-8"))}
    if set(KOREAN) != set(missed):
        raise SystemExit(f"table drift: {sorted(set(KOREAN) ^ set(missed))}")

    todo = json.loads(TODO.read_text(encoding="utf-8"))
    known = {entry["off"] for entry in todo}
    korean: dict[str, str] = {}
    for offset, lines in KOREAN.items():
        japanese = missed[offset]["jp"]
        separator = "\r" if "\r" in japanese else "\n"
        wanted = japanese.count(separator) + 1
        if len(lines) != wanted:
            raise SystemExit(f"0x{offset:X}: {len(lines)} lines, the field has {wanted}")
        korean[f"0x{offset:X}"] = separator.join(lines)
        if offset not in known:
            # capacity is the Japanese itself; the padding behind it is not ours
            todo.append({"off": offset, "len": missed[offset]["len"], "slack": 0, "jp": japanese})

    todo.sort(key=lambda entry: entry["off"])
    TODO.write_text(json.dumps(todo, ensure_ascii=False, indent=1), encoding="utf-8")
    OUT.write_text(json.dumps(korean, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"exe_todo now {len(todo)} fields; wrote {len(korean)} translations to {OUT}")


if __name__ == "__main__":
    main()
