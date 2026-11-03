#!/usr/bin/env python3
"""저장소 최상위의 수업 화면·앱 HTML 목록으로 목차(index.html)를 만든다.
사용: python3 makeindex.py <저장소 폴더> [아티팩트용 출력 파일]
  - <저장소>/index.html 을 새로 쓴다(깃허브·컴퓨터 저장용, 전자칠판 바로가기 주소).
  - 두 번째 인자를 주면 아티팩트 게시용 조각도 쓴다.
  - 파일 이름 규칙: hak17 = 단원 수업 화면 / 17-13, 17-etc1, 17normal, 09sol-08 = 단원별 앱 / tong03-10 = 통수 앱
  - 새 파일을 올리거나 이름을 바꿀 때마다 다시 돌려 함께 커밋한다.
"""
import sys, os, re, json, glob, datetime

repo = sys.argv[1]
here = os.path.dirname(os.path.abspath(__file__))
files = []
for p in sorted(glob.glob(os.path.join(repo, '*.html'))):
    name = os.path.basename(p)
    fid = name[:-5]
    if fid == 'index':
        continue
    head = open(p, encoding='utf-8', errors='ignore').read(20000)
    m = re.search(r'<title>(.*?)</title>', head, re.S)
    full = (m.group(1).strip() if m else fid)
    f = dict(file=name, id=fid, full=full)
    # 제목 앞뒤의 문항번호·과목명 군더더기 정리
    t = re.sub(r'\s*·\s*확률과\s*통계\s*$', '', full)
    t = re.sub(r'^\s*(tong)?\d+(-\w+|\.)\s*·?\s*', '', t)  # '10-17 · ', '13. ', 'tong03-10 · '
    t = re.sub(r'^\s*\d+번\s*·\s*', '', t)
    if m2 := re.fullmatch(r'hak(\d+)', fid):
        f.update(kind='hak', unit=int(m2.group(1)), title=re.sub(r'\s*수업\s*풀이\s*$', '', full), order=0)
    elif m2 := re.fullmatch(r'tong(\d+)-(\w+)', fid):
        f.update(kind='tong', unit=int(m2.group(1)), short=m2.group(2), title=t, order=0)
    elif m2 := re.fullmatch(r'(\d{2})(.*)', fid):
        rest = m2.group(2)
        if re.fullmatch(r'sol-.*', rest):
            short, tag, order = rest[4:], '풀이', 1
        elif rest.startswith('-etc'):
            short, tag, order = rest[1:], '교과서 외', 2
        elif rest.startswith('-'):
            short, tag, order = rest[1:], '', 1
        else:
            short, tag, order = '개념', '', 0
        f.update(kind='unit', unit=int(m2.group(1)), short=short, tag=tag, title=t, order=order)
    else:
        f.update(kind='unit', unit=0, short=fid, title=t, order=9)
    files.append(f)

today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime('%Y-%m-%d')
frag = (open(os.path.join(here, 'index_template.html'), encoding='utf-8').read()
        .replace('__FILES__', json.dumps(files, ensure_ascii=False))
        .replace('__DATE__', today))
doc = ('<!doctype html>\n<html lang="ko">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
       '<style>html,body{margin:0}[hidden]{display:none!important}</style>\n')
i = frag.index('</style>') + len('</style>')
doc += frag[:i] + '\n</head>\n<body>\n' + frag[i:] + '\n</body>\n</html>\n'
open(os.path.join(repo, 'index.html'), 'w', encoding='utf-8').write(doc)
if len(sys.argv) > 2:
    open(sys.argv[2], 'w', encoding='utf-8').write(frag)
print('ok index.html', len(files), '개', {k: sum(f['kind'] == k for f in files) for k in ('hak', 'unit', 'tong')})
