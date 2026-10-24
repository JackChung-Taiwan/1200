"""Validate the preserved source, extracted text, asset URLs, and optional MP3 decoding."""
from pathlib import Path
from urllib.parse import unquote
import json,hashlib,runpy,re,collections,sys,subprocess,concurrent.futures
BASE=Path(__file__).resolve().parent.parent
m=runpy.run_path(str(BASE/'scripts/build_index.py'))
data=m['records'];src=m['SRC'];assets=json.loads((BASE/'dist/asset-map.json').read_text())
assert len(data)==1171 and len({w['id'] for w in data})==1171
assert sum(len(w['examples']) for w in data)==1277
manifest=json.loads((BASE/'data/original-manifest.json').read_text())
assert len(manifest)==5360
for row in manifest:
 p=BASE/'dist/original'/row['path']
 assert p.stat().st_size==row['size'] and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'],row['path']
for a in assets:
 p=BASE/'dist'/unquote(a['url']);assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256'],a
for w in data:
 assert w['word'] and w['meaning'] and w['audio'] and w['examples'],w['source']
 assert all(e['english'] and e['translation'] for e in w['examples']),w['source']
 assert '\ufffd' not in json.dumps(w,ensure_ascii=False),w['source']
 root=m['Parser']((src/w['source']).read_bytes().decode('cp950')).root
 main=next(n for n in root.nodes() if 'main' in n.attrs.get('class','').split())
 original=re.sub(r'\s','',main.text())
 indexed=re.sub(r'\s','',''.join([w['word'],w['meaning']]+[s for e in w['examples'] for s in [e['english'],e['translation']]]))
 assert collections.Counter(original)==collections.Counter(indexed),('Text preservation mismatch',w['source'])
result={'indexedWords':len(data),'exampleGroups':sum(len(w['examples']) for w in data),'originalFileHashesVerified':len(manifest),'assetUrlsVerified':len(assets),'canonicalPageTextPreservationChecks':len(data),'textComparison':'比較原頁主內容與索引文字的非空白字元計數，保留全部可見內容；版面與空白正規化。'}
if '--audio' in sys.argv:
 def check(p):
  r=subprocess.run(['ffmpeg','-v','error','-nostdin','-i',str(p),'-f','null','-'],capture_output=True,text=True)
  return {'path':p.relative_to(src).as_posix(),'exit':r.returncode,'error':r.stderr.strip()} if r.returncode or r.stderr.strip() else None
 paths=list(src.rglob('*.mp3'))
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:errors=[x for x in ex.map(check,paths) if x]
 result['sourceMp3Decoded']=len(paths);result['audioDecodeErrors']=errors
 assert not errors,errors
(BASE/'data/verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2))
