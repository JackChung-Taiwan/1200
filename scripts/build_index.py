from pathlib import Path
from html.parser import HTMLParser
import re,json,hashlib,collections,shutil,posixpath
from urllib.parse import unquote, quote
BASE=Path(__file__).resolve().parent.parent; SRC=BASE/'dist/original/English1200-0514'; OUT=BASE/'dist'; OUT.mkdir(parents=True,exist_ok=True)
class N:
 def __init__(self,tag='',attrs=(),parent=None):self.tag=tag;self.attrs=dict(attrs);self.parent=parent;self.children=[]
 def nodes(self,tag=None):
  for x in self.children:
   if isinstance(x,N):
    if tag is None or x.tag==tag:yield x
    yield from x.nodes(tag)
 def text(self,exclude=None):
  if exclude and exclude(self):return ''
  return ''.join(x.text(exclude)+(' ' if x.tag in ['p','br','div','td'] else '') if isinstance(x,N) else x for x in self.children)
 def ancestor(self,tag):
  p=self.parent
  while p and p.tag!=tag:p=p.parent
  return p
class Parser(HTMLParser):
 def __init__(self,s):super().__init__(convert_charrefs=True);self.root=N();self.stack=[self.root];self.feed(s)
 def handle_starttag(self,t,a):
  n=N(t,a,self.stack[-1]);self.stack[-1].children.append(n)
  if t not in ['img','br','meta','link','input','hr','embed','source','area','base','param','wbr']:self.stack.append(n)
 def handle_startendtag(self,t,a):self.handle_starttag(t,a);self.handle_endtag(t)
 def handle_endtag(self,t):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i].tag==t:self.stack=self.stack[:i];break
 def handle_data(self,s):self.stack[-1].children.append(s)
def clean(s):return re.sub(r'\s+',' ',s).strip()
def aud(n):
 h=n.attrs.get('href','');m=re.search(r"(?:playAudio|PlaySound)\(\s*['\"](.*?)['\"]\s*\)",h,re.I)
 return m.group(1) if m else (h if re.search(r'\.mp3$',h,re.I) else None)
files={p.relative_to(SRC).as_posix():p for p in SRC.rglob('*') if p.is_file()};lower=collections.defaultdict(list)
for k in files:lower[k.lower()].append(k)
issues=[];used=set();assetmap={};records=[];excluded=[]
def asset(page,ref,kind):
 key=posixpath.normpath(posixpath.join(page.parent.relative_to(SRC).as_posix(),unquote(ref).replace('\\','/')))
 resolved=key
 if key not in files:
  candidates=lower.get(key.lower(),[])
  if len(candidates)==1:resolved=candidates[0];issues.append(dict(page=page.relative_to(SRC).as_posix(),kind=kind,status='case_corrected',reference=ref,resolved=resolved))
  else:issues.append(dict(page=page.relative_to(SRC).as_posix(),kind=kind,status='missing',reference=ref));return None
 used.add(resolved)
 if resolved not in assetmap:
  p=files[resolved];h=hashlib.sha256(p.read_bytes()).hexdigest();target='original/English1200-0514/'+quote(resolved,safe='/')
  assetmap[resolved]={'url':target,'sha256':h,'original':resolved}
 return assetmap[resolved]['url']
for p in sorted(SRC.glob('letter_*/*.html')):
 b=p.read_bytes()
 try:s=b.decode('cp950')
 except UnicodeDecodeError:s=b.decode('cp950',errors='replace');issues.append(dict(page=p.relative_to(SRC).as_posix(),kind='encoding',status='review'))
 root=Parser(s).root;main=next((n for n in root.nodes() if 'main' in n.attrs.get('class','').split()),None)
 if not main:excluded.append(p.relative_to(SRC).as_posix());continue
 anchors=[n for n in main.nodes('a') if aud(n) and re.search('[A-Za-z]',n.text())];
 if not anchors:excluded.append(p.relative_to(SRC).as_posix());continue
 first=anchors[0];row=first.ancestor('tr');cells=[n for n in row.nodes('td') if n.ancestor('tr') is row]
 word=clean(first.ancestor('td').text());meaning=clean(' '.join(n.text() for n in cells if first not in list(n.nodes()) and not list(n.nodes('img'))))
 rec={'id':p.parent.name+'-'+p.stem,'letter':p.parent.name[-1].upper(),'word':word,'meaning':meaning,'audio':asset(p,aud(first),'word_audio'),'audioSource':aud(first),'phonetics':[],'examples':[],'source':p.relative_to(SRC).as_posix()}
 for img in row.nodes('img'):
  u=asset(p,img.attrs.get('src',''),'phonetic_image')
  rec['phonetics'].append({'url':u,'source':img.attrs.get('src','')})
 seen=[]
 for a in anchors[1:]:
  tr=a.ancestor('tr')
  if tr is row or tr in seen:continue
  seen.append(tr);aa=[x for x in tr.nodes('a') if aud(x) and re.search('[A-Za-z]',x.text()) and not (p.name=='have.html' and clean(x.text())=='Kim')]
  english=clean(' '.join(x.text() for x in aa));translation=clean(tr.text(lambda x:x in aa))
  audioRefs=list(dict.fromkeys(aud(x) for x in aa))
  rec['examples'].append({'english':english,'translation':translation,'audio':[asset(p,ref,'example_audio') for ref in audioRefs],'audioSources':audioRefs})
 if not meaning:issues.append(dict(page=rec['source'],kind='meaning',status='missing'))
 if not rec['examples']:issues.append(dict(page=rec['source'],kind='examples',status='missing'))
 if '\ufffd' in main.text():issues.append(dict(page=rec['source'],kind='encoding_content',status='review'))
 if rec['source']=='letter_h/have.html':
  issues.append(dict(page=rec['source'],kind='translation_audio_link',status='removed_from_example_audio',reference='sounds/have02.mp3',text='Kim',reason='中文翻譯中的人名誤連到上一例句；保留文字。'))
 if rec['source']=='letter_c/cheap.html':
  for ex in rec['examples']:
   ex['warning']='原教材例句連到 cake.mp3，內容對應待核對，暫不播放。'
   ex['originalAudio']=ex['audio'];ex['audio']=[None for _ in ex['audio']]
  issues.append(dict(page=rec['source'],kind='example_audio',status='suspected_mismatch_disabled',reference='sounds/cake.mp3'))
 records.append(rec)
report={'sourceArchive':'English1200-0514.rar','sourceSha256':'63c05869561fa7c931e87352c1b99b59ca1a6c4f70d4aada7d0e6356aebed9b8','files':len(files),'words':len(records),'examples':sum(len(x['examples']) for x in records),'mp3Files':sum(k.lower().endswith('.mp3') for k in files),'referencedAssets':len(used),'uniqueAssets':len(set(x['url'] for x in assetmap.values())),'letterCounts':dict(collections.Counter(x['letter'] for x in records)),'issues':issues,'excludedPages':excluded,'ignoredNonEnglishAudioLinks':[],'duplicatePageComparisons':[],'unreferencedMp3':[k for k in files if k.lower().endswith('.mp3') and k not in used]}
# Audit duplicate/backup pages and ignored empty or punctuation-only links.
for p in sorted(SRC.rglob('*')):
 if not p.is_file() or p.suffix.lower() not in ['.html','.htm']:continue
 root=Parser(p.read_bytes().decode('cp950',errors='replace')).root
 main=next((n for n in root.nodes() if 'main' in n.attrs.get('class','').split()),None)
 if main:
  for a in main.nodes('a'):
   if aud(a) and not re.search('[A-Za-z]',a.text()):report['ignoredNonEnglishAudioLinks'].append({'page':p.relative_to(SRC).as_posix(),'text':clean(a.text()),'audio':aud(a)})
 rel=p.relative_to(SRC)
 if len(rel.parts)>2 or p.suffix=='.htm':
  canonical=SRC/rel.parts[0]/(p.stem+'.html')
  if canonical.exists():
   other=Parser(canonical.read_bytes().decode('cp950',errors='replace')).root
   om=next((n for n in other.nodes() if 'main' in n.attrs.get('class','').split()),None)
   if main and om:
    same=clean(main.text())==clean(om.text())
    report['duplicatePageComparisons'].append({'page':rel.as_posix(),'canonical':canonical.relative_to(SRC).as_posix(),'sameVisibleContent':same,'alternateText':None if same else clean(main.text()),'canonicalText':None if same else clean(om.text())})
records.sort(key=lambda w:(w['word'].lower(),w['id']))
(OUT/'data.js').write_text('window.ENGLISH_DATA='+json.dumps(records,ensure_ascii=False,separators=(',',':'))+';\nwindow.DATA_AUDIT='+json.dumps({k:v for k,v in report.items() if k not in ['issues','excludedPages','unreferencedMp3','ignoredNonEnglishAudioLinks','duplicatePageComparisons']},ensure_ascii=False)+';',encoding='utf8')
(OUT/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
(OUT/'asset-map.json').write_text(json.dumps(list(assetmap.values()),ensure_ascii=False,indent=2))
(BASE/'data').mkdir(exist_ok=True);(BASE/'data/vocabulary.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
print(json.dumps({'words':len(records),'examples':report['examples'],'issues':len(issues)},ensure_ascii=False))
