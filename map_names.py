# -*- coding: utf-8 -*-
"""Korean names for the 52 battle maps.

Each name is stored at offset 0 of ``data/map/_asm/mapNNN._as`` -- as a loose
file, inside the ``asm.dat`` pack, and again inside the copy of ``asm.dat`` that
``init0.dat`` carries.  Binary script data starts immediately after the NUL, so
a name may not be one byte longer than the Japanese it replaces: a Hangul
syllable costs two bytes and a space one, which buys four syllables for an
eight-byte name.  The map-select header draws these with the game font, so they
did not have to be redrawn as art.

These are written by ``patch_scripts.py`` now, out of
``itp_work/kr_scripts/map_names.json``, alongside the advice in the same files:
padded with spaces to the bytes the Japanese used, and with every pack member
required to come back no larger than the stream it replaces.  The old
``patch_map_names.py``, which let ``asm.dat`` grow by 203 bytes and froze the
game, is no longer used.
"""

from __future__ import annotations

NAMES: dict[int, str] = {
    0: "나그네숲",
    1: "통곡 오아시스",
    2: "암운의 섬",
    3: "허무 요궁",
    4: "사구 신기루",
    5: "한파감옥",
    6: "어둔 굴의 노래",
    7: "침수 폐궁",
    8: "안개 동굴",
    9: "고요한 섬광",
    10: "불꽃 잠든 산",
    11: "달빛의 궁전",
    12: "격절의 섬",
    13: "어둠의품",
    14: "물밑의 힘",
    15: "수호 방진",
    16: "물이 가른 길",
    17: "지하 포진",
    18: "맥맥한 습원",
    19: "불가침의 어둠",
    20: "호수의 섬",
    21: "만년설 계곡",
    22: "바다 위의 거리",
    23: "종언 옥좌",
    24: "마도 결계",
    25: "쟁탈 쌍채",
    26: "안녕 심판",
    27: "망각의 낙원",
    28: "미지의 광휘",
    29: "아득한 아성",
    30: "살의의숲",
    31: "지맥 고동",
    32: "열사의 지평",
    33: "내달리는 선풍",
    34: "마정 가도",
    35: "요사 회랑",
    36: "암흑의 포효",
    37: "빙하 끝의 땅",
    38: "분연이 나부낀 뒤",
    39: "다리없는강",
    40: "사선을 넘어",
    41: "무지개 너머",
    42: "유구한흐름",
    43: "빛 없는 땅밑",
    44: "부동의 심연",
    45: "물을 머금은 신전",
    46: "명부의 주인",
    47: "끝자락 단애",
    48: "선전포고",
    49: "대립 파도",
    50: "무에의도전",
    51: "대해의 쌍성",
}

ASM_PACK = "asm.dat"
LOOSE_DIR = "/PSP_GAME/USRDIR/data/map/_asm"
