#!/usr/bin/env python3
"""교과서 설명앱(1600x900 스테이지형 HTML)을 수업 화면 안에 넣을 모듈로 변환한다.
사용: python3 embedapp.py <앱.html> <앱id> <출력.html>
- 앱 CSS/마크업은 Shadow DOM 안에 넣어 수업 화면과 충돌하지 않게 한다.
- 어두운 칠판 색을 흰 배경용 색으로 바꾼다(COLOR_MAP). 앱마다 색이 다르면 맵을 보강한다.
"""
import re, sys
src_path, app_id, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
src = open(src_path, encoding='utf-8').read()
css = re.search(r'<style>(.*?)</style>', src, re.S).group(1)
body = re.search(r'<body>(.*?)<script>', src, re.S).group(1)
js = re.search(r'<script>(.*?)</script>', src, re.S).group(1)
KEEP_COLORS = {"['#8ec5ff','#9d8cf5','#ff7d6a','#7fd48a']": "['#2f7fc1','#7c5cd6','#d6453a','#2f9a4a']"}
COLOR_MAP = {'#0a1420': '#ffffff', '#0e1b2b': '#ffffff', '#16283e': '#f7f8fb', '#1d3350': '#eef0f6',
  'rgba(214,229,245,.16)': 'rgba(28,34,49,.12)', 'rgba(214,229,245,.34)': 'rgba(28,34,49,.26)', 'rgba(214,229,245,.4)': 'rgba(28,34,49,.30)',
  '#eaf1f8': '#1c2231', '#b9cadd': '#4a5264', '#7d94ad': '#7a8296',
  '#f5b642': '#d9480f', 'rgba(245,182,66,.12)': 'rgba(217,72,15,.08)', 'rgba(245,182,66,.25)': 'rgba(217,72,15,.18)',
  '#49d1c0': '#0f8577', 'rgba(73,209,192,.12)': 'rgba(15,133,119,.10)',
  '#9d8cf5': '#5d3b8f', 'rgba(157,140,245,.12)': 'rgba(93,59,143,.08)', 'rgba(157,140,245,.14)': 'rgba(93,59,143,.10)',
  '#ff7d6a': '#d6453a'}
for a, b in KEEP_COLORS.items(): js = js.replace(a, b)
for a, b in COLOR_MAP.items(): css = css.replace(a, b); js = js.replace(a, b)
css = css.replace(':root{', ':host{position:absolute;inset:0;display:block;')
css = re.sub(r'html,body\{[^}]*\}', '', css)
css = re.sub(r'\nbody\{([^}]*)\}', r'\n.viewport{\1}', css)
css = css.replace('.viewport{position:fixed;inset:0}', '.viewport{position:absolute;inset:0;overflow:hidden;background:var(--bg)}')
css += '\n#fsBtn{display:none}\n.viewport{color:var(--chalk);user-select:none;-webkit-user-select:none}\n'
js = js.replace('document.getElementById(', 'R.getElementById(').replace('document.querySelectorAll(', 'R.querySelectorAll(').replace('document.querySelector(', 'R.querySelector(')
js = js.replace('getComputedStyle(document.documentElement)', 'getComputedStyle(R.host)')
m = re.search(r'const STAGE_W.*?fitSoon\(\);', js, re.S)
if m:
    js = js[:m.start()] + """const STAGE_W=1600, STAGE_H=900, stage=R.getElementById('stage');
function fitStage(){ const w=R.host.clientWidth,h=R.host.clientHeight; if(!w||!h) return;
  const s=Math.min(w/STAGE_W,h/STAGE_H);
  stage.style.transform=`translate(${Math.round((w-STAGE_W*s)/2)}px,${Math.round((h-STAGE_H*s)/2)}px) scale(${s})`; }
new ResizeObserver(fitStage).observe(R.host);""" + js[m.end():]
else:
    print('! 스테이지 맞춤 코드를 못 찾음 — 앱 구조 확인 필요')
js = js.replace("addEventListener('keydown',e=>{", f"addEventListener('keydown',e=>{{ if(window.__appOn!=='{app_id}') return;", 1)
if 'document.getElementById' in js: print('! document.getElementById 남음')
mod = (f'<script type="text/html" id="app-{app_id}"><style>{css}</style>{body}</script>\n'
       f'<script>\nwindow.__appInit=window.__appInit||{{}};\nwindow.__appInit["{app_id}"]=function(R){{\n{js}\n}};\n</script>\n')
open(out_path, 'w', encoding='utf-8').write(mod)
print('ok', out_path, len(mod))
