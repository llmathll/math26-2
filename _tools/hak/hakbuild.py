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
VECTOR = getattr(C, 'VECTOR', True)        # 손풀이를 PDF 펜 획(벡터)으로 그려 쓰는 순서대로 보여줌
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdfstrokes import extract as extract_paths
PATHS = {}
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
        yellow=((h >= 20) & (h <= 35) & (s > 60) & (v > 200)),    # 노란 형광펜(구분선 등)
    )
    for k in M: M[k] &= hand
    M['ink'] = M['green'] | M['red'] | M['navy'] | M['yellow']
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
    PIECES = it.get('pieces')
    def piece_of(x, y):                               # 원래 좌표(2000 기준) -> 그 점을 담은 조각
        for P in PIECES:
            for r in P['src']:
                if r[0] <= x <= r[2] and r[1] <= y <= r[3]: return P
        return None
    def mv(r):                                        # 원래 좌표 사각형 -> 옮긴 좌표 (중심이 든 조각 기준)
        P = piece_of((r[0] + r[2]) / 2, (r[1] + r[3]) / 2) if PIECES else None
        if not P: return r
        dx, dy = P['to']; return [r[0] + dx, r[1] + dy, r[2] + dx, r[3] + dy]
    if PIECES:                                        # pieces: 문항 조각을 옮겨 새로 배치한 가상 페이지
        vim = np.full_like(im, 255); vcl = np.full_like(cl, 255)
        for P in PIECES:
            dx, dy = sc([P['to'][0], P['to'][1]])
            for r in P['src']:
                x0, y0, x1, y1 = sc(r)
                vim[y0 + dy:y1 + dy, x0 + dx:x1 + dx] = im[y0:y1, x0:x1]
                if P.get('base', True): vcl[y0 + dy:y1 + dy, x0 + dx:x1 + dx] = cl[y0:y1, x0:x1]
        im, cl = vim, vcl
        M = colors(im, cl)
        it = dict(it); it['steps'] = [dict(st, **{k: [mv(r) for r in st[k]] for k in ('rects', 'blue', 'g') if k in st}) for st in it['steps']]
        it['cm'] = [(a, mv(r), c) for (a, r, c) in it.get('cm', [])]
    else:
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
        n_, lab_, st_, _ = cv2.connectedComponentsWithStats(cv2.dilate(left.astype(np.uint8), K(9)))
        print('   남은잉크 위치:', [[round(v / S) for v in (x, y, x + w, y + h)] for (x, y, w, h, a_) in st_[1:] if a_ > 30][:8])
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
    # paste: 문제만 PDF의 인쇄물(확률표 등)을 다른 위치에 붙여 처음부터 보이게 함. 페이지 밖(오른쪽·아래)도 허용
    PADR, PADB = int(500 * S), int(300 * S)
    bwP = np.full((bw.shape[0] + PADB, bw.shape[1] + PADR, 3), 255, np.uint8); bwP[:bw.shape[0], :bw.shape[1]] = bw
    extra = []; plays = []
    for ps in it.get('paste', []):
        src = CLEAN[ps.get('page', pg)]; x0, y0, x1, y1 = sc(ps['src']); ax, ay = sc(ps['at'])
        if 'step' in ps:                              # step: 처음엔 없다가 그 단계에서 나타남
            plays.append(dict(step=ps['step'] - 1, X=ax, Y=ay, w=int(x1 - x0), h=int(y1 - y0), src=b64(src[y0:y1, x0:x1].copy()), hl=1))
        else: bwP[ay:ay + (y1 - y0), ax:ax + (x1 - x0)] = src[y0:y1, x0:x1]
        extra.append((ax, ay, ax + x1 - x0, ay + y1 - y0))
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
    vstrokes = []
    if VECTOR:
        if pg not in PATHS: PATHS[pg] = extract_paths(C.MARKED, pg)
        kp = DPI / 72.0; rr = max(2, int(3 * F)); Hh, Ww = claim.shape
        rx0, ry0, rx1, ry1 = sc(it['crop'])
        for pth in PATHS[pg]:
            rgb = pth['sc'] if pth['stroke'] else pth['fc']
            r_, g_, b_ = [int(round(max(0, min(1, v)) * 255)) for v in rgb[:3]]
            if abs(r_ - 130) < 15 and abs(g_ - 33) < 15 and abs(b_ - 139) < 15: continue   # 보라 = 표시 전용
            segs = []; pts = []
            for sub in pth['subs']:
                for sg in sub:
                    if sg[0] == 'Z': segs.append(('Z',)); continue
                    q = [(x * kp, y * kp) for (x, y) in sg[1:]]; segs.append((sg[0], *q)); pts.append(q[-1])
            if not pts: continue
            if PIECES:                                # 획이 대부분 들어 있는 조각을 따라 옮김
                cnt_ = {}
                for (x, y) in pts:
                    P = piece_of(x / S, y / S)
                    if P is not None: cnt_[id(P)] = cnt_.get(id(P), 0) + 1
                if not cnt_: continue
                P = next(Q for Q in PIECES if id(Q) == max(cnt_, key=cnt_.get)); ox, oy = P['to'][0] * S, P['to'][1] * S
                segs = [sg if sg[0] == 'Z' else (sg[0], *[(x + ox, y + oy) for (x, y) in sg[1:]]) for sg in segs]
                pts = [(x + ox, y + oy) for (x, y) in pts]
            xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
            if max(xs) < rx0 or min(xs) > rx1 or max(ys) < ry0 or min(ys) > ry1: continue
            samp = pts[::max(1, len(pts) // 25)] + [pts[-1]]; votes = {}
            for (x, y) in samp:
                X, Y = int(x), int(y)
                if not (rr <= X < Ww - rr and rr <= Y < Hh - rr): continue
                win = claim[Y - rr:Y + rr + 1, X - rr:X + rr + 1]; win = win[win >= 0]
                if win.size: v = int(np.bincount(win).argmax()); votes[v] = votes.get(v, 0) + 1
            if not votes: continue
            st_, hits = max(votes.items(), key=lambda kv: kv[1])
            if hits < max(1, 0.3 * len(samp)): continue
            vstrokes.append(dict(s=st_, segs=segs, c='#%02x%02x%02x' % (r_, g_, b_), w=round(pth['w'] * kp, 2),
                f=bool(pth['fill'] and not pth['stroke']), dash=[round(x * kp, 2) for x in pth['dash']] if pth['dash'] else None,
                a=round(pth['CA'] if pth['stroke'] else pth['ca'], 2), mb=pth['bm'] == 'Multiply'))
    cont = ((cv2.cvtColor(bw, cv2.COLOR_BGR2GRAY) < 235) & region) | allink
    ys, xs = np.where(cont); pad = int(14 * S)
    cx0, cy0, cx1, cy1 = xs.min(), ys.min(), xs.max(), ys.max()
    for (ax0, ay0, ax1, ay1) in extra: cx0, cy0, cx1, cy1 = min(cx0, ax0), min(cy0, ay0), max(cx1, ax1), max(cy1, ay1)
    bx0, by0 = max(0, cx0 - pad), max(0, cy0 - pad)
    bx1, by1 = min(bwP.shape[1], cx1 + pad), min(bwP.shape[0], cy1 + pad)
    # hl: 그 단계에서 확률표 행 등에 형광 강조(반투명 노랑, 곱하기)
    layers += plays
    for (si, r) in it.get('hl', []):
        x0, y0, x1, y1 = sc(r); lay = np.zeros((y1 - y0, x1 - x0, 3), np.uint8); lay[:] = (92, 226, 255)
        layers.append(dict(step=si, X=x0, Y=y0, w=int(x1 - x0), h=int(y1 - y0), src=b64(lay), hl=1))
    for L in layers: L['x'] = int(L.pop('X') - bx0); L['y'] = int(L.pop('Y') - by0)
    base_c = bwP[by0:by1, bx0:bx1]
    rec = dict(sec=it['sec'], num=it['num'], toc=it.get('toc', it['num']), g=it.get('group', it['sec']),
               w=int(bx1 - bx0), h=int(by1 - by0), n=n - it.get('pre', 0), base=b64(base_c), steps=layers)
    if it.get('follow'): rec['follow'] = 1            # 폭에만 맞춰 공통 배율, 넘치는 아래쪽은 화면이 따라 내려감
    if it.get('follow'):                              # 줄 사이 빈 띠(문항 px): 따라 내려갈 때 화면 위 끝이 글자 중간을 자르지 않게
        ink = cv2.cvtColor(base_c, cv2.COLOR_BGR2GRAY) < 200
        al = np.zeros(ink.shape, bool); sub = allink[by0:by1, bx0:bx1]; al[:sub.shape[0], :sub.shape[1]] = sub
        row = (ink | al).any(axis=1); gaps = []; y = 0; H_ = len(row)
        while y < H_:
            if not row[y]:
                y1 = y
                while y1 < H_ and not row[y1]: y1 += 1
                if y1 - y >= int(4 * F): gaps.append(int((y + y1) // 2))
                y = y1
            else: y += 1
        rec['gaps'] = gaps
    if it.get('scale'): rec['scale'] = it['scale']    # 공통 배율에 곱하는 값(예 0.9: 이 문항만 조금 작게)
    if it.get('solo'): rec['solo'] = 1                # 공통 배율 계산에서 뺌(이 문항만 필요하면 조금 더 축소)
    if it.get('link'): rec['link'] = it['link']; rec['linkName'] = it.get('linkName', '연결 자료')
    PRE = it.get('pre', 0)                            # pre: 앞의 PRE개 단계는 처음부터 한꺼번에 보임(단계 번호 −1)
    if PRE:
        for t in vstrokes: t['s'] = -1 if t['s'] < PRE else t['s'] - PRE
        for L in layers: L['step'] = -1 if L['step'] < PRE else L['step'] - PRE
    if vstrokes:
        outS = []
        for t in vstrokes:
            d = []; ln = 0.0; last = None
            for sg in t.pop('segs'):
                if sg[0] == 'Z': d.append('Z'); continue
                q = [(x - bx0, y - by0) for (x, y) in sg[1:]]
                if sg[0] == 'M': d.append('M%.1f,%.1f' % q[0])
                elif sg[0] == 'L': d.append('L%.1f,%.1f' % q[0]); ln += float(np.hypot(q[0][0] - last[0], q[0][1] - last[1]))
                elif sg[0] == 'C':
                    d.append('C%.1f,%.1f %.1f,%.1f %.1f,%.1f' % (q[0] + q[1] + q[2]))
                    ln += float(np.hypot(q[0][0] - last[0], q[0][1] - last[1]) + np.hypot(q[1][0] - q[0][0], q[1][1] - q[0][1]) + np.hypot(q[2][0] - q[1][0], q[2][1] - q[1][1]))
                last = q[-1]
            t['d'] = ' '.join(d); t['l'] = round(ln, 1); outS.append(t)
        rec['strokes'] = outS
        rec['steps'] = [L for L in layers if False]      # 펜 획으로 그리므로 단계 그림은 싣지 않음
        cnt = np.bincount([t['s'] for t in outS if t['s'] >= 0], minlength=n - PRE)
        if (cnt == 0).any(): print('   ! 펜 획이 없는 단계:', [i + 1 for i in np.where(cnt == 0)[0]], '— 그 단계는 그림으로 대체')
        if (cnt == 0).any(): rec['steps'] = [L for L in layers if L['step'] in set(np.where(cnt == 0)[0].tolist()) and not L.get('until') and not L.get('hl')]
        rec['steps'] += [L for L in layers if L.get('hl')]
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
