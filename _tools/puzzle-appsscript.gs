/****************************************************************
 * 형성평가(퍼즐 퀴즈) 결과 저장용 Apps Script
 *
 * [설치 순서 — PC에서 약 10분]
 * 1. 구글 시트를 새로 만든다. (이름 예: 형성평가 결과)
 * 2. 메뉴 [확장 프로그램] → [Apps Script] 를 연다.
 * 3. 원래 있던 코드를 모두 지우고 이 파일 내용을 붙여넣은 뒤 저장(Ctrl+S).
 * 4. 오른쪽 위 [배포] → [새 배포] → 톱니바퀴에서 [웹 앱] 선택
 *      - 다음 사용자로서 실행: 나
 *      - 액세스 권한이 있는 사용자: 모든 사용자
 *    → [배포] → 권한 승인(내 계정 선택 → '고급' → '안전하지 않은 페이지로 이동' → 허용)
 * 5. 나오는 '웹 앱 URL'(…/exec 로 끝남)을 복사해서
 *    puzzle-quiz.html 과 puzzle-board.html 맨 위의 API = '' 따옴표 안에 붙여넣는다.
 *
 * [시트 탭] 처음 제출이 들어오면 자동으로 만들어진다.
 *  - 제출기록 : 학생이 한 문항을 끝낼 때마다 한 줄씩 쌓임
 *  - 명단     : (선택) 반 | 번호 | 이름 을 적어 두면 학생 화면에서 "김○정 학생이 맞나요?" 확인
 *               비워 두면 이름 확인 없이 바로 시작
 *
 * 코드를 고친 뒤에는 [배포] → [배포 관리] → 연필 → 버전 '새 버전' → [배포] 해야 반영된다.
 ****************************************************************/

const HEADER = ['시각', '퀴즈', '반', '번호', '문항', '첫시도', '최종', '시도', '오답'];

function getSheet_(name, header) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
    if (header) { sh.appendRow(header); sh.setFrozenRows(1); }
  }
  return sh;
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

/* 이름 가리기: 김민정 → 김○정, 이준 → 이○ */
function mask_(name) {
  name = String(name || '').trim();
  if (name.length <= 1) return name;
  if (name.length === 2) return name[0] + '○';
  return name[0] + '○'.repeat(name.length - 2) + name[name.length - 1];
}

/* 읽기: 이름 확인, 칠판용 통계 */
function doGet(e) {
  const p = e.parameter || {};

  if (p.action === 'name') {
    const sh = getSheet_('명단', ['반', '번호', '이름']);
    const v = sh.getDataRange().getValues();
    for (let i = 1; i < v.length; i++) {
      if (String(v[i][0]) === String(p.cls) && String(v[i][1]) === String(p.num)) {
        return json_({ ok: true, name: mask_(v[i][2]) });
      }
    }
    return json_({ ok: true, name: '' });
  }

  if (p.action === 'stats') {
    const sh = getSheet_('제출기록', HEADER);
    const v = sh.getDataRange().getValues();
    const rows = [];
    for (let i = 1; i < v.length; i++) {
      const r = v[i];
      if (String(r[1]) === String(p.quiz) && String(r[2]) === String(p.cls)) {
        rows.push({ num: Number(r[3]), q: Number(r[4]), first: r[5], fin: r[6], wrong: String(r[8] || '') });
      }
    }
    return json_({ ok: true, rows: rows });
  }

  return json_({ ok: false, msg: 'unknown action' });
}

/* 쓰기: 학생이 문항 하나를 끝낼 때마다 호출됨 */
function doPost(e) {
  const d = JSON.parse(e.postData.contents);
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    getSheet_('제출기록', HEADER).appendRow([
      new Date(), d.quiz, Number(d.cls), Number(d.num), Number(d.q),
      d.first, d.fin, Number(d.attempts), (d.wrong || []).join(' | ')
    ]);
  } finally {
    lock.releaseLock();
  }
  return json_({ ok: true });
}
