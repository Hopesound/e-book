from pathlib import Path
import json,copy,re
from PIL import Image,ImageDraw,ImageFont
from pypdf import PdfReader,PdfWriter
from pypdf.generic import RectangleObject,DictionaryObject,NameObject
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
root=Path(__file__).resolve().parents[1];rv=root/'tmp/ebook-review-v2'
pdf=root/'output/pdf/조선토지조사사업보고서추록_일한대역.pdf'
pdfmetrics.registerFont(TTFont('K','C:/Windows/Fonts/malgun.ttf'))
r=PdfReader(pdf);w=PdfWriter();w.clone_document_from_reader(r)
aa=w.pages[2]['/Annots']
assert len(aa)==54
for i in range(27):
    col=0 if i<14 else 1;row=i if i<14 else i-14;x=60+col*560;y=660-row*41;n=i+1
    main=aa[i*2].get_object();app=aa[i*2+1].get_object()
    main[NameObject('/Rect')]=RectangleObject((x,y-16,x+505,y))
    prefix=pdfmetrics.stringWidth(f'본문 {n+3}  ·  ','K',9)
    app[NameObject('/Rect')]=RectangleObject((x+26+prefix,y-32,x+26+prefix+75,y-16))
    b=DictionaryObject(dict(main));b[NameObject('/Rect')]=RectangleObject((x+26,y-32,x+26+prefix-5,y-16));aa.append(w._add_object(b))
temp=pdf.with_suffix('.reviewed.pdf')
with temp.open('wb') as f:w.write(f)
rr=PdfReader(temp);assert len(rr.pages)==58 and len(rr.pages[2]['/Annots'])==81
assert all(a.extract_text()==b.extract_text() for a,b in zip(r.pages,rr.pages))
temp.replace(pdf)
s=root/'scripts/build-reviewed-ebook.py';t=s.read_text(encoding='utf8')
t=t.replace("c.linkRect('',f'p{p[\"page\"]}',(x,y-32,x+375,y),relative=0,thickness=0)","c.linkRect('',f'p{p[\"page\"]}',(x,y-16,x+505,y),relative=0,thickness=0)\n    prefix=pdfmetrics.stringWidth(f'본문 {p[\"page\"]+3}  ·  ','K',9)\n    c.linkRect('',f'p{p[\"page\"]}',(x+26,y-32,x+26+prefix-5,y-16),relative=0,thickness=0)")
t=t.replace("c.linkRect('',f'a{p[\"page\"]}',(x+375,y-32,x+505,y),relative=0,thickness=0)","c.linkRect('',f'a{p[\"page\"]}',(x+26+prefix,y-32,x+26+prefix+75,y-16),relative=0,thickness=0)")
s.write_text(t,encoding='utf8')
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
for start in (1,17,33,49):
    nums=list(range(start,min(start+16,59)))
    sheet=Image.new('RGB',(1320,4*266),'#e3e7de');d=ImageDraw.Draw(sheet)
    for j,n in enumerate(nums):
        im=Image.open(rv/f'pdf-{n:02d}.png');im.thumbnail((320,233))
        x=(j%4)*330+5;y=(j//4)*266+24
        sheet.paste(im,(x,y));d.text((x,y-22),f'PDF {n}',font=font,fill='#243c36')
    sheet.save(rv/f'contact-{start:02d}.jpg',quality=93)
qa=root/'output/ebook/제작검수.json';a=json.loads(qa.read_text(encoding='utf8'))
b=json.loads((rv/'browser-validation.json').read_text(encoding='utf8'))
a['browser_validation']={'html_units':len(b['html_units']),'epub_pages':len(b['epub']),'paired_navigation':b['paired_navigation'],'search_hits':b['search_hits'],'preferences':b['preferences'],'errors':b['errors'],'overflow':b['overflow']}
a['pdf_toc_links']=81;a['rendered_pdf_pages']=58;a['outputs'][pdf.name]=pdf.stat().st_size
qa.write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'pages':58,'pdf_toc_links':81,'html_units':len(b['html_units']),'epub_pages':len(b['epub']),'errors':b['errors'],'overflow':b['overflow']},ensure_ascii=False))



