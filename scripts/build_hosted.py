"""Build a compact hosted edition. Original MP3 bytes are restored in-browser using gzip."""
from pathlib import Path
from urllib.parse import unquote
import json,gzip,shutil
BASE=Path(__file__).resolve().parent.parent;SRC=BASE/'dist';OUT=BASE/'out'
if OUT.exists():shutil.rmtree(OUT)
OUT.mkdir(exist_ok=True)
for name in ['index.html','style.css','audit.json']:
 shutil.copyfile(SRC/name,OUT/name)
assetmap=json.loads((SRC/'asset-map.json').read_text());urlmap={};compressed=0;before=0;after=0
for a in assetmap:
 p=SRC/unquote(a['url']);url=a['url'];b=p.read_bytes();before+=len(b)
 if p.suffix.lower()=='.mp3':
  payload=gzip.compress(b,compresslevel=6,mtime=0)
  assert gzip.decompress(payload)==b
  urlmap[url]=url+'.gz';url=url+'.gz';a['url']=url;a['compression']='gzip';a['sha256Describes']='decompressed original bytes';compressed+=1
 else:payload=b
 dest=OUT/unquote(url);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(payload);after+=len(payload)
(OUT/'asset-map.json').write_text(json.dumps(assetmap,ensure_ascii=False,indent=2))
s=(SRC/'data.js').read_text()
for old,new in urlmap.items():s=s.replace(json.dumps(old),json.dumps(new))
(OUT/'data.js').write_text(s)
s=(SRC/'app.js').read_text()
s=s.replace("audio.preload='none';", "audio.preload='none'; let audioObjectUrl=null,fetchController=null;")
s=s.replace("function stop(){seq++;audio.pause();", "function stop(){seq++; if(fetchController){fetchController.abort();fetchController=null;} audio.pause();")
s=s.replace("audio.load();$('playerBar').hidden=true;", "audio.load();if(audioObjectUrl){URL.revokeObjectURL(audioObjectUrl);audioObjectUrl=null;}$('playerBar').hidden=true;")
s=s.replace("const token=seq;audio.src=url;audio.playbackRate=speed;audio.preservesPitch=true;", "const token=seq;")
s=s.replace("try{await audio.play();", """try{
   let playable=url;
   if(url.endsWith('.gz')){
    if(typeof DecompressionStream==='undefined')throw new Error('BROWSER_GZIP');
    fetchController=new AbortController();
    const response=await fetch(url,{signal:fetchController.signal});
    if(!response.ok)throw new Error('Audio download failed');
    const blob=await new Response(response.body.pipeThrough(new DecompressionStream('gzip'))).blob();
    if(token!==seq)return;
    audioObjectUrl=URL.createObjectURL(new Blob([blob],{type:'audio/mpeg'}));playable=audioObjectUrl;
   }
   if(token!==seq)return;
   audio.src=playable;audio.playbackRate=speed;audio.preservesPitch=true;await audio.play();""")
s=s.replace("toast(e.name==='NotAllowedError'?", "toast(e.message==='BROWSER_GZIP'?'請使用新版 Chrome、Edge、Firefox 或 Safari 播放音檔。':e.name==='NotAllowedError'?")
s=s.replace('音檔已檢查路徑與檔案完整性，未逐段人工聽辨錄音內容。','線上版音檔採可完整還原的 gzip 壓縮，播放前還原為原始 MP3，音質不變。音檔已檢查路徑與完整性，未逐段人工聽辨內容。')
(OUT/'app.js').write_text(s)
size=sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())
assert size<251*1024*1024, size
report={'files':sum(p.is_file() for p in OUT.rglob('*')),'expandedBytes':size,'limitBytes':256*1024*1024,'gzipMp3Files':compressed,'assetBytesBefore':before,'assetBytesAfter':after,'validation':'Every gzip payload was decompressed and compared byte-for-byte with the original MP3.'}
(BASE/'data/hosted-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,indent=2))
