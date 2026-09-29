from pathlib import Path
import json,urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
r=Path(__file__).resolve().parents[1]
d=r/'tmp/ebook-sources';full=d/'full';full.mkdir(exist_ok=True)
ocr=json.loads((d/'ndl-ocr.json').read_text(encoding='utf8'))['list']
manifest=json.loads((d/'manifest.json').read_text(encoding='utf8'))
def get(n):
    dest=full/f'scan-{n:02d}.jpg'
    if not dest.exists():
        url=manifest['sequences'][0]['canvases'][n-1]['images'][0]['resource']['@id']
        with urllib.request.urlopen(url,timeout=90) as f:dest.write_bytes(f.read())
    return n
with ThreadPoolExecutor(max_workers=3) as pool:
    for n in pool.map(get,range(7,21)):print('scan',n,flush=True)
for page in range(1,28):
    n=7 if page==1 else 7+page//2
    im=Image.open(full/f'scan-{n:02d}.jpg');w,h=im.size
    a,b=(.05,.494) if page%2 else (.494,.95)
    im.crop((int(w*a),int(h*.045),int(w*b),int(h*.95))).save(full/f'p{page:02d}.jpg',quality=95)
    # Text-only review image, retaining all printed text including marginal heads.
    a,b=(.10,.434) if page%2 else (.535,.875)
    crop=im.crop((int(w*a),int(h*.18),int(w*b),int(h*.84)))
    crop.thumbnail((1650,2350));crop.save(full/f'read-{page:02d}.jpg',quality=96)
    blocks=json.loads(next(p['coordjson'] for p in ocr if p['page']==n))
    side=[b for b in blocks if ((b['xmin']+b['xmax'])/2 < w*.5)==bool(page%2)]
    side.sort(key=lambda x:(-round((x['xmin']+x['xmax'])/2/40),x['ymin']))
    (full/f'p{page:02d}-ocr.txt').write_text('\n'.join(f"{b['xmin']:.0f},{b['ymin']:.0f}: {b['contenttext']}" for b in side),encoding='utf8')

