from pathlib import Path
import json,re,html,base64,zipfile,uuid,shutil,hashlib
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from pypdf import PdfReader
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/ebook';PDFOUT=ROOT/'output/pdf';REVIEW=ROOT/'tmp/ebook-review-v2'
NAME='조선토지조사사업보고서추록_일한대역'
for d in (OUT,PDFOUT,OUT/'assets',REVIEW):d.mkdir(parents=True,exist_ok=True)
backup=ROOT/'tmp/ebook-version-1'
if not backup.exists():
    backup.mkdir()
    for p in [OUT/(NAME+'.html'),OUT/(NAME+'.epub'),PDFOUT/(NAME+'.pdf'),OUT/'edition-data.json',OUT/'읽어주세요.txt',OUT/'제작검수.json']:
        if p.exists():shutil.copy2(p,backup/p.name)
pages=json.loads((ROOT/'manuscript/reviewed-pages.json').read_text(encoding='utf-8-sig'))[:7]
for suffix in ('08-14','15-18','19-22','23-27'):
    pages+=json.loads((ROOT/f'manuscript/pages-{suffix}.json').read_text(encoding='utf-8-sig'))
assert [p['page'] for p in pages]==list(range(1,28))
# Translate across a page break without breaking a Korean word in half.
pages[4]['ko'][-1]=pages[4]['ko'][-1].replace('이 토지대장 등…','이 토지대장 등록사항은…')
pages[5]['ko'][0]=pages[5]['ko'][0].replace('[5쪽에서 계속] …록사항은','[5쪽에서 계속] 이 등록사항은')
pages[21]['ko'][-1]=pages[21]['ko'][-1].replace('소작…','소작인…')
pages[22]['ko'][0]=pages[22]['ko'][0].replace('[22쪽에서 계속] 인 성명란에','[22쪽에서 계속] 소작인 성명란에')
for ix in (24,25):
    pages[ix]['ko']=[s.replace(' / ','\n') if s.startswith('면적 ') else s for s in pages[ix]['ko']]
(ROOT/'manuscript/complete-reviewed-edition.json').write_text(json.dumps(pages,ensure_ascii=False,indent=2),encoding='utf8')

def esc(s):return html.escape(s,quote=True)
notice=[
'수록 범위는 원서의 인쇄면 1~27쪽이다. 기존 두 첨부 원고가 다룬 범위를 통합했으며, 겹치던 8~10쪽은 한 번만 수록했다. 원서 전체의 완역본은 아니다.',
'본문은 왼쪽에 일본어 원문 스캔, 오른쪽에 새 한국어 번역을 놓았다. 기존 요약·발췌를 바탕으로 문장을 늘린 것이 아니라 원문 이미지를 대조하여 수록 범위의 본문·항목·서식을 다시 번역했다.',
'맨 뒤 부록에는 인쇄 쪽수별 일본어 전사를 실었다. 원문의 구자체와 역사적 가나 표기를 가능한 한 보존하되, 세로쓰기를 가로쓰기로 바꾸고 문단과 서식 항목을 읽기 쉽게 구분했다. 반복되는 난외 장·절 표제와 쪽수는 본문 전사에서 제외했다.',
'전사는 국립국회도서관 공개 OCR을 보조 자료로 삼아 원문 스캔과 대조해 교정했다. 작은 활자, 원문의 오식·교정 표시와 해석상의 사항은 해당 쪽의 편집 주에 밝혔으며, 전사는 원본 이미지와 함께 확인할 수 있다.',
'田·畓·垈는 각각 밭·논·대지로, 地積은 면적으로, 地籍은 지적으로 구분했다. 원문의 행정단위 府郡島는 부·군·도(島)로 옮겼다. 괄호 안의 서기 연도와 쪽 연결 안내는 독자를 위해 덧붙였다.',
'보고서 작성기관의 판단과 사업 성과에 관한 평가는 원문의 서술로서 옮겼다. 원문에 없는 역사 해설을 번역 본문에 섞지 않았다. 이 판은 AI가 원문을 대조하여 작성한 재번역·전사본이다.',
'인쇄면 1쪽은 NDL 스캔 7면 왼쪽이다. 스캔 8면은 인쇄면 2~3쪽이며 이후 스캔 20면은 26~27쪽이다. 27쪽 끝의 문장은 원서 28쪽으로 이어지므로 이번 판에서 종결되지 않는다.'
]
assets={};units=[]
for p in pages:
    n=p['page'];im=Image.open(ROOT/f'tmp/ebook-sources/full/p{n:02d}.jpg')
    im.thumbnail((1850,2600))
    fn=f'reviewed-page-{n:02d}.jpg';im.save(OUT/'assets'/fn,quality=90,optimize=True)
    assets[str(n)]='data:image/jpeg;base64,'+base64.b64encode((OUT/'assets'/fn).read_bytes()).decode()
    p['image']=fn;p['scan']=7+n//2;p['url']=f"https://dl.ndl.go.jp/pid/1878691/1/{p['scan']}"
for part in (1,2):
    for p in pages:
        n=p['page'];u=dict(p)
        u.update(id=('p' if part==1 else 'a')+str(n),part=part,label=f'인쇄면 {n}쪽',status='재번역' if part==1 else '원문 전사',
                 blocks=[('한국어 번역',p['ko'])] if part==1 else [('日本語 転記',p['ja'].split('\n'))])
        u['search']=' '.join([u['title'],u['label'],u['status'],u['ja'],' '.join(p['ko']),' '.join(p['notes'])])
        units.append(u)
book=dict(title='조선토지조사사업보고서 추록',subtitle='원문 대조 재번역 · 쪽별 일본어 전사',notice=notice,units=units,assets=assets)
(OUT/'edition-data.json').write_text(json.dumps({k:v for k,v in book.items() if k!='assets'},ensure_ascii=False,indent=2),encoding='utf8')
pdfmetrics.registerFont(TTFont('K','C:/Windows/Fonts/malgun.ttf'));pdfmetrics.registerFont(TTFont('KB','C:/Windows/Fonts/malgunbd.ttf'))
pdfmetrics.registerFontFamily('K',normal='K',bold='KB')
pdfmetrics.registerFont(TTFont('J','C:/Windows/Fonts/yumin.ttf'))
allchars=set(''.join(p['ja']+''.join(p['ko'])+''.join(p['notes']) for p in pages))
missing=sorted(c for c in allchars if not c.isspace() and ord(c) not in pdfmetrics.getFont('K').face.charToGlyph)
fallback_chars=missing
missing=[c for c in missing if ord(c) not in pdfmetrics.getFont('J').face.charToGlyph]
assert not missing,('Missing font glyphs',missing)
INK='#243C36';MUTED='#697568';PAPER='#F7F4EA';RED='#A24B3D';W,H=1200,840
def para(text,size=13,leading=None,color=INK,bold=False):
    markup=esc(text).replace('\n','<br/>')
    for ch in fallback_chars:markup=markup.replace(ch,'<font name="J">'+ch+'</font>')
    return Paragraph(markup,ParagraphStyle('p',fontName='KB' if bold else 'K',fontSize=size,leading=leading or size*1.65,textColor=HexColor(color),wordWrap='CJK'))
def draw(c,text,x,y,width,size=13,leading=None,color=INK,bold=False):
    p=para(text,size,leading,color,bold);_,ph=p.wrap(width,4000);p.drawOn(c,x,y-ph);return y-ph
def frame(c,label,number):
    c.setFillColor(HexColor(PAPER));c.rect(0,0,W,H,fill=1,stroke=0)
    c.setStrokeColor(HexColor('#CFD4C6'));c.line(46,786,1154,786);c.line(46,43,1154,43)
    draw(c,'조선토지조사사업보고서 추록',46,815,850,10,14)
    draw(c,label,920,815,235,10,14,color=MUTED)
    draw(c,'1919 원간 · 인쇄면 1~27쪽 · 원문 대조 재번역 및 일본어 전사',46,31,1000,9,12,color=MUTED)
    draw(c,str(number),1117,31,35,10,12,color=MUTED)
def textheight(u,size):
    h=sum(para(s,size).wrap(510,4000)[1]+8 for _,ps in u['blocks'] for s in ps)
    if u['notes']:h+=12+sum(para('주 '+s,10.3,16,color=MUTED).wrap(510,4000)[1]+6 for s in u['notes'])
    return h
for u in units:
    titleh=para(u['title'],18,26,bold=True).wrap(510,4000)[1]
    u['top']=720-titleh-17
    for size in [14,13.5,13,12.5,12,11.5,11]:
        if textheight(u,size)<u['top']-65:
            u['font']=size;u['height']=textheight(u,size);break
    else:raise ValueError(('Overflow',u['id'],textheight(u,11)))

pdfpath=PDFOUT/(NAME+'.pdf');c=canvas.Canvas(str(pdfpath),pagesize=(W,H),pageCompression=1)
c.setTitle(book['title']+' | 원문 대조 재번역 · 일본어 전사 부록')
c.setAuthor('원저: 朝鮮總督府臨時土地調査局 / AI 원문 대조 재번역·전사')
c.setSubject('인쇄면 1~27쪽. 왼쪽 일본어 원문, 오른쪽 한국어. 말미에 쪽별 원문 전사.')
c.bookmarkPage('cover');c.addOutlineEntry('표지','cover')
c.setFillColor(HexColor(INK));c.rect(0,0,W,H,fill=1,stroke=0)
c.setStrokeColor(HexColor('#91A396'));c.rect(46,46,W-92,H-92,fill=0,stroke=1)
draw(c,'HISTORICAL ARCHIVE / REVISED PARALLEL EDITION',85,747,1020,12,20,color='#D0D8C8')
draw(c,'조선토지조사\n사업보고서 추록',85,645,1010,49,76,color=PAPER,bold=True)
draw(c,'朝鮮土地調査事業報告書追錄',89,437,1000,23,35,color='#D0D8C8')
draw(c,'원문 대조 재번역 · 쪽별 일본어 전사',89,303,1020,25,39,color=PAPER)
draw(c,'일본어 원문을 왼쪽에, 한국어 번역을 오른쪽에.',89,244,1020,16,26,color='#D0D8C8')
draw(c,'인쇄면 1~27쪽 / 본문 27개 펼침면 + 전사 부록 27개 펼침면',89,156,1020,13,22,color='#D0D8C8')
draw(c,'1919 원간 · 국립국회도서관 소장 · 2026.09.30 개정',89,110,1020,11,18,color='#D0D8C8');c.showPage()
frame(c,'편집 안내',2);c.bookmarkPage('note');c.addOutlineEntry('편집 안내와 출처','note')
draw(c,'이 판의 범위와 편집 원칙',60,757,1080,27,40,bold=True)
y=697
for i,s in enumerate(notice,1):y=draw(c,f'{i:02d}  {s}',60,y,1080,13,21)-12
y=draw(c,'원문: 朝鮮総督府臨時土地調査局 편 / 朝鮮総督府 발행 / 1919.\n국립국회도서관 디지털컬렉션 · DOI 10.11501/1878691 · 공개 이미지 권리표시 PDM.\nhttps://dl.ndl.go.jp/pid/1878691\nOCR 보조 자료: https://lab.ndl.go.jp/dl/api/book/fulltext-json/1878691',60,y-5,1080,11,18,color=MUTED)
assert y>55;y=draw(c,'한 PDF 페이지 안에 좌우를 함께 배치했다. PDF 뷰어에서는 한 페이지 보기로 열람한다.',60,y-15,1080,11,18)
c.showPage()
frame(c,'목차',3);c.bookmarkPage('toc');c.addOutlineEntry('목차','toc')
draw(c,'본문과 부록 찾아보기',60,756,1040,27,40,bold=True)
draw(c,'본문: PDF 4~30쪽 / 맨 뒤 원문 전사 부록: PDF 32~58쪽',60,704,1040,12,20,color=MUTED)
for i,p in enumerate(pages):
    col=0 if i<14 else 1;r=i if i<14 else i-14;x=60+col*560;y=660-r*41
    draw(c,f'{p["page"]:02d}  {p["title"]}',x,y,505,11.5,16,bold=True)
    draw(c,f'본문 {p["page"]+3}  ·  부록 {p["page"]+31}',x+26,y-18,470,9,13,color=MUTED)
    c.linkRect('',f'p{p["page"]}',(x,y-16,x+505,y),relative=0,thickness=0)
    prefix=pdfmetrics.stringWidth(f'본문 {p["page"]+3}  ·  ','K',9)
    c.linkRect('',f'p{p["page"]}',(x+26,y-32,x+26+prefix-5,y-16),relative=0,thickness=0)
    c.linkRect('',f'a{p["page"]}',(x+26+prefix,y-32,x+26+prefix+75,y-16),relative=0,thickness=0)
c.showPage()
pdfstats=[]
for idx,u in enumerate(units):
    if idx==27:
        frame(c,'부록',31);c.bookmarkPage('appendix');c.addOutlineEntry('부록 · 쪽별 일본어 원문 전사','appendix',0)
        draw(c,'부록',75,708,1040,19,32,color=RED)
        draw(c,'쪽별 일본어 원문 전사',75,615,1040,40,62,bold=True)
        draw(c,'인쇄면 1~27쪽',75,491,1030,25,40)
        draw(c,'왼쪽 스캔과 오른쪽 전사를 대조하여 읽을 수 있다.\n인쇄 쪽수를 기준으로 한 쪽씩 구분하였다.\n세로쓰기 원문을 가로쓰기로 옮기고, 표·서식의 항목 관계를 풀어 적었다.',75,390,990,18,34)
        draw(c,'한글 번역은 앞의 본문에 수록되어 있다. 각 쪽의 ‘본문’ 링크로 돌아갈 수 있다.',75,211,1000,13,22,color=MUTED);c.showPage()
    num=idx+4+(1 if idx>=27 else 0)
    label=('본문' if u['part']==1 else '원문 전사 부록')+' · '+u['label']
    frame(c,label,num);c.bookmarkPage(u['id']);c.addOutlineEntry(label+' · '+u['title'],u['id'],0 if u['part']==1 else 1)
    c.setStrokeColor(HexColor('#CFD4C6'));c.line(600,66,600,768)
    draw(c,'日本語 原文',55,760,510,13,20)
    draw(c,u['label']+f' / NDL 스캔 {u["scan"]}면',55,733,500,11,18,color=MUTED)
    c.drawImage(str(OUT/'assets'/u['image']),55,77,width=514,height=620,preserveAspectRatio=True,anchor='c')
    c.linkURL(u['url'],(55,710,569,770),relative=0,thickness=0)
    draw(c,'한국어 번역' if u['part']==1 else '日本語 転記',635,760,500,13,20,color=RED)
    draw(c,u['title'],635,720,510,18,26,bold=True);y=u['top']
    for _,ps in u['blocks']:
        for s in ps:y=draw(c,s,635,y,510,u['font'])-8
    if u['notes']:
        y-=12
        for s in u['notes']:y=draw(c,'주 '+s,635,y,510,10.3,16,color=MUTED)-6
    assert y>57,(u['id'],y)
    target=('a' if u['part']==1 else 'p')+str(u['page'])
    draw(c,'원문 전사 부록으로 →' if u['part']==1 else '← 한국어 번역 본문으로',635,56,510,9,12,color=RED)
    c.linkRect('',target,(630,44,970,59),relative=0,thickness=0)
    pdfstats.append(dict(id=u['id'],pdf_page=num,font=u['font'],bottom=round(y,1)))
    c.showPage()
c.save()
r=PdfReader(pdfpath);assert len(r.pages)==58
def squash(s):return re.sub(r'\s+','',s)
for u,stat in zip(units,pdfstats):
    txt=squash(r.pages[stat['pdf_page']-1].extract_text())
    for _,ps in u['blocks']:
        for s in ps:assert squash(s) in txt,('PDF text mismatch',u['id'],s[:60])

css='''@font-face{font-family:Book;src:url(fonts/korean.ttf)}@font-face{font-family:Japanese;src:url(fonts/japanese.ttf)}*{box-sizing:border-box}html,body{margin:0;width:1200px;height:840px;background:#f7f4ea;color:#243c36;font-family:Book,Japanese,sans-serif}body{padding:26px 46px;overflow:hidden}.top{height:29px;border-bottom:1px solid #cfd4c6;font-size:10px;display:flex;justify-content:space-between}.columns{display:grid;grid-template-columns:514px 510px;column-gap:66px;margin:17px 9px 0}.left{position:relative}.left:after{content:"";position:absolute;right:-31px;top:0;height:696px;border-right:1px solid #cfd4c6}.eyebrow{font-size:13px;line-height:20px;margin:0 0 9px;font-weight:normal}.label{font-size:11px;line-height:18px;margin-bottom:17px;color:#697568}.scan{display:block;width:514px;height:620px;object-fit:contain}.right h1{font-size:18px;line-height:26px;margin:17px 0 17px;font-weight:600}.right .eyebrow{color:#a24b3d}.body{line-height:1.65;overflow-wrap:anywhere;line-break:auto}.body p{margin:0 0 8px}.notes{margin-top:12px;color:#697568;font-size:10.3px;line-height:16px}.notes p{margin:0 0 6px}.foot{position:absolute;bottom:16px;left:46px;right:46px;border-top:1px solid #cfd4c6;padding-top:10px;font-size:9px;color:#697568}.back{position:absolute;bottom:44px;left:635px;font-size:9px;color:#a24b3d}.cover{background:#243c36;color:#f7f4ea;padding:75px 85px}.cover h1{font-size:49px;line-height:1.55;margin:70px 0 32px}.cover h2{font-size:25px;font-weight:normal}.cover p{font-size:15px;line-height:1.9}.minor{color:#697568}.cover .minor{color:#d0d8c8}.note h1{font-size:27px;line-height:40px;margin:28px 14px 20px}.note p{font-size:13px;line-height:21px;margin:0 14px 12px}.note .source{font-size:11px;line-height:18px}.tocgrid{display:grid;grid-template-columns:1fr 1fr;gap:6px 45px;margin:18px 14px}.tocgrid p{font-size:11.5px;line-height:17px;margin:0;min-height:36px}.tocgrid small{font-size:9px;color:#697568}.appendix{padding:80px 75px}.appendix h1{font-size:40px;line-height:1.5;margin:90px 0 35px}.appendix p{font-size:18px;line-height:2}.appendix small{font-size:13px}a{color:inherit}'''
def xhtml(title,content,cls='',lang='ko'):
    return '<?xml version="1.0" encoding="utf-8"?>\n<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="'+lang+'" xml:lang="'+lang+'"><head><title>'+esc(title)+'</title><meta name="viewport" content="width=1200,height=840"/><link rel="stylesheet" type="text/css" href="style.css"/></head><body class="'+cls+'">'+content+'</body></html>'
def ps(seq):return ''.join('<p>'+esc(s).replace('\n','<br/>')+'</p>' for s in seq)
ef={}
ef['cover.xhtml']=xhtml(book['title'],'<p class="minor">HISTORICAL ARCHIVE / REVISED PARALLEL EDITION</p><h1>조선토지조사<br/>사업보고서 추록</h1><h2 lang="ja">朝鮮土地調査事業報告書追錄</h2><p>원문 대조 재번역 · 쪽별 일본어 전사</p><p class="minor">인쇄면 1~27쪽<br/>본문 27개 펼침면 + 원문 전사 부록 27개 펼침면</p><p class="minor">1919 원간 · 국립국회도서관 소장 · 2026.09.30 개정</p>','cover')
ef['note.xhtml']=xhtml('편집 안내와 출처','<h1>이 판의 범위와 편집 원칙</h1>'+ps([f'{i:02d}  {s}' for i,s in enumerate(notice,1)])+'<p class="source">원문: 朝鮮総督府臨時土地調査局 편 / 朝鮮総督府 발행 / 1919.<br/>국립국회도서관 디지털컬렉션 · DOI 10.11501/1878691 · 공개 이미지 PDM.<br/><a href="https://dl.ndl.go.jp/pid/1878691">국립국회도서관 원문</a> · <a href="https://lab.ndl.go.jp/dl/api/book/fulltext-json/1878691">공개 OCR 보조 자료</a></p>','note')
ef['toc.xhtml']=xhtml('본문과 부록 찾아보기','<h1>본문과 부록 찾아보기</h1><p>각 인쇄 쪽수에 해당하는 번역 본문과 원문 전사 부록으로 이동합니다.</p><div class="tocgrid">'+''.join(f'<p><a href="p{p["page"]}.xhtml">{p["page"]:02d}　{esc(p["title"])}</a><br/><small><a href="p{p["page"]}.xhtml">한국어 번역</a> / <a href="a{p["page"]}.xhtml">일본어 전사 부록</a></small></p>' for p in pages)+'</div>','note')
ef['appendix.xhtml']=xhtml('부록 · 쪽별 일본어 원문 전사','<p>부록</p><h1>쪽별 일본어 원문 전사</h1><p>인쇄면 1~27쪽</p><p>왼쪽 스캔과 오른쪽 전사를 대조하여 읽을 수 있다.<br/>인쇄 쪽수를 기준으로 한 쪽씩 구분하였다.</p><small>세로쓰기를 가로쓰기로 바꾸고, 표·서식의 항목 관계를 풀어 적었다.<br/>각 쪽의 ‘한국어 번역 본문’ 링크로 돌아갈 수 있다.</small>','appendix')
for u in units:
    label=('본문' if u['part']==1 else '원문 전사 부록')+' · '+u['label']
    target=('a' if u['part']==1 else 'p')+str(u['page'])+'.xhtml'
    body=ps([s for _,seq in u['blocks'] for s in seq])
    nt='<div class="notes">'+ps(['주 '+s for s in u['notes']])+'</div>' if u['notes'] else ''
    ef[u['id']+'.xhtml']=xhtml(label,f'<div class="top"><span>조선토지조사사업보고서 추록</span><span>{esc(label)}</span></div><main class="columns"><section class="left"><h2 class="eyebrow" lang="ja">日本語 原文</h2><div class="label">{u["label"]} / NDL 스캔 {u["scan"]}면</div><img class="scan" src="images/{u["image"]}" alt="{u["label"]} 일본어 원문 스캔"/></section><section class="right"><h2 class="eyebrow">{"한국어 번역" if u["part"]==1 else "日本語 転記"}</h2><h1>{esc(u["title"])}</h1><div class="body" lang="{"ko" if u["part"]==1 else "ja"}" style="font-size:{u["font"]}px">{body}</div>{nt}</section></main><a class="back" href="{target}">{"원문 전사 부록으로 →" if u["part"]==1 else "← 한국어 번역 본문으로"}</a><footer class="foot">{esc(label)} / <a href="{u["url"]}">국립국회도서관 원문</a> / 2026.09.30 개정</footer>')
# Navigation document is not a fixed-layout reading page.
navitems='<li><a href="cover.xhtml">표지</a></li><li><a href="note.xhtml">편집 안내</a></li><li><a href="toc.xhtml">찾아보기</a></li>'
navitems+='<li><a href="p1.xhtml">본문 · 한국어 번역</a><ol>'+''.join(f'<li><a href="p{p["page"]}.xhtml">인쇄면 {p["page"]}쪽 · {esc(p["title"])}</a></li>' for p in pages)+'</ol></li>'
navitems+='<li><a href="appendix.xhtml">부록 · 일본어 원문 전사</a><ol>'+''.join(f'<li><a href="a{p["page"]}.xhtml">인쇄면 {p["page"]}쪽 원문 전사</a></li>' for p in pages)+'</ol></li>'
ef['nav.xhtml']=xhtml('목차','<nav epub:type="toc" id="toc"><h1>목차</h1><ol>'+navitems+'</ol></nav>')
ef['style.css']=css
order=['cover','note','toc']+['p'+str(i) for i in range(1,28)]+['appendix']+['a'+str(i) for i in range(1,28)]
manifest=['<item id="jfont" href="fonts/japanese.ttf" media-type="font/ttf"/>','<item id="style" href="style.css" media-type="text/css"/>','<item id="font" href="fonts/korean.ttf" media-type="font/ttf"/>','<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>']
for k in order:manifest.append(f'<item id="{k}" href="{k}.xhtml" media-type="application/xhtml+xml"/>')
for p in pages:manifest.append(f'<item id="img{p["page"]}" href="images/{p["image"]}" media-type="image/jpeg"/>')
uid='urn:uuid:'+str(uuid.uuid5(uuid.NAMESPACE_URL,'https://dl.ndl.go.jp/pid/1878691#retranslated-20260930'))
opf='<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid" xml:lang="ko" prefix="rendition: http://www.idpf.org/vocab/rendition/#"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="uid">'+uid+'</dc:identifier><dc:title>'+esc(book['title'])+' - 원문 대조 재번역·전사본</dc:title><dc:language>ko</dc:language><dc:language>ja</dc:language><dc:creator>朝鮮總督府臨時土地調査局</dc:creator><dc:source>https://dl.ndl.go.jp/pid/1878691</dc:source><dc:description>인쇄면 1~27쪽의 일본어 스캔·한국어 재번역과 말미의 쪽별 일본어 전사 부록.</dc:description><meta property="dcterms:modified">2026-09-30T00:00:00Z</meta><meta property="rendition:layout">pre-paginated</meta><meta property="rendition:orientation">landscape</meta><meta property="rendition:spread">none</meta></metadata><manifest>'+''.join(manifest)+'</manifest><spine page-progression-direction="ltr">'+''.join(f'<itemref idref="{k}"/>' for k in order)+'</spine></package>'
epubpath=OUT/(NAME+'.epub')
with zipfile.ZipFile(epubpath,'w') as z:
    z.writestr('mimetype','application/epub+zip',compress_type=zipfile.ZIP_STORED)
    z.writestr('META-INF/container.xml','<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/package.opf" media-type="application/oebps-package+xml"/></rootfiles></container>',compress_type=zipfile.ZIP_DEFLATED)
    z.writestr('OEBPS/package.opf',opf,compress_type=zipfile.ZIP_DEFLATED)
    for k,v in ef.items():z.writestr('OEBPS/'+k,v,compress_type=zipfile.ZIP_DEFLATED)
    z.write('C:/Windows/Fonts/yumin.ttf','OEBPS/fonts/japanese.ttf',compress_type=zipfile.ZIP_DEFLATED)
    z.write('C:/Windows/Fonts/malgun.ttf','OEBPS/fonts/korean.ttf',compress_type=zipfile.ZIP_DEFLATED)
    for p in pages:z.write(OUT/'assets'/p['image'],'OEBPS/images/'+p['image'],compress_type=zipfile.ZIP_STORED)
with zipfile.ZipFile(epubpath) as z:
    assert z.namelist()[0]=='mimetype' and z.getinfo('mimetype').compress_type==0
    for n in z.namelist():
        if n.endswith(('.xml','.opf','.xhtml')):ET.fromstring(z.read(n))
    assert z.testzip() is None
    z.extractall(REVIEW/'epub')
template=(ROOT/'scripts/reviewed-reader-template.html').read_text(encoding='utf8')
htmlpath=OUT/(NAME+'.html')
htmlpath.write_text(template.replace('__BOOK_JSON__',json.dumps(book,ensure_ascii=False).replace('</','<\\/')),encoding='utf8')
(OUT/'원문전사_인쇄면1-27.txt').write_text('朝鮮土地調査事業報告書追錄\n인쇄면 1~27쪽 원문 전사\n\n'+ '\n\n'.join(f'===== 인쇄면 {p["page"]}쪽 / NDL {p["scan"]}면 =====\n\n{p["ja"]}'+('\n\n[편집 주] '+' / '.join(p['notes']) if p['notes'] else '') for p in pages),encoding='utf-8-sig')
(OUT/'읽어주세요.txt').write_text('조선토지조사사업보고서 추록 · 원문 대조 재번역·전사본\n2026.09.30 개정\n\nHTML: 더블클릭하여 인터넷 없이 읽습니다. 본문 27면 뒤에 일본어 전사 부록 27면이 있습니다. 상단의 「원문 전사 부록」 또는 「한국어 번역 본문」 버튼으로 같은 쪽을 오갈 수 있습니다. 목차·검색, 책갈피, 원문 확대, 글자 크기 조절을 지원합니다.\n\nPDF: 58페이지입니다. 한 페이지에 원문과 번역이 좌우로 배치되어 있으므로 한 페이지 보기로 엽니다. 본문은 PDF 4~30쪽, 전사 부록은 32~58쪽입니다.\n\nEPUB: EPUB 3 고정 레이아웃 지원 리더에서 엽니다. 한 고정 페이지에 좌우가 함께 들어 있습니다. 일반 텍스트 변환식 리더에서는 HTML이나 PDF를 사용하세요.\n\n'+'\n\n'.join(notice)+'\n\n원문: https://dl.ndl.go.jp/pid/1878691\n',encoding='utf-8-sig')
checks=dict(version=2,printed_pages=27,translation_spreads=27,appendix_spreads=27,pdf_pages=58,epub_spine_pages=len(order),font_missing_characters=missing,pdf_text_verified=True,pdf_layout=pdfstats,outputs={p.name:p.stat().st_size for p in (htmlpath,epubpath,pdfpath)})
(OUT/'제작검수.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in checks.items() if k!='pdf_layout'},ensure_ascii=False,indent=2))

