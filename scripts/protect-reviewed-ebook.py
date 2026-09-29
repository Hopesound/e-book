from pathlib import Path
import os,sys,json,base64,secrets,hashlib,shutil,datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pypdf import PdfReader,PdfWriter
from pypdf.errors import FileNotDecryptedError
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tmp/ebook-password-deps'))
import pyzipper
OUT=ROOT/'output/ebook';PDFOUT=ROOT/'output/pdf'
NAME='조선토지조사사업보고서추록_일한대역'
password=os.environ.get('EBOOK_PASSWORD')
if not password:raise RuntimeError('EBOOK_PASSWORD 환경변수에 접근 암호를 지정해야 합니다.')
htmlpath=OUT/(NAME+'.html');pdfpath=PDFOUT/(NAME+'.pdf');epubpath=OUT/(NAME+'.epub')
raw=htmlpath.read_text(encoding='utf8')
if 'data-protected-ebook="aes-gcm-v1"' in raw[:500]:
    raise RuntimeError('이미 암호화된 HTML입니다. 새 원고는 build-reviewed-ebook.py로 먼저 생성하세요.')
original_html=htmlpath.read_bytes();original_pdf=pdfpath.read_bytes()
raw=raw.replace('<button class="btn" id="infoBtn">편집 안내</button>','<button class="btn" id="infoBtn">편집 안내</button><button class="btn" id="lockBook" onclick="location.reload()" title="전자책을 잠그고 암호 입력 화면으로 돌아갑니다">잠금</button>')
raw=raw.replace('</body>','<script>window.addEventListener("pageshow",function(e){if(e.persisted)location.reload()});</script></body>')
assert 'id="lockBook"' in raw
plain=raw.encode('utf8');salt=secrets.token_bytes(16);iv=secrets.token_bytes(12);iterations=600000;aad=b'NDL-1878691-parallel-ebook-v1'
key=hashlib.pbkdf2_hmac('sha256',password.encode('utf8'),salt,iterations,dklen=32)
cipher=AESGCM(key).encrypt(iv,plain,aad)
assert AESGCM(key).decrypt(iv,cipher,aad)==plain
bad=hashlib.pbkdf2_hmac('sha256',b'wrong-access-password',salt,iterations,dklen=32)
try:AESGCM(bad).decrypt(iv,cipher,aad)
except Exception:pass
else:raise AssertionError('Incorrect HTML password accepted')
b64=lambda b:base64.b64encode(b).decode('ascii')
envelope={'version':1,'kdf':'PBKDF2-SHA256','iterations':iterations,'cipher':'AES-256-GCM','salt':b64(salt),'iv':b64(iv),'aad':aad.decode(),'ciphertext':b64(cipher)}
stage=ROOT/'tmp/ebook-password-stage';stage.mkdir(parents=True,exist_ok=True)
sealed=(ROOT/'scripts/password-reader-template.html').read_text(encoding='utf8').replace('__SEALED_PAYLOAD__',json.dumps(envelope,separators=(',',':')))
assert '<script id="book-data"' not in sealed and '調査は土地臺帳' not in sealed
(stage/'book.html').write_text(sealed,encoding='utf8')
source=PdfReader(pdfpath);writer=PdfWriter();writer.clone_document_from_reader(source)
writer.encrypt(user_password=password,owner_password=secrets.token_urlsafe(36),algorithm='AES-256')
with (stage/'book.pdf').open('wb') as f:writer.write(f)
locked=PdfReader(stage/'book.pdf');assert locked.is_encrypted and not locked.decrypt('wrong-access-password')
try:len(locked.pages)
except FileNotDecryptedError:pass
else:raise AssertionError('PDF opened without correct password')
assert locked.decrypt(password)
assert len(locked.pages)==len(source.pages)==58
assert all(a.extract_text()==b.extract_text() for a,b in zip(source.pages,locked.pages))
assert sum(len(p.get('/Annots',[])) for p in locked.pages)==sum(len(p.get('/Annots',[])) for p in source.pages)
zipfiles=[epubpath,OUT/'원문전사_인쇄면1-27.txt']
with pyzipper.AESZipFile(stage/'book.zip','w',compression=pyzipper.ZIP_DEFLATED,encryption=pyzipper.WZ_AES) as z:
    z.setpassword(password.encode());z.setencryption(pyzipper.WZ_AES,nbits=256)
    for path in zipfiles:z.write(path,path.name)
with pyzipper.AESZipFile(stage/'book.zip') as z:
    z.setpassword(b'wrong-access-password')
    try:z.read(z.namelist()[0])
    except RuntimeError:pass
    else:raise AssertionError('ZIP wrong password accepted')
    z.setpassword(password.encode())
    for path in zipfiles:assert z.read(path.name)==path.read_bytes()
# Keep source material separately; the delivery folders contain protected editions.
backup=ROOT/'manuscript'/('before-password-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
backup.mkdir()
shutil.copy2(htmlpath,backup/htmlpath.name);shutil.copy2(pdfpath,backup/pdfpath.name)
for name in ('읽어주세요.txt','제작검수.json'):
    if (OUT/name).exists():shutil.copy2(OUT/name,backup/name)
(stage/'book.html').replace(htmlpath);(stage/'book.pdf').replace(pdfpath)
archivepath=OUT/(NAME+'_EPUB_암호보호.zip');(stage/'book.zip').replace(archivepath)
move_paths=[epubpath,OUT/'원문전사_인쇄면1-27.txt',OUT/'edition-data.json',OUT/'assets']
for path in move_paths:
    dest=backup/path.name
    assert path.resolve().is_relative_to(ROOT.resolve()) and dest.resolve().is_relative_to(ROOT.resolve())
    if path.exists():path.rename(dest)
info={'protected':True,'html':'AES-256-GCM / PBKDF2-SHA256','pdf':'AES-256','epub_container':'WinZip AES-256 ZIP','password_stored':False,'updated':'2026-09-30','html_password_on_every_open':True}
(OUT/'access-protection.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf8')
(OUT/'읽어주세요.txt').write_text('조선토지조사사업보고서 추록 · 암호 보호판\n\nHTML: 전자책을 열면 접근 암호를 묻습니다. 암호 입력 후 기존의 양면 읽기, 번역 및 전사 부록 기능을 사용할 수 있습니다. 책 상단의 잠금 버튼이나 새로고침으로 다시 잠급니다. 접근 암호는 HTML 파일이나 읽던 위치 저장값에 포함하지 않았습니다.\n\nPDF: 파일을 열 때 같은 접근 암호를 입력합니다. 58페이지의 배치와 목차 링크는 유지했습니다.\n\nEPUB: 이름 끝이 EPUB_암호보호.zip인 파일을 AES 암호 ZIP을 지원하는 압축 프로그램으로 엽니다. 같은 접근 암호로 압축을 풀면 EPUB과 쪽별 원문 전사 텍스트가 나옵니다. 추출된 파일에는 별도의 열기 암호가 없으므로 배포할 때에는 암호 ZIP을 사용하세요.\n\n현재 output/ebook과 output/pdf의 완성본은 암호가 적용된 판입니다. 편집용 원고와 이전 판은 작업 폴더의 manuscript 및 tmp에 보관됩니다. 해당 작업 폴더는 배포용이 아닙니다.\n',encoding='utf-8-sig')
qa_path=OUT/'제작검수.json';qa=json.loads(qa_path.read_text(encoding='utf8'))
qa['access_protection']={**info,'wrong_password_rejected':['HTML','PDF','ZIP'],'correct_password_verified':['HTML','PDF','ZIP'],'pdf_text_and_links_preserved':True}
qa['outputs']={p.name:p.stat().st_size for p in (htmlpath,pdfpath,archivepath)}
qa_path.write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf8')
(stage/'password-validation.json').write_text(json.dumps(qa['access_protection'],ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'protected':True,'pdf_pages':58,'epub_zip_entries':2,'plaintext_delivery_files_relocated':True,'backup':str(backup),'outputs':qa['outputs']},ensure_ascii=False,indent=2))

