// 점검 스크린샷: node shots.js <html> <outdir> [문항index...]
const {chromium}=require('playwright');const path=require('path');
(async()=>{const [,,file,outdir,...idx]=process.argv;const b=await chromium.launch();const errs=[];
 const pg=await b.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:2});
 pg.on('pageerror',e=>errs.push(e.message));
 await pg.goto('file://'+path.resolve(file));await pg.waitForTimeout(600);
 const n=await pg.$$eval('#toc button',x=>x.length);const list=idx.length?idx.map(Number):[...Array(n).keys()];
 for(const i of list){await pg.click(`#toc button[data-i="${i}"]`);await pg.waitForTimeout(250);
   await pg.screenshot({path:`${outdir}/q${String(i).padStart(2,'0')}-0.png`});
   await pg.keyboard.press('End');await pg.waitForTimeout(450);await pg.mouse.move(2,2);
   await pg.screenshot({path:`${outdir}/q${String(i).padStart(2,'0')}-all.png`});}
 console.log('errors',errs);await b.close();})();
