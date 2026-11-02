#!/usr/bin/env python3
"""손풀이 PDF + 문제만 PDF -> 수업 화면 데이터(data.json)

사용: python3 hakbuild.py <cfg.py> <outdir>
좌표 단위: 페이지 가로 = 2000 (세로는 같은 비율). 미리보기 이미지를 2000px 폭으로 보고 읽은 값 그대로 쓴다.
"""
import sys, os, io, json, base64, subprocess, importlib.util
import cv2, numpy as np
from PIL import Image

cfg_path, outdir = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location('cfg', cfg_path); C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
DPI = getattr(C, 'DPI', 500)
os.makedirs(f'{outdir}/render', exist_ok=True); os.makedirs(f'{outdir}/check', exist_ok=True)

def render(pdf, tag):
    pre = f'{outdir}/render/{tag}'
    if not os.path.exists(pre + '-1.png'):
        subprocess.run(['pdftoppm', '-r', str(DPI), '-png', pdf, pre], stderr=subprocess.DEVNULL)
    pages = {}
    i = 1
    while os.path.exists(f'{pre}-{i}.png') or os.path.exists(f'{pre}-0{i}.png'):
        f = f'{pre}-{i}.png' if os.path.exists(f'{pre}-{i}.png') else f'{pre}-0{i}.png'
        pages[i] = cv2.imread(f); i += 1
    return pages

MARK = render(C.MARKED, 'mark'); CLEAN = render(C.CLEAN, 'clean')
W = next(iter(MARK.values())).shape[1]
S = W / 2000.0; F = DPI / 200.0
def sc(r): return [int(round(v * S)) for v in r]
def K(n):
    m = max(1, int(round(n * F))); m += (m % 2 == 0)
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (m, m))
def rectmask(shape, rects):
    m = np.zeros(shape[:2], bool)
    for r in rects:
        x0, y0, x1, y1 = sc(r); m[y0:y1, x0:x1] = True
    return m

def colors(im, cl):
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV); h, s, v = cv2.split(hsv)
    hand = cv2.absdiff(im, cl).max(axis=2) > 40          # 문제만 PDF에 없는 픽셀 = 손글씨
    hand = cv2.dilate(hand.astype(np.uint8), K(3)).astype(bool)
    M = dict(
        purple=((h >= 136) & (h <= 170) & (s > 55) & (v < 240)),
        green=((h >= 40) & (h <= 85) & (s > 60) & (v < 225)),
        red=(((h < 8) | (h > 172)) & (s > 100) & (v > 110)),
        blue=((h >= 95) & (h <= 118) & (s > 25) & (v > 195)),     # 하늘색 형광/음영
        navy=((h >= 100) & (h <= 135) & (s > 140) & (v < 200)),   # 풀이 펜
    )
    for k in M: M[k] &= hand
    M['ink'] = M['green'] | M['red'] | M['navy']
    return M

def b64(a):
    b = io.BytesIO()
    Image.fromarray(cv2.cvtColor(a, cv2.COLOR_BGR2RGB)).quantize(colors=48, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(b, 'PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()

out = []; cache = {}
for idx, it in enumerate(C.ITEMS):
    if it.get('kind') == 'app':
        out.append(dict(kind='app', app=it['app'], sec=it['sec'], num=it['num'], toc=it.get('toc', it['num']), g=it.get('group', it['sec']), w=1600, h=900, n=0, steps=[]))
        print(idx, 'APP', it['app']); continue
    pg = it['page']; im = MARK[pg]; cl = CLEAN[pg]
    if pg not in cache: cache[pg] = colors(im, cl)
    M = cache[pg]
    region = rectmask(im.shape, [it['crop']])
    blank = rectmask(im.shape, it.get('blank', []))
    rule = rectmask(im.shape, getattr(C, 'RULES', {}).get(pg, []))
    ign = rectmask(im.shape, getattr(C, 'IGNORE', {}).get(pg, []))
    zone = region & ~blank & ~ign
    ink = M['ink'] & zone & ~rule
    blu = M['blue'] & zone
    pur = M['purple'] & zone
    steps = it['steps']; n = len(steps)
    claim = np.full(im.shape[:2], -1, np.int16)
    def take(i, r, mm):
        x0, y0, x1, y1 = sc(r); sub = mm[y0:y1, x0:x1] & (claim[y0:y1, x0:x1] < 0)
        claim[y0:y1, x0:x1][sub] = i
    for (si, r, name) in it.get('cm', []):          # 색별 지정 (적은 순서대로 먼저 차지)
        take(si, r, (ink | blu) if name == 'any' else (blu if name == 'blue' else M[name] & zone & ~rule))
    for i, st in enumerate(steps):
        for r in st.get('blue', []): take(i, r, blu)
    for i, st in enumerate(steps):
        for r in st.get('g', []): take(i, r, ink & M['green'])
    for i in sorted(range(n), key=lambda i: steps[i].get('prio', i)):
        for r in steps[i].get('rects', []): take(i, r, ink)
    left = (ink | blu) & (claim < 0)
    if left.any():                                    # 남은 잉크는 가장 가까운 단계로
        best = np.full(im.shape[:2], 1e9, np.float32); lab = np.full(im.shape[:2], -1, np.int16)
        for i in range(n):
            m = claim == i
            if not m.any(): continue
            d = cv2.distanceTransform((~m).astype(np.uint8), cv2.DIST_L2, 3)
            upd = d < best; best[upd] = d[upd]; lab[upd] = i
        claim[left] = lab[left]
    base = cl.copy()
    for r in it.get('baseblank', []) + getattr(C, 'BANNER', {}).get(pg, []):
        x0, y0, x1, y1 = sc(r); base[y0:y1, x0:x1] = 255
    base[blank] = 255
    bw = np.full(base.shape, 255, np.uint8); bw[region] = base[region]
    layers = []; allink = np.zeros(im.shape[:2], bool)
    for i in range(n):
        m = claim == i
        if not m.any(): print('   ! 단계', i + 1, '비어 있음'); continue
        md = cv2.dilate(m.astype(np.uint8), K(5)).astype(bool) & zone
        printed = (cv2.cvtColor(cl, cv2.COLOR_BGR2GRAY) < 200)
        md &= (~printed) | m
        other = (claim >= 0) & (claim != i)
        md &= ~cv2.dilate(other.astype(np.uint8), K(3)).astype(bool) | m
        md &= ~cv2.dilate(pur.astype(np.uint8), K(3)).astype(bool) | m
        allink |= md
        ys, xs = np.where(md); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        lay = np.full((y1 - y0, x1 - x0, 3), 255, np.uint8); sub = md[y0:y1, x0:x1]; lay[sub] = im[y0:y1, x0:x1][sub]
        layers.append(dict(step=i, X=x0, Y=y0, w=int(x1 - x0), h=int(y1 - y0), src=b64(lay)))
    for (si, until, r, name) in it.get('ghost', []):  # 빨간 덧칠 아래 원래 곡선을 남색으로 임시 표시
        gm = rectmask(im.shape, [r]) & M[name] & zone
        col = np.median(im[M['navy'] & zone], axis=0).astype(np.uint8)
        gm = cv2.dilate(gm.astype(np.uint8), K(3)).astype(bool)
        thin = cv2.erode(gm.astype(np.uint8), K(5)).astype(bool)
        ys, xs = np.where(gm); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        lay = np.full((y1 - y0, x1 - x0, 3), 255, np.uint8); sel = (thin if thin.sum() > 200 else gm)[y0:y1, x0:x1]; lay[sel] = col
        layers.append(dict(step=si, until=until, X=x0, Y=y0, w=int(x1 - x0), h=int(y1 - y0), src=b64(lay)))
    cont = ((cv2.cvtColor(bw, cv2.COLOR_BGR2GRAY) < 235) & region) | allink
    ys, xs = np.where(cont); pad = int(14 * S)
    bx0, by0 = max(0, xs.min() - pad), max(0, ys.min() - pad)
    bx1, by1 = min(bw.shape[1], xs.max() + pad), min(bw.shape[0], ys.max() + pad)
    for L in layers: L['x'] = int(L.pop('X') - bx0); L['y'] = int(L.pop('Y') - by0)
    base_c = bw[by0:by1, bx0:bx1]
    rec = dict(sec=it['sec'], num=it['num'], toc=it.get('toc', it['num']), g=it.get('group', it['sec']),
               w=int(bx1 - bx0), h=int(by1 - by0), n=n, base=b64(base_c), steps=layers)
    if it.get('link'): rec['link'] = it['link']; rec['linkName'] = it.get('linkName', '연결 자료')
    out.append(rec)
    # 점검용: 풀이 전체를 겹치고 단계 상자·번호 표시
    chk = base_c.astype(float) / 255
    for L in layers:
        if L.get('until'): continue
        arr = np.array(Image.open(io.BytesIO(base64.b64decode(L['src'].split(',')[1]))).convert('RGB'))[:, :, ::-1].astype(float) / 255
        chk[L['y']:L['y'] + L['h'], L['x']:L['x'] + L['w']] *= arr
    chk = (chk * 255).astype(np.uint8)
    for L in layers:
        if L.get('until'): continue
        cv2.rectangle(chk, (L['x'], L['y']), (L['x'] + L['w'], L['y'] + L['h']), (0, 140, 255), max(2, int(F)))
        cv2.putText(chk, str(L['step'] + 1), (L['x'] + 4, L['y'] + int(26 * F)), cv2.FONT_HERSHEY_SIMPLEX, 0.9 * F, (0, 0, 230), max(2, int(1.5 * F)))
    cv2.imwrite(f'{outdir}/check/{idx:02d}.png', cv2.resize(chk, None, fx=1200 / chk.shape[1], fy=1200 / chk.shape[1]))
    print(idx, it['sec'], it['num'], '단계', n, '남은잉크', int(left.sum()), '크기', base_c.shape[1], base_c.shape[0])
json.dump(out, open(f'{outdir}/data.json', 'w'))
print('data.json', round(os.path.getsize(f'{outdir}/data.json') / 1e6, 2), 'MB')
