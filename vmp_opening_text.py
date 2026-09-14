# -*- coding: utf-8 -*-
"""Korean text for Vantage Master Portable's opening.

Every entry is ``(label, offset, korean)``; the Japanese source is read back
from the executable at build time, so nothing here has to be transcribed by
hand.  Offsets are into the decrypted ELF that the ISO stores as BOOT.BIN.
"""

from __future__ import annotations

# --- title screen and mode selection ---------------------------------------

MODE_SELECT: list[tuple[str, int, str]] = [
    ("yes", 0x161C7C, "예"),
    ("no", 0x161C84, "아니오"),
    ("confirm", 0x161C8C, "결정"),
    ("suspend load warning", 0x161CC4,
     "중단 데이터는 한 번 불러오면 삭제됩니다. 불러오시겠습니까?"),
    ("new game", 0x161D0C, "새로 게임을 시작합니다."),
    ("continue", 0x161D28, "게임 데이터를 불러와 이어서 진행합니다."),
    ("scenario mode", 0x161D5C, "【시나리오】 이야기를 따라 진행하는 모드입니다."),
    ("start from beginning", 0x161D90, "처음부터 시작합니다."),
    ("scenario normal", 0x161DAC,
     "【노멀】 표준 난이도입니다. 해볼 만한 전투를 즐길 수 있습니다."),
    ("scenario hard", 0x161DF0,
     "【하드】 난이도가 높습니다. 짜릿한 전투를 즐길 수 있습니다."),
    ("sora no kiseki cast", 0x161E30, "『하늘의 궤적』 캐릭터로 플레이합니다."),
    ("expert normal", 0x161E5C,
     "【노멀】 초기 레벨 １０. 초보자도 안심인 난이도입니다."),
    ("expert hard", 0x161E98,
     "【하드】 초기 레벨 １０. 중급자 이상에게 권장하는 난이도."),
    ("expert mode", 0x161ED4, "【엑스퍼트】 궁극의 전투가 모인 특별 모드입니다."),
    ("expert start", 0x161F0C, "처음부터 공략을 시작합니다. 초상급자용."),
    ("expert cast", 0x161F38,
     "『하늘의 궤적』 캐릭터로 플레이. 상급자 이상에게 권장."),
    ("free mode", 0x161F78, "【프리】 원하는 맵을 골라 자유롭게 싸우는 모드입니다."),
    ("network mode", 0x161FBC, "【네트워크】 네트워크로 대전할 수 있는 모드입니다."),
    ("resume battle", 0x161FFC, "지난번 저장한 전투 상황을 불러와 게임을 재개합니다."),
    ("system menu", 0x162038, "시스템 메뉴를 엽니다."),
    ("back to title", 0x162058, "모드 선택을 끝내고 타이틀로 돌아갑니다."),
]

# --- name entry -------------------------------------------------------------

NAME_ENTRY: list[tuple[str, int, str]] = [
    ("symbols", 0x166138, "기호"),
    ("hiragana", 0x166140, "히라가나"),
    ("katakana", 0x16614C, "가타카나"),
    ("alphanumeric", 0x166158, "영숫자"),
    ("decide", 0x166160, "결정"),
    ("backspace", 0x166168, "한글자삭제"),
    ("default", 0x166174, "기본값"),
    ("quit", 0x166180, "종료"),
    ("sample", 0x166188, "★샘플"),
    ("name prompt", 0x1661A4, "이름을 입력하세요."),
]

# --- class and card selection ----------------------------------------------

SELECTION_PROMPTS: list[tuple[str, int, str]] = [
    ("class prompt", 0x1645F4, "클래스를 선택하세요."),
    ("master confirmation", 0x1646BC, "이 마스터로 하시겠습니까?"),
]

# (offset, class name, poetic line).  Both lines share one template.
CLASS_INTROS: list[tuple[int, str, str]] = [
    (0x163550, "파이터", "힘과 무의 틈에서 흔들리는 꿈"),
    (0x16359C, "듀크", "꿈의 실현에 쏟아지는 힘"),
    (0x1635E4, "소드맨", "운명 속의 무한한 힘"),
    (0x16362C, "나이트", "힘 있는 신뢰와 꿈"),
    (0x16366C, "팔라딘", "이 세상에 희망을 가져오는 자"),
    (0x1636B8, "섀도", "어둠 속에 숨 쉬는 운명"),
    (0x1636FC, "레인저", "꿈과 이상을 좇는 희망"),
    (0x163744, "새비지", "운명에 맞서는 존재"),
    (0x16378C, "시프", "꿈과 숙업 사이에 흔들리는 그림자"),
    (0x1637D4, "바드", "미와 꿈을 연주하는 허공"),
    (0x163818, "시스터", "이 세상의 어둠을 비추는 빛"),
    (0x163860, "소서러", "진실을 추구하는 숙업"),
    (0x1638A8, "위치", "신뢰의 아름다움이 낳는 꿈"),
    (0x1638F4, "몽크", "끝없는 신앙 속의 무"),
    (0x16393C, "스피릿", "존재를 믿는 꿈"),
    (0x163980, "비스트", "환몽을 알리는 힘"),
    (0x1639C4, "나이트메어", "어둠을 가리키는 무"),
    (0x163A08, "프로일라인", "빛 속의 꿈"),
    (0x163A48, "로드마스터", "사람들에게 용기를 주는 빛"),
    (0x163A98, "스트라이더", "세상의 어둠을 부수려는 이빨"),
    (0x163AE4, "플레이보이", "아름다움을 좇는 환영"),
    (0x163B28, "프린세스", "힘과 신뢰를 아는 운명"),
    (0x163B70, "테크노크라트", "끝없는 꿈을 좇는 자"),
    (0x163BBC, "헤비에지", "희망을 힘으로 삼는 존재"),
    (0x163C04, "지니어스", "빛과 어둠 사이의 허무"),
    (0x163C50, "퀸뷰트", "꿈과 운명을 응시하는 어스름"),
    (0x163C9C, "다크나이트", "세상에 진실을 묻는 수라"),
    (0x163CE8, "그래플러", "무 속의 빛을 아는 자"),
]

# Longest form first; the builder falls back when a field runs out of room.
CLASS_TEMPLATES = (
    "당신은 {poem}.\n{cls}로서 이 세계에 이끌려 왔습니다.",
    "당신은 {poem}.\n{cls}로서 이 세계에 왔습니다.",
    "당신은 {poem}.\n{cls}로서 이곳에 왔습니다.",
)

CARDS: list[tuple[str, int, str]] = [
    ("card Shine", 0x163D30, "빛과 밝음, 정의를 뜻합니다."),
    ("card Twilight", 0x163D74, "어스름과 불안, 중립을 뜻합니다."),
    ("card Shade", 0x163DC0, "그늘과 어둠, 사악함을 뜻합니다."),
    ("card Sacred Book", 0x163E04, "신앙과 경건한 마음, 평온을 나타냅니다."),
    ("card Emblem", 0x163E54, "명예, 힘, 충성, 전투를 뜻합니다."),
    ("card Fair", 0x163E9C, "아름다움과 명성, 집착을 뜻합니다."),
    ("card Dream", 0x163EE0, "환상과 가공을 뜻합니다."),
    ("card Karma", 0x163F20, "현실과 운명을 뜻합니다."),
    ("card Trust", 0x163F60, "신뢰와 인간관계, 배려를 뜻합니다."),
    ("card Vacant", 0x163FAC, "무와 공허를 뜻합니다."),
    ("card Ego", 0x163FE8, "자아와 자기 과시를 뜻합니다."),
]

# The card name stays in Latin script, exactly as the Japanese field has it.
CARD_TEMPLATE = "당신이 고른 것은 {name} 카드.\n{meaning}"

# --- master aptitude lines --------------------------------------------------

APTITUDES: list[tuple[str, int, str]] = [
    ("aptitude atk/def/spd", 0x1629A0,
     "당신은 공격력과 방어력, 민첩함이 뛰어납니다.\n마력이 낮고 마법 방어가 부족하지만,\n마스터의 자질은 충분합니다."),
    ("aptitude mag/spd", 0x162A14,
     "당신은 마력과 민첩함이 있습니다.\n마법 방어와 이동력이 다소 부족하지만,\n마스터의 자질은 충분합니다."),
    ("aptitude atk/mag", 0x162A7C,
     "당신은 공격력과 마력이 있습니다.\n방어력이 낮다는 결점은 있지만,\n마스터의 자질은 충분합니다."),
    ("aptitude atk/def/mdef", 0x162AE8,
     "당신은 높은 공격력과 방어력, 마법 방어를\n지녔습니다. 마력과 민첩함이 부족하지만,\n마스터의 자질은 충분합니다."),
    ("aptitude atk/def/mag", 0x162B5C,
     "당신은 공격력과 방어력, 마력이 뛰어납니다.\n느리다는 결점은 있지만,\n마스터의 자질은 충분합니다."),
    ("aptitude spd/mov/range", 0x162BC4,
     "당신은 민첩함과 이동력, 원거리 공격을\n지녔습니다. 마법 방어력은 부족하지만\n마스터의 자질은 충분합니다."),
    ("aptitude balanced bow", 0x162C34,
     "당신은 특별히 뛰어난 능력은 없지만\n약점도 없습니다. 그 활이 도움이 될 것입니다.\n마스터의 자질은 충분합니다."),
    ("aptitude atk/def/spd/mov", 0x162CA8,
     "당신은 공격력, 방어력, 민첩함, 이동력이\n뛰어납니다. 마력은 떨어지지만\n마스터의 자질은 충분합니다."),
    ("aptitude spd/mov", 0x162D18,
     "당신은 민첩함과 이동력이 뛰어납니다.\n방어력과 마력은 떨어지지만\n마스터의 자질은 충분합니다."),
    ("aptitude mag only", 0x162D80,
     "당신은 마력이 뛰어납니다.\n방어력과 마법 방어가 부족하지만\n마스터의 자질은 충분합니다."),
    ("aptitude mag/mdef", 0x162DDC,
     "당신은 마력과 마법 방어가 뛰어납니다.\n민첩함이 떨어지는 결점은 있지만\n마스터의 자질은 충분합니다."),
    ("aptitude high mag", 0x162E44,
     "당신은 높은 마력을 타고났습니다.\n낮은 민첩함과 방어력, 이동력이 결점이지만\n마스터의 자질은 충분합니다."),
    ("aptitude mag, low def", 0x162EB0,
     "당신은 마력이 뛰어납니다.\n방어력과 민첩함은 낮지만,\n마스터의 자질은 충분합니다."),
    ("aptitude balanced", 0x162F0C,
     "당신은 균형 잡힌 능력을 지녔습니다.\n특별히 결점이 되는 점은 없습니다.\n마스터의 자질은 충분합니다."),
    ("aptitude mag/mov", 0x162F7C,
     "당신은 마력과 이동력이 뛰어납니다.\n낮은 방어력이 결점이지만,\n마스터의 자질은 충분합니다."),
    ("aptitude atk/mag/mov", 0x162FD8,
     "당신은 공격력과 마력, 이동력이 뛰어납니다.\n마법 방어력은 낮지만,\n마스터의 자질은 충분합니다."),
    ("aptitude mag/mdef high", 0x163044,
     "당신은 마력과 마법 방어가 뛰어납니다.\n방어력이 낮은 것이 결점이지만,\n마스터의 자질은 충분합니다."),
    ("aptitude mdef/spd", 0x1630AC,
     "당신은 마법 방어와 민첩함이 있습니다.\n공격력과 방어력은 부족하지만\n마스터의 자질은 충분합니다."),
    ("aptitude atk/spd", 0x163110,
     "당신은 공격력과 민첩함이 뛰어납니다.\n마력이 다소 낮은 결점이 있지만,\n마스터의 자질은 충분합니다."),
    ("aptitude high mag/spd", 0x16317C,
     "당신은 높은 마력과 민첩함을 지녔습니다.\n방어력이 다소 부족하지만,\n마스터의 자질은 충분합니다."),
    ("aptitude mag/ranged", 0x1631E4,
     "당신은 높은 마력과 원거리 공격을 지닙니다.\n방어력이 낮고 민첩함이 부족하지만,\n마스터의 자질은 충분할 것입니다."),
    ("aptitude very high mag/mdef", 0x163258,
     "당신은 매우 높은 마력과 마법 방어를\n지녔습니다. 물리 면은 뒤떨어지지만,\n마스터의 자질은 충분합니다."),
    ("aptitude average cannon", 0x1632C4,
     "당신은 평균적인 능력을 지녔습니다.\n방어력은 떨어지지만 도력포가 도움이 될\n것입니다. 마스터의 자질은 충분합니다."),
    ("aptitude very high atk/def", 0x16333C,
     "당신은 매우 높은 공격력과 방어력을\n지녔습니다. 마력이 다소 부족하지만,\n마스터의 자질은 충분합니다."),
    ("aptitude strongest mag", 0x1633A8,
     "당신은 최강의 마력과 전반적으로 높은\n능력을 지닙니다. 방어력은 부족하지만,\n마스터의 자질은 충분합니다."),
    ("aptitude all-round high", 0x163414,
     "당신은 전반적으로 높은 능력을 지녔습니다.\n안정적인 전투가 가능할 것입니다.\n마스터의 자질은 충분합니다."),
    ("aptitude highest all", 0x163484,
     "당신은 모든 면에서\n매우 높은 능력을 지녔습니다.\n마스터의 자질은 충분할 것입니다."),
    ("aptitude atk/def/spd top", 0x1634E4,
     "당신은 매우 높은 공격・방어・민첩함을\n지녔습니다. 마력은 부족하지만,\n마스터의 자질은 충분합니다."),
]

# --- Mellett's prologue -----------------------------------------------------

PROLOGUE: list[tuple[str, int, str]] = [
    ("Mellett introduction", 0x164028,
     "저는 《보랏빛 멜렛》.\n네이티얼 마스터라 불리는 존재입니다."),
    ("question", 0x16406C, "……그럼, 아까 그\n질문의 답은 정하셨나요?"),
    ("wish", 0x16409C,
     "그래요, 강해지고 싶다는 거군요.\n당신의 그 소망,\n받아들이도록 하죠."),
    ("ask about player", 0x1640EC, "먼저,\n당신에 대해 들려주세요."),
    ("understood", 0x164114, "당신에 대해 대략 알았습니다."),
    ("master explanation", 0x164138, "（마스터 설명）"),
    ("grant four Neatials", 0x16414C,
     "그럼 기본이 되는\n네 종류의 네이티얼을\n당신에게 드리겠습니다."),
    ("go", 0x164190, "자, 가 볼까요.\n강해지기 위해서."),
    ("returning player", 0x1641B8, "더 강해지기를 바라며,\n당신은 이곳에 왔군요.\n"),
    ("returning wish", 0x1641EC, "당신의 그 소망,\n받아들이도록 하죠."),
    ("returning understood", 0x164218, "당신에 대해 대략 알았습니다."),
    ("grant all Neatials", 0x16423C,
     "２４종의 네이티얼과,\n６가지 마법.\n그 모두를 당신에게 맡깁니다."),
    ("returning go", 0x164284, "그럼 가 볼까요.\n위대한 싸움의 장으로."),
]

# --- the four starting items ------------------------------------------------

STARTING_ITEMS: list[tuple[str, int, str]] = [
    ("Koma item", 0x1642B0, "【인형 팽이】를 손에 넣었다.\n꼭두각시 모양의 팽이."),
    ("Koma description", 0x1642E8,
     "절묘한 균형을 유지하며 도는 모습은\n보는 이에게 평온함을 준다.\n땅의 네이티얼, 파・란셀을 소환할 수 있다."),
    ("bottle item", 0x164354,
     "【병 속의 배】를 손에 넣었다.\n어떻게 넣었는지는 알 수 없지만,\n정교한 배 모형이 든 작은 병 장식품."),
    ("bottle description", 0x1643BC,
     "어떻게 놓아도 안의 작은 배는 가라앉지 않고,\n항상 안정적으로 떠 있다고 한다.\n물의 네이티얼, 레큐를 소환할 수 있다."),
    ("hammer item", 0x164434,
     "【적동 대망치】를 손에 넣었다.\n신화 시대에 벼려졌다는 적동 대망치."),
    ("hammer description", 0x164480,
     "대장장이 신의 힘이 깃들어 있어,\n휘두르면 쇠도 녹일 고열을 낸다고 한다.\n불의 네이티얼, 헤피타스를 소환할 수 있다."),
    ("sakaki staff item", 0x1644F4,
     "【신목 지팡이】를 손에 넣었다.\n제례에 쓰는 지팡이."),
    ("sakaki staff description", 0x16452C,
     "본래는 마를 물리치는 데 쓰였으며,\n휘두르면 하늘의 사자가 나타난다고 한다.\n하늘의 네이티얼, 규네・포스를 소환할 수 있다."),
    ("Koma item/status description", 0x16664C,
     "꼭두각시 모양의 팽이.\n절묘한 균형을 유지하며 도는 모습은\n보는 이에게 평온함을 준다.\n땅의 네이티얼, 파・란셀을 소환할 수 있다."),
    ("bottle item/status description", 0x166ABC,
     "어떻게 넣었는지는 알 수 없지만,\n정교한 배 모형이 든 작은 병 장식품.\n어떻게 놓아도 안의 작은 배는 가라앉지 않고,\n항상 안정적으로 떠 있다고 한다.\n물의 네이티얼, 레큐를 소환할 수 있다."),
    ("hammer item/status description", 0x166FA0,
     "신화 시대에 벼려졌다는 적동 대망치.\n대장장이 신의 힘이 깃들어 있어,\n휘두르면 쇠도 녹일 고열을 낸다고 한다.\n불의 네이티얼, 헤피타스를 소환할 수 있다."),
    ("sakaki staff item/status description", 0x167628,
     "제례를 올릴 때 쓰는 지팡이.\n본래는 마를 물리치는 데 쓰였으며,\n휘두르면 하늘의 사자가 나타난다고 한다.\n하늘의 네이티얼, 규네・포스를 소환할 수 있다."),
    ("Koma item name", 0x166640, "인형 팽이"),
    ("bottle item name", 0x166AB0, "병 속의 배"),
    ("hammer item name", 0x166F94, "적동대망치"),
    ("sakaki staff item name", 0x16761C, "신목지팡이"),
]

# --- the tutorial battle ----------------------------------------------------

TUTORIAL: list[tuple[str, int, str]] = [
    ("magic HP heal", 0x15E0AC, "ＨＰ 회복 마법을 씁니다.\n【소비ＭＰ ： %d】"),
    ("magic gold", 0x15E0DC, "상태이상 마법（금화）을 씁니다.\n【소비ＭＰ ： %d】"),
    ("magic silver", 0x15E114, "상태이상 마법（은화）을 씁니다.\n【소비ＭＰ ： %d】"),
    ("magic freeze", 0x15E14C, "상태이상 마법（동결）을 씁니다.\n【소비ＭＰ ： %d】"),
    ("magic cure", 0x15E184, "상태이상 회복 마법을 씁니다.\n【소비ＭＰ ： %d】"),
    ("magic attack", 0x15E1B8, "공격 마법을 씁니다.\n【소비ＭＰ ： %d】"),
    ("movement tutorial", 0x15E1FC, "이동 범위를 표시하고 있습니다.\n목표 지점을 선택하세요."),
    ("movement range detail", 0x15E238,
     "１회 행동으로 이동 가능한 범위입니다.\n선택한 지점으로 가상 이동할 수 있습니다.\nＬ버튼으로 범위 표시 종류를 바꿉니다."),
    ("range target", 0x15E2BC, "사거리를 표시하고 있습니다.\n공격・마법의 대상을 선택하세요."),
    ("range goal", 0x15E2FC, "사거리를 표시하고 있습니다.\n공격・마법의 목표를 선택하세요."),
    ("summon range", 0x15E33C, "소환 가능 범위를 표시하고 있습니다.\n소환할 지점을 선택하세요."),
    ("effect range", 0x15E37C, "효과 범위를 표시하고 있습니다.\n○버튼을 누르면 마법을 실행합니다."),
    ("dismiss confirm", 0x15EBA4, "네이티얼을 소멸시키겠습니까?"),
    ("time over", 0x15EBD0, "%s의 시간이 끝났습니다."),
    ("water level back", 0x15EC18, "수위가 되돌아왔다."),
    ("return to world", 0x15EC2C, "대전을 끝내고 월드 화면으로 돌아갈까요?"),
    ("not enough MP", 0x15EC74, "ＭＰ가 부족합니다!"),
    ("not a master", 0x15EC88, "마스터가 아니므로 선택 불가."),
    ("unit limit", 0x15ECB0, "%G유닛 수가 상한에 도달하여\n더 이상 소환할 수 없습니다."),
    ("summon command", 0x15ECEC, "네이티얼을 소환합니다."),
    ("wait tutorial", 0x15ED08, "대기하여 행동을 종료합니다."),
    ("attack command", 0x15ED28, "공격을 합니다."),
    ("no magic", 0x15ED3C, "마법이 없어 선택할 수 없습니다."),
    ("magic command", 0x15ED68, "마법을 사용합니다."),
    ("unit info command", 0x15ED7C, "유닛의 상세 정보를 표시합니다."),
    ("show move range", 0x15EDA0, "이동 범위를 표시합니다."),
    ("show attack range", 0x15EDC0, "공격 사거리를 표시합니다."),
    ("show magic range", 0x15EDE0, "마법 사거리를 표시합니다."),
    ("show magic effect", 0x15EE00, "마법 효과 범위를 표시합니다."),
    ("show unit influence", 0x15EE24, "유닛의 영향 범위를 표시합니다."),
    ("show move+attack", 0x15EE48, "이동＋공격 사거리를 표시합니다."),
    ("show move+magic", 0x15EE6C, "이동＋마법 사거리를 표시합니다."),
    ("show move+effect", 0x15EE90, "이동＋마법 효과 범위를 표시합니다."),
    ("win", 0x15EFB4, "승리"),
    ("lose", 0x15EFBC, "패배"),
    ("draw", 0x15EFD4, "서로 쓰러졌습니다"),
    ("surrendered", 0x15EFE8, "%s 항복했습니다"),
    ("surrender confirm", 0x15EFFC, "항복하시겠습니까?"),
    ("defeat message", 0x16103C, "%s 패배했습니다."),
    ("draw message", 0x161050, "서로 쓰러졌습니다."),
    ("battle confirmation", 0x164D04, "전투를 시작합니다. 괜찮겠습니까?"),
    ("battle waiting", 0x164D28, "상대의 준비가 끝날 때까지 잠시 기다려 주세요."),
    ("unranked battle", 0x164D60, "전적에 반영되지 않는 전투입니다. 괜찮습니까?"),
    ("battle confirmation duplicate", 0x16D090, "전투를 시작합니다. 괜찮겠습니까?"),
    ("no earth Neatial", 0x1661C0, "땅의 네이티얼이 없습니다.\n"),
    ("no water Neatial", 0x1661E8, "물의 네이티얼이 없습니다.\n"),
    ("no fire Neatial", 0x166210, "불의 네이티얼이 없습니다.\n"),
    ("no sky Neatial", 0x166238, "하늘의 네이티얼이 없습니다.\n"),
]


# --- system data, ranking and the pre-battle setup screen -------------------

SYSTEM_AND_SETUP: list[tuple[str, int, str]] = [
    ("memory stick missing", 0x162318, "메모리 스틱이 삽입되지 않았습니다."),
    ("system data created", 0x162588, "시스템 데이터 작성이 완료되었습니다."),
    ("checking system data", 0x16275C,
     "시스템 데이터를 확인하고 있습니다.\n메모리 스틱을 뽑지 마세요."),
    ("creating system data", 0x1627AC,
     "시스템 데이터를 새로 만들고 있습니다.\n메모리 스틱을 뽑지 마세요."),
    ("rank Vantage", 0x1604EC, "밴티지 마스터"),
    ("rank Shining", 0x160504, "샤이닝 마스터"),
    ("rank Legend", 0x16051C, "레전드 마스터"),
    ("rank Grand", 0x160530, "그랜드 마스터"),
    ("rank Neatial", 0x160544, "네이티얼 마스터"),
    ("rank Great", 0x16055C, "그레이트마스터"),
    ("rank Super", 0x160570, "슈퍼 마스터"),
    ("rank Excellent", 0x160584, "엑설런트 마스터"),
    ("rank Chick", 0x16059C, "칙 마스터"),
    ("rank Beginner", 0x1605AC, "비기너 마스터"),
    ("rank Petit", 0x1605C0, "쁘띠마스터"),
    ("result next", 0x1605D0, "다음"),
    ("result toggle", 0x1605D8, "표시전환"),
    ("result back", 0x1605E4, "뒤로"),
    ("AI type normal", 0x16BF60,
     "적의 사고 타입을 바꿉니다.\n현재는 통상 타입입니다."),
    ("AI type reckless", 0x16BF98,
     "적의 사고 타입을 바꿉니다.\n현재는 방어 경시 타입입니다.\n※통상 타입보다 난이도는 낮지만,\n　속공과 돌격에 주의가 필요합니다.\n　또한 전투 평가도 낮아집니다."),
    ("AI type unavailable", 0x16C044,
     "유저끼리의 대전이라\n사고 타입은 설정할 수 없습니다."),
    ("time short", 0x16C07C,
     "유저의 제한 시간을 바꿉니다.\n현재 설정은 쇼트.\n생각할 시간이 거의 없어\n난이도가 크게 올라갑니다.\n※전투 평가에는 영향이 없습니다."),
    ("time middle", 0x16C114,
     "유저의 제한 시간을 바꿉니다.\n현재 설정은 미들.\n생각할 시간이 넉넉하지 않아\n난이도가 꽤 올라갑니다.\n※전투 평가에는 영향이 없습니다."),
    ("time long", 0x16C1A4,
     "유저의 제한 시간을 바꿉니다.\n현재 설정은 롱.\n생각할 시간이 제한되어\n난이도가 올라갑니다.\n※전투 평가에는 영향이 없습니다."),
    ("time unlimited", 0x16C22C,
     "유저의 제한 시간을 바꿉니다.\n현재 설정은 무제한.\n제한 시간을 신경 쓰지 않고\n느긋하게 전략을 짤 수 있습니다.\n※전투 평가에는 영향이 없습니다."),
    ("time unavailable", 0x16C2C4,
     "컴퓨터끼리의 대전이라\n제한 시간은 설정할 수 없습니다."),
    ("map already cleared", 0x16C300, "이 맵은 이미 공략했습니다."),
    ("brightness change", 0x16C3DC, "밝기 변동"),
    ("always twilight", 0x16C3E8, "항상박명"),
    ("always bright", 0x16C3F4, "항상 밝음"),
    ("always dark", 0x16C400, "항상어둠"),
    ("obtained item", 0x16C40C, "획득 아이템:"),
    ("obtained none", 0x16C428, "　　　　　없음"),
    ("quit to title confirm", 0x16C4A0, "대전을 끝내고 타이틀로 돌아갈까요?"),
    ("back to title confirm", 0x16C4CC, "타이틀로 돌아갈까요?"),
]


EVENT_FILES: list[tuple[str, list[tuple[str, str]]]] = [
    (path, [
        ("私は《紫のメルレット》。", "저는 《보랏빛 멜렛》."),
        ("ネイティアルマスターと呼ばれる存在です。", "네이티얼 마스터라 불리는 존재입니다."),
    ])
    for path in (
        "/PSP_GAME/USRDIR/data/event/_asm/ev00219._as",
        "/PSP_GAME/USRDIR/data/pack/ev00219.dat",
        "/PSP_GAME/USRDIR/data/event/_asm/ev00125._as",
        "/PSP_GAME/USRDIR/data/pack/ev00125.dat",
    )
] + [
    (path, [("ふふ、私は《紫のメルレット》。", "후후, 저는 《보랏빛 멜렛》.")])
    for path in (
        "/PSP_GAME/USRDIR/data/event/_asm/ev00521._as",
        "/PSP_GAME/USRDIR/data/pack/ev00521.dat",
    )
]
