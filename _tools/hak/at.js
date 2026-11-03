// node at.js html item step out : step 화면(쓰기 완료 상태)
const {chromium}=require('playwright');const path=require('path');
(async()=>{const [,,f,...specs]=process.argv;const b=await chromium.launch();const pg=await b.newPage({viewport:{width:1920,height:1080}});
 await pg.goto('file://'+path.resolve(f));await pg.waitForTimeout(500);
 for(const sp of specs){const [i,s,out]=sp.split(':');
  await pg.click(`#toc button[data-i="${i}"]`);await pg.waitForTimeout(150);
  await pg.evaluate(n=>{go(p,+n,false)},s);await pg.waitForTimeout(500);await pg.mouse.move(2,2);
  await pg.screenshot({path:out});}
 await b.close()})();
