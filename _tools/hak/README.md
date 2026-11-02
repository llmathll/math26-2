# hak — 손풀이 PDF로 전자칠판 수업 화면 만들기

`_` 로 시작하는 폴더라 GitHub Pages 사이트에는 공개되지 않는다.

| 파일 | 하는 일 |
|---|---|
| `hakbuild.py <cfg> <build>` | 손풀이 PDF + 문제만 PDF → `build/data.json`, 점검 그림 `build/check/*.png` |
| `loops.py <손풀이.pdf> <쪽> <out.png>` | 보라색 닫힌 테두리 → 단계 영역 후보 좌표(설정 초안용) |
| `embedapp.py <앱.html> <id> <build/apps/id.html>` | 교과서 설명앱을 흰 배경으로 바꿔 끼울 모듈로 변환 |
| `assemble.py <cfg> <build>` | `build/artifact.html`(아티팩트용) + `build/<OUT_NAME>`(깃허브·컴퓨터용) |
| `shots.js <html> <outdir> [index...]` | 4K 밀도 스크린샷(문제만 / 풀이 전체) |
| `template.html` | 화면 틀(조작줄, 키보드·탭, 앱 끼우기) |
| `cfg17.py` | 17단원 설정 예시 — 새 단원은 이걸 복사해서 고친다 |

좌표는 모두 페이지 가로 2000 기준 `[x0, y0, x1, y1]`.
