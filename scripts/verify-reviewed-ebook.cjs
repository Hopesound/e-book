const {chromium}=require('C:/Users/kwg/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path'),{pathToFileURL}=require('url');
(async()=>{
const root='E:/A programm/upload/e-book',out=path.join(root,'tmp/ebook-review-v2');
const fname='조선토지조사사업보고서추록_일한대역.html';
const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
const context=await browser.newContext({viewport:{width:1500,height:1020},deviceScaleFactor:1});
const p=await context.newPage(),errors=[];p.on('pageerror',e=>errors.push(e.message));
await p.goto(pathToFileURL(path.join(root,'output/ebook',fname)).href);await p.locator('#start').click();
await p.locator('#scanImage').evaluate(im=>im.decode());await p.screenshot({path:path.join(out,'reader-main.png')});
const all=[];
for(let i=0;i<54;i++){
 await p.locator('#pageSelect').selectOption(String(i));await p.locator('#scanImage').evaluate(im=>im.decode());
 all.push(await p.evaluate(()=>({label:document.getElementById('sourceLabel').textContent,title:document.getElementById('title').textContent,rightLabel:document.getElementById('rightLabel').textContent,img:document.getElementById('scanImage').naturalWidth,text:document.getElementById('text').textContent.length,left:document.querySelector('.original').getBoundingClientRect().x,right:document.querySelector('.translation').getBoundingClientRect().x,overHeader:document.getElementById('title').getBoundingClientRect().bottom>document.querySelector('.translation .leafhead').getBoundingClientRect().bottom})));
}
if(all.some(v=>!v.img||v.text<150||v.left>=v.right||v.overHeader))throw Error('Content/layout missing '+JSON.stringify(all.filter(v=>v.overHeader)));
if(!(await p.locator('#next').isDisabled()))throw Error('Last page not last');
await p.locator('#pageSelect').selectOption('8');await p.locator('#pairedBtn').click();
if(await p.locator('#pageSelect').inputValue()!=='35')throw Error('Paired appendix wrong');
await p.screenshot({path:path.join(out,'reader-appendix.png')});
await p.locator('#pairedBtn').click();if(await p.locator('#pageSelect').inputValue()!=='8')throw Error('Return to translation failed');
await p.locator('#zoom').fill('200');await p.locator('#zoom').dispatchEvent('input');
if(!await p.locator('#imageFrame').evaluate(e=>e.clientWidth>e.parentElement.clientWidth))throw Error('Zoom failed');
await p.locator('#resetZoom').click();await p.locator('#fontUp').click();await p.locator('#markBtn').click();await p.reload();
if(await p.locator('#pageSelect').inputValue()!=='8'||await p.locator('#markBtn').getAttribute('aria-pressed')!=='true'||await p.locator('#fontOut').textContent()!=='19px')throw Error('Preferences lost');
await p.locator('#tocBtn').click();await p.locator('#search').fill('不符合調書');
const hits=await p.locator('.toc-row').count();if(!hits||hits===54)throw Error('Japanese search failed');
await p.locator('#search').fill('xyznone');if(await p.locator('.toc-row').count())throw Error('Empty search failed');
await p.locator('#search').fill('');await p.locator('#marksOnly').check();if(await p.locator('.toc-row').count()!==1)throw Error('Bookmark filter failed');
await p.locator('#tocDialog [data-close]').click();await p.setViewportSize({width:390,height:844});await p.screenshot({path:path.join(out,'reader-mobile.png')});
await p.setViewportSize({width:1200,height:840});
const epub=[];
for(const name of fs.readdirSync(path.join(out,'epub/OEBPS')).filter(n=>n.endsWith('.xhtml')&&n!=='nav.xhtml')){
 await p.goto(pathToFileURL(path.join(out,'epub/OEBPS',name)).href);await p.evaluate(()=>document.fonts.ready);
 await p.evaluate(()=>Promise.all([...document.images].map(i=>i.decode())));
 const r=await p.evaluate(()=>{const right=document.querySelector('.right'),back=document.querySelector('.back');const images=[...document.images];return {bodyBottom:right?right.getBoundingClientRect().bottom:null,backTop:back?back.getBoundingClientRect().top:null,brokenImages:images.some(x=>!x.complete||!x.naturalWidth),height:document.body.scrollHeight,lastBottom:Math.max(...[...document.querySelectorAll('p,li,h1,h2')].map(e=>e.getBoundingClientRect().bottom),0)}});
 epub.push({name,...r});
 if(['cover.xhtml','toc.xhtml','note.xhtml','p9.xhtml','p25.xhtml','a9.xhtml','a24.xhtml','p7.xhtml','appendix.xhtml'].includes(name))await p.screenshot({path:path.join(out,'epub-'+name+'.png')});
}
await browser.close();
const overflow=epub.filter(x=>(x.bodyBottom&&x.bodyBottom>x.backTop-6)||x.brokenImages||(!x.bodyBottom&&x.lastBottom>808));
const result={html_units:all,paired_navigation:true,search_hits:hits,preferences:true,errors,epub,overflow};
fs.writeFileSync(path.join(out,'browser-validation.json'),JSON.stringify(result,null,2));
console.log(JSON.stringify({html_units:all.length,epub_pages:epub.length,paired_navigation:true,search_hits:hits,preferences:true,errors,overflow},null,2));
if(errors.length||overflow.length)process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});

