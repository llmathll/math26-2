"""PDF 페이지에서 펜 획(벡터 경로)을 그려진 순서대로 뽑는다: 점(top 기준 pt), 굵기, 색, 점선, 투명도."""
import pikepdf, math
def mul(a,b):  # 3x3 affine as (a,b,c,d,e,f)
    return (a[0]*b[0]+a[1]*b[2], a[0]*b[1]+a[1]*b[3], a[2]*b[0]+a[3]*b[2], a[2]*b[1]+a[3]*b[3], a[4]*b[0]+a[5]*b[2]+b[4], a[4]*b[1]+a[5]*b[3]+b[5])
def extract(path, pageno):
    pdf=pikepdf.open(path); pg=pdf.pages[pageno-1]
    H=float(pg.mediabox[3]); gsr=pg.Resources.get('/ExtGState',{})
    st=dict(ctm=(1,0,0,1,0,0),w=1.0,sc=(0,0,0),fc=(0,0,0),dash=None,CA=1.0,ca=1.0,bm='Normal')
    stack=[]; cur=[]; sub=None; out=[]
    def T(x,y):
        a,b,c,d,e,f=st['ctm']; X=a*x+c*y+e; Y=b*x+d*y+f; return (X,H-Y)
    for operands,op in pikepdf.parse_content_stream(pg):
        o=str(op); v=[float(x) if isinstance(x,(int,float)) or type(x).__name__ in('Decimal',) else x for x in operands]
        try: v=[float(x) for x in operands]
        except Exception: pass
        if o=='q': stack.append(dict(st))
        elif o=='Q': st=stack.pop() if stack else st
        elif o=='cm': st['ctm']=mul(tuple(float(x) for x in operands),st['ctm'])
        elif o=='w': st['w']=float(operands[0])
        elif o=='d':
            arr=[float(x) for x in operands[0]]; st['dash']=arr if arr else None
        elif o in('SC','SCN','RG') and len(operands)>=3: st['sc']=tuple(float(x) for x in operands[:3])
        elif o in('sc','scn','rg') and len(operands)>=3: st['fc']=tuple(float(x) for x in operands[:3])
        elif o=='G': st['sc']=(float(operands[0]),)*3
        elif o=='g': st['fc']=(float(operands[0]),)*3
        elif o=='gs':
            g=gsr.get(str(operands[0]),{})
            if '/CA' in g: st['CA']=float(g['/CA'])
            if '/ca' in g: st['ca']=float(g['/ca'])
            if '/BM' in g: st['bm']=str(g['/BM']).strip('/')
        elif o=='m': sub=[('M',T(*map(float,operands)))]; cur.append(sub)
        elif o=='l' and sub is not None: sub.append(('L',T(*map(float,operands))))
        elif o=='c' and sub is not None:
            p=list(map(float,operands)); sub.append(('C',T(p[0],p[1]),T(p[2],p[3]),T(p[4],p[5])))
        elif o in('v','y') and sub is not None:
            p=list(map(float,operands)); last=sub[-1][-1]
            if o=='v': sub.append(('C',last,T(p[0],p[1]),T(p[2],p[3])))
            else: sub.append(('C',T(p[0],p[1]),T(p[2],p[3]),T(p[2],p[3])))
        elif o=='h' and sub is not None: sub.append(('Z',))
        elif o=='re':
            x,y,w,h=map(float,operands); sub=[('M',T(x,y)),('L',T(x+w,y)),('L',T(x+w,y+h)),('L',T(x,y+h)),('Z',)]; cur.append(sub)
        elif o in('S','s','f','F','f*','B','B*','b','b*','n'):
            if o!='n' and cur:
                a,b,c,d,_,_=st['ctm']; sc=math.sqrt(abs(a*d-b*c))
                out.append(dict(subs=cur, stroke=o in('S','s','B','B*','b','b*'), fill=o in('f','F','f*','B','B*','b','b*'),
                    w=st['w']*sc, sc=st['sc'], fc=st['fc'], dash=[x*sc for x in st['dash']] if st['dash'] else None,
                    CA=st['CA'], ca=st['ca'], bm=st['bm']))
            cur=[]; sub=None
    return out
