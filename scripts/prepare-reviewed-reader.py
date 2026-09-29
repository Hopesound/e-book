from pathlib import Path
p=Path('scripts/parallel-reader-template.html').read_text(encoding='utf-8-sig')
p=p.replace('.leafhead{height:88px','.leafhead{height:108px')
p=p.replace('.text-scroll details{','.text-scroll [lang="ja"] p{word-break:normal;line-height:1.9}.text-scroll details{')
p=p.replace('<button class="btn" id="infoBtn">편집 안내</button>','<button class="btn" id="pairedBtn">원문 전사 부록 ↗</button><button class="btn" id="infoBtn">편집 안내</button>')
p=p.replace('<span>번역 글자</span>','<span>본문 글자</span>')
p=p.replace('<span>한국어 번역</span><span class="tag"','<span id="rightLabel">한국어 번역</span><span class="tag"')
p=p.replace('<span>발췌·초안 수록본</span>','<span>2026.09.30 개정</span>')
p=p.replace('오른쪽에는 제공된 한국어 번역을 담았습니다.','오른쪽에는 원문과 대조하여 다시 옮긴 한국어 번역을 담았습니다.')
p=p.replace('인쇄면 1~27쪽 범위의 대역 20개입니다. 두 원고의 범위가 겹치는 8~10쪽을 보존했습니다.','인쇄면 1~27쪽의 본문 뒤에 같은 쪽수의 일본어 원문 전사 부록을 실었습니다.')
p=p.replace('발췌·초안 수록본으로 책 전체의 완역이 아닙니다. 스캔 16·20면은 한국어 번역 보류 상태이며, 원문 이미지는 열람할 수 있습니다.','수록 범위의 문장·항목·서식을 재번역한 판입니다. 원서 28쪽 이후는 이번 수록 범위에 포함되지 않습니다.')
p=p.replace("const key='ndl1878691.parallel.v1';","const key='ndl1878691.parallel.v2';")
p=p.replace("Math.min(19,saved.page)","Math.min(book.units.length-1,saved.page)")
p=p.replace("v<20","v<book.units.length")
p=p.replace("String(i+1).padStart(2,'0')+' / 20 · '+u.label","(u.part===1?'본문':'부록')+' · '+u.label")
start=p.index('function render(){')
end=p.index('function toc()',start)
p=p[:start]+"""
function render(){
const u=book.units[index];const main=u.part===1;
$('scanLabel').textContent='NDL '+u.scan+'면';$('sourceLabel').textContent=u.label;
$('title').textContent=u.title;$('status').textContent=u.status;
$('rightLabel').textContent=main?'한국어 번역':'日本語 転記';
document.querySelector('.translation').setAttribute('aria-label',main?'오른쪽 한국어 번역':'오른쪽 일본어 원문 전사');
$('text').setAttribute('aria-label',main?'한국어 재번역 내용':'일본어 원문 전사 내용');
$('manuscript').textContent=main?'본문 · 원문 대조 재번역':'맨 뒤 부록 · 쪽별 원문 전사';
$('pairedBtn').textContent=main?'원문 전사 부록 ↗':'한국어 번역 본문 ↗';
$('pairedBtn').title=u.label+'의 '+(main?'일본어 전사':'한국어 번역')+'로 이동';
$('scanImage').src=book.assets[String(u.page)];$('scanImage').alt=u.label+' 일본어 원문 스캔';
$('sourceLink').href=u.url;$('text').replaceChildren();
for(const [heading,paragraphs] of u.blocks){
 const s=el('section');s.lang=main?'ko':'ja';s.append(el('h3',heading));
 for(const text of paragraphs)s.append(el('p',text));$('text').append(s);
}
if(u.notes.length){const s=el('section',undefined,'editorial');s.lang='ko';s.append(el('h3','편집 주'));for(const text of u.notes)s.append(el('p',text));$('text').append(s)}
const jump=el('button',main?'이 쪽의 일본어 원문 전사 보기 →':'이 쪽의 한국어 번역 보기 →','btn');jump.onclick=()=>go(main?index+27:index-27);$('text').append(jump);
$('text').scrollTop=0;$('imageScroll').scrollTop=0;$('imageScroll').scrollLeft=0;$('zoom').value=100;zoom();
$('pageSelect').value=index;$('prev').disabled=index===0;$('next').disabled=index===book.units.length-1;
$('locationLabel').textContent=(main?'본문':'원문 전사 부록')+' '+u.page+' / 27';
markset();fontset();document.title=(main?'본문 ':'부록 ')+u.label+' · 조선토지조사사업보고서 추록';
$('announcement').textContent=(main?'본문 ':'부록 ')+u.label+' · '+u.title;
persist()
}
function go(n){if(n>=0&&n<book.units.length){index=n;render()}}
$('pairedBtn').onclick=()=>go(index<27?index+27:index-27);
""" +p[end:]
p=p.replace("'해당하는 대역면이 없습니다.'","'해당하는 본문 또는 부록 쪽이 없습니다.'")
p=p.replace("String(i+1).padStart(2,'0'),'toc-num'","(u.part===1?'본문 ':'부록 ')+u.page,'toc-num'")
p=p.replace('.toc-num{font-size:12px;color:var(--accent);min-width:30px}', '.toc-num{font-size:12px;color:var(--accent);min-width:55px}')
p=p.replace("목차와 번역문 검색","목차와 번역문·일본어 전사 검색").replace("제목·쪽수·번역문에서 검색","제목·쪽수·한국어·일본어 검색")
p=p.replace('각 페이지 안에서는 따로 스크롤합니다.','각 페이지 안에서는 따로 스크롤합니다. 본문 27개 뒤에 전사 부록 27개가 이어집니다. 상단 버튼으로 같은 쪽의 번역과 전사를 오갈 수 있습니다.')
p=p.replace('번역 글자는 14~28px','본문 글자는 14~28px')
p=p.replace("const first=!saved.seen;render();","const hash=location.hash.slice(1);const found=book.units.findIndex(u=>u.id===hash);if(found>=0)index=found;const first=!saved.seen;render();")
Path('scripts/reviewed-reader-template.html').write_text(p,encoding='utf8')

