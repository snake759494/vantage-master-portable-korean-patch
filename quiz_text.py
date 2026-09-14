# -*- coding: utf-8 -*-
"""Korean text for the class-determining questionnaire.

The whole quiz is pre-rendered art in make_7/make_8/make_9.itp.  Each entry is
``(x, y, w, h, [lines])``; the box is the area the Japanese occupied and the
lines are drawn centred inside it at the original line pitch.

Sources: the in-game screenshots the user captured (the questions render at a
legible size there) plus the atlases themselves for the two scenes that were
not captured.
"""

from __future__ import annotations

# --- make_7: the framing question, the sword shop and the street performer --

MAKE_7_TEXT: list[tuple[int, int, int, int, list[str]]] = [
    (64, 0, 160, 32, [
        "만약 소원이 이루어진다면,",
        "당신은 무엇을 바라겠습니까?",
    ]),
    (16, 40, 256, 24, [
        "지위, 명예, 권력, 재산, 아니면 힘……?",
    ]),
    (0, 80, 272, 104, [
        "당신은 새 검을 구하러 거리로 나섰다.",
        "인파를 지나 무기점에 들어가 검을 고르던 중,",
        "마음에 드는 검을 발견할 수 있었다.",
        "",
        "그 검에는 그에 걸맞은 값이 매겨져 있었다.",
        "당신이 검을 바라보고 있으니, 주인은 볼일이 있어",
        "안쪽으로 들어가 버렸다.",
    ]),
    (0, 192, 272, 32, [
        "다른 손님도 없어, 당신을 보는 사람은 없다.",
        "밖은 여전히 인파로 붐비고 있다.",
    ]),
    (0, 232, 288, 48, [
        "광장을 걷고 있으니, 사람들이 모여 있었다.",
        "약장수가 주머니에서 비둘기를 몇 마리나 날려,",
        "갈채를 받고 있는 참이었다.",
    ]),
    (0, 288, 288, 48, [
        "약장수 앞에 뒤집어 놓인 모자에는,",
        "구경꾼이 던져 넣은 동전이 얼마간 들어 있었다.",
        "약장수는 이어서 카드를 쓰는 마술을 시작했다.",
    ]),
    (32, 344, 224, 32, [
        "그 마술은 전에 본 적이 있어서,",
        "당신은 이미 속임수를 알고 있지만……",
    ]),
    (0, 384, 288, 48, [
        "당신은 일개 병사였지만,",
        "지난 전투에서의 공적을 인정받아,",
        "왕으로부터 직접 이웃 나라 공주의 호위를 맡게 되었다.",
    ]),
    (0, 440, 288, 32, [
        "공주의 저택에서 왕이 당신에게 치하의 말을 건넨 뒤,",
        "세 가지 포상 중 마음에 드는 것을 고르라고 했다.",
    ]),
    (80, 480, 144, 24, [
        "무엇을 고르겠는가?",
    ]),
]

# The option strips sit on a 20px grid down the right edge; each choice appears
# twice, once plain and once on its highlight plate.  Index 12 and 15 are the
# one label that could not be read off the atlas with confidence, so they keep
# their Japanese art until the screen is captured.
MAKE_7_OPTIONS: dict[int, str] = {
    0: "검을 훔쳐 달아난다",
    1: "다른 검을 산다",
    2: "돈을 빌린다",
    3: "검을 훔쳐 달아난다",
    4: "다른 검을 산다",
    5: "돈을 빌린다",
    6: "그냥 지나간다",
    7: "잠자코 본다",
    8: "구경꾼에게 알린다",
    9: "그냥 지나간다",
    10: "잠자코 본다",
    11: "구경꾼에게 알린다",
    # 12/15 are art only -- the string is nowhere in the ISO and the 12-pixel
    # kanji have merged into blobs.  The cell widths run 24/10/24, the same
    # kanji-kanji-no-kanji-kanji shape as 14's 士官の位, and the last glyph is a
    # stack of horizontal bars with no vertical split, so it is 章 and not 剣.
    12: "명예의 훈장",
    13: "금화 가득한 주머니",
    14: "사관의 지위",
    15: "명예의 훈장",
    16: "금화 가득한 주머니",
    17: "사관의 지위",
}

# --- make_8: the sculptor, the fox cub and the cracked church wall ----------

MAKE_8_TEXT: list[tuple[int, int, int, int, list[str]]] = [
    (3, 0, 279, 13, ["당신은 당대 제일로 꼽히는 조각가의 솜씨를 지녔다."]),
    (38, 14, 208, 13, ["당신의 수제자도 독립한 뒤,"]),
    (21, 29, 243, 12, ["당신과 어깨를 나란히 할 평가를 얻게 되었다."]),
    (26, 56, 232, 28, [
        "영주는 사원에 봉헌할 여신상을",
        "당신과 제자에게 겨루게 할 생각을 했다.",
    ]),
    (25, 99, 233, 13, ["두 사람은 영주의 관에 여신상을 놓았다."]),
    (1, 113, 281, 14, ["제자가 만든 것을 본 순간, 당신은 패배를 느꼈다."]),
    (27, 144, 236, 13, ["그러나 영주는 당신을 택했다. 어쩌겠는가?"]),
    (3, 167, 279, 28, [
        "당신은 산길에서 덫에 걸린 새끼 여우를 발견했다.",
        "가엾다고는 생각했지만, 입은 상처가 깊어 보여",
    ]),
    (19, 196, 245, 13, ["놓아준들 오래 살지는 못할 것이다."]),
    (20, 223, 243, 15, ["또한 애써 잡은 사냥감을 놓아주면,"]),
    (55, 239, 173, 12, ["사냥꾼에게도 큰 민폐일 것이다."]),
    (26, 268, 232, 13, ["그렇게 생각하고 자리를 뜨려 했지만,"]),
    (8, 283, 268, 13, ["그때 새끼 여우가 애원하듯 우는 소리를 냈다."]),
    (61, 311, 165, 13, ["새끼 여우를 놓아주어야 할까?"]),
    (13, 335, 257, 29, [
        "큰 지진이 일어나, 교회 벽에 균열이 생겼다.",
        "당장 수리하지 않으면 무너질 우려도 있다.",
    ]),
    (2, 378, 280, 15, ["그러나 사제는 마봉의 비석을 들어 완강히 거절했다."]),
    (13, 407, 257, 14, ["균열이 가장 심한 벽은 마봉의 비석과 붙어 있어,"]),
    (14, 422, 256, 29, [
        "그것을 옮기지 않으면 수리는 불가능했지만,",
        "마봉의 비석을 움직이면 마의 봉인이 풀려",
    ]),
    (31, 452, 219, 12, ["재앙을 부른다고 전해진다는 것이다."]),
    (1, 480, 286, 14, ["수리를 명받은 당신에게도 입장이 있다. 어쩌겠는가?"]),
]

MAKE_8_OPTIONS: dict[int, str] = {
    0: "영예를 받는다",
    1: "패배를 인정한다",
    2: "다시 만들자고 제안한다",
    3: "영예를 받는다",
    4: "패배를 인정한다",
    5: "다시 만들자고 제안한다",
    6: "놓아준다",
    7: "그대로 둔다",
    8: "놓아준다",
    9: "그대로 둔다",
    10: "수리한다",
    11: "가능한 범위만 수리한다",
    12: "수리한다",
    13: "가능한 범위만 수리한다",
}

# --- make_9: the night patrol, the travelling companion and Mellett's reply -

MAKE_9_TEXT: list[tuple[int, int, int, int, list[str]]] = [
    (36, 1, 221, 29, [
        "야간 경비를 맡은 당신은,",
        "영지 순찰 중 기묘한 그림자를 발견했다.",
    ]),
    (36, 43, 220, 29, [
        "본 적 없는 맹수가 가엾은 가축을 물고,",
        "끌고 가는 참이었다.",
    ]),
    (48, 88, 197, 15, ["요즘 소문이 도는 마수일지도 모른다."]),
    (18, 115, 262, 30, [
        "다행히 이쪽은 눈치채지 못한 듯하니,",
        "쫓아가면 소굴을 확인할 수 있을 듯한데, 어쩔까?",
    ]),
    (0, 160, 316, 44, [
        "여행 도중에 알게 된 남자와 목적지가 같아",
        "함께 걷기로 했다. 깊은 숲에 들어선 지 얼마 지나,",
        "남자가 진창에 빠져 발을 삐고 말았다.",
    ]),
    (32, 216, 263, 30, [
        "어떻게든 걸을 수는 있겠지만, 해가 있는 동안",
        "다음 숙소에는 닿지 못할 것 같았다.",
    ]),
    (51, 257, 219, 30, [
        "되돌아가면 하루를 허비하게 되지만,",
        "어젯밤 묵은 숙소로는 돌아갈 수 있다.",
    ]),
    (36, 304, 239, 16, ["남자는 신경 쓰지 말고 가라고 하지만……"]),
    (48, 344, 214, 15, ["당신이 그것을 바란다면……"]),
    (73, 370, 143, 29, [
        "저는 당신의 소망을 이루는",
        "인도자가 되어 드리죠.",
    ]),
]

MAKE_9_OPTIONS: dict[int, str] = {
    0: "혼자 추적한다",
    1: "지원 요청",
    2: "못 본 것으로 한다",
    3: "혼자 추적한다",
    4: "지원 요청",
    5: "못 본 것으로 한다",
    6: "혼자 먼저 간다",
    7: "함께 되돌아간다",
    8: "남자를 업고 간다",
    9: "혼자 먼저 간다",
    10: "함께 되돌아간다",
    11: "남자를 업고 간다",
}

# Every option is stored in the atlas twice: the copy the game draws while the
# cursor sits on it and the copy it draws while it does not.  The game always
# takes the cursor's copy from the LOWER index of the pair -- read off the
# screen, where the option on the highlight bar was the one drawn in whichever
# colour this table had given the low index.  Ink weight in the Japanese art is
# not a reliable guide: it points the right way for make_7 and make_9 and the
# wrong way for make_8.  Drawing both copies alike makes every option look
# selected at once.
FOCUSED: dict[str, set[int]] = {
    "make_7": {0, 1, 2, 6, 7, 8, 12, 13, 14},
    "make_8": {0, 1, 2, 6, 7, 10, 11},
    "make_9": {0, 1, 2, 6, 7, 8},
}

# atlas -> (paragraph boxes, option column, option pitch, options)
QUIZ = {
    "make_7": (MAKE_7_TEXT, (370, 512), 20, MAKE_7_OPTIONS),
    "make_8": (MAKE_8_TEXT, (370, 512), 20, MAKE_8_OPTIONS),
    "make_9": (MAKE_9_TEXT, (330, 512), 20, MAKE_9_OPTIONS),
}
