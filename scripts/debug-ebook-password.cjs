const {chromium}=require('C:/Users/kwg/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const {pathToFileURL}=require('url');
(async()=>{const b=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
try{
 const p=await b.newPage();p.on('pageerror',e=>console.log('PAGEERROR',e.message));
 await p.goto(pathToFileURL('E:/A programm/upload/e-book/output/ebook/조선토지조사사업보고서추록_일한대역.html').href);
 for(let turn=0;turn<2;turn++){
  await p.locator('#password').fill(process.env.EBOOK_PASSWORD);await p.locator('#unlockButton').click();
  await p.waitForFunction(()=>document.getElementById('scanImage')||document.getElementById('feedback')?.textContent.includes('올바르지'));
  console.log('UNLOCK',turn,await p.evaluate(()=>({url:location.href,title:document.title,feedback:document.getElementById('feedback')?.textContent,img:document.getElementById('scanImage')?.getAttribute('src')?.slice(0,20),scripts:document.scripts.length})));
  if(await p.locator('#introDialog').isVisible())await p.locator('#start').click();
  if(await p.locator('#lockBook').count()){
   await p.locator('#lockBook').click();await p.locator('#password').waitFor();
   console.log('LOCK',turn,await p.title(),p.url());
  }
 }
 await p.screenshot({path:'E:/A programm/upload/e-book/tmp/ebook-password-stage/debug-unlock.png'});
}finally{await b.close()}})().catch(e=>{console.error(e);process.exitCode=1});

