"""inkpaste.py — 손풀이 PDF에 이미 쓴 손글씨 획을 오려 다른 자리에 붙인 사본을 만든다(21단원~).

교사 글씨를 흉내 내지 않고, 손풀이에 있는 글자·기호 획(벡터)을 그대로 복사해 색만 바꿔 붙인다.
붙인 획은 보통 펜 획과 똑같이 hakbuild가 읽으므로, 빈 자리(어느 문항 칸에도 안 드는 곳)에 붙이고
그 문항의 `pieces`로 원하는 자리에 옮겨 단계로 쓴다.

사용: python3 inkpaste.py cfg.py 원본손풀이.pdf 출력.pdf
cfg의 INKPASTE = [dict(src_page=2, rect=[x0,y0,x1,y1], page=1, to=(x, y), color=(r,g,b), z=1.0), ...]
  - 좌표는 페이지 가로 2000 기준. rect 안에 통째로 든 획(보라·분홍 표시 제외)을 가져와
    그 묶음의 왼쪽 위가 (x, y)에 오도록 page 쪽에 붙인다. color를 주면 그 색으로, z는 배율.
  - (x, y) 대신 cy=로 세로 가운데를 맞출 수 있다: to=(x, None), cy=418
"""
import sys, importlib.util, os
import pikepdf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pdfstrokes import extract

spec = importlib.util.spec_from_file_location('cfg', sys.argv[1]); C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)
src_pdf, out_pdf = sys.argv[2], sys.argv[3]
pdf = pikepdf.open(src_pdf)
cache = {}
def paths(pg):
    if pg not in cache: cache[pg] = extract(src_pdf, pg)
    return cache[pg]
skip = lambda c: (abs(c[0] - 130) < 15 and abs(c[1] - 33) < 15 and abs(c[2] - 139) < 15) or (abs(c[0] - 230) < 15 and abs(c[1] - 124) < 15 and abs(c[2] - 131) < 15)
adds = {}
for E in C.INKPASTE:
    pg = E['src_page']; W = float(pdf.pages[pg - 1].mediabox[2]) - float(pdf.pages[pg - 1].mediabox[0]); u = 2000.0 / W
    x0, y0, x1, y1 = E['rect']; sel = []
    for t in paths(pg):
        rgb = t['sc'] if t['stroke'] else t['fc']; c = [int(round(v * 255)) for v in rgb[:3]]
        if skip(c): continue
        pts = [q for sub in t['subs'] for sg in sub if sg[0] != 'Z' for q in sg[1:]]
        if pts and all(x0 <= q[0] * u <= x1 and y0 <= q[1] * u <= y1 for q in pts): sel.append(t)
    if not sel: print('! 획 없음', E); continue
    allp = [q for t in sel for sub in t['subs'] for sg in sub if sg[0] != 'Z' for q in sg[1:]]
    bx, by = min(q[0] for q in allp) * u, min(q[1] for q in allp) * u
    bh = max(q[1] for q in allp) * u - by
    z = E.get('z', 1.0); tx, ty = E['to']
    if ty is None: ty = E['cy'] - bh * z / 2
    dp = pdf.pages[E['page'] - 1]; Wd = float(dp.mediabox[2]) - float(dp.mediabox[0]); Hd = float(dp.mediabox[3]) - float(dp.mediabox[1]); ud = 2000.0 / Wd
    P = lambda q: ((tx + (q[0] * u - bx) * z) / ud, (ty + (q[1] * u - by) * z) / ud)
    ops = []
    for t in sel:
        rgb = [v / 255 for v in E['color']] if E.get('color') else (t['sc'] if t['stroke'] else t['fc'])[:3]
        d = []
        for sub in t['subs']:
            for sg in sub:
                if sg[0] == 'Z': d.append('h'); continue
                q = [P(v) for v in sg[1:]]
                d.append(' '.join('%.3f %.3f' % v for v in q) + {'M': ' m', 'L': ' l', 'C': ' c'}[sg[0]])
        if t['stroke']: ops.append('%.4f %.4f %.4f RG %.3f w 1 J 1 j %s S' % (*rgb, t['w'] * z, ' '.join(d)))
        else: ops.append('%.4f %.4f %.4f rg %s f' % (*rgb, ' '.join(d)))
    adds.setdefault(E['page'], []).append('q 1 0 0 -1 %.4f %.4f cm %s Q' % (float(dp.mediabox[0]), Hd + float(dp.mediabox[1]), ' '.join(ops)))
    print('붙임', len(sel), '획', E.get('name', ''), '→ 쪽', E['page'], (round(tx), round(ty)))
for pg, L in adds.items():
    pdf.pages[pg - 1].contents_add(pikepdf.Stream(pdf, ('\n'.join(L)).encode()), prepend=False)
pdf.save(out_pdf)
