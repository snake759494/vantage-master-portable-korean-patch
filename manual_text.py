# -*- coding: utf-8 -*-
"""What the rulebook pages say, in Korean.

``data/system/histor*.itp`` is the 전적 (record) section and ``manual*.itp`` the
game manual.  Neither exists anywhere but as pixels, so the Japanese was read
off the atlas and translated here; the terminology follows the executable
(전적, 마스터 랭크, 전투 평가 포인트, 네이티얼), and the map, class and enemy
names are taken from the tables that already carry them so the two cannot
drift apart.

Each page is a list of lines::

    {"y": (top, bottom),                 # the rows the Japanese occupies
     "text": [("body", "..."), ...],     # spans, coloured body / red / blue
     "bold": True,                       # headings are drawn heavier
     "x": (left, right),                 # measure and clear only this window
     "pad": 2, "flat": True,             # table cells have no room for a ramp
     "align": "right"}                   # right-hand cross references

Only ``y`` and ``text`` are required.  The ``y`` bands come from ``_bands.py``
where the page is plain parchment, and were read off a ruler render where an
illustration defeats it.  A table cell needs its own ``x`` window: the row rule
and the neighbouring column are ink too, so measuring across them finds the
wrong left edge and clears the wrong strip.
"""

from __future__ import annotations

import manual_pages
import map_names

TITLE_HELP = "해　설"
TITLE_RANK = "현재 마스터 랭크"
TITLE_RANKS = "랭크표"
TITLE_SCORE = "전투 평가"
TITLE_BONUS = "보너스 합계"
TITLE_KILLS = "격파 이력"
TITLE_CLEAR = "클리어 이력"
TITLE_STANDARD = "전투 평가 포인트의 평가 기준"

# The class names and the enemy master names are already translated in the
# executable; reusing them keeps the record screens and the game itself
# spelling every name the same way.
CLASSES = [
    "파이터", "듀크", "소드맨", "나이트", "팔라딘", "섀도우",
    "레인저", "사베지", "시프", "바드", "시스터", "소서러",
    "위치", "몽크", "스피릿", "비스트", "나이트메어", "프로일라인",
    "로드마스터", "스트라이더", "퀸뷰트", "헤비엣지",
    "프린세스", "플레이보이", "테크노크라트", "그래플러",
    "지니어스", "다크나이트",
]

MASTERS = {
    "scenario": [
        "스케자", "닷츠・와트", "골다・나트", "메레나＆마기",
        "크라운", "카에데", "루피", "아잔",
        "리・린", "디세르", "파킬", "아토미스", "유리오",
    ],
    "phase456": [
        "녹시・메드", "아프사라", "브로우만", "베르바스", "제오트",
        "길・간다로스", "페랄・미리나", "가드롬", "라이라＆후",
        "퓨레나스", "스트라제", "카쿠노스", "미스트록",
        "멜렛", "마잠", "스카랏", "기드・칸",
    ],
    "expert": [
        "트로켄", "크로네", "월탄", "마그나・렉",
        "파르마", "마야", "지아스", "기드・칸",
    ],
}

# --- geometry ---------------------------------------------------------------
# The page counter shares the title bar, so the title is cleared only up to
# x=300 and everything right of that is left alone.
TITLE_Y = (13, 28)
TITLE_X = (112, 420)

# Two-column map tables: the name cell, then the score cell, twice across.
MAP_L = (118, 210)
MAP_R = (288, 380)


def title(text: str) -> dict:
    return {"y": TITLE_Y, "text": [("body", text)], "bold": True, "x": TITLE_X}


def line(y, text, **kw) -> dict:
    spans = text if isinstance(text, list) else [("body", text)]
    return {"y": y, "text": spans, **kw}


def map_rows(bands, first: int) -> list[dict]:
    """Two map names per row, left column then right, running in pairs."""
    out = []
    index = first
    for band in bands:
        for window in (MAP_L, MAP_R):
            out.append({"y": band, "text": [("body", map_names.NAMES[index])],
                        "x": window, "pad": 1})
            index += 1
    return out


def cells(bands, windows, names, **kw) -> list[dict]:
    """A grid of short labels, filled left to right and then down."""
    out = []
    values = list(names)
    for band in bands:
        for window in windows:
            if not values:
                return out
            out.append({"y": band, "text": [("body", values.pop(0))],
                        "x": window, **kw})
    return out


PAGES: dict[str, list[dict]] = {}

PAGES["histor1"] = [
    title(TITLE_RANK),
    line((54, 63), "마스터 랭크", x=(112, 320)),
]

PAGES["histor2"] = [
    title(TITLE_HELP),
    line((49, 59), "■전적과 마스터 랭크", bold=True),
    line((72, 81), "『전적』이란 지금까지의 전투 결과와, 전투를 통해"),
    line((86, 95), "달성한 각종 항목을 모은 당신 자신의 싸움의 기록입니다."),
    line((100, 109), "이 기록에 따라 당신에게 걸맞은 칭호——"),
    line((114, 123), [("red", "『마스터 랭크』"), ("body", "가 주어지게 됩니다.")]),
    line((129, 138), [("blue", "⇒마스터 랭크［랭크표］참조")], align="right"),
    line((142, 152), "■평가 방법에 대해", bold=True),
    line((164, 173), [("body", "평가는 크게 나눠 "), ("red", "『전투 평가 포인트』"), ("body", "와")]),
    line((180, 189), [("red", "『보너스 포인트』"), ("body", " 두 가지 기준으로 판정합니다.")]),
    line((196, 205), "이 두 포인트를 합한 토탈 값으로,"),
    line((212, 221), "마스터 랭크를 판정합니다."),
]

PAGES["histor3"] = [
    title(TITLE_HELP),
    line((49, 59), "■포인트의 구분", bold=True),
    line((75, 85), "【전투 평가 포인트】", bold=True),
    line((93, 102), "각 모드의 맵 단위 전투를"),
    line((109, 118), "특정 기준으로 평가해 얻을 수 있는 포인트입니다."),
    line((125, 134), [("blue", "⇒［전투 평가 기준］참조")], align="right"),
    line((137, 147), "【보너스 포인트】", bold=True),
    line((156, 165), "전투를 거듭하는 중에 특정 조건을 채웠을 때,"),
    line((172, 181), "얻을 수 있는 포인트입니다."),
    line((188, 197), "보너스 포인트에는,"),
    line((204, 213), [("red", "누적형과 달성형"), ("body", " 두 가지 타입이 있습니다.")]),
]

PAGES["histor4"] = [
    title(TITLE_HELP),
    line((49, 59), "■보너스 포인트의 종류", bold=True),
    line((65, 74), "보너스 포인트는 아래 ２종류로 크게 나뉩니다."),
    line((86, 96), "【누적형】", bold=True),
    line((105, 114), "시나리오／엑스퍼트 모드에서 적 마스터를 쓰러뜨렸을 때"),
    line((119, 128), "얻는 포인트입니다."),
    line((133, 142), "마스터를 바꿀 때마다 목록의 체크가 초기화되어,"),
    line((147, 156), [("red", "몇 번이든 포인트를 얻을 수 있습니다.")]),
    line((162, 171), [("blue", "⇒보너스 ｐｔ［격파 이력①~③］참조")], align="right"),
    line((184, 194), "【달성형】", bold=True),
    line((201, 210), "시나리오／엑스퍼트／프리 모드에서 특정 조건을"),
    line((215, 224), "달성했을 때 얻는 포인트입니다."),
    line((229, 238), [("red", "포인트는 한 번만 얻을 수 있습니다.")]),
]

# --- the rank table ---------------------------------------------------------
RANK_ROWS = [
    ("밴티지 마스터", "최고위 칭호를 얻은 마스터"),
    ("샤이닝 마스터", "빛을 두른 고귀한 마스터"),
    ("레전드 마스터", "세상에 전해지는 전설의 마스터"),
    ("그랜드 마스터", "천하를 누비는 무쌍의 마스터"),
    ("네이티얼 마스터", "《멜렛》을 이은 마스터"),
    ("그레이트 마스터", "전장을 내달리는 노도의 마스터"),
    ("슈퍼 마스터", "이미 일류. 인정받은 마스터"),
    ("엑설런트 마스터", "활약이 눈부신 주목의 마스터"),
    ("칙 마스터", "경험을 쌓은 베테랑 마스터"),
    ("비기너 마스터", "앞날이 기대되는 신인 마스터"),
    ("쁘띠 마스터", "아직 풋내기 마스터"),
]
RANK_NAME_X = (130, 258)
RANK_TEXT_X = (272, 448)
PAGES["histor5"] = [
    title(TITLE_RANKS),
    line((55, 64), "마스터 랭크", x=RANK_NAME_X, pad=1),
    line((55, 64), "해설", x=RANK_TEXT_X, pad=1),
]
for _i, (_name, _desc) in enumerate(RANK_ROWS):
    _top = 72 + _i * 16
    PAGES["histor5"].append(line((_top, _top + 10), _name, x=RANK_NAME_X, pad=1))
    PAGES["histor5"].append(line((_top, _top + 10), _desc, x=RANK_TEXT_X, pad=1))

# --- the map score tables ---------------------------------------------------
PAGES["histor6"] = [
    title(f"{TITLE_SCORE}（시나리오 모드）"),
    line((44, 61), "시나리오 모드（Normal/Hard）", x=(112, 330)),
    *map_rows([(74, 88), (93, 108), (112, 127), (131, 146),
               (150, 164), (169, 183), (188, 203), (207, 222)], 0),
]

PAGES["histor7"] = [
    title(f"{TITLE_SCORE}（시나리오 모드）"),
    *map_rows([(50, 64), (69, 83), (88, 102), (107, 121),
               (126, 140), (145, 159), (164, 178)], 16),
]

PAGES["histor8"] = [
    title(f"{TITLE_SCORE}（엑스퍼트 모드）"),
    line((44, 61), "엑스퍼트 모드", x=(112, 330)),
    *map_rows([(74, 88), (93, 108), (112, 127), (131, 146)], 30),
]

PAGES["histor9"] = [
    title(f"{TITLE_SCORE}（프리 모드）"),
    line((44, 61), "프리 모드", x=(112, 330)),
    *map_rows([(74, 88), (93, 108), (112, 127), (131, 146),
               (150, 164), (169, 183), (188, 203), (207, 222)], 0),
]

PAGES["histor10"] = [
    title(f"{TITLE_SCORE}（프리 모드）"),
    *map_rows([(50, 64), (69, 83), (88, 102), (107, 121), (126, 140),
               (145, 159), (164, 178), (183, 197), (202, 216), (221, 235)], 16),
]

PAGES["histor11"] = [
    title(f"{TITLE_SCORE}（프리 모드）"),
    *map_rows([(50, 64), (69, 83), (88, 102), (107, 121),
               (126, 140), (145, 159), (164, 178), (183, 197)], 36),
]

PAGES["histor12"] = [
    title(TITLE_BONUS),
    line((66, 77), "보너스 포인트 합계", x=(112, 340)),
    line((233, 245), "＝ 달성함", x=(146, 260)),
]

# --- the defeat history -----------------------------------------------------
KILL_L = (118, 248)
KILL_R = (290, 452)
PAGES["histor13"] = [
    title(TITLE_KILLS),
    line((43, 57), "적 마스터 격파 이력（시나리오 모드）", x=(118, 380)),
    *cells([(105, 114), (118, 128)], [KILL_L, KILL_R], MASTERS["scenario"][:4]),
    *cells([(152, 161), (166, 175)], [KILL_L, KILL_R], MASTERS["scenario"][4:8]),
    *cells([(198, 207), (212, 221), (226, 235)], [KILL_L, KILL_R],
           MASTERS["scenario"][8:]),
    line((244, 256), "＝ 격파함", x=(146, 260)),
]

PAGES["histor14"] = [
    title(TITLE_KILLS),
    *cells([(58, 67), (72, 81), (86, 95)], [KILL_L, KILL_R],
           MASTERS["phase456"][:5]),
    *cells([(117, 127), (132, 141), (145, 155), (160, 169)], [KILL_L, KILL_R],
           MASTERS["phase456"][5:13]),
    *cells([(190, 199), (204, 213)], [KILL_L, KILL_R], MASTERS["phase456"][13:]),
    line((244, 256), "＝ 격파함", x=(146, 260)),
]

PAGES["histor15"] = [
    title(TITLE_KILLS),
    line((43, 57), "적 마스터 격파 이력（엑스퍼트 모드）", x=(118, 400)),
    *cells([(108, 117), (122, 131), (136, 145), (150, 159)], [KILL_L, KILL_R],
           MASTERS["expert"]),
    line((244, 256), "＝ 격파함", x=(146, 260)),
]

# --- the clear history ------------------------------------------------------
CLEAR_LABEL = "클리어한 마스터（시나리오／엑스퍼트）"
CLEAR3 = [(112, 196), (220, 316), (340, 436)]
CLEAR2 = [(140, 248), (277, 383)]
PAGES["histor16"] = [
    title(TITLE_CLEAR),
    line((43, 57), CLEAR_LABEL, x=(118, 400)),
    *cells([(75, 87), (99, 111), (122, 134), (145, 157), (167, 179), (191, 203)],
           CLEAR3, CLASSES[:18], pad=1),
    line((246, 257), "＝ 클리어", x=(146, 260)),
]

PAGES["histor17"] = [
    title(TITLE_CLEAR),
    line((43, 57), CLEAR_LABEL, x=(118, 400)),
    *cells([(75, 87), (98, 110), (121, 133), (144, 156), (167, 179)],
           CLEAR2, CLASSES[18:], pad=1),
    line((246, 257), "＝ 클리어", x=(146, 260)),
]

# --- the single-count bonus pages ------------------------------------------
COUNT_PAGES = [
    ("histor18", "전투의 행동 보너스", "각 항목의 카운트 값", (112, 330)),
    ("histor19", "네이티얼 격파 보너스", "네이티얼 격파 수", (112, 330)),
    ("histor20", "소환수・땅", "땅의 네이티얼 소환수", (140, 340)),
    ("histor21", "소환수・물", "물의 네이티얼 소환수", (140, 340)),
    ("histor22", "소환수・불", "불의 네이티얼 소환수", (140, 340)),
    ("histor23", "소환수・하늘", "하늘의 네이티얼 소환수", (140, 340)),
]
for _stem, _title, _label, _window in COUNT_PAGES:
    PAGES[_stem] = [
        title(_title),
        line((44, 61), _label, x=_window),
        line((233, 245), "＝ 달성함", x=(146, 260)),
    ]

# --- the scoring standard ---------------------------------------------------
STD_L = (112, 246)
STD_R = (248, 464)
PAGES["histor24"] = [
    title(TITLE_STANDARD),
    line((48, 58), "■전투 평가 포인트의 평가 항목", bold=True),
    line((66, 75), "아래 ３가지 항목을 각 모드별로 맵 단위로 판정해,"),
    line((80, 89), "결과를 점수로 환산합니다. 각 항목의 자세한 설명은 아래와 같습니다."),
    line((103, 113), "① 소요 시간", x=STD_L),
    line((103, 113), "…적은 소요 시간으로 클리어하면 고득점.", x=STD_R),
    line((118, 127), "（최대 ６０점）", x=STD_L),
    line((118, 127), "『빠름, 표준, 느림』 ３단계로 판정.", x=STD_R),
    line((141, 151), "② 마정석 점거 수", x=STD_L),
    line((141, 151), "…더 많은 마정석을 점거하고 클리어하면", x=STD_R),
    line((155, 164), "（최대 ３０점）", x=STD_L),
    line((155, 164), "고득점. 『점거한 수／전체 수』로 산정해,", x=STD_R),
    line((169, 178), "비율에 따라 ４단계로 판정.", x=STD_R),
    line((189, 200), "③ 소비 MP 효율", x=STD_L),
    line((189, 200), "…적보다 MP를 덜 쓰고 클리어하면 고득점.", x=STD_R),
    line((203, 212), "（최대 ２０점）", x=STD_L),
    line((203, 212), "『상대 소비 MP／자신 소비 MP』로 산정해,", x=STD_R),
    line((217, 226), "비율에 따라 ５단계로 판정.", x=STD_R),
    line((236, 244), [("red", "（주）　합계 점수는 １００점에서 멈춥니다.")]),
]

PAGES["histor25"] = [
    title(TITLE_STANDARD),
    line((48, 58), "■공략 랭크와 획득 포인트", bold=True),
    line((67, 76), "맵 단위로 산정된 득점에서,"),
    line((81, 90), "그 맵에 대한 당신의 『공략 랭크』를 인정하고,"),
    line((95, 104), "랭크에 맞는 포인트를 획득합니다."),
    line((119, 129), "득점", x=(140, 236), pad=1),
    line((119, 129), "공략 랭크", x=(240, 344), pad=1),
    line((119, 129), "획득 포인트", x=(348, 452), pad=1),
    # The score column is the only cell with a Japanese unit in it.
    line((136, 146), "100~95점", x=(172, 248), pad=1),
    line((152, 162), "90~85점", x=(172, 248), pad=1),
    line((167, 177), "80~60점", x=(172, 248), pad=1),
    line((182, 192), "55~10점", x=(172, 248), pad=1),
    line((207, 215), [("red", "（주）　위 획득 포인트는 시나리오 모드(노멀)의 경우.")]),
    line((221, 228), [("red", "시나리오 모드(하드)의 경우는 ×2배,")], x=(160, 464)),
    line((235, 242), [("red", "엑스퍼트 모드에서는 ×5배가 됩니다.")], x=(160, 464)),
]

PAGES["histor26"] = [
    title(TITLE_STANDARD),
    line((48, 58), "■공략 랭크의 갱신", bold=True),
    line((65, 74), "공략 랭크 표기는 랭크가 오를 때만 정보가 갱신되어,"),
    line((80, 89), "이후에는 늘 최고 평가가 반영된 상태가 됩니다."),
    line((95, 104), "또한 공략 랭크가 갱신되지 않아도, 전투 평가 포인트는"),
    line((110, 119), [("red", "맵을 클리어할 때마다 매번 획득할 수 있습니다.")]),
    line((129, 139), [("red", "기록은 갱신된다")], x=(355, 462)),
    line((144, 157), "이전 랭크", x=(123, 212), pad=1),
    line((144, 157), "이번 랭크", x=(227, 316), pad=1),
    line((144, 157), "전적의 기록", x=(358, 430), pad=1),
    line((192, 205), "이전 포인트", x=(123, 212), pad=1),
    line((192, 205), "이번 포인트", x=(227, 316), pad=1),
    line((192, 205), "평가 포인트", x=(353, 438), pad=1),
    line((236, 246), [("red", "포인트는 누적된다")], x=(330, 462)),
]

PAGES["histor27"] = [
    title(TITLE_STANDARD),
    line((48, 58), "■프리 모드의 평가 조건", bold=True),
    line((68, 77), "프리 모드의 경우는,"),
    line((82, 91), "플레이어가 아래 조건을 만족한 경우에만,"),
    line((96, 105), "『전적』으로 반영되어 포인트를 얻을 수 있습니다."),
    line((128, 137), "1. USER 대 COM, COM 대 USER 전투일 것."),
    line((146, 155), "2. 레벨 설정이 기본값（LV25）일 것."),
    line((164, 173), "3. 자신이나 상대의 파라미터 값을 바꾸지 않았을 것."),
    line((182, 191), "4. 아이템과 마법을 전부 쓸 수 있는 상태일 것."),
    line((221, 229), [("red", "（주）　자신이나 상대 마스터의 클래스・이름 변경은 조건에 없으므로,")]),
    line((235, 243), [("red", "자유롭게 설정할 수 있습니다.")], x=(140, 464)),
]

PAGES["histor28"] = [
    title(TITLE_STANDARD),
    line((48, 58), "■전투 시 설정에 대해", bold=True),
    line((67, 76), "전투 평가 포인트는, 적 사고 타입이 「통상」 설정으로"),
    line((82, 91), "되어 있는 것을 기준으로 삼습니다."),
    line((97, 106), "그래서 「방어 경시」로 설정된 상태로"),
    line((112, 121), "전투를 끝내면, 평가가 통상보다 내려가 버립니다."),
    line((130, 139), "예를 들어 Ｓ랭크 기준을 달성했더라도,"),
    line((145, 154), "전투 평가에서는 한 랭크 아래 평가 「S-」가 됩니다."),
    line((160, 169), "포인트도 기준값에서 「-1pt」 됩니다."),
    # The switch bar below is a screenshot of the battle-setup strip rather
    # than a caption: its plates are only 12px tall and sit shoulder to
    # shoulder, and clearing them takes the plate with the label.
    line((235, 243), [("red", "（주）　보유 시간 설정을 바꿔도 평가에 영향은 없습니다.")]),
]

# The manual proper lives in its own module; it is the larger half of the book.
PAGES.update(manual_pages.PAGES)
