# hak — 손풀이 PDF로 전자칠판 수업 화면 만들기

`_` 로 시작하는 폴더라 GitHub Pages 사이트에는 공개되지 않는다.

| 파일 | 하는 일 |
|---|---|
| `hakbuild.py <cfg> <build>` | 손풀이 PDF + 문제만 PDF → `build/data.json`, 점검 그림 `build/check/*.png` |
| `loops.py <손풀이.pdf> <쪽> <out.png>` | 보라색 닫힌 테두리 → 단계 영역 후보 좌표(설정 초안용) |
| `embedapp.py <앱.html> <id> <build/apps/id.html>` | 교과서 설명앱을 흰 배경으로 바꿔 끼울 모듈로 변환 |
| `assemble.py <cfg> <build>` | `build/artifact.html`(아티팩트용) + `build/<OUT_NAME>`(깃허브·컴퓨터용) |
| `shots.js <html> <outdir> [index...]` | 4K 밀도 스크린샷(문제만 / 풀이 전체) |
| `at.js <html> 문항:단계:out.png ...` | 특정 단계 화면 스크린샷(단계 경계에 다른 단계 획이 섞였는지 확인) |
| `template.html` | 화면 틀(조작줄, 키보드·탭, 앱 끼우기) — 모든 단원이 함께 쓴다 |
| `retemplate.py <hak17.html> <out>` | 완성된 hak 파일에 지금의 template.html을 다시 입힘(PDF 없이). 틀 수정을 지난 단원에 넣을 때 |
| `makeindex.py <저장소> [아티팩트용]` | 저장소 최상위 html 목록으로 목차 `index.html` 생성(틀: `index_template.html`) |
| `notes/` | 오답노트 — 단원을 만들며 겪은 실수·결정·요령(README 참고) |
| `cfg17.py` | 17단원 설정 예시 — 새 단원은 이걸 복사해서 고친다 |
| `cfg18.py` | 18단원 설정 — 확률표 붙이기(`paste`)·행 형광 강조(`hl`) 예시, 개념 상자와 문항이 겹친 자리 지우기 |

좌표는 모두 페이지 가로 2000 기준 `[x0, y0, x1, y1]`.


항목 옵션(18단원에서 추가)
- `paste`: `[dict(page, src, at)]` 문제만 PDF의 인쇄물(확률표 등)을 `at`(왼쪽 위) 자리에 붙여 처음부터 보이게 함. 페이지 오른쪽·아래 밖도 허용(화면이 그만큼 넓어짐).
- `hl`: `[(단계index, 사각형)]` 그 단계에서 사각형에 노란 형광 강조(곱하기).
- `paste`에 `step=n`을 주면 처음엔 없다가 n단계에서 나타남.
- `pieces`: `[dict(src=[사각형...], to=(dx, dy), base=True)]` 문항 조각(인쇄물·손글씨·펜 획)을 옮겨 새로 배치. steps·cm 좌표는 원래 위치로 쓰면 자동으로 옮겨지고, crop·paste·hl은 옮긴 뒤 위치로 쓴다. `base=False`면 그 조각의 인쇄물은 가져오지 않음.
- `follow`: 화면보다 긴 문항을 폭에만 맞춰 공통 배율로 크게 보이고, 아래쪽 단계를 쓸 때 화면이 따라 내려감(지금까지 쓴 것의 가장 아래와 지금 단계의 윗부분이 보이게). 풀이 중 문제를 다시 보려면 조작줄의 ↑문제 보기 버튼(다시 누르면 ↓풀이로), 화면 위아래 끌기, 마우스 휠. 다음·이전을 누르면 다시 따라가기.
- `scale`: 공통 배율에 곱하는 값(예 0.9 = 이 문항만 90% 크기, follow 문항의 내려가는 양을 줄일 때).
- `pre`: 앞의 n개 단계는 처음부터 한꺼번에 보이고, 그 뒤 단계부터 한 단계씩(예: 개념 상자 ①~⑩은 바로 보이고 문제 풀이 ⑪부터). steps·hl·paste의 단계 번호는 원래 번호 그대로 쓴다.
- `solo`: 공통 배율 계산에서 빼는 문항(이 문항이 살짝 커서 다른 문항까지 작아지는 것을 막음).
- 노란 형광펜 획도 손글씨로 인식(구분선 등).

cfg 기본 항목
- 상단: MARKED, CLEAN, OUT_NAME(`hak{단원}.html`), TITLE, BANNER, RULES, IGNORE, ITEMS, VECTOR(기본 True).
- ITEMS 순서 = 화면 순서. 문항 항목: page, sec(묶음 이름: 이항분포 복습/중단원 학습 점검/대단원 학습 평가/수학 익힘책/교과서 외 문제 등), num, crop(그 문항 칸 전체), steps[{rects, blue, g, prio}], blank, baseblank, cm, ghost, link, linkName.
- 앱 항목: `dict(kind='app', app='17normal', sec='개념 탐구 · 교과서', num='정규분포', toc='정규분포', group='중단원 학습 점검')`
- `embedapp.py`는 어두운 칠판색 → 흰 배경색으로 바꾼다. 앱마다 색이 다르면 COLOR_MAP 보강.

화면 규격(template.html에 구현됨)
- 흰 배경(시험 기간 기준). 문항마다 내용 영역만 잘라 왼쪽 위에 붙이고, 문제 번호는 왼쪽 위, 좌우 여백 없음. 문제 바탕은 500dpi 그림, 손풀이는 펜 획(벡터).
- 공통 배율로 글자 크기 통일(화면 크기에 따라 실행 중 자동 계산, UNIFORM_TOL=0.9).
- 쓰기: 단계 획을 PDF에 든 순서대로, WRITE_SPEED=1.7, 한 단계 최대 약 3.2초(STEP_MAX_MS). 쓰는 도중 다음 → 그 단계 즉시 완성, 한 번 더 → 다음 단계. 이전·문제만·풀이 전체·문항 이동은 즉시. 점선·칠한 도형·표·강조는 fade, 형광펜은 반투명 곱하기.
- 맨 아래 한 줄: 왼쪽 문항 제목(+Link), 가운데 단원별 문항 목록, 오른쪽 문제만·풀이 전체·이전·다음·전체화면. 진행상황 표시 없음. 문항 번호 글자를 키우지 않는다.
- 조작: 화면 탭·→·스페이스·PageDown 다음, ←·PageUp 이전, Home 문제만, End 풀이 전체.
- 앱 페이지: Shadow DOM에 넣어 상태 유지, 키보드·탭은 앱에 넘김(PageUp/PageDown만 이동). 앱은 공통 배율과 관계없이 화면에 맞춤.
