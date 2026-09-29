from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json, urllib.request

root = Path(__file__).resolve().parents[1]
dest = root / 'tmp' / 'ebook-sources'
dest.mkdir(parents=True, exist_ok=True)
url = 'https://dl.ndl.go.jp/api/iiif/1878691/manifest.json'
with urllib.request.urlopen(url, timeout=40) as response:
    manifest = json.load(response)
(dest / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf8')

def get_scan(n):
    canvas = manifest['sequences'][0]['canvases'][n-1]
    service = canvas['images'][0]['resource']['service']['@id']
    output = dest / f'scan-{n:02d}.jpg'
    if not output.exists():
        with urllib.request.urlopen(service + '/full/2800,/0/default.jpg', timeout=90) as response:
            output.write_bytes(response.read())
    return {'scan': n, 'path': str(output), 'bytes': output.stat().st_size}

with ThreadPoolExecutor(max_workers=3) as pool:
    for item in pool.map(get_scan, range(7,21)):
        print(json.dumps(item), flush=True)

