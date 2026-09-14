# -*- coding: utf-8 -*-
"""Korean replacements for the pre-rendered Japanese labels in the UI atlases.

Each entry is ``(x, y, w, h, korean)`` in texture pixels.  The boxes are the
ink bounds of the Japanese label they replace, so the Korean stays inside the
same UV rectangle the game samples.
"""

from __future__ import annotations

# data/system/battle.itp -- everything drawn during a battle.
BATTLE: list[tuple[int, int, int, int, str]] = [
    # terrain names down the left edge
    (2, 232, 29, 16, "평지"),
    (0, 256, 31, 16, "사막"),
    (0, 280, 31, 16, "수풀"),
    (0, 304, 31, 16, "습지"),
    (1, 328, 31, 16, "적설"),
    (1, 352, 31, 16, "늪지"),
    (1, 376, 47, 16, "수면판"),
    (1, 400, 30, 16, "물벽"),
    (0, 424, 47, 16, "장애물"),
    (0, 448, 42, 16, "바닥없음"),
    (0, 472, 48, 16, "마정석"),
    # the command / sub-command name grid
    (360, 384, 24, 12, "소환"),
    (392, 384, 47, 12, "상세정보"),
    (456, 384, 48, 12, "영향범위"),
    (360, 400, 24, 12, "대기"),
    (392, 400, 47, 12, "이동범위"),
    (456, 400, 55, 12, "이동+공격"),
    (360, 416, 24, 12, "공격"),
    (392, 416, 47, 12, "공격거리"),
    (456, 416, 54, 12, "이동+마법"),
    (360, 432, 24, 9, "마법"),
    (392, 432, 47, 11, "마법거리"),
    (456, 432, 52, 12, "이+마+효"),
    (360, 448, 24, 12, "이동"),
    (392, 448, 55, 12, "마법+효과"),
    (457, 448, 23, 11, "소멸"),
    # day/night behaviour and movement type shown on the unit panel
    (288, 3, 23, 13, "보통"),
    (321, 4, 23, 11, "낮형"),
    (353, 3, 23, 13, "밤형"),
    # A unit that walks but can also swim, and one that swims but can also
    # walk.  The Japanese abbreviates each type to its first character, so the
    # Korean does the same: 보(행) and 수(영).
    (288, 27, 35, 13, "보(수)"),
    (328, 27, 35, 13, "수(보)"),
    # the two gauge strips above the action buttons, each drawn light and dark
    (446, 136, 26, 10, "공격"),
    (447, 152, 24, 10, "공격"),
    (445, 168, 24, 10, "마법"),
    (445, 184, 25, 10, "마법"),
    # the action buttons, in a blue set for your side and a red set for the
    # enemy's.  The executable already names these commands in its own text,
    # so the art has to agree with it.
    (370, 266, 37, 15, "마법"),
    (370, 290, 49, 15, "마법 목록"),
    (370, 314, 37, 15, "소환"),
    (370, 338, 49, 15, "소환 목록"),
    (370, 362, 52, 15, "유닛 정보"),
    (452, 266, 36, 15, "마법"),
    (452, 290, 48, 15, "마법 목록"),
    (452, 314, 37, 15, "소환"),
    (452, 338, 48, 15, "소환 목록"),
    (452, 362, 54, 15, "유닛 정보"),
]

# data/system/common.itp -- the pieces every screen borrows: button glyphs,
# the arrows, and the little heading the unit panel puts over its element row.
COMMON: list[tuple[int, int, int, int, str]] = [
    (0, 155, 37, 14, "공격력"),
    (52, 155, 13, 13, "불"),
    (84, 157, 13, 11, "천"),
    (51, 171, 14, 13, "땅"),
    (84, 172, 12, 12, "물"),
]

# data/system/info2.itp -- the button hints and the battle-setup switches.
# Each hint plate is cut to the width of its own text: 결정, 시스템, 뒤로, 다음
# and 타이틀 stop at x=495, the rest run to the atlas edge.  A box that reaches
# past its plate takes the bare atlas beyond it for the background and erases
# the plate instead of the lettering.
INFO2: list[tuple[int, int, int, int, str]] = [
    # The four mode plates, Latin in the original but named in Korean on the
    # title screen's own strip and in every description the executable prints.
    (9, 26, 133, 15, "시나리오 모드"),
    (9, 58, 94, 15, "프리 모드"),
    (9, 90, 115, 15, "엑스퍼트 모드"),
    (9, 122, 131, 15, "네트워크 모드"),
    # The difficulty and the user's time limit, whose descriptions call them
    # 노멀/하드 and 쇼트/미들/롱; the art has to agree with those.
    (157, 402, 44, 12, "노멀"),
    (157, 419, 39, 12, "하드"),
    (4, 475, 34, 10, "쇼트"),
    (53, 475, 35, 10, "미들"),
    (106, 475, 25, 10, "롱"),
    (4, 499, 34, 11, "쇼트"),
    (51, 499, 37, 11, "미들"),
    (103, 499, 29, 11, "롱"),
    (449, 226, 22, 12, "결정"),
    (449, 243, 44, 10, "시스템"),
    (449, 259, 21, 11, "뒤로"),
    (449, 274, 56, 12, "맵 선택"),
    (449, 291, 22, 11, "다음"),
    (449, 307, 45, 11, "타이틀"),
    (450, 322, 54, 11, "유저 전환"),
    (450, 338, 48, 12, "마스터 전환"),
    (450, 355, 57, 12, "적 사고 타입"),
    (450, 371, 45, 11, "제한 시간"),
    # the two enemy AI types, dimmed and lit
    (20, 426, 24, 12, "통상"),
    (85, 426, 46, 12, "방어 경시"),
    (21, 450, 23, 12, "통상"),
    (85, 450, 46, 12, "방어 경시"),
]

# data/system/make_3.itp -- the button hints shown on every character-creation
# and questionnaire screen, plus the expert-mode button.
MAKE_3: list[tuple[int, int, int, int, str]] = [
    (274, 3, 22, 11, "다음"),
    (274, 17, 49, 13, "스킵"),
    (274, 34, 24, 12, "결정"),
    (274, 50, 47, 12, "이름 변경"),
    (274, 66, 33, 12, "빨리감기"),
    (274, 83, 45, 11, "타이틀"),
    (343, 26, 70, 15, "상급자용"),
]

# data/system/rank.itp -- the master rank shown on the mode-select and result
# screens.  The executable carries the same names as text; both are patched.
RANK: list[tuple[int, int, int, int, str]] = [
    # Each name sits on its own brown plate 128px wide, and the longest of them
    # fill it edge to edge.  The boxes are the ink and no more: the "NOW
    # LOADING" art is packed against the plates' right edge, and the first
    # three rows used to reach into it.
    (1, 0, 127, 19, "밴티지 마스터"),
    (1, 21, 127, 20, "샤이닝 마스터"),
    (7, 46, 114, 18, "레전드 마스터"),
    (14, 69, 102, 19, "그랜드 마스터"),
    (0, 94, 128, 18, "네이티얼 마스터"),
    (13, 117, 102, 19, "그레이트 마스터"),
    (13, 141, 103, 19, "슈퍼 마스터"),
    (0, 166, 128, 18, "엑설런트 마스터"),
    (20, 190, 90, 18, "칙 마스터"),
    (13, 213, 102, 19, "비기너 마스터"),
    (26, 237, 77, 18, "쁘띠 마스터"),
]

# data/system/title.itp -- the mode caption on the versus/loading banner.
TITLE: list[tuple[int, int, int, int, str]] = [
    # the menu itself.  Scenario, Expert, Free, Network and System are Latin
    # in the original and stay that way; only these four were ever Japanese.
    (13, 378, 75, 17, "중단 데이터"),
    (20, 426, 56, 14, "처음부터"),
    (20, 450, 56, 14, "이어하기"),
    (16, 474, 65, 13, "시크릿"),
    # The difficulty beside the menu.  The pair on the banner above it is left
    # in Latin: those plates are 45x10 with the lettering running edge to edge
    # inside a four-pixel inset border, so there is no plate showing anywhere
    # the patcher could read a background from.
    (104, 426, 60, 13, "노멀"),
    (104, 450, 60, 14, "하드"),
    # the strip along the bottom that names the mode under the cursor
    (161, 483, 71, 12, "시나리오 모드"),
    (240, 483, 92, 12, "엑스퍼트 모드"),
    (344, 483, 61, 12, "프리 모드"),
    (416, 483, 93, 12, "네트워크 모드"),
]

# data/system/result0.itp -- the result screen: the same master rank plates the
# rank atlas carries, and the column headings down the right edge.
RESULT0: list[tuple[int, int, int, int, str]] = [
    (217, 253, 125, 19, "밴티지 마스터"),
    (217, 277, 125, 19, "샤이닝 마스터"),
    (223, 302, 113, 18, "레전드 마스터"),
    (230, 326, 102, 18, "그랜드 마스터"),
    (216, 350, 126, 18, "네이티얼 마스터"),
    (229, 374, 102, 17, "그레이트 마스터"),
    (229, 398, 103, 18, "슈퍼 마스터"),
    (216, 422, 126, 18, "엑설런트 마스터"),
    (236, 446, 90, 18, "칙 마스터"),
    (229, 470, 102, 19, "비기너 마스터"),
    (242, 494, 77, 17, "쁘띠 마스터"),
    # the five section ribbons down the left edge
    (14, 276, 87, 14, "《전투 평가》"),
    (18, 300, 78, 14, "《보너스》"),
    (14, 324, 87, 14, "《전투 결과》"),
    (4, 348, 103, 14, "《획득 아이템》"),
    (22, 372, 71, 14, "《리절트》"),
    # the per-element tally headings, in a pale and a lit copy 96px apart
    (448, 7, 24, 9, "마법"),
    (448, 24, 64, 8, "네이티얼"),
    (448, 38, 11, 10, "땅"),
    (464, 38, 11, 10, "물"),
    (480, 38, 11, 10, "불"),
    (496, 40, 11, 8, "천"),
    (448, 53, 28, 11, "횟수"),
    (448, 103, 24, 9, "마법"),
    (448, 120, 64, 8, "네이티얼"),
    (448, 134, 11, 10, "땅"),
    (464, 134, 11, 10, "물"),
    (480, 134, 11, 10, "불"),
    (496, 136, 11, 8, "천"),
    (448, 149, 28, 11, "횟수"),
    # the two summary plates at the top of each side, blue for you and orange
    # for the enemy; the same pair sits on result1 as well
    (12, 35, 36, 13, "마정석"),
    (12, 62, 38, 13, "소비 MP"),
    (324, 35, 36, 13, "마정석"),
    (324, 62, 38, 13, "소비 MP"),
    # the score line and the two column headings under it
    (0, 438, 18, 18, "점"),
    (72, 486, 41, 18, "득점"),
    (120, 485, 47, 19, "랭크"),
]

# data/system/result1.itp -- the four graph headings, each in a normal and a
# highlighted variant on its own 16px row.
RESULT1: list[tuple[int, int, int, int, str]] = [
    (0, 2, 88, 14, "《네이티얼》"),
    (92, 2, 51, 14, "사용 횟수"),
    (153, 2, 87, 14, "마스터의 행동"),
    (1, 18, 49, 14, "《마법》"),
    (54, 18, 51, 14, "사용 횟수"),
    (153, 18, 90, 14, "마스터의 행동"),
    (0, 34, 88, 14, "《네이티얼》"),
    (92, 34, 51, 14, "사용 횟수"),
    (153, 34, 111, 14, "네이티얼의 동향"),
    (0, 50, 50, 14, "《마법》"),
    (54, 50, 51, 14, "사용 횟수"),
    (153, 50, 111, 14, "네이티얼의 동향"),
    # The action legend beside the bar graphs and the four element cells under
    # it, in a blue set and a brown set 80 rows apart.  Left column is 地 over
    # 火 and right is 水 over 天, which is not the order the four are listed in
    # anywhere else.
    (6, 72, 23, 13, "대기"),
    (6, 90, 23, 15, "마법"),
    (106, 72, 23, 13, "공격"),
    (106, 90, 23, 15, "소환"),
    (10, 111, 21, 15, "땅"),
    (10, 129, 15, 15, "불"),
    (109, 111, 15, 15, "물"),
    (109, 129, 15, 15, "천"),
    (7, 153, 22, 12, "대기"),
    (7, 171, 22, 13, "마법"),
    (106, 153, 22, 12, "공격"),
    (106, 171, 22, 13, "소환"),
    (10, 191, 16, 15, "땅"),
    (10, 209, 15, 15, "불"),
    (108, 191, 17, 15, "물"),
    (109, 209, 15, 15, "천"),
    # the units under the play-time counter
    (0, 231, 13, 15, "일"),
    (19, 231, 27, 16, "시간"),
    (51, 231, 14, 16, "분"),
    # the summary panel at the bottom of the screen
    (62, 339, 78, 13, "《종합 결과》"),
    (168, 344, 108, 16, "마스터의 공략 결과"),
    (286, 373, 33, 14, "마정석"),
    (286, 405, 33, 14, "소비 MP"),
    (286, 437, 44, 14, "소요 시간"),
]

# data/system/sysmenu.itp -- the menu list down the left edge and the settings
# column beside it, every option of which is drawn twice, dimmed and lit.
SYSMENU: list[tuple[int, int, int, int, str]] = [
    (8, 80, 64, 14, "시스템 데이터"),
    (20, 98, 37, 12, "전적"),
    (12, 112, 57, 14, "튜토리얼"),
    (15, 128, 58, 14, "커스터마이즈"),
    (15, 144, 49, 14, "타이틀로"),
    (19, 161, 39, 13, "세이브"),
    (17, 177, 40, 13, "삭제"),
    (6, 192, 67, 15, "월드로 돌아가기"),
    (10, 208, 59, 14, "게임 데이터"),
    (18, 224, 46, 14, "갤러리"),
    (21, 240, 36, 14, "중단"),
    (104, 80, 41, 13, "최대화"),
    (152, 80, 42, 13, "최소화"),
    (103, 95, 43, 15, "최대화"),
    (151, 95, 44, 15, "최소화"),
    (117, 112, 58, 16, "각종 설정"),
    (189, 113, 58, 15, "사운드"),
    (176, 185, 40, 15, "목차"),
    (105, 194, 28, 13, "표준"),
    (137, 194, 28, 13, "높음"),
    (103, 209, 31, 15, "표준"),
    (136, 209, 29, 15, "높음"),
    (196, 209, 37, 13, "로드"),
    (105, 226, 50, 13, "어레인지"),
    (161, 226, 65, 13, "오리지널"),
    (104, 241, 52, 15, "어레인지"),
    (160, 241, 67, 15, "오리지널"),
]

# data/system/network.itp -- the ad-hoc lobby.  The first two items are drawn
# twice, dim and lit; the prompts below them start after a button glyph at x=0,
# which the box must not cover.
NETWORK: list[tuple[int, int, int, int, str]] = [
    (16, 289, 103, 15, "대전 상대 대기"),
    (15, 312, 105, 16, "대전 상대 대기"),
    (15, 337, 104, 15, "대전 상대 선택"),
    (14, 360, 106, 16, "대전 상대 선택"),
    (12, 385, 155, 15, "항목을 선택해 주세요"),
    (12, 409, 183, 15, "대전 상대를 선택해 주세요"),
    (12, 433, 100, 15, "엔트리 접수"),
]

# data/system/info3.itp -- the 52 battle map names, pre-rendered as art for the
# map-select list.  They sit in a 3 x 21 grid of 128x16 cells: column 0 holds
# maps 0-20, column 1 maps 21-41, column 2 maps 42-51 followed by the
# <PHASE 1>..<VS> banners, which are Latin and left alone.
#
# This is the atlas that makes Korean map names possible at all.  The names are
# also the first string in each ``mapNNN._as``, but translating them there makes
# asm.dat 203 bytes longer, which pushes unit._as past the length it shipped
# with and freezes the scenario map list -- so ``--map-names`` stays off and the
# names are replaced here instead, where nothing moves.
# Where each name's lettering actually sits.  The cells are a uniform 128x22
# grid but the Japanese in them is left-aligned and only as wide as the name
# is, so a name centred in its cell sits up to thirty pixels right of where it
# belongs.  Measured off the original atlas by refit_ui_boxes.py.
INFO3_BOXES: dict[int, tuple[int, int, int, int]] = {
     0: (0, 5, 71, 22),
     1: (0, 29, 111, 22),
     2: (0, 53, 88, 22),
     3: (0, 77, 89, 22),
     4: (0, 101, 108, 22),
     5: (0, 125, 72, 22),
     6: (0, 149, 119, 22),
     7: (0, 173, 89, 22),
     8: (0, 197, 89, 22),
     9: (0, 221, 100, 22),
    10: (0, 245, 99, 22),
    11: (0, 269, 101, 22),
    12: (0, 293, 89, 22),
    13: (0, 317, 73, 22),
    14: (0, 341, 104, 22),
    15: (0, 365, 88, 22),
    16: (0, 389, 105, 22),
    17: (0, 413, 89, 22),
    18: (0, 437, 104, 22),
    19: (0, 461, 112, 22),
    20: (0, 485, 89, 19),
    21: (144, 5, 106, 22),
    22: (144, 29, 118, 22),
    23: (144, 53, 91, 22),
    24: (144, 77, 89, 22),
    25: (144, 101, 90, 22),
    26: (144, 125, 89, 22),
    27: (144, 149, 108, 22),
    28: (144, 173, 102, 22),
    29: (144, 197, 102, 22),
    30: (144, 221, 71, 22),
    31: (144, 245, 90, 22),
    32: (144, 269, 108, 22),
    33: (144, 293, 119, 22),
    34: (144, 317, 90, 22),
    35: (144, 341, 84, 22),
    36: (144, 365, 119, 22),
    37: (144, 389, 118, 22),
    38: (144, 413, 128, 22),
    39: (144, 437, 84, 22),
    40: (144, 461, 100, 22),
    41: (144, 485, 110, 19),
    42: (288, 5, 87, 22),
    43: (288, 29, 118, 22),
    44: (288, 53, 116, 22),
    45: (288, 77, 128, 22),
    46: (288, 101, 105, 22),
    47: (288, 125, 103, 22),
    48: (288, 149, 76, 22),
    49: (288, 173, 90, 22),
    50: (288, 197, 87, 22),
    51: (288, 221, 118, 22),
}


def _map_name_labels() -> list[tuple[int, int, int, int, str]]:
    import map_names
    return [(*INFO3_BOXES[index], korean)
            for index, korean in sorted(map_names.NAMES.items())]


INFO3: list[tuple[int, int, int, int, str]] = _map_name_labels()

# data/system/info5.itp -- the unit panel, drawn once in blue for your side and
# once in orange for the enemy's, the two copies 192px apart.
# The two tabs on each panel are opened out to their ruled frame rather than
# closed down onto the katakana: three Hangul syllables in the 24 pixels
# アイテム occupies come out as a smudge, and there is clear space inside the
# frame to take them.
INFO5: list[tuple[int, int, int, int, str]] = [
    (4, 80, 28, 13, "아이템"),
    (196, 80, 27, 13, "아이템"),
    (4, 209, 28, 13, "마법"),
    (196, 209, 27, 13, "마법"),
    (401, 210, 51, 13, "전투 개시"),
]

# data/system/info15.itp -- the master-editing screen.
# The title is pale gold engraved into a gold plate, and the frame around it
# is what the columns beside a taller box would read as its background: set by
# hand to the rows the lettering actually occupies.
INFO15: list[tuple[int, int, int, int, str]] = [
    (293, 37, 106, 12, "《마스터 편집》"),
    (386, 67, 23, 11, "결정"),
    (386, 82, 61, 13, "기본 설정"),
]

# data/system/cursor.itp -- the button hints along the top of the map list.
CURSOR: list[tuple[int, int, int, int, str]] = [
    (150, 44, 44, 12, "목록 넘김"),
]

PATCHES: dict[str, list[tuple[int, int, int, int, str]]] = {
    "battle": BATTLE,
    "common": COMMON,
    "cursor": CURSOR,
    "info2": INFO2,
    "info3": INFO3,
    "info5": INFO5,
    "info15": INFO15,
    "make_3": MAKE_3,
    "network": NETWORK,
    "rank": RANK,
    "result0": RESULT0,
    "result1": RESULT1,
    "sysmenu": SYSMENU,
    "title": TITLE,
}

# Most of these atlases are read out of a pack archive, and the loose copy in
# data/system is decoration; the builder checks that every packed copy was
# found, because a name with no packed copy is usually a typo.  These are the
# exceptions -- the loader really does read them straight from data/system.
LOOSE_ONLY: frozenset[str] = frozenset({"network"})

ISO_DIR = "/PSP_GAME/USRDIR/data/system"
