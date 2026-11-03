#!/usr/bin/env python3
"""완성된 hak 화면에 '지금의 template.html'을 다시 입힌다 (손풀이 PDF 없이).
template.html(화면 틀)을 고친 뒤, 지난 단원에도 그 변경을 넣고 싶을 때만 쓴다.
사용: python3 retemplate.py <hak17.html> <출력폴더>
  - 기존 파일에서 제목·문항 데이터(DATA)·끼운 앱을 꺼내 현재 template.html에 넣는다.
  - 출력: <출력폴더>/artifact.html (아티팩트 게시용), <출력폴더>/<원래 파일명> (깃허브·컴퓨터 저장용)
  - 점검: 템플릿을 고치기 전에 돌리면 원본과 바이트까지 같아야 한다(같으면 '원본과 동일' 출력).
"""
import sys, os, re, json

src, out = sys.argv[1], sys.argv[2]
here = os.path.dirname(os.path.abspath(__file__))
s = open(src, encoding='utf-8').read()

title = re.search(r'<title>(.*?)</title>', s, re.S).group(1)
i = s.index('const DATA=') + len('const DATA=')
j = s.index(';\nconst $=', i)
data = s[i:j]
json.loads(data)  # 데이터가 온전한지 확인
k = s.index('<script>\nconst DATA=')
f = s.rindex('</footer>', 0, k) + len('</footer>\n\n')
apps = s[f:k - 1]  # 템플릿의 '__APPS__' 뒤 줄바꿈 제외

t = open(os.path.join(here, 'template.html'), encoding='utf-8').read()
html = t.replace('__TITLE__', title).replace('__APPS__', apps).replace('__DATA__', data)
os.makedirs(out, exist_ok=True)
open(f'{out}/artifact.html', 'w', encoding='utf-8').write(html)
a = html.index('</style>', html.index('<style>')) + len('</style>')
doc = ('<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
       '<style>html,body{margin:0}[hidden]{display:none!important}img{max-width:100%}</style>\n'
       + html[:a] + '\n</head>\n<body>\n' + html[a:] + '\n</body>\n</html>\n')
name = os.path.basename(src)
open(f'{out}/{name}', 'w', encoding='utf-8').write(doc)
print('ok', f'{out}/{name}', round(len(doc) / 1e6, 2), 'MB', '(원본과 동일)' if doc == s else '(템플릿 변경 반영됨)')
