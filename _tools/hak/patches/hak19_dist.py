#!/usr/bin/env python3
"""hak19에 '표본평균분포' 개념 페이지를 끼운다(교과서 외 4 다음).
내용: hak20 02·03의 ① 개념 정리 손글씨(하늘색 테두리 제외). PDF 없이 hak20.html의 펜 획·가리개를 옮겨 씀.
  왼쪽 '표본평균의 분포' — 02 오른쪽(모집단 그림·E,V,σ)을 위에, X~N(m,σ²)⇒X̄~N(…) 줄을 그 아래로
  오른쪽 '표본비율의 분포' — 03 개념 정리 그대로
  분홍 가리개는 처음부터 보이고 「다음」마다 하나씩 열림(차례 가리개 c.o, template.html)
사용: python3 hak19_dist.py <hak19 원본.html> <hak20.html> <출력폴더>
  hak19 원본에 이미 이 페이지가 있으면 바꿔 끼움. 출력: artifact.html, hak19.html
"""
import sys, os, re, json, io, base64
from PIL import Image, ImageDraw, ImageFont
src19, src20, out = sys.argv[1:4]
here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def parts(f):
    s = open(f, encoding='utf-8').read()
    i = s.index('const DATA=') + len('const DATA='); j = s.index(';\nconst $=', i)
    k = s.index('<script>\nconst DATA='); fo = s.rindex('</footer>', 0, k) + len('</footer>\n\n')
    return s, re.search(r'<title>(.*?)</title>', s, re.S).group(1), json.loads(s[i:j]), s[fo:k - 1]

_, title, D19, apps = parts(src19)
D20 = parts(src20)[2]
NUM = '표본평균분포'
D19 = [d for d in D19 if d.get('num') not in (NUM, '모평균(비율) 분포', '표본평균(비율) 분포')]   # 예전 이름도 바꿔 끼움
for d in D19:                                            # 개념 앱(정규 근사) 목록·제목 이름 → '개념' (cfg19에도 반영됨)
    if d.get('kind') == 'app' and d.get('app') == '19binorm': d['num'] = d['toc'] = '개념'

def nums(t): v = [float(x) for x in re.findall(r'-?\d+\.?\d*', t['d'])]; return v[0::2], v[1::2]
def bb(t): xs, ys = nums(t); return min(xs), min(ys), max(xs), max(ys)
def shift(t, dx, dy):
    t = dict(t); t['d'] = re.sub(r'(-?\d+\.?\d*),(-?\d+\.?\d*)', lambda m: '%.1f,%.1f' % (float(m[1]) + dx, float(m[2]) + dy), t['d']); return t
SKY = '#88c8ff'                                         # 하늘색 테두리(개념 상자) — 빼기

M, TOP = 50, 170                                         # 바깥 여백, 내용 시작 y(위는 제목)
strokes, covers = [], []
def put(item, sel, cov_ids, dx, dy):
    """item의 ① 획 중 sel을 (dx,dy) 옮겨 넣고, cov_ids 가리개를 차례대로 붙임"""
    base = len(covers); remap = {}
    for n_, ci in enumerate(cov_ids):
        c = item['covers'][ci]; remap[ci] = base + n_
        covers.append(dict(s=-1, o=base + n_, x=round(c['x'] + dx, 1), y=round(c['y'] + dy, 1), w=c['w'], h=c['h']))
    for t in item['strokes']:
        if t['s'] != 0 or t['c'] == SKY or not sel(t): continue
        u = shift(t, dx, dy); u['s'] = -1
        if t.get('k') is not None:
            if t['k'] in remap: u['k'] = remap[t['k']]
            else: u.pop('k')
        strokes.append(u)

a, b = D20[0], D20[1]                                    # hak20 02, 03
def bot02(t): x0, y0, x1, y1 = bb(t); return (x0 + x1) / 2 < 1560 and (y0 + y1) / 2 > 640
TOPB, BOTB, B03 = [1563, 89, 2491, 950], [118, 645, 1442, 925], [1437, 96, 2747, 1080]   # 각 부분 테두리(획+가리개)
LW = BOTB[2] - BOTB[0]                                    # 왼쪽 칸 폭
tx = M + (LW - (TOPB[2] - TOPB[0])) // 2                  # 위 부분은 왼쪽 칸 가운데
put(a, lambda t: not bot02(t), [0, 1, 2], tx - TOPB[0], TOP - TOPB[1])
by = TOP + (TOPB[3] - TOPB[1]) + 50
put(a, bot02, [3], M - BOTB[0], by - BOTB[1])
RX = M + LW + 130                                         # 오른쪽 칸 시작
put(b, lambda t: True, [0, 1, 2, 3, 4, 5, 6], RX - B03[0], TOP - B03[1])
W = RX + (B03[2] - B03[0]) + M
H = by + (BOTB[3] - BOTB[1]) + M

img = Image.new('RGB', (W, H), 'white'); dr = ImageDraw.Draw(img)
F = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 74, index=1)   # KR
for x, txt in [(M, '표본평균의 분포'), (RX, '표본비율의 분포')]:
    dr.rounded_rectangle([x, 52, x + 14, 128], 4, fill=(47, 95, 170))
    dr.text((x + 36, 90), txt, font=F, fill=(29, 42, 68), anchor='lm')
xm = M + LW + 65; dr.line([xm, 60, xm, H - 40], fill=(200, 205, 214), width=4)
bio = io.BytesIO(); img.save(bio, 'PNG', optimize=True)
rec = dict(sec='교과서 외 문제', num=NUM, toc=NUM, g='교과서 외 문제', w=W, h=H, n=len(covers),
           base='data:image/png;base64,' + base64.b64encode(bio.getvalue()).decode(), steps=[], solo=1,
           covers=covers, strokes=strokes)
at = next(i for i, d in enumerate(D19) if d.get('sec') == '교과서 외 문제' and d.get('num') == '4') + 1
D19.insert(at, rec)
data = json.dumps(D19, ensure_ascii=False, separators=(',', ':'))

t = open(os.path.join(here, 'template.html'), encoding='utf-8').read()
html = t.replace('__TITLE__', title).replace('__APPS__', apps).replace('__DATA__', data)
os.makedirs(out, exist_ok=True)
open(f'{out}/artifact.html', 'w', encoding='utf-8').write(html)
a_ = html.index('</style>', html.index('<style>')) + len('</style>')
doc = ('<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
       '<style>html,body{margin:0}[hidden]{display:none!important}img{max-width:100%}</style>\n'
       + html[:a_] + '\n</head>\n<body>\n' + html[a_:] + '\n</body>\n</html>\n')
open(f'{out}/hak19.html', 'w', encoding='utf-8').write(doc)
print('ok', W, H, '획', len(strokes), '가리개', len(covers), '위치', at, round(len(doc) / 1e6, 2), 'MB')
