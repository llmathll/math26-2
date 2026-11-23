#!/usr/bin/env python3
"""hak23 맨 끝에 '확률과통계(김) 수업 후 정리 설문' QR 페이지(apps/23survey.html)를 끼운다(PDF 없이).
  아래 왼쪽 제목·문항 목록 = '설문'. QR 주소는 apps/23survey.html 안 SVG(https://forms.gle/bhjvMSNUM7dmRJsy9).
사용: python3 hak23_survey.py <hak23.html> <출력폴더>   → 출력: artifact.html, hak23.html
  이미 넣은 파일에 다시 돌리면 같은 결과. cfg23으로 다시 만들 때는 ITEMS 끝 항목 + build/apps에 23survey.html 복사로 같은 결과.
"""
import sys, os, json
src, out = sys.argv[1:3]
here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mod = open(os.path.join(here, 'apps', '23survey.html'), encoding='utf-8').read()
ITEM = {'kind': 'app', 'app': '23survey', 'sec': '설문', 'num': '설문', 'label': '설문', 'toc': '설문',
        'g': '수업 정리', 'w': 1600, 'h': 900, 'n': 0, 'steps': []}

s = open(src, encoding='utf-8').read()
# 이미 넣은 모듈 빼기
a = s.find('<script type="text/html" id="app-23survey">')
if a >= 0:
    b = s.index('window.__appInit["23survey"]', a); b = s.index('</script>\n', b) + len('</script>\n')
    s = s[:a] + s[b:]
# 모듈 넣기(앱 모듈은 이름순 — 23survey는 23timer 앞)
k = s.index('<script type="text/html" id="app-23timer">')
s = s[:k] + mod + s[k:]
# DATA 끝에 항목
i = s.index('const DATA=') + len('const DATA='); j = s.index(';\nconst $=', i)
D = [d for d in json.loads(s[i:j]) if d.get('app') != '23survey'] + [ITEM]
s = s[:i] + json.dumps(D, ensure_ascii=False) + s[j:]

os.makedirs(out, exist_ok=True)
open(os.path.join(out, 'hak23.html'), 'w', encoding='utf-8').write(s)
# 아티팩트용: assemble.py가 씌운 html/head/body 껍데기 벗기기
h0 = s.index('<title>')                                    # <title>부터가 template 본문
art = s[h0:].replace('\n</head>\n<body>\n', '', 1)
art = art[:art.rindex('\n</body>\n</html>')]
open(os.path.join(out, 'artifact.html'), 'w', encoding='utf-8').write(art)
print('ok', len(D), '항목', round(len(s) / 1e6, 2), 'MB')
