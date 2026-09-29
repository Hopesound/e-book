const {chromium}=require('C:/Users/kwg/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url');
(async()=>{
const root='E:/A programm/upload/e-book',out=path.join(root,'tmp/ebook-review');
const html=fs.readdirSync(path.join(root,'output/ebook')).find(x=>x.endsWith('.html'));
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
const context=await browser.newContext({viewport:{width:1500,height:1020},deviceScaleFactor:1});
const p=await context.newPage(),errors=[];p.on('pageerror',e=>errors.push(e.message));
await p.goto(pathToFileURL(path.join(root,'output/ebook',html)).href);
await p.locator('#start').click();
await p.locator('#scanImage').evaluate(im=>im.decode());
await p.screenshot({path:path.join(out,'html-desktop.png')});
const all=[];
for(let i=0;i<20;i++){
await p.locator('#pageSelect').selectOption(String(i));await p.locator('#scanImage').evaluate(im=>im.decode());
all.push(await p.evaluate(()=>({title:document.getElementById('title').textContent,label:document.getElementById('sourceLabel').textContent,img:document.getElementById('scanImage').naturalWidth,text:document.getElementById('text').textContent.length,left:document.querySelector('.original').getBoundingClientRect().x,right:document.querySelector('.translation').getBoundingClientRect().x})));
}
if(all.some(v=>!v.img||v.text<100||v.left>=v.right))throw Error('Missing content / layout');
await p.locator('#pageSelect').selectOption('10');await p.locator('#scanImage').evaluate(im=>im.decode());
await p.screenshot({path:path.join(out,'html-two-original-pages.png')});
await p.locator('#zoom').fill('200');await p.locator('#zoom').dispatchEvent('input');
const zoomed=await p.locator('#imageFrame').evaluate(e=>e.clientWidth>e.parentElement.clientWidth);
if(!zoomed)throw Error('Image zoom failed');
await p.locator('#resetZoom').click();
await p.locator('#fontUp').click();
await p.locator('#markBtn').click();
await p.reload();
if(await p.locator('#pageSelect').inputValue()!=='10')throw Error('Reading position lost');
if(await p.locator('#markBtn').getAttribute('aria-pressed')!=='true')throw Error('Bookmark lost');
if(await p.locator('#fontOut').textContent()!=='19px')throw Error('Font preference lost');
await p.locator('#tocBtn').click();
await p.locator('#search').fill('지적');
const hits=await p.locator('.toc-row').count();if(!hits||hits===20)throw Error('Search did not narrow');
await p.locator('#search').fill('xyznotfound');
if(await p.locator('.toc-row').count()!==0)throw Error('Empty search incorrect');
await p.locator('#search').fill('');await p.locator('#marksOnly').check();
if(await p.locator('.toc-row').count()!==1)throw Error('Bookmark filter failed');
await p.locator('#tocDialog [data-close]').click();
await p.locator('#pageSelect').selectOption('15');
if(!((await p.locator('#status').textContent()).includes('보류')))throw Error('Missing pending translation label');
await p.setViewportSize({width:390,height:844});
await p.screenshot({path:path.join(out,'html-mobile.png')});
await p.setViewportSize({width:1200,height:840});
const epub=[];
for(const name of fs.readdirSync(path.join(out,'epub')).filter(n=>n.endsWith('.xhtml'))){
await p.goto(pathToFileURL(path.join(out,'epub',name)).href);await p.evaluate(()=>document.fonts.ready);
const r=await p.evaluate(()=>{const body=document.querySelector('.body'),foot=document.querySelector('.foot');const images=[...document.images];return {bodyBottom:body?body.getBoundingClientRect().bottom:null,footerTop:foot?foot.getBoundingClientRect().top:null,brokenImages:images.some(x=>!x.complete||!x.naturalWidth),height:document.body.scrollHeight,lastBottom:Math.max(...[...document.querySelectorAll('p,li')].map(e=>e.getBoundingClientRect().bottom),0)}});
epub.push({name,...r});
if(name==='s11.xhtml'||name==='p1.xhtml'||name==='nav.xhtml')await p.screenshot({path:path.join(out,'epub-'+name+'.png')});
}
await browser.close();
const result={html_units:all,search_hits:hits,zoomed,bookmark_and_position:true,errors,epub};
fs.writeFileSync(path.join(out,'browser-validation.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify({html_units:all.length,search_hits:hits,zoomed,bookmark_and_position:true,errors,epub_overflow:epub.filter(x=>(x.bodyBottom&&x.bodyBottom>x.footerTop-5)||x.brokenImages||x.lastBottom>817)}));
if(errors.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});

