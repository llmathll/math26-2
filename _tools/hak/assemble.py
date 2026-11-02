#!/usr/bin/env python3
"""data.json + template.html + 앱 모듈 -> 아티팩트용 HTML과 독립 실행 HTML
사용: python3 assemble.py <cfg.py> <build폴더>
  - <build>/apps/<앱id>.html 이 있으면 끼워 넣는다(embedapp.py 결과)
  - 출력: <build>/artifact.html (아티팩트 게시용), <build>/<OUT_NAME> (깃허브·컴퓨터 저장용)
"""
import sys, os, json, glob, importlib.util
cfg_path, bd = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location('cfg', cfg_path); C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
here = os.path.dirname(os.path.abspath(__file__))
t = open(os.path.join(here, 'template.html'), encoding='utf-8').read()
data = json.load(open(f'{bd}/data.json'))
need = {d['app'] for d in data if d.get('kind') == 'app'}
apps = ''
for a in sorted(need):
    f = f'{bd}/apps/{a}.html'
    if not os.path.exists(f): sys.exit(f'! 앱 모듈 없음: {f} (embedapp.py로 먼저 만들 것)')
    apps += open(f, encoding='utf-8').read()
title = getattr(C, 'TITLE', '수업 풀이')
html = t.replace('__TITLE__', title).replace('__APPS__', apps).replace('__DATA__', json.dumps(data, ensure_ascii=False))
open(f'{bd}/artifact.html', 'w', encoding='utf-8').write(html)
i = html.index('</style>', html.index('<style>')) + len('</style>')
doc = ('<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
       '<style>html,body{margin:0}[hidden]{display:none!important}img{max-width:100%}</style>\n'
       + html[:i] + '\n</head>\n<body>\n' + html[i:] + '\n</body>\n</html>\n')
open(f'{bd}/{C.OUT_NAME}', 'w', encoding='utf-8').write(doc)
print('ok', f'{bd}/artifact.html', f'{bd}/{C.OUT_NAME}', round(len(doc) / 1e6, 2), 'MB')
