"""손풀이 PDF에서 펜 획(손글씨 색 경로)만 지워 '문제만' PDF를 만든다. 사용: stripink.py in.pdf out.pdf"""
import sys, pikepdf
HW = {(0,3,71),(130,33,139),(0,117,0),(246,83,83),(136,200,255),(255,255,131)}
def key(v): return tuple(int(round(max(0,min(1,float(x)))*255)) for x in v[:3])
pdf = pikepdf.open(sys.argv[1])
PATH = {'m','l','c','v','y','h','re'}; PAINT = {'S','s','f','F','f*','B','B*','b','b*','n'}
for pg in pdf.pages:
    ops = pikepdf.parse_content_stream(pg); out = []; buf = []; sc = (0,0,0); fc = (0,0,0); st = []
    for operands, op in ops:
        o = str(op)
        if o == 'q': st.append((sc, fc))
        elif o == 'Q' and st: sc, fc = st.pop()
        if o in ('RG','SC','SCN') and len(operands) >= 3: sc = key(operands)
        if o in ('rg','sc','scn') and len(operands) >= 3: fc = key(operands)
        if o == 'G': sc = key([operands[0]]*3)
        if o == 'g': fc = key([operands[0]]*3)
        if o in PATH: buf.append((operands, op)); continue
        if o in PAINT:
            stroke = o in ('S','s','B','B*','b','b*'); fill = o in ('f','F','f*','B','B*','b','b*')
            hw = (stroke and sc in HW) or (fill and not stroke and fc in HW)
            if not hw: out += buf; out.append((operands, op))
            buf = []; continue
        out += buf; buf = []; out.append((operands, op))
    pg.Contents = pdf.make_stream(pikepdf.unparse_content_stream(out))
pdf.save(sys.argv[2]); print('ok')
