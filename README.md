# 밴티지 마스터 포터블 PSP 한글패치

일본판 PSP **ヴァンテージマスターポータブル / Vantage Master Portable (ULJM05332, v1.01)**용 비공식 한국어 패치입니다. 현재 배포판은 **v1.0.0**입니다. 이벤트 대사, 실행 파일의 메뉴·설명·튜토리얼, 맵 이름과 조언, 마스터·유닛·기술 이름, 갤러리·매뉴얼·설문 페이지와 UI 아틀라스에 구워진 글자까지 한국어로 표시하도록 글꼴, 실행 파일, 스크립트, 텍스처를 수정했습니다.

[최신 xdelta 다운로드](https://github.com/snake759494/vantage-master-portable-korean-patch/releases/latest) · [구현 및 수정 내역](docs/TECHNICAL.md) · [개발 소스 안내](docs/BUILD.md) · [변경 기록](CHANGELOG.md) · [권리 및 글꼴](RIGHTS.md)

릴리즈에 직접 첨부하는 파일은 **`VMP_Korean_v1.0.0.xdelta` 하나**입니다. 저장소에는 제작 소스, 자체 도구, 번역·검수 자료를 공개합니다. 원본·패치 적용 ISO, 추출한 게임 파일, 원본·수정 텍스처, 한글을 써넣은 글꼴 파일, 글꼴 TTF, 외부 실행 파일은 배포하지 않습니다. GitHub가 자동 생성하는 Source code ZIP/TAR는 저장소 소스의 압축본이며 게임 파일이 아닙니다.

## 게임 소개 및 대상 버전

밴티지 마스터는 日本ファルコム(Nihon Falcom)의 택틱스 RPG입니다. 두 마스터가 땅·물·불·천 네 속성의 정령 '네이티얼'을 소환해 맵을 두고 싸우며, 마정석을 점유해 MP 회복을 늘리고 상대 마스터의 HP를 0으로 만들면 이깁니다. 1997년 PC판을 바탕으로 한 PSP판은 2008년 4월 24일 일본에서 발매되었고, 마스터 18명 각자의 시나리오와 『하늘의 궤적』 캐릭터가 추가되었습니다. [팔콤 공식 사이트](https://www.falcom.co.jp/vmp/), [작품 정보](https://www.falcom.co.jp/games-data/vmp).

이 패치는 **PSP 일본판 v1.01 ISO**에만 적용합니다. PC판·PS2판(VM Japan)이나 다른 지역판용이 아닙니다. 파일 이름보다 아래 크기와 해시가 일치하는지가 중요합니다.

## 적용할 원본

| 항목 | 값 |
| --- | --- |
| 게임 ID | ULJM05332 (DISC_VERSION 1.01) |
| 원본 형식 | 수정되지 않은 일본판 ISO |
| 원본 크기 | 612,728,832 바이트 |
| **원본 MD5** | `5b4355c58f0dd9e0091ba17dda8783c6` |
| 원본 SHA-256 | `76df5a15c4441b8c738bb97b850ef2feba28b7582e96c22a3c51d489a929bfbc` |
| xdelta 파일 크기 | 7,216,766 바이트 |
| xdelta SHA-256 | `069572210bcfa7105a9cb52f3a93b25ecd470f1955598461eb5a83ffaf252470` |
| 적용 결과 ISO 크기 | 612,728,832 바이트 |
| 적용 결과 ISO SHA-256 | `dcfb4ca92cd2eed5784ba25c11576a6646030d63fb04cf847fc5b116f4e76a54` |

이 값들은 이번 배포에 사용한 로컬 파일을 직접 해시한 값입니다([release_verification.json](release_verification.json)). 원본 게임 파일은 사용자가 별도로 준비해야 합니다. 이전 한글판에 덧씌우지 말고 항상 위 원본에 적용하세요.

## 패치 적용 방법

### Windows에서 원본 확인

PowerShell에서 실제 파일 경로를 넣어 실행합니다.

```powershell
Get-FileHash -Algorithm MD5 -LiteralPath '.\Vantage Master Portable (Japan).iso'
Get-FileHash -Algorithm SHA256 -LiteralPath '.\Vantage Master Portable (Japan).iso'
```

위 표와 다르면 적용을 중단하고 원본 버전 및 파일 상태를 확인하세요. CSO 파일을 ISO처럼 이름만 바꿔서는 사용할 수 없습니다.

### xdelta UI 사용

1. 릴리즈에서 `VMP_Korean_v1.0.0.xdelta`를 받습니다.
2. xdelta3 패치를 지원하는 도구의 **Apply Patch** 기능을 엽니다.
3. **Patch**에 xdelta 파일, **Source File**에 해시가 일치하는 원본 ISO를 선택합니다.
4. **Output File**에 원본과 다른 새 파일명, 예를 들어 `Vantage Master Portable (Korean).iso`를 지정합니다.
5. 적용 완료 후 결과 ISO의 SHA-256을 위 표와 비교합니다.

UI 명칭은 도구마다 조금 다릅니다. 외부 도구 실행 파일은 이 릴리즈에 포함하지 않습니다. xdelta 자체의 소스와 배포 안내는 [공식 프로젝트](https://github.com/jmacd/xdelta)를 참고하세요.

### 명령줄 사용

```powershell
.\xdelta3.exe -d -s '.\Vantage Master Portable (Japan).iso' '.\VMP_Korean_v1.0.0.xdelta' '.\Vantage Master Portable (Korean).iso'
Get-FileHash -Algorithm SHA256 -LiteralPath '.\Vantage Master Portable (Korean).iso'
```

원본·패치·결과의 해시를 자동 검사하는 자체 도구도 제공합니다. Python 3와 xdelta3 실행 파일을 준비한 뒤 저장소 루트에서 다음처럼 사용합니다.

```powershell
python tools/apply_release.py --xdelta '.\xdelta3.exe' --source '.\Vantage Master Portable (Japan).iso' --patch '.\VMP_Korean_v1.0.0.xdelta' --output '.\Vantage Master Portable (Korean).iso'
```

이 도구는 기존 출력 파일을 덮어쓰지 않습니다. 패치 적용 실패나 결과 해시 불일치 시 성공으로 처리하지 않습니다.

### PPSSPP에서 실행

게임을 완전히 종료한 뒤 새 ISO를 여세요. 이전 버전의 상태 저장(에뮬레이터 Save State)은 과거 실행 코드와 글꼴을 메모리에 보관할 수 있으므로 **게임 내 일반 저장 데이터**로 이어 하세요. 이름 입력 화면의 일본어·영문 입력 기능은 원본 그대로입니다.

## 작업 내용과 범위

빌드 보고서와 검증 도구에 집계된 작업량입니다. 중복을 제외한 번역 수와 실제 삽입 필드 수는 서로 다릅니다.

| 구분 | 작업량 및 내용 |
| --- | --- |
| 이벤트 대사 | 고유 대사 4,130쌍 → 스크립트 필드 5,736개, 루즈 파일과 226개 팩 사본 모두 |
| 실행 파일 문자열 | 필드 1,063개 — 타이틀·모드 선택·튜토리얼·전투 메시지·메뉴·설정·시스템 안내 |
| 맵·유닛·마스터 스크립트 | 92개 파일, 348개 번역(맵 조언 104, 맵 이름 52, 마스터 소개 75, 유닛·클래스·기술 이름 117), `asm.dat` 멤버 91개 재구축 |
| 글꼴 | 완성형 한글 2,350자를 게임 글꼴의 JIS 2수준·확장 구역에 15 px로 삽입, 루즈·팩 사본 모두 |
| UI 아틀라스 | 14장(전투·정보·랭킹·결과·시스템 메뉴·타이틀 등), 라벨 272개를 원본 위치에 다시 그림 |
| 갤러리·매뉴얼·설문 | 갤러리 108장, 매뉴얼·역사 67장, 설문 3장의 구워진 글자 재작성 |

원문 목록, 번역 JSON, 용어집과 최종 표는 함께 공개합니다. 수정할 때는 [번역 파일 우선순위](docs/BUILD.md)를 확인하세요. 용어는 [용어집](itp_work/todo/GLOSSARY.md)을 따르며, 고유명사 195개가 실행 파일·스크립트·대사에서 한 가지 표기로 적히는지 `check_names.py`가 검사합니다.

## v1.0.0 검증

- 원본에 xdelta를 적용한 결과와 배포용 완성 ISO의 바이트 일치 확인(`tools/apply_release.py`).
- `verify_korean_iso.py`: 실행 파일 길이·센티널·상수, 텍스처 슬롯 길이와 디코드, `asm.dat`(449개)·`init0.dat`(91개) 멤버가 모두 제자리에서 복원되는지 통과. 결과는 [validation/verify_korean_iso.txt](validation/verify_korean_iso.txt).
- 스크립트 번역 348개 바이트·줄 수 검사, 압축 멤버 91개 슬롯 검사, 고유명사 195개 표기 일치, 5,569줄 기계 교정 모두 0건([validation/checks.txt](validation/checks.txt)).
- 전체 대사·스크립트·실행 파일 문자열을 원문과 대조하는 정독 검수를 마쳤습니다(15곳 수정, [CHANGELOG.md](CHANGELOG.md)).
- PPSSPP 1.17.1에서 타이틀, 모드 선택, 튜토리얼, 전투, 결과, 갤러리, 매뉴얼, 설문 등 주요 화면을 스크린샷으로 확인하며 제작했습니다.

**전체 시나리오와 18명 마스터 루트를 완주한 검증은 아닙니다. 실제 PSP 기기는 시험하지 않았습니다.** 알려진 한계:

- 매뉴얼 삽화 안에 직접 얹힌 짧은 라벨 10여 개(通りぬけ不可!, 行動後, 攻撃!, 充填, かべ, 効果あり/なし, 目標 등)는 일본어로 남아 있습니다. 본문은 모두 한국어입니다.
- 마스터 편집 화면의 금색 제목판과 타이틀 화면의 「시크릿」 테두리는 원본보다 다소 거칩니다(읽는 데는 지장 없음).
- 이름 입력 화면은 원본의 가나·영문 입력이며 한글 입력은 지원하지 않습니다.

오류 제보에는 패치 버전, 결과 ISO SHA-256, PPSSPP 버전, 장소·대사·재현 순서를 적어 주세요. 기존 상태 저장으로 재현했는지도 알려 주시면 원인 구분에 도움이 됩니다. 게임 ISO나 추출 바이너리는 이슈에 첨부하지 마세요.

## 저장소 구성 및 권리

- 루트 `*.py`: 글꼴·실행 파일·이벤트·스크립트·텍스처 패처와 검사 도구. 역할별 설명은 [docs/BUILD.md](docs/BUILD.md).
- `itp_work/`: 원문 목록(`*_todo.json`, `todo/`), 번역(`kr/`, `kr_scripts/`, `event_kr/`), 용어집.
- `korean_font_slotmapped/korean_slot_map.csv`: 한글 2,350자와 글꼴 슬롯의 대응표.
- `korean_opening_build/`: 배포 ISO의 빌드 보고서(모든 필드의 원문·번역·오프셋).
- `tools/`: 배포 패치 적용·공개 파일 검사 도구. `validation/`: 검증 출력.
- `docs/`: 구현 설명, 빌드 안내, 글꼴 출처.

원작 게임의 권리는 日本ファルコム에 있습니다. 이 프로젝트는 공식 한국어판이 아니며 권리자의 지원·승인을 뜻하지 않습니다. 글꼴 및 외부 도구는 각각의 라이선스를 따릅니다. [글꼴 출처](docs/FONT_CREDITS.md)와 [권리 안내](RIGHTS.md)를 참고하세요.
