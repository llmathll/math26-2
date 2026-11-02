#!/usr/bin/env python3
"""보라색 닫힌 테두리를 찾아 단계 영역 후보를 만든다(설정 초안용).
사용: python3 loops.py <손풀이.pdf 또는 렌더 png> <페이지번호> <출력.png>
- 후보마다 [x0,y0,x1,y1](페이지 가로 2000 기준)를 출력하고, 미리보기 그림에 번호를 붙인다.
- 원 번호(①②…)는 작은 고리로 따로 표시한다(small). 어느 번호가 어느 영역인지는 그림을 보고 정한다.
"""
import sys, subprocess, os, cv2, numpy as np
src, page, outp = sys.argv[1], int(sys.argv[2]), sys.argv[3]
if src.lower().endswith('.pdf'):
    pre = '/tmp/_loops'; subprocess.run(['pdftoppm', '-r', '200', '-f', str(page), '-l', str(page), '-png', src, pre], stderr=subprocess.DEVNULL)
    f = [x for x in os.listdir('/tmp') if x.startswith('_loops') and x.endswith('.png')]; im = cv2.imread('/tmp/' + sorted(f)[-1])
else:
    im = cv2.imread(src)
S = im.shape[1] / 2000
hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV); h, s, v = cv2.split(hsv)
pur = ((h >= 136) & (h <= 170) & (s > 55) & (v < 240)).astype(np.uint8) * 255
pur = cv2.morphologyEx(pur, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(9 * S) | 1, int(9 * S) | 1)))
cnts, hier = cv2.findContours(pur, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
vis = im.copy(); k = 0
for i, c in enumerate(cnts):
    if hier[0][i][3] < 0: continue          # 안쪽 구멍(=닫힌 고리 내부)만
    x, y, w, hh = cv2.boundingRect(c); a = cv2.contourArea(c)
    if a < (12 * S) ** 2: continue
    k += 1; small = max(w, hh) < 45 * S
    col = (0, 160, 0) if small else (0, 0, 230)
    cv2.rectangle(vis, (x, y), (x + w, y + hh), col, 2)
    cv2.putText(vis, str(k), (x + 2, y + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, col, 2)
    r = [round(x / S), round(y / S), round((x + w) / S), round((y + hh) / S)]
    print(k, 'small(원번호 후보)' if small else 'area', r)
cv2.imwrite(outp, vis); print('->', outp)
