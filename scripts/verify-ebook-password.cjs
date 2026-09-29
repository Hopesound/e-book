const {chromium}=require('C:/Users/kwg/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url');
(async()=>{
const root='E:/A programm/upload/e-book',out=path.join(root,'tmp/ebook-password-stage');
const url=pathToFileURL(path.join(root,'output/ebook/조선토지조사사업보고서추록_일한대역.html')).href;
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
const context=await browser.newContext({viewport:{width:1500,height:1020}});const page=await context.newPage(),errors=[];
page.on('pageerror',e=>errors.push(e.message));
await page.goto(url);await page.locator('#unlockForm').waitFor();
if(await page.locator('#scanImage').count()||await page.locator('#book-data').count())throw Error('Content visible before unlock');
await page.screenshot({path:path.join(out,'password-screen.png')});
await page.locator('#password').fill('wrong-access-password');await page.locator('#unlockButton').click();
await page.getByText('암호가 올바르지 않습니다. 다시 입력해 주세요.',{exact:true}).waitFor();
if(await page.locator('#book-data').count())throw Error('Wrong password exposed content');
async function unlock(){
 await page.locator('#password').fill(process.env.EBOOK_PASSWORD);
 await page.locator('#unlockButton').click();await page.locator('#scanImage').waitFor();
 if(await page.locator('#introDialog').isVisible())await page.locator('#start').click();
 await page.locator('#scanImage').evaluate(i=>i.decode());
}
await unlock();
if(await page.locator('#pageSelect option').count()!==54)throw Error('Missing pages');
await page.screenshot({path:path.join(out,'unlocked-reader.png')});
await page.locator('#pageSelect').selectOption('0');await page.locator('#pairedBtn').click();
if(await page.locator('#pageSelect').inputValue()!=='27')throw Error('Appendix navigation failed');
await page.locator('#pageSelect').selectOption('53');await page.locator('#scanImage').evaluate(i=>i.decode());
if(!(await page.locator('#text').innerText()).includes('驛屯土臺帳'))throw Error('Appendix text missing');
await page.locator('#lockBook').click();await page.locator('#unlockForm').waitFor();
if(await page.locator('#book-data').count())throw Error('Lock failed');
await unlock();
if(await page.locator('#pageSelect').inputValue()!=='53')throw Error('Reading position lost');
await page.reload();await page.locator('#unlockForm').waitFor();
if(await page.locator('#book-data').count())throw Error('Reload did not lock');
await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(out,'password-mobile.png')});
const result={locked_by_default:true,wrong_password_rejected:true,correct_password_opens:true,units:54,appendix_navigation:true,lock_button:true,reload_locks:true,reading_position_preserved:true,errors};
fs.writeFileSync(path.join(out,'browser-password-validation.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify(result,null,2));await browser.close();
if(errors.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});

