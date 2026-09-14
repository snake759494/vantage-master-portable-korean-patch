# 한글 글꼴

이 패치의 한글은 전부 **NanumSquareNeo**(나눔스퀘어 네오)로 렌더링했습니다.
Copyright © 2022 NAVER Corp. All rights reserved. Font Designed by Sandoll Inc.

- 공식 배포 및 라이선스: https://campaign.naver.com/nanumsquare_neo/
- 네이버 글꼴 안내: https://hangeul.naver.com/font

| 굵기 | 파일 | 사용 위치 |
| --- | --- | --- |
| Bold | `NanumSquareNeo-cBd.ttf` | 게임 글꼴 `pspfont.dat`의 한글 2,350자(15 px 래스터), 갤러리 페이지, 매뉴얼 본문, UI 라벨 대부분 |
| Regular | `NanumSquareNeo-bRg.ttf` | 매뉴얼의 가는 본문, 일부 UI 라벨 |
| ExtraBold | `NanumSquareNeo-dEb.ttf` | 굵은 UI 라벨 |

TTF 파일은 저장소에 포함하지 않습니다. 빌드하려면 위 세 파일을 저장소 루트에 두어야 합니다(`build_korean_font.py --ttf`, `patch_ui_textures.py`, `patch_gallery_textures.py`, `patch_manual_textures.py`가 파일명으로 찾습니다).

게임 글꼴에 써넣은 래스터(`korean_font_slotmapped/pspfont_korean.dat`)와 그 압축 사본(`init0_korean.dat`)은 게임 파일 위에 만든 파생물이므로 공개하지 않습니다. 어느 코드 자리에 어느 음절이 들어갔는지는 `korean_font_slotmapped/korean_slot_map.csv`에 있습니다.
