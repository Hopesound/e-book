from pathlib import Path
p=Path('scripts/build-reviewed-ebook.py');s=p.read_text(encoding='utf8')
s=s.replace('import json,re,html,base64,zipfile,uuid,shutil,hashlib','import json,re,html,base64,zipfile,uuid,shutil,hashlib,os,sys,subprocess')
s=s.replace("NAME='조선토지조사사업보고서추록_일한대역'","NAME='조선토지조사사업보고서추록_일한대역'\nprotect_output=(OUT/'access-protection.json').exists()\nif protect_output and not os.environ.get('EBOOK_PASSWORD'):\n    raise RuntimeError('암호 보호판입니다. EBOOK_PASSWORD를 지정해야 새로 생성할 수 있습니다.')")
s+="\n# Preserve access protection when regenerating this edition.\nif protect_output:\n    subprocess.run([sys.executable,str(ROOT/'scripts/protect-reviewed-ebook.py')],check=True)\n"
p.write_text(s,encoding='utf8')

