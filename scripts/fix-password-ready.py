from pathlib import Path
for p in [Path('scripts/password-reader-template.html'),Path('output/ebook/조선토지조사사업보고서추록_일한대역.html')]:
    s=p.read_text(encoding='utf-8-sig')
    s=s.replace('id="unlockButton" type="submit"','id="unlockButton" type="submit" disabled')
    s=s.replace("});\n})();\n</script>","});\nbutton.disabled=false;\n})();\n</script>")
    assert 'button.disabled=false;\n})();' in s
    p.write_text(s,encoding='utf8')

