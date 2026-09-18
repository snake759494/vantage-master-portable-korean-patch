# 개발 및 번역 자료 안내

일반 사용자는 README의 xdelta 적용 절차만 따르면 됩니다. 이 저장소는 실제 제작에 쓴 소스와 번역 자료를 공개하는 개발 아카이브입니다. 원본 ISO, ISO에서 추출한 파일, 원본·수정 텍스처, 한글을 써넣은 글꼴 파일은 포함하지 않으므로 clone 직후 명령 하나로 같은 ISO가 나오는 환경은 아닙니다. 아래는 구조 설명이며, 재현하려면 원본을 직접 준비하고 각 스크립트 상단의 기본 경로를 자신의 환경에 맞춰야 합니다.

## 환경과 외부 의존성

- Windows, Python 3.13. Python 패키지: **Pillow**(글꼴 렌더링·이미지), **numpy**, **pycdlib**(ISO 읽기·쓰기).
- xdelta3 실행 파일(배포 패치 생성·적용). 저장소에 포함하지 않습니다.
- NanumSquareNeo TTF 세 종(`-cBd`, `-bRg`, `-dEb`)을 저장소 루트에. 출처는 [FONT_CREDITS.md](FONT_CREDITS.md).
- PPSSPP 1.17.1로 화면을 확인했습니다. 스크립트는 에뮬레이터를 실행하지 않습니다.

## 스크립트가 기대하는 로컬 자료

| 경로 | 내용 | 만드는 방법 |
| --- | --- | --- |
| `Vantage Master Portable (1.01).iso` | 수정되지 않은 일본판 원본. 스크립트·이벤트·갤러리·매뉴얼 원본은 빌드 스크립트가 여기서 직접 읽습니다 | 직접 준비 (README의 해시와 일치해야 함) |
| `pspfont.dat` | 원본 `PSP_GAME/USRDIR/system/pspfont.dat`. `init0.dat` 안의 압축 사본과 바이트 단위로 같아 인코더도 이 파일로 만듭니다 | ISO에서 추출 |
| `jis2utf.bin` | 원본 `PSP_GAME/USRDIR/system/jis2utf.bin` (`extract_pspfont.py`만 사용) | ISO에서 추출 |
| `itp_work/init0_orig.dat` | 원본 `PSP_GAME/USRDIR/data/pack/init0.dat` — `patch_packed_pspfont.py`의 입력 | ISO에서 추출 |
| `itp_work/asm_orig.dat` | 원본 `data/pack/asm.dat` — `check_pack_fit.py`의 기준 | ISO에서 추출 |
| `itp_work/BOOT_orig.bin` | 원본 `PSP_GAME/SYSDIR/BOOT.BIN` — `lint_korean.py`가 원문을 읽는 곳 | ISO에서 추출 |
| `itp_work/raw/*.itp` | 원본 UI·설문 아틀라스 | ISO의 `data/system`에서 추출 |
| `korean_font_slotmapped/pspfont_korean.dat`, `init0_korean.dat` | 한글을 써넣은 글꼴과 그 압축 사본 | 아래 2단계에서 생성 |
| `itp_work/patched/*.itp` | 한글로 다시 그린 텍스처 | 아래 4단계에서 생성 |

`itp_work/tex/`는 디코드 검사용 임시 파일 자리로, 필요한 스크립트가 알아서 만듭니다. 원본 파일은 반드시 원본 ISO에서 추출하세요 — 다른 번역 프로젝트 저장소에 들어 있는 `init0.dat` 같은 파일은 이미 수정된 것일 수 있습니다.

## 제작 흐름

1. **추출.** 원본 ISO에서 위 표의 파일을 꺼냅니다. `extract_pspfont.py`는 원본 한자 글꼴의 배치를 조사해 `font_extraction/japanese_kanji_map.csv`를 만듭니다.
2. **글꼴.** `python build_korean_font.py --font pspfont.dat --ttf NanumSquareNeo-cBd.ttf --out korean_font_slotmapped` → `pspfont_korean.dat`와 `korean_slot_map.csv`. 이어서 `python patch_packed_pspfont.py` (기본값 `--pack itp_work/init0_orig.dat --replacement korean_font_slotmapped/pspfont_korean.dat --out korean_font_slotmapped/init0_korean.dat`). 슬롯 선택과 인코딩은 `korean_slots.py`, 글꼴 레코드 해석은 `falcom_font.py`.
3. **실행 파일 문자열.** 원문 목록 `itp_work/exe_todo.json`(오프셋·길이·원문)에 대응하는 번역을 `itp_work/kr/chunk_*.json`(오프셋 → 한국어)에 적습니다. `python build_system_text.py`가 이를 `vmp_system_text.py`로 생성하고, 오프닝 212개 필드는 `vmp_opening_text.py`에 직접 적혀 있습니다. `check_fit.py`가 바이트 예산을 검사합니다.
4. **텍스처.** ITP 읽기·쓰기는 `falcom_itp.py`. UI 아틀라스는 `python patch_ui_textures.py`(`itp_work/raw` → `itp_work/patched`, 라벨 표는 `ui_texture_text.py`), 설문은 `python patch_quiz_textures.py`(`quiz_text.py`), 갤러리는 `python build_gallery_textures.py`(`gallery_text.py`, 이름은 `vmp_system_text.py`에서), 매뉴얼은 `python build_manual_textures.py`(`manual_text.py`, `manual_pages.py`). 상자 좌표를 다시 재려면 `python refit_ui_boxes.py --write`, 잘린 획 검사는 `python check_ui_labels.py`, 매뉴얼 페이지 검사는 `check_manual_pages.py`.
5. **이벤트 대사.** `itp_work/event_todo.json`(스크립트별 원문·오프셋·길이)에 대응하는 번역을 `itp_work/event_kr/chunk_*.json`(일본어 → 한국어)에 적습니다. `check_event_fit.py`가 예산을 검사하고, 삽입은 빌드 단계에서 `patch_event_scripts.build()`가 합니다.
6. **맵·유닛·마스터 스크립트.** 원문은 `itp_work/todo/{map_help_*,map_names,master,unit}.json`, 번역은 `itp_work/kr_scripts/*.json`. `python check_script_fit.py`(바이트 예산·줄 수), `python check_pack_fit.py`(압축 슬롯). 삽입은 `patch_scripts.build()`, 압축은 `patch_packed_pspfont.ed7_compress`와 `ed7_optimal.py`.
7. **빌드.** `python build_korean_opening_iso.py --input "Vantage Master Portable (1.01).iso" --output "<새 ISO>"`. 글꼴·실행 파일·이벤트·스크립트·텍스처를 한 번에 넣고 `korean_opening_build/opening_patch_report.txt`에 필드 단위 보고서를 씁니다. 스크립트가 하나라도 슬롯을 넘치면 ISO를 만들지 않습니다.
8. **검증.** `python verify_korean_iso.py "<새 ISO>" --original "Vantage Master Portable (1.01).iso"`, `python lint_korean.py`, `python check_names.py`. 그다음 PPSSPP에서 화면을 확인합니다.
9. **배포.** `xdelta3 -e -s "Vantage Master Portable (1.01).iso" "<새 ISO>" VMP_Korean_v1.0.0.xdelta`. 적용·해시 검사는 `tools/apply_release.py`.

## 번역 데이터

| 파일 | 역할 |
| --- | --- |
| `itp_work/event_kr/chunk_*.json` | 이벤트 대사 4,130쌍, 일본어 → 한국어 |
| `itp_work/event_todo.json` | 이벤트 스크립트별 원문 목록(오프셋·바이트 길이) |
| `itp_work/kr/chunk_*.json`, `zz_fixups.json`, `zz_missed.json` | 실행 파일 문자열 번역, 오프셋 → 한국어 (뒤의 두 파일이 우선) |
| `itp_work/exe_todo.json`, `exe_missed.json`, `exe_left.json` | 실행 파일 원문 목록과 누락·잔여 조사 |
| `itp_work/kr_scripts/*.json` | 맵 조언·맵 이름·마스터 소개·유닛/기술 이름 348쌍 |
| `itp_work/todo/*.json`, `as_left.json` | 위 스크립트의 원문 목록과 조사 결과 |
| `itp_work/todo/GLOSSARY.md` | 용어집 — 새 번역은 반드시 이 표기를 따릅니다 |
| `itp_work/existing_pairs.txt` | 초기 번역 메모리 |
| `vmp_opening_text.py`, `vmp_system_text.py` | 실행 파일에 들어가는 최종 표(후자는 생성 파일) |
| `gallery_text.py`, `manual_text.py`, `quiz_text.py`, `ui_texture_text.py`, `map_names.py` | 텍스처와 맵 목록에 그려 넣는 최종 표 |
| `korean_opening_build/opening_patch_report.txt` | 배포 ISO의 빌드 보고서 — 모든 필드의 원문·번역·오프셋 |

이름 표기의 기준은 `check_names.py`가 검사하는 실행 파일 이름 필드입니다. 스크립트 번역이 실행 파일과 다른 표기를 쓰면 검사에 걸립니다.

## 남겨 둔 것과 폐기한 것

- `build_korean_test_iso.py`, `build_packed_font_test_iso.py`, `apply_korean_font_test.py`, `build_korean_dialogue_mapping_fixed.py`, `patch_dialogue_text.py`, `pspfont_debug.py`는 글꼴 배치를 찾던 초기 시험 빌드입니다. 출력 폴더는 정리했고 기록용으로만 남겨 둡니다. `patch_map_names.py`는 팩을 제자리에서 늘리던 이전 방식으로, `patch_scripts.py`로 대체되었습니다.
- 작업 중 만든 PNG 덤프·스크린샷·일회성 탐침 스크립트·시험 빌드는 저장소에 넣지 않았습니다. `python tools/audit_public.py`가 Git이 추적하는 파일이 허용된 텍스트 종류뿐인지 검사하고 `publication_manifest.json`을 갱신합니다.
