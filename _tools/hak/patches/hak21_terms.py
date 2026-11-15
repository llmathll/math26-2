#!/usr/bin/env python3
"""hak21 '용어 정리' 페이지 오른쪽 여백에 손글씨 두 묶음을 더 넣는다(사용자 요청, PDF 없이 펜 획을 옮김).
  그림2  X̄ ~ N(m, σ²/n)  — hak22 익힘책 02의 ① 획(남색). 'σ 대신 S 사용 가능' 위. m·σ²/n은 답 가리개.
          ①(첫 화면) 바로 다음 단계로 나타남.
  그림1  p̂ ~ N(p, pq/n) … 신뢰구간, √ 안의 pq 대신 p̂q̂ — hak21 12번 ① 획. 오른쪽 넓은 여백.
          '신뢰구간의 길이'(⑥)까지 나온 뒤 한 줄씩 단계로, 필요한 곳은 답 가리개.
  맨 아래 2×1.96×√(p̂q̂/n) → 신뢰구간의 길이  — 손풀이에 없는 내용. 식은 초록, 화살표·용어는 청색(남색)
          (2×1.96× = 11번 ①, √(p̂q̂/n) = 13번 ②, 화살표·신뢰구간의 길이 = 용어 정리 ⑥ 획을 복사)
사용: python3 hak21_terms.py <hak21.html> <hak22.html> <출력폴더>
  이미 넣은 hak21.html에 다시 돌리면 넣었던 것을 빼고 새로 넣는다. 출력: artifact.html, hak21.html
  cfg21로 hak21을 다시 만들면(build·assemble) 이 패치를 그 뒤에 한 번 더 돌려야 한다.
"""
import sys, os, re, json, io, base64
from PIL import Image
src21, src22, out = sys.argv[1:4]
here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def parts(f):
    s = open(f, encoding='utf-8').read()
    i = s.index('const DATA=') + len('const DATA='); j = s.index(';\nconst $=', i)
    k = s.index('<script>\nconst DATA='); fo = s.rindex('</footer>', 0, k) + len('</footer>\n\n')
    return s, re.search(r'<title>(.*?)</title>', s, re.S).group(1), json.loads(s[i:j]), s[fo:k - 1]

_, title, D, apps = parts(src21)
D22 = parts(src22)[2]
item = lambda DD, sec, num: next(d for d in DD if d.get('sec') == sec and d.get('num') == num)
T = item(D, '중단원 학습 점검', '용어 정리')
Q11, Q12, Q13 = (item(D, '중단원 학습 점검', n_) for n_ in ('11', '12', '13'))
H22 = item(D22, '수학 익힘책', '02')

def nums(t): v = [float(x) for x in re.findall(r'-?\d+\.?\d*', t['d'])]; return v[0::2], v[1::2]
def bb(t): xs, ys = nums(t); return min(xs), min(ys), max(xs), max(ys)
def ctr(t): b = bb(t); return (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
def inr(t, r): x, y = ctr(t); return r[0] <= x <= r[2] and r[1] <= y <= r[3]
def box(ts):
    b = [bb(t) for t in ts]; return min(x[0] for x in b), min(x[1] for x in b), max(x[2] for x in b), max(x[3] for x in b)
def shift(t, dx, dy, **kw):
    t = dict(t); t['d'] = re.sub(r'(-?\d+\.?\d*),(-?\d+\.?\d*)', lambda m: '%.1f,%.1f' % (float(m[1]) + dx, float(m[2]) + dy), t['d'])
    t.pop('k', None); t.update(kw); t['x'] = 1; return t          # x=1: 이 패치가 넣은 획
GREEN, NAVY, SKY = '#007500', '#000347', '#88c8ff'

# ---- 이미 넣은 파일이면 원래대로 되돌린 뒤 다시 ----
if 'p21' in T:
    o = T.pop('p21')
    T['strokes'] = [t for t in T['strokes'] if not t.get('x')]
    for t in T['strokes']:
        if t['s'] >= 1: t['s'] -= 1
    T['covers'] = T['covers'][:o['ncov']]
    T.update(w=o['w'], h=o['h'], n=o['n'], base=o['base'])
orig = dict(w=T['w'], h=T['h'], n=T['n'], base=T['base'], ncov=len(T.get('covers', [])))

# ---- 단계 번호: 원래 ②~⑥(0~4) → 1~5, 그림2 = 0, 그림1 = 6~ ----
for t in T['strokes']:
    if t['s'] >= 0: t['s'] += 1
S2, S1 = 0, orig['n'] + 1
covers = T.setdefault('covers', [])
PAD = 12
def cover(ts, step):
    """획 묶음 ts를 덮는 가리개를 만들고 그 획에 k를 붙임"""
    x0, y0, x1, y1 = box(ts); k = len(covers)
    covers.append(dict(s=step, x=round(x0 - PAD, 1), y=round(y0 - PAD, 1), w=round(x1 - x0 + 2 * PAD, 1), h=round(y1 - y0 + 2 * PAD, 1)))
    for t in ts: t['k'] = k
add = []

# ---- 그림2: X̄ ~ N(m, σ²/n) (hak22 02 ①) → 'σ 대신 S 사용 가능'(x 795~, y 658~) 위 ----
R2 = [860, 530, 1395, 690]
src = [t for t in H22['strokes'] if t['s'] == 0 and inr(t, R2)]
b = box(src); dx, dy = 800 - b[0], 462 - b[1]
for ci in sorted({t['k'] for t in src if t.get('k') is not None}):
    grp = [shift(t, dx, dy, s=S2) for t in src if t.get('k') == ci]
    c = H22['covers'][ci]; k = len(covers)                       # 가리개는 손풀이의 분홍 네모 그대로
    covers.append(dict(s=S2, x=round(c['x'] + dx, 1), y=round(c['y'] + dy, 1), w=c['w'], h=c['h']))
    for t in grp: t['k'] = k
    add += grp
add += [shift(t, dx, dy, s=S2) for t in src if t.get('k') is None]

# ---- 그림1: 12번 ① (하늘색 구분선 제외) → 오른쪽 여백 ----
DX, DY = -30, 0
g1 = [t for t in Q12['strokes'] if t['s'] == 0 and t['c'] != SKY]
def line(t):
    x, y = ctr(t)
    if t['c'] == NAVY: return 5                                  # 물결 밑줄 + 신뢰구간(청색)
    if y < 300: return 0 if x < 2240 else 1                      # p̂~N(p,pq/n) / Z=(p̂−p)/√(pq/n)
    if y < 455: return 2                                         # P(−1.96≤Z≤1.96)=0.95
    if y < 640: return 3                                         # =P(−1.96√ ≤ p̂−p ≤ 1.96√)
    if y < 830: return 4                                         # =P(p̂−1.96√ ≤ p ≤ p̂+1.96√)
    return 6                                                     # √ 안의 pq 대신 p̂q̂ 대입 가능
COV1 = {0: [[1995, 70, 2040, 150], [2080, 40, 2165, 170]],       # p, pq/n
        1: [[2400, 35, 2580, 275]],                              # (p̂−p)/√(pq/n)
        2: [[2440, 325, 2600, 400]],                             # 0.95
        3: [[2160, 505, 2285, 600]],                             # p̂−p
        4: [[1805, 655, 2145, 805], [2312, 655, 2645, 805]],     # p̂−1.96√, p̂+1.96√
        6: [[2340, 840, 2445, 940]]}                             # p̂q̂
moved = [(line(t), t, shift(t, DX, DY, s=S1 + line(t))) for t in g1]
for ln, rects in COV1.items():
    for r in rects:
        grp = [u for l, t, u in moved if l == ln and inr(t, r)]
        assert grp, (ln, r)
        cover(grp, S1 + ln)
add += [u for _, _, u in moved]
b1 = box([u for _, _, u in moved])

# ---- 맨 아래(손풀이에 없는 내용): 2×1.96×√(p̂q̂/n) → 신뢰구간의 길이 ----
S7 = S1 + 7
old6 = [t for t in T['strokes'] if t['s'] == orig['n'] and not t.get('x')]   # 용어 정리 ⑥(지금 번호 5)
CY = sum(box([t for t in old6 if t['c'] == NAVY])[i] for i in (1, 3)) / 2     # 왼쪽 '신뢰구간의 길이'와 같은 높이
def piece(ts, x, color=None):
    """ts를 왼쪽 끝 x, 세로 가운데 CY에 놓음 → (옮긴 획, 오른쪽 끝)"""
    b = box(ts); kw = dict(s=S7);
    if color: kw['c'] = color
    return [shift(t, x - b[0], CY - (b[1] + b[3]) / 2, **kw) for t in ts], x + b[2] - b[0]
two = [t for t in Q11['strokes'] if t['s'] == 0 and inr(t, [1830, 170, 2115, 260])]      # 2×1.96×
root = [t for t in Q13['strokes'] if t['s'] == 1 and inr(t, [1925, 245, 2100, 400])]     # √(p̂q̂/n) — 12번 ②의 것은 q̂를 덧쓴 자국이 있어 13번 ② 것을 씀
arrow = [t for t in old6 if t['c'] == NAVY and bb(t)[2] < 1065]
word = [t for t in old6 if t['c'] == NAVY and bb(t)[2] >= 1065]
wtot = sum(box(p)[2] - box(p)[0] for p in (two, root, arrow, word)) + 18 + 30 + 24
x = (b1[0] + b1[2]) / 2 - wtot / 2
f1, x = piece(two, x, GREEN); f2, x = piece(root, x + 18, GREEN)
a1, x = piece(arrow, x + 30, NAVY); w1, x = piece(word, x + 24, NAVY)
cover(f1 + f2, S7)                                               # 식은 가리고, → 신뢰구간의 길이만 먼저 보임
add += f1 + f2 + a1 + w1

T['strokes'] += add
T['n'] = S7 + 1
W = int(round(max(orig['w'], box(add)[2] + 40))); H = int(round(max(orig['h'], box(add)[3] + 40)))
img = Image.new('1', (W, H), 1); bio = io.BytesIO(); img.save(bio, 'PNG', optimize=True)
T.update(w=W, h=H, base='data:image/png;base64,' + base64.b64encode(bio.getvalue()).decode())
T['p21'] = orig

data = json.dumps(D, ensure_ascii=False, separators=(',', ':'))
t = open(os.path.join(here, 'template.html'), encoding='utf-8').read()
html = t.replace('__TITLE__', title).replace('__APPS__', apps).replace('__DATA__', data)
os.makedirs(out, exist_ok=True)
open(f'{out}/artifact.html', 'w', encoding='utf-8').write(html)
a_ = html.index('</style>', html.index('<style>')) + len('</style>')
doc = ('<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
       '<style>html,body{margin:0}[hidden]{display:none!important}img{max-width:100%}</style>\n'
       + html[:a_] + '\n</head>\n<body>\n' + html[a_:] + '\n</body>\n</html>\n')
open(f'{out}/hak21.html', 'w', encoding='utf-8').write(doc)
print('ok', W, H, '단계', T['n'], '넣은 획', len(add), '가리개', len(covers) - orig['ncov'],
      '2×1.96×', len(two), '√', len(root), '화살표', len(arrow), '용어', len(word), round(len(doc) / 1e6, 2), 'MB')
