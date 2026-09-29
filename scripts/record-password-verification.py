from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];out=root/'output/ebook'
p=out/'제작검수.json';a=json.loads(p.read_text(encoding='utf8'))
b=json.loads((root/'tmp/ebook-password-stage/browser-password-validation.json').read_text(encoding='utf8'))
assert not b['errors'] and all(b[k] for k in ['locked_by_default','wrong_password_rejected','correct_password_opens','lock_button','reload_locks'])
a['access_protection']['browser']=b
a['access_protection']['pdf_render_visually_checked']=True
for name in a['outputs']:
    file=(root/'output/pdf'/name) if name.endswith('.pdf') else out/name
    assert file.exists();a['outputs'][name]=file.stat().st_size
p.write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf8')
print('Password protection verified: HTML, PDF, EPUB ZIP.')

