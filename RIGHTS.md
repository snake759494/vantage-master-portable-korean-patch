# 권리 및 외부 자료

이 저장소는 비공식 한국어 패치의 소스·번역·검수 자료 공개용입니다. 『ヴァンテージマスターポータブル』(Vantage Master Portable)과 그 텍스트·그래픽·글꼴의 권리는 日本ファルコム(Nihon Falcom)에 있습니다. 이 프로젝트는 공식 한국어판이 아니며 권리자의 지원·승인을 뜻하지 않습니다. 원본 게임, 패치 적용 게임, 게임에서 추출한 파일은 배포하지 않습니다.

저장소 공개 자체가 모든 파일에 동일한 오픈소스 라이선스를 부여한다는 뜻은 아닙니다. 자체 제작 코드·번역 전체에 대한 별도 포괄 라이선스는 지정하지 않았습니다. 파일에 개별 조건이 명시돼 있으면 해당 조건을 따릅니다.

## 포함하지 않는 것

- 원본 ISO, 패치 적용 ISO, `EBOOT.BIN`/`BOOT.BIN`, `pspfont.dat`, `data/pack/*.dat` 등 ISO에서 추출한 바이너리와 그 복사본.
- 게임 텍스처(`*.itp`)의 원본·수정본, 그 PNG 변환본, 작업 중 찍은 스크린샷.
- 한글 글리프를 써넣은 `pspfont_korean.dat`, `init0_korean.dat` — 게임 글꼴 파일 위에 만든 파생물이므로 공개하지 않습니다. 대신 어느 코드 자리에 어느 음절을 넣었는지 적은 `korean_font_slotmapped/korean_slot_map.csv`를 공개합니다.
- 글꼴 TTF, xdelta·PPSSPP 등 외부 실행 파일.

## 글꼴 출처

한글 글리프와 UI·갤러리·매뉴얼 텍스처의 한글은 **NanumSquareNeo**(네이버 나눔스퀘어 네오)로 렌더링했습니다. Copyright © 2022 NAVER Corp. All rights reserved. Font Designed by Sandoll Inc. 배포 및 라이선스 안내는 [나눔스퀘어 네오 공식 페이지](https://campaign.naver.com/nanumsquare_neo/)와 [네이버 글꼴 안내](https://hangeul.naver.com/font)를 참고하세요. TTF 파일은 저장소에 포함하지 않습니다. 자세한 사용 위치는 [docs/FONT_CREDITS.md](docs/FONT_CREDITS.md)에 있습니다.

xdelta, PPSSPP, Python 및 Pillow·numpy 등 라이브러리는 각 프로젝트의 조건을 따르며 바이너리를 재배포하지 않습니다.
