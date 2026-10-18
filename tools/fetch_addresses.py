#!/usr/bin/env python3
"""Fetch public source snapshots; normal placement uses committed snapshots offline.

python3 tools/fetch_addresses.py [--uprn] [--osm]
OS ZIP is processed sequentially and never saved nationally. Only bbox CSV is kept.
"""
import argparse,csv,datetime,hashlib,io,json,struct,time,urllib.parse,urllib.request,zlib
import http.client
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data'
BBOX=(50.86,-0.40,50.955,-0.29)  # includes northern Ashurst entries at 50.948
OS_API='https://api.os.uk/downloads/v1/products/OpenUPRN/downloads'
OVERPASS='https://maps.mail.ru/osm/tools/overpass/api/interpreter'

def get(url):
 return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'SteyningSatnav-PinReview/1.0'}),timeout=240)

class RangeStream:
 """Ordered stream with a bounded eight-chunk read-ahead; never stores the archive."""
 def __init__(self,url,size):
  self.size=size;self.chunk=4*1024*1024;self.workers=8;self.pool=ThreadPoolExecutor(self.workers);self.futures={};self.index=0;self.buffer=b'';self.pos=0
  with urllib.request.urlopen(urllib.request.Request(url,headers={'Range':'bytes=0-0','User-Agent':'SteyningSatnav-PinReview/1.0'}),timeout=90) as r:
   if r.status!=206:raise ValueError('OS download does not support byte ranges')
   self.url=url  # Resolve a fresh short-lived OS redirect for every range.
  for i in range(self.workers):self.schedule(i)
 def schedule(self,i):
  if i*self.chunk<self.size:self.futures[i]=self.pool.submit(self.fetch,i)
 def fetch(self,i):
  start=i*self.chunk;end=min(self.size,start+self.chunk)-1;data=bytearray();failures=0
  while len(data)<end-start+1:
   offset=start+len(data)
   req=urllib.request.Request(self.url,headers={'Range':f'bytes={offset}-{end}','User-Agent':'SteyningSatnav-PinReview/1.0'})
   try:
    with urllib.request.urlopen(req,timeout=90) as r:
     if r.status!=206 or not r.headers.get('Content-Range','').startswith(f'bytes {offset}-'):raise ValueError('Invalid HTTP range response')
     while len(data)<end-start+1:
      part=r.read(min(65536,end-start+1-len(data)))
      if not part:raise EOFError('Interrupted HTTP range')
      data.extend(part)
   except (OSError,EOFError,http.client.IncompleteRead) as exc:
    if isinstance(exc,http.client.IncompleteRead):data.extend(exc.partial)
    failures+=1
    if failures>8:raise
    print(f'Retrying interrupted OS chunk {i}, attempt {failures}, retained {len(data)} bytes',flush=True)
    time.sleep(min(4,failures))
  return bytes(data)
 def read(self,n):
  parts=[]
  while n and self.pos<self.size:
   if not self.buffer:
    self.buffer=self.futures.pop(self.index).result();self.schedule(self.index+self.workers);self.index+=1
    if self.index%8==0:print(f'{self.pos/1e6:.0f}/{self.size/1e6:.0f} MB streamed',flush=True)
   b=self.buffer[:n];self.buffer=self.buffer[len(b):];parts.append(b);self.pos+=len(b);n-=len(b)
  return b''.join(parts)
 def __enter__(self):return self
 def __exit__(self,*args):self.pool.shutdown(wait=False,cancel_futures=True)

def read_exact(stream,n):
 parts=[]
 while n:
  b=stream.read(n)
  if not b: raise EOFError('Truncated ZIP')
  parts.append(b);n-=len(b)
 return b''.join(parts)

def fetch_uprn():
 metadata=json.load(get(OS_API));entry=next(e for e in metadata if e['format']=='CSV' and e['area']=='GB')
 md5=hashlib.md5();total=0;seen=0;kept=[]
 print('Streaming '+entry['fileName']+' ('+str(entry['size'])+' bytes)',flush=True)
 with RangeStream(entry['url'],entry['size']) as stream:
  def read(n):
   nonlocal total
   b=read_exact(stream,n);md5.update(b);total+=len(b);return b
  while True:
   sig=read(4)
   if sig!=b'PK\x03\x04':
    # Read central directory too, to verify the publisher's whole-archive checksum.
    while True:
     b=stream.read(1024*1024)
     if not b:break
     md5.update(b);total+=len(b)
    break
   hdr=struct.unpack('<HHHHHIIIHH',read(26));flags,method=hdr[1:3];crc,compressed,size=hdr[5:8];nlen,xlen=hdr[-2:]
   name=read(nlen).decode();read(xlen)
   if method not in (0,8):raise ValueError('Unsupported ZIP compression method')
   if flags&8 or compressed==0xffffffff:raise ValueError('Unsupported streaming ZIP layout (descriptor/ZIP64)')
   inflater=zlib.decompressobj(-15) if method==8 else None
   pending=b'';remaining=compressed;checksum=0;unpacked=0;header=None
   while remaining:
    chunk=read(min(1024*1024,remaining));remaining-=len(chunk)
    out=inflater.decompress(chunk) if inflater else chunk
    checksum=zlib.crc32(out,checksum);unpacked+=len(out)
    if not name.lower().endswith('.csv'):continue
    lines=(pending+out).split(b'\n');pending=lines.pop()
    for line in lines:
     if not line:continue
     fields=line.decode('utf-8-sig').strip().split(',')
     if header is None:
      header=fields;ilat=header.index('LATITUDE');ilon=header.index('LONGITUDE');continue
     seen+=1;lat=float(fields[ilat]);lon=float(fields[ilon])
     if BBOX[0]<=lat<=BBOX[2] and BBOX[1]<=lon<=BBOX[3]:kept.append(fields)
    if seen and seen%1000000<25000:print(f'{seen:,} rows scanned; {len(kept):,} local; {total/1e6:.0f} MB streamed',flush=True)
   if checksum!=crc or unpacked!=size:raise ValueError('ZIP member checksum/size mismatch: '+name)
   if name.lower().endswith('.csv'):
    if pending.strip():raise ValueError('CSV missing final newline; parser refuses incomplete record')
    csv_header=header
 if md5.hexdigest()!=entry['md5'] or total!=entry['size']:raise ValueError('National archive checksum/size mismatch')
 kept.sort(key=lambda r:int(r[0]));dest=DATA/'os-open-uprn.csv'
 with dest.open('w',newline='') as f:
  writer=csv.writer(f);writer.writerow(csv_header);writer.writerows(kept)
 write_meta('os-open-uprn',{'api':OS_API,'download':{k:v for k,v in entry.items() if k!='url'},'bbox':BBOX,'national_rows_scanned':seen,'filtered_rows':len(kept),'licence':'Open Government Licence v3.0','attribution':'Contains OS data © Crown copyright and database right 2026','csv_sha256':hashlib.sha256(dest.read_bytes()).hexdigest()})
 print(f'Saved {len(kept)} local UPRNs from {seen:,} national rows')

def write_meta(name,info):
 info['retrieved_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 (DATA/(name+'.source.json')).write_text(json.dumps(info,indent=2)+'\n')

def fetch_osm():
 query=(DATA/'addresses.overpassql').read_text();url=OVERPASS+'?'+urllib.parse.urlencode({'data':query})
 raw=get(url).read();value=json.loads(raw)
 if value.get('remark'):raise ValueError('Overpass partial/error response: '+value['remark'])
 dest=DATA/'osm-addresses.json';dest.write_bytes(raw)
 write_meta('osm-addresses',{'endpoint':OVERPASS,'bbox':BBOX,'elements':len(value['elements']),'osm_base':value.get('osm3s',{}),'query_file':'addresses.overpassql','licence':'Open Database Licence 1.0','attribution':'© OpenStreetMap contributors','sha256':hashlib.sha256(raw).hexdigest()})

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--uprn',action='store_true');parser.add_argument('--osm',action='store_true');args=parser.parse_args();DATA.mkdir(exist_ok=True)
 if not args.uprn and not args.osm:parser.error('Choose --uprn and/or --osm; no network requests are made implicitly')
 if args.uprn:fetch_uprn()
 if args.osm:fetch_osm()
