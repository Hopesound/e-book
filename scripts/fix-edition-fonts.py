from pathlib import Path
p=Path('scripts/build-reviewed-ebook.py')
s=p.read_text(encoding='utf-8-sig')
s=s.replace("pdfmetrics.registerFontFamily('K',normal='K',bold='KB')","pdfmetrics.registerFontFamily('K',normal='K',bold='KB')\npdfmetrics.registerFont(TTFont('J','C:/Windows/Fonts/yumin.ttf'))")
s=s.replace("assert not missing,('Missing font glyphs',missing)","fallback_chars=missing\nmissing=[c for c in missing if ord(c) not in pdfmetrics.getFont('J').face.charToGlyph]\nassert not missing,('Missing font glyphs',missing)")
s=s.replace("return Paragraph(esc(text).replace('\\n','<br/>'),ParagraphStyle", "markup=esc(text).replace('\\n','<br/>')\n    for ch in fallback_chars:markup=markup.replace(ch,'<font name=\"J\">'+ch+'</font>')\n    return Paragraph(markup,ParagraphStyle")
s=s.replace("@font-face{font-family:Book;src:url(fonts/korean.ttf)}","@font-face{font-family:Book;src:url(fonts/korean.ttf)}@font-face{font-family:Japanese;src:url(fonts/japanese.ttf)}")
s=s.replace("font-family:Book,sans-serif","font-family:Book,Japanese,sans-serif")
s=s.replace("manifest=['<item id=\"style\"", "manifest=['<item id=\"jfont\" href=\"fonts/japanese.ttf\" media-type=\"font/ttf\"/>','<item id=\"style\"")
s=s.replace("z.write('C:/Windows/Fonts/malgun.ttf'", "z.write('C:/Windows/Fonts/yumin.ttf','OEBPS/fonts/japanese.ttf',compress_type=zipfile.ZIP_DEFLATED)\n    z.write('C:/Windows/Fonts/malgun.ttf'")
p.write_text(s,encoding='utf8')

