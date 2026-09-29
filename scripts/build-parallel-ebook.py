from pathlib import Path
import re,json,html,base64,zipfile,hashlib,shutil,uuid
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
SOURCES=ROOT/'tmp/ebook-sources'
OUT=ROOT/'output/ebook'
PDFOUT=ROOT/'output/pdf'
for d in (OUT,PDFOUT,OUT/'assets',ROOT/'tmp/ebook-review'):d.mkdir(parents=True,exist_ok=True)
NAME='조선토지조사사업보고서추록_일한대역'
src10=Path('C:/Users/kwg/Downloads/10PAGE.txt').read_text(encoding='utf-8-sig')
src20=Path('C:/Users/kwg/Downloads/20PAGE.txt').read_text(encoding='utf-8-sig')
def clean(s):
    s=re.sub(r'.*?','',s).replace('**','').replace(chr(96),'')
    return re.sub(r'<br\s*/?>','\n',s).strip()
def paras(s):return [p.strip() for p in re.split(r'\n\s*\n',clean(s)) if p.strip()]
def esc(s):return html.escape(s,quote=True)
rows=[]
for line in src10.splitlines():
    if re.match(r'\| \*\*\d+쪽\*\*',line):
        cells=[x.strip() for x in line.strip('|').split('|')]
        assert len(cells)==5
        rows.append(cells)
assert len(rows)==10
titles=['총설','역둔토분필조사 · 개설','조사의 준비 · 지번과 면적','소도 작성','신고서의 취합','신고서 기재 원칙','역둔토소작신고서','조사의 방법 · 요항','소작인의 조사','강계와 지목의 조사','조사의 요항 · 소작인 조사','강계와 지목의 조사','강계·지목 · 지번 결정','등급 조사 · 신고서류 정리','측량의 방법 · 소도 수정','측량 · 지도와 일람도','지도 작성 · 도서 검사','도서 검사의 세부 항목','지적(면적)의 산정','부서(장부·서류)의 조제']
units=[]
for i,cells in enumerate(rows,1):
    scan=7 if i==1 else 7+i//2
    im=Image.open(SOURCES/f'scan-{scan:02d}.jpg');w,h=im.size
    box=(int(w*.05),int(h*.045),int(w*.493),int(h*.945)) if i%2 else (int(w*.493),int(h*.045),int(w*.946),int(h*.949))
    im=im.crop(box);img=f'page-{i:02d}.jpg';im.save(OUT/'assets'/img,quality=88,optimize=True)
    units.append(dict(id=f'p{i}',part=1,title=titles[i-1],label=f'인쇄면 {i}쪽',scan=scan,image=img,source='10PAGE.txt',ja=clean(cells[1]),literal=clean(cells[2]),natural=clean(cells[3]),note=clean(cells[4]),status='발췌 번역',blocks=[('발췌 직역',paras(cells[2])),('자연스러운 한국어 · 요약',paras(cells[3])),('첨부 원고의 주석',paras(cells[4]))]))
sections=re.findall(r'### NDL 제(\d+)코마[^\n]*\n(.*?)(?=\n### |\n## |\Z)',src20,re.S)
assert len(sections)==10
for k,(ns,body) in enumerate(sections):
    n=int(ns)
    tr=re.search(r'\*\*한국어 번역(?: 초안)?\*\*(.*?)(?=\n\*\*|\Z)',body,re.S).group(1)
    headings=re.findall(r'^\x60([^\x60]+)\x60',body.split('**페이지 Executive Summary.**')[0],re.M)
    note_match=re.search(r'\*\*판독상 애매한 부분\*\*(.*?)(?=\n\*\*|\Z)',body,re.S)
    extra_match=re.search(r'\*\*해설\*\*(.*?)(?=\n\*\*|\Z)',body,re.S)
    note=clean(note_match.group(1)) if note_match else ''
    editorial=('첨부 원고에는 이 구간의 번역이 보류되어 있습니다. 이번 전자책에는 원문 스캔을 추가했으며, 아래 설명은 완역문이 아닙니다.' if n in (16,20) else '첨부 원고의 번역 초안입니다. 생략·수치 판독 보류가 있어 완역문이 아닙니다.')
    if n in (11,12):editorial+=' 제1부의 인쇄면 8~10쪽과 일부 범위가 겹칩니다.'
    img=f'scan-{n:02d}.jpg';im=Image.open(SOURCES/img);w,h=im.size
    im.crop((int(w*.045),int(h*.04),int(w*.95),int(h*.95))).save(OUT/'assets'/img,quality=88,optimize=True)
    blocks=[('편집 안내',[editorial]),('번역 보류 · 첨부 원고의 설명' if n in (16,20) else '한국어 번역 초안',paras(tr))]
    if note:blocks.append(('첨부 원고의 판독 메모',paras(note)))
    units.append(dict(id=f's{n}',part=2,title=titles[10+k],label=f'NDL {n}면 · 인쇄면 {2*n-14}~{2*n-13}쪽',scan=n,image=img,source='20PAGE.txt',ja='\n'.join(headings),status='번역 보류' if n in (16,20) else '번역 초안',blocks=blocks,note=note,explanation=clean(extra_match.group(1)) if extra_match else ''))
assert len(units)==20
for u in units:
    u['url']=f"https://dl.ndl.go.jp/pid/1878691/1/{u['scan']}"
    u['search']=clean(u['title']+' '+u['label']+' '+u['ja']+' '+' '.join(' '.join(p) for _,p in u['blocks']))
    u['datauri']='data:image/jpeg;base64,'+base64.b64encode((OUT/'assets'/u['image']).read_bytes()).decode()
notice=[
'이 전자책은 첨부된 두 번역·검토 원고를 일본어 원문 스캔과 나란히 편집한 대역 열람본입니다. 1919년 간행된 책 전체의 완역본은 아닙니다.',
'제1부는 10PAGE.txt의 인쇄면 1~10쪽 발췌 직역·요약·주석을, 제2부는 20PAGE.txt의 NDL 스캔 11~20면(인쇄면 8~27쪽) 번역 초안을 수록했습니다. 두 원고의 체계를 보존하여 인쇄면 8~10쪽이 겹칩니다.',
'왼쪽은 국립국회도서관(NDL)의 실제 일본어 스캔, 오른쪽은 제공 원고의 한국어입니다. 원문의 전체 글자와 오른쪽의 발췌·요약·초안이 문장 단위로 모두 대응하는 것은 아닙니다.',
'스캔 16·20면의 일본어 원문 이미지는 이번에 추가했습니다. 이 구간은 첨부 원고에 번역이 없어 판독 보류 및 절의 기능 설명을 유지했습니다. 나머지 [불명]·생략·수치 보류도 그대로 남겼습니다.',
'서지와 스캔 대응을 확인했습니다. 제공 원고의 일본어 전사·번역·역사 해설 전체를 새로 교감하거나 검증한 판본은 아닙니다. 주석과 해설은 제공 원고의 내용으로 구분했습니다.',
'인쇄면 1쪽은 NDL 스캔 7면입니다. 스캔 8면은 인쇄면 2~3쪽이며, 이후 스캔 20면은 26~27쪽입니다. 책의 인쇄 쪽수와 뷰어의 스캔 면 번호를 구별해 표시했습니다.',
'원고의 이전 대화용 인용 토큰과 존재하지 않는 HWPX 다운로드·저장 안내는 본문에서 제외했습니다. 원문 출처는 NDL 직접 링크로 연결합니다.'
]
book=dict(title='조선토지조사사업보고서 추록',subtitle='일본어 원문 · 한국어 대역 열람본',notice=notice,units=units)
(OUT/'edition-data.json').write_text(json.dumps({**book,'units':[{k:v for k,v in u.items() if k!='datauri'} for u in units]},ensure_ascii=False,indent=2),encoding='utf8')
pdfmetrics.registerFont(TTFont('K','C:/Windows/Fonts/malgun.ttf'))
pdfmetrics.registerFont(TTFont('KB','C:/Windows/Fonts/malgunbd.ttf'))
pdfmetrics.registerFontFamily('K',normal='K',bold='KB')
INK='#243C36';MUTED='#73786E';PAPER='#F7F4EA';RED='#A24B3D';W,H=1200,840
def pdraw(c,text,x,y,width,font=13,leading=None,color=INK,bold=False):
    st=ParagraphStyle('p',fontName='KB' if bold else 'K',fontSize=font,leading=leading or font*1.68,textColor=HexColor(color),wordWrap='CJK')
    p=Paragraph(esc(text).replace('\n','<br/>'),st);pw,ph=p.wrap(width,2000);p.drawOn(c,x,y-ph)
    return y-ph
def header(c,left,right):
    c.setFillColor(HexColor(PAPER));c.rect(0,0,W,H,fill=1,stroke=0)
    c.setStrokeColor(HexColor('#D4D7CA'));c.line(46,H-57,W-46,H-57)
    pdraw(c,left,46,H-24,850,10,14);pdraw(c,right,W-246,H-24,200,10,14,color=MUTED)
def footer(c,label,num):
    c.setStrokeColor(HexColor('#D4D7CA'));c.line(46,42,W-46,42)
    pdraw(c,label,46,31,1050,9,12,color=MUTED);pdraw(c,str(num),W-75,31,40,10,12,color=MUTED)
def fitblocks(blocks):
    for size in [13,12.5,12,11.5,11]:
        height=0
        for heading,ps in blocks:
            height+=28
            for text in ps:
                p=Paragraph(esc(text),ParagraphStyle('x',fontName='K',fontSize=size,leading=size*1.62,wordWrap='CJK'))
                height+=p.wrap(510,2000)[1]+9
        if height<=630:return size,height
    raise ValueError(('Text overflows',height))
for u in units:u['font'],u['height']=fitblocks(u['blocks'])
pdfpath=PDFOUT/(NAME+'.pdf')
c=canvas.Canvas(str(pdfpath),pagesize=(W,H),pageCompression=1)
c.setTitle('조선토지조사사업보고서 추록 | 일한 대역 열람본')
c.setAuthor('원저: 조선총독부 임시토지조사국 / 번역: 사용자 제공 원고')
c.setSubject('인쇄면 1~27쪽 범위의 발췌 번역·초안과 NDL 원문 스캔 대조')
c.bookmarkPage('cover');c.addOutlineEntry('표지','cover',0)
c.setFillColor(HexColor(INK));c.rect(0,0,W,H,fill=1,stroke=0)
c.setStrokeColor(HexColor('#91A396'));c.rect(46,46,W-92,H-92,fill=0,stroke=1)
pdraw(c,'HISTORICAL ARCHIVE  /  PARALLEL EDITION',85,738,900,12,20,color='#D0D8C8')
pdraw(c,'조선토지조사',85,621,950,48,74,color=PAPER,bold=True)
pdraw(c,'사업보고서 추록',85,548,1000,48,74,color=PAPER,bold=True)
pdraw(c,'朝鮮土地調査事業報告書追錄',89,432,1000,23,35,color='#D0D8C8')
pdraw(c,'일본어 원문 · 한국어 대역 열람본',90,300,950,23,35,color=PAPER)
pdraw(c,'왼쪽에는 기록을, 오른쪽에는 우리말을.',90,248,900,15,25,color='#D0D8C8')
pdraw(c,'1919 원간  |  인쇄면 1~27쪽 범위  |  발췌 번역 및 번역 초안',90,147,1000,13,23,color='#D0D8C8')
pdraw(c,'원문 소장: 일본 국립국회도서관  ·  전자책 편집: 2026.09.29',90,112,1000,11,18,color='#D0D8C8');c.showPage()
header(c,'이 책을 읽는 방법','EDITORIAL NOTE');c.bookmarkPage('note');c.addOutlineEntry('편집 안내와 수록 범위','note',0)
y=747
for i,n in enumerate(notice):y=pdraw(c,f'{i+1:02d}  {n}',60,y,1080,14,23)-16
footer(c,'완역본이 아닌 제공 원고 기반의 대역 열람본',2);c.showPage()
header(c,'목차 · 원문과 번역의 대응','CONTENTS');c.bookmarkPage('toc');c.addOutlineEntry('목차','toc',0)
for col in range(2):
    x=60+col*585
    pdraw(c,'제1부  인쇄면 1~10쪽' if col==0 else '제2부  스캔 11~20면',x,750,515,20,30,bold=True)
    pdraw(c,'10PAGE.txt · 발췌 번역' if col==0 else '20PAGE.txt · 번역 초안 / 인쇄면 8~27쪽',x,707,515,11,18,color=MUTED)
    y=665
    for ix in range(col*10,col*10+10):
        u=units[ix];pdraw(c,f"{ix+1:02d}   {u['title']}",x,y,500,14,22,bold=True)
        pdraw(c,u['label']+'  /  '+u['status'],x+35,y-25,475,10,16,color=MUTED)
        c.linkRect('',u['id'],(x,y-44,x+515,y+2),relative=0,thickness=0);y-=57
footer(c,'제2부의 시작 범위는 제1부 인쇄면 8~10쪽과 겹칩니다.',3);c.showPage()
pdf_stats=[]
for ix,u in enumerate(units,4):
    c.bookmarkPage(u['id']);c.addOutlineEntry(u['label']+' · '+u['title'],u['id'],0)
    header(c,'조선토지조사사업보고서 추록',f"제{u['part']}부  /  {u['status']}")
    pdraw(c,'日本語 原文',50,756,500,13,20,bold=True);pdraw(c,u['label'],50,726,525,11,18,color=MUTED)
    pdraw(c,'한국어 번역',640,756,510,13,20,bold=True);pdraw(c,u['title'],640,726,510,18,27,bold=True)
    c.setStrokeColor(HexColor('#D4D7CA'));c.line(610,62,610,770)
    ip=OUT/'assets'/u['image'];im=Image.open(ip);iw,ih=im.size;aw,ah=530,610
    scale=min(aw/iw,ah/ih);dw,dh=iw*scale,ih*scale;c.drawImage(str(ip),50+(aw-dw)/2,690-dh,width=dw,height=dh)
    pdraw(c,f"국립국회도서관 소장 · NDL 스캔 {u['scan']}면",50,72,530,9,14,color=MUTED)
    c.linkURL(u['url'],(50,55,575,78),relative=0,thickness=0)
    y=681
    for title,ps in u['blocks']:
        y=pdraw(c,title,640,y,510,10,15,color=RED,bold=True)-10
        for p in ps:y=pdraw(c,p,640,y,510,u['font'],u['font']*1.62)-9
        y-=3
    assert y>47,(u['id'],y)
    pdf_stats.append({'id':u['id'],'bottom_y':round(y,1),'font':u['font']})
    footer(c,u['label']+'  |  '+u['source']+'  |  왼쪽 원문 스캔 · 오른쪽 제공 번역',ix);c.showPage()
header(c,'서지와 원문 출처','SOURCE RECORD');c.bookmarkPage('sources');c.addOutlineEntry('서지와 원문 출처','sources',0)
y=742
for title,text in [
('원저','朝鮮土地調査事業報告書追録 / 조선토지조사사업보고서 추록'),
('편찬 · 발행','朝鮮総督府臨時土地調査局 編 · 朝鮮総督府 · 1919'),
('소장 · 식별자','国立国会図書館 National Diet Library, JAPAN / info:ndljp/pid/1878691 / DOI 10.11501/1878691'),
('원문 출처','https://dl.ndl.go.jp/pid/1878691'),
('스캔 · 권리 표시','NDL IIIF 공개 매니페스트: Access Restrictions = PDM. 스캔 7~20면을 사용하고 첫 부는 해당 인쇄면 영역을 발췌했습니다. 색과 본문은 재구성하지 않았습니다.'),
('한국어 원고','사용자가 제공한 10PAGE.txt 및 20PAGE.txt. 번역자 이름은 제공되지 않았습니다. 원고의 대화 기록·파일 생성 안내는 편집에서 제외했습니다.'),
('열람 범위','인쇄면 1~27쪽에 해당하는 대역 20개. 제1부 인쇄면 8~10쪽은 제2부 스캔 11~12면과 겹칩니다.'),
('편집 원칙','원문 스캔 확보와 지면 편집을 수행했습니다. 번역의 내용·불명 표시·초안 상태는 제공 원고에 따릅니다. 이번 판을 책 전체의 완역이나 확정 번역으로 표시하지 않습니다.')]:
    y=pdraw(c,title,60,y,1060,12,20,color=RED,bold=True)-6;y=pdraw(c,text,60,y,1060,14,23)-20
footer(c,'원문 스캔 확인일 2026.09.29 · 전자책 제작 원고와 수록 범위를 함께 보존',24);c.showPage();c.save()
reader=PdfReader(pdfpath);assert len(reader.pages)==24
extracted='\n'.join(p.extract_text() for p in reader.pages)
for u in units:assert u['title'] in extracted
assert not re.search(r'|sandbox:',extracted)
(ROOT/'tmp/ebook-review/pdf-validation.json').write_text(json.dumps({'pages':24,'layout':pdf_stats},ensure_ascii=False,indent=2),encoding='utf8')

pagecss='''@font-face{font-family:Book;src:url(fonts/korean.ttf)}*{box-sizing:border-box}html,body{margin:0;width:1200px;height:840px;background:#f7f4ea;color:#243c36;font-family:Book,sans-serif}body{padding:34px 48px;overflow:hidden}.top{font-size:11px;border-bottom:1px solid #d4d7ca;padding-bottom:18px;display:flex;justify-content:space-between}.columns{display:flex;gap:54px;height:700px;padding-top:22px}.left,.right{width:525px;min-width:0}.left{border-right:1px solid #d4d7ca;padding-right:25px}.eyebrow{font-size:13px;margin:0 0 12px}.label{font-size:11px;color:#73786e;margin-bottom:15px}.scan{display:block;max-width:100%;max-height:605px;object-fit:contain;margin:0 auto}.right h1{font-size:18px;line-height:1.45;margin:0 0 15px}.body{font-size:13px;line-height:1.62;overflow-wrap:anywhere}.body h2{font-size:10px;color:#a24b3d;line-height:1.5;margin:12px 0 8px}.body p{margin:0 0 9px}.foot{position:absolute;bottom:23px;left:48px;right:48px;border-top:1px solid #d4d7ca;padding-top:10px;font-size:9px;color:#73786e}.note h1{font-size:30px;margin:22px 0}.note p{font-size:15px;line-height:1.8;margin:0 0 16px}.cover{background:#243c36;color:#f7f4ea;padding:75px 85px}.cover h1{font-size:50px;line-height:1.5;margin:80px 0 30px}.cover h2{font-size:24px;font-weight:normal}.cover p{font-size:15px;line-height:2}.cover .minor{color:#d0d8c8}.toc ol{columns:2;column-gap:70px;padding-left:25px}.toc li{font-size:14px;line-height:1.6;margin-bottom:10px;break-inside:avoid}.toc small{font-size:11px}a{color:inherit}'''
def xhtml(title,content,cls=''):
    return '<?xml version="1.0" encoding="utf-8"?>\n<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="ko" xml:lang="ko"><head><title>'+esc(title)+'</title><meta name="viewport" content="width=1200,height=840"/><link rel="stylesheet" type="text/css" href="style.css"/></head><body class="'+cls+'">'+content+'</body></html>'
def blockshtml(u):return ''.join('<section><h2>'+esc(t)+'</h2>'+''.join('<p>'+esc(p).replace('\n','<br/>')+'</p>' for p in ps)+'</section>' for t,ps in u['blocks'])
epubfiles={}
epubfiles['cover.xhtml']=xhtml(book['title'],'<p class="minor">HISTORICAL ARCHIVE / PARALLEL EDITION</p><h1>조선토지조사<br/>사업보고서 추록</h1><h2 lang="ja">朝鮮土地調査事業報告書追錄</h2><p>일본어 원문 · 한국어 대역 열람본</p><p class="minor">1919 원간 / 인쇄면 1~27쪽 범위<br/>발췌 번역 및 번역 초안 · 2026.09.29 편집<br/>원문 소장: 일본 국립국회도서관</p>','cover')
epubfiles['note.xhtml']=xhtml('편집 안내','<h1>이 책을 읽는 방법</h1>'+''.join(f'<p>{i+1:02d}　{esc(n)}</p>' for i,n in enumerate(notice)),'note')
for u in units:
    epubfiles[u['id']+'.xhtml']=xhtml(u['label'],f'<div class="top"><span>조선토지조사사업보고서 추록</span><span>제{u["part"]}부 / {esc(u["status"])}</span></div><main class="columns"><section class="left"><h2 class="eyebrow" lang="ja">日本語 原文</h2><div class="label">{esc(u["label"])}</div><img class="scan" src="images/{u["image"]}" alt="{esc(u["label"])} 일본어 원문 스캔"/></section><section class="right"><h2 class="eyebrow">한국어 번역</h2><h1>{esc(u["title"])}</h1><div class="body" style="font-size:{u["font"]}px">{blockshtml(u)}</div></section></main><footer class="foot">{esc(u["label"])} / {esc(u["source"])} / <a href="{u["url"]}">국립국회도서관 원문</a></footer>')
tocitems='<li><a href="cover.xhtml">표지</a></li><li><a href="note.xhtml">편집 안내</a></li>'+''.join(f'<li><a href="{u["id"]}.xhtml">{esc(u["title"])}</a><br/><small>{esc(u["label"])} · {esc(u["status"])}</small></li>' for u in units)
epubfiles['nav.xhtml']=xhtml('목차','<nav epub:type="toc" id="toc"><h1>목차</h1><ol>'+tocitems+'</ol></nav>','note toc')
epubfiles['style.css']=pagecss
epubpath=OUT/(NAME+'.epub')
manifestitems=['<item id="style" href="style.css" media-type="text/css"/>','<item id="font" href="fonts/korean.ttf" media-type="font/ttf"/>']
spine=[]
for key in ['cover','note','nav']+[u['id'] for u in units]:
    manifestitems.append(f'<item id="{key}" href="{key}.xhtml" media-type="application/xhtml+xml"'+(' properties="nav"' if key=='nav' else '')+'/>');spine.append(f'<itemref idref="{key}"/>')
for i,u in enumerate(units):manifestitems.append(f'<item id="im{i}" href="images/{u["image"]}" media-type="image/jpeg"/>')
uid='urn:uuid:'+str(uuid.uuid5(uuid.NAMESPACE_URL,'https://dl.ndl.go.jp/pid/1878691#parallel-20260929'))
opf='<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid" xml:lang="ko" prefix="rendition: http://www.idpf.org/vocab/rendition/#"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="uid">'+uid+'</dc:identifier><dc:title>조선토지조사사업보고서 추록 - 일한 대역 열람본</dc:title><dc:language>ko</dc:language><dc:language>ja</dc:language><dc:creator>朝鮮總督府臨時土地調査局</dc:creator><dc:source>https://dl.ndl.go.jp/pid/1878691</dc:source><dc:description>사용자 제공 발췌 번역·초안과 원문 스캔. 인쇄면 1~27쪽 범위. 완역본 아님.</dc:description><meta property="dcterms:modified">2026-09-29T00:00:00Z</meta><meta property="rendition:layout">pre-paginated</meta><meta property="rendition:orientation">landscape</meta><meta property="rendition:spread">none</meta></metadata><manifest>'+''.join(manifestitems)+'</manifest><spine page-progression-direction="ltr">'+''.join(spine)+'</spine></package>'
with zipfile.ZipFile(epubpath,'w') as z:
    z.writestr('mimetype','application/epub+zip',compress_type=zipfile.ZIP_STORED)
    z.writestr('META-INF/container.xml','<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/package.opf" media-type="application/oebps-package+xml"/></rootfiles></container>',compress_type=zipfile.ZIP_DEFLATED)
    z.writestr('OEBPS/package.opf',opf,compress_type=zipfile.ZIP_DEFLATED)
    for key,value in epubfiles.items():z.writestr('OEBPS/'+key,value,compress_type=zipfile.ZIP_DEFLATED)
    z.write('C:/Windows/Fonts/malgun.ttf','OEBPS/fonts/korean.ttf',compress_type=zipfile.ZIP_DEFLATED)
    for u in units:z.write(OUT/'assets'/u['image'],'OEBPS/images/'+u['image'],compress_type=zipfile.ZIP_STORED)
review=ROOT/'tmp/ebook-review/epub';(review/'images').mkdir(parents=True,exist_ok=True);(review/'fonts').mkdir(exist_ok=True)
for key,value in epubfiles.items():(review/key).write_text(value,encoding='utf8')
shutil.copy('C:/Windows/Fonts/malgun.ttf',review/'fonts/korean.ttf')
for u in units:shutil.copy(OUT/'assets'/u['image'],review/'images'/u['image'])
template=(ROOT/'scripts/parallel-reader-template.html').read_text(encoding='utf8')
htmlpath=OUT/(NAME+'.html')
htmlpath.write_text(template.replace('__BOOK_JSON__',json.dumps(book,ensure_ascii=False).replace('</','<\\/')),encoding='utf8')
(OUT/'읽어주세요.txt').write_text('조선토지조사사업보고서 추록 · 일한 대역 열람본\n\nHTML 파일을 더블클릭하면 인터넷 연결 없이 읽을 수 있습니다. 왼쪽 원문, 오른쪽 한국어 번역이 한 대역면으로 움직입니다. 원문 확대, 번역 글자 크기, 목차 검색, 책갈피, 읽던 위치 저장을 지원합니다.\n\nPDF는 한 PDF 페이지에 원문과 번역을 함께 고정한 펼침면입니다. PDF 뷰어에서 한 페이지 보기 또는 페이지 너비 맞춤을 사용하세요.\n\nEPUB은 EPUB 3 고정 레이아웃을 지원하는 리더가 필요합니다. 기존 온리프 리더는 EPUB을 일반 텍스트로 변환하므로 양면 원문 이미지 배치를 유지하지 못합니다. 이 책은 제공 HTML 또는 PDF로 열어 주세요.\n\n'+'\n\n'.join(notice)+'\n\n원문: https://dl.ndl.go.jp/pid/1878691\n',encoding='utf8')
with zipfile.ZipFile(epubpath) as z:
    assert z.namelist()[0]=='mimetype' and z.getinfo('mimetype').compress_type==0
    for n in z.namelist():
        if n.endswith(('.xml','.opf','.xhtml')):ET.fromstring(z.read(n))
    assert z.testzip() is None
checks={'pdf_pages':24,'parallel_units':len(units),'pending_translation_scans':[16,20],'scan_mapping':[{k:u[k] for k in ('id','label','scan','source')} for u in units],'source_hashes':{name:hashlib.sha256(Path('C:/Users/kwg/Downloads',name).read_bytes()).hexdigest() for name in ('10PAGE.txt','20PAGE.txt')},'outputs':{p.name:p.stat().st_size for p in (pdfpath,epubpath,htmlpath)},'min_pdf_text_bottom':min(x['bottom_y'] for x in pdf_stats)}
(OUT/'제작검수.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(checks,ensure_ascii=False,indent=2))



