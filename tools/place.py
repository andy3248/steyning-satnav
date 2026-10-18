#!/usr/bin/env python3
"""Repeatable pin placement from committed OSM/UPRN snapshots; no network access.

python3 tools/place.py --write    # rebuild placements, audit and offline review page
python3 tools/place.py --check    # reproduce and compare without writing

Frame identities and all pre-existing map pins are immutable. A real UPRN point
is not a verified address match. Heuristics without sufficient anchors remain guess.
"""
import argparse,collections,csv,hashlib,json,math,re,statistics,sys
from pathlib import Path
from geo import Buildings,Road,Spatial,center,decode,dist,ll,norm,number,roadnorm,xy
ROOT=Path(__file__).resolve().parents[1];DATA=ROOT/'data';ROUNDS=('annington','ashurst','wiston')
MOTOR={'motorway','trunk','primary','secondary','tertiary','unclassified','residential','living_street','service','track','road'}

def pointkey(p):return tuple(ll(p))
def counts(rows):return dict(collections.Counter(r[5] for r in rows))
def clean_title(s):return re.sub(r'\s*\([^)]*\)','',s).strip()
def housenorm(s):
 # Unit-tagged cottage groups use both singular and plural forms in the frame.
 return re.sub(r'cottages$', 'cottage', norm(s))
def unit_group(label):
 m=re.match(r'^(\d+)[a-zA-Z]?\s+(.+)$',clean_title(label))
 return (int(m[1]),housenorm(m[2])) if m else None

def sources():
 for name,key in [('osm-addresses','sha256'),('os-open-uprn','csv_sha256')]:
  metadata=json.loads((DATA/(name+'.source.json')).read_text());source=DATA/(name+('.csv' if name=='os-open-uprn' else '.json'))
  if hashlib.sha256(source.read_bytes()).hexdigest()!=metadata[key]:raise ValueError('Source checksum does not match provenance: '+name)
 osm=json.loads((DATA/'osm-addresses.json').read_text())
 if osm.get('remark'):raise ValueError('Incomplete Overpass snapshot')
 features=[];ways=collections.defaultdict(list);polygons=[]
 for e in osm['elements']:
  t=e.get('tags',{});p=center(e)
  if t.get('building') and len(e.get('geometry',[]))>3:polygons.append([xy(g['lat'],g['lon']) for g in e['geometry'] if 'lat' in g])
  if t.get('highway') in MOTOR and t.get('name') and e.get('geometry'):
   ways[roadnorm(t['name'])].append([xy(g['lat'],g['lon']) for g in e['geometry'] if 'lat' in g])
  if p and (any(k.startswith('addr:') for k in t) or (t.get('name') and (t.get('building') or t.get('amenity') or t.get('office') or t.get('shop')))):
   features.append({'id':e['type']+'/'+str(e['id']),'tags':t,'p':p})
 # Basemap street lines fill omissions, but never replace better OSM geometry.
 for r in ROUNDS:
  fallback=collections.defaultdict(list)
  for line in (ROOT/'src'/r/'basemap.txt').read_text().splitlines():
   fields=line.split('|')
   if fields[0]=='B':polygons.append(decode(fields[1]))
   if fields[0]=='R' and fields[2]:fallback[roadnorm(fields[2])].append(decode(fields[3]))
  for name,lines in fallback.items():
   if name not in ways:ways[name]=lines
 uprns=[];duplicates=collections.defaultdict(list)
 for row in csv.DictReader((DATA/'os-open-uprn.csv').open()):
  p=xy(float(row['LATITUDE']),float(row['LONGITUDE']));duplicates[pointkey(p)].append(row['UPRN'])
 buildings=Buildings(polygons)
 for key,ids in sorted(duplicates.items()):
  p=xy(*key);uprns.append({'p':p,'ids':sorted(ids,key=int),'lat':key[0],'lon':key[1],'building':buildings.contains(p)})
 return features,ways,uprns

def match_feature(row,model,features):
 """Exact normalised labels only; street contradictions disqualify a match."""
 road,label=row[1:3];rn=roadnorm(road);labelnorm=housenorm(clean_title(label));n=number(label);matches=[]
 for f in features:
  t=f['tags'];street=t.get('addr:street','');substreet=t.get('addr:substreet','');num=t.get('addr:housenumber','')
  names=[t.get('addr:housename',''),t.get('name','')]
  names += [num+' '+v for v in [t.get('addr:housename',''),substreet,street] if num and v]
  unit=t.get('addr:unit','')
  names += [unit+' '+v for v in [t.get('addr:housename',''),t.get('name','')] if unit and v]
  exact_name=not n and any(labelnorm==housenorm(v) for v in names if v)
  exact_number=bool(n and norm(num)==norm(label) and roadnorm(street or substreet)==rn)
  if not (exact_name or exact_number):continue
  # A sub-address (e.g. 1 Iris Cottages on Charlton Street) may carry its own
  # addr:street; only accept it when that full sub-address was matched.
  full_sub=any(labelnorm==housenorm(num+' '+v) for v in [substreet,street] if num and v)
  if street and roadnorm(street)!=rn and not full_sub:continue
  d=model.project(f['p'])[0] if model else dist(xy(row[3],row[4]),f['p'])
  if d>(180 if n else 650 if street else 75):continue
  olddist=dist(xy(row[3],row[4]),f['p'])
  if olddist>4000:continue
  matches.append((d*.6+olddist*.1,f))
 matches.sort(key=lambda x:(x[0],x[1]['id']))
 if not matches:return None
 # Node and building representations of the same address are harmless duplicates;
 # similarly named houses at different positions need human disambiguation.
 if len(matches)>1 and dist(matches[0][1]['p'],matches[1][1]['p'])>35 and matches[1][0]-matches[0][0]<25:return None
 return matches[0][1]

def isotonic_assignment(rows,candidates,cost):
 """Minimum-cost injective ordered assignment, allowing unmatched rows."""
 # Skipping an entry is preferable to an implausible candidate costing > 80,000.
 n=len(rows);m=len(candidates);prev=[0.]*(m+1);choices=[]
 for i,row in enumerate(rows):
  cur=[prev[0]+80000];trace=bytearray(m+1);trace[0]=2
  for j,candidate in enumerate(candidates,1):
   vals=(cur[j-1],prev[j]+80000,prev[j-1]+cost(row,candidate));k=min(range(3),key=lambda k:vals[k]);cur.append(vals[k]);trace[j]=k
  prev=cur;choices.append(trace)
 out={};i=n;j=m
 while i:
  k=choices[i-1][j]
  if not j or k==1:i-=1
  elif k==0:j-=1
  else:out[rows[i-1]]=candidates[j-1];i-=1;j-=1
 return out

def place_all(before,features,ways,uprns):
 result={r:[x[:] for x in before[r]] for r in ROUNDS};audit={r:[{} for _ in before[r]] for r in ROUNDS};models={};road_audits={r:[] for r in ROUNDS}
 space=Spatial([u['p'] for u in uprns]);used=set();reserved=[]
 # Protect map pins in every round before allocating a single unconfirmed point.
 for r in ROUNDS:
  for i,row in enumerate(before[r]):
   if row[5]=='map':used.add(pointkey(xy(row[3],row[4])));reserved.append(xy(row[3],row[4]));audit[r][i]={'method':'preserved-map','reason':'Existing confirmed map pin; not moved.'}
 used_uprns=set()
 for p in reserved:
  for d,j in space.near(p,4):used_uprns.add(j)
 def available(j):return j not in used_uprns and pointkey(uprns[j]['p']) not in used
 def claim(r,i,p,quality,info,u=None):
  k=pointkey(p)
  if k in used:return False
  if u is not None and not available(u):return False
  result[r][i][3:6]=[*ll(p),quality];used.add(k)
  if u is not None:used_uprns.add(u);info.update(uprn=uprns[u]['ids'][0],coincident_uprns=uprns[u]['ids'],on_mapped_building=uprns[u].get('building',True))
  # Also reserve an adjacent UPRN if a confirmed OSM centroid is within 4m.
  if quality=='map':
   for d,j in space.near(p,4):used_uprns.add(j)
  audit[r][i]=info;return True
 # Build each street model, oriented using the smallest confirmed number where possible.
 for r in ROUNDS:
  for road in dict.fromkeys(x[1] for x in before[r]):
   inds=[i for i,x in enumerate(before[r]) if x[1]==road];numbered=[i for i in inds if number(before[r][i][2])];verified=[i for i in numbered if before[r][i][5]=='map']
   start=min(verified or numbered or inds,key=lambda i:number(before[r][i][2]) or (i,''));reference=xy(*before[r][start][3:5]);lines=ways.get(roadnorm(road),[])
   override=json.loads((DATA/'road-models.json').read_text()).get(r+':'+road,{})
   for alias in override.get('osm_names',[]):lines=lines+ways.get(roadnorm(alias),[])
   if override.get('osm_ways'):
    selected=set(override['osm_ways']);osm=json.loads((DATA/'osm-addresses.json').read_text())
    lines=lines+[[xy(g['lat'],g['lon']) for g in e.get('geometry',[]) if 'lat' in g] for e in osm['elements'] if e['type']=='way' and e['id'] in selected]
   models[r,road]=Road(road,lines,reference) if lines else None
 # Exact OSM identity matching comes before *any* heuristic allocations.
 for r in ROUNDS:
  for i,row in enumerate(before[r]):
   if row[5]=='map':continue
   f=match_feature(row,models[r,row[1]],features)
   if f:
    ref=f['tags'].get('ref:GB:uprn');near=space.near(f['p'],20);j=next((j for d,j in near if ref in uprns[j]['ids']),None) if ref else None
    p=uprns[j]['p'] if j is not None and available(j) else f['p']
    if not claim(r,i,p,'map',{'method':'osm-exact','osm':f['id'],'reason':'Exact normalised house name/number with compatible street or sub-address.'},j if j is not None and available(j) else None):
     audit[r][i]={'method':'osm-collision','osm':f['id'],'reason':'OSM match shares an already occupied coordinate; requires review.'}
 # Resolve pre-existing overlapping pins before loose heuristics consume their
 # few local points. This is only a distinct-point proposal, never confirmation.
 duplicate_groups=collections.defaultdict(list)
 for r in ROUNDS:
  for i,row in enumerate(before[r]):duplicate_groups[tuple(row[3:5])].append((r,i))
 for group in duplicate_groups.values():
  if len(group)<2:continue
  for r,i in group:
   row=before[r][i]
   if row[5]=='map' or audit[r][i].get('method')=='osm-exact':continue
   p=xy(*row[3:5]);model=models[r,row[1]];corridor=max(85,model.project(p)[0]+40) if model else math.inf
   pool=[(not uprns[j].get('building',True),d,j) for d,j in space.near(p,180) if available(j) and (model is None or model.project(uprns[j]['p'])[0]<corridor)]
   if pool:
    _,d,j=min(pool)
    claim(r,i,uprns[j]['p'],'guess',{'method':'duplicate-unverified','reason':'Old entries shared one pin and the open sources do not distinguish every house. This distinct nearby real point is an unverified review proposal.','old_shared_frames':[{'round':rr,'frame':ii+1} for rr,ii in group]},j)
 # Cache nearest-road ownership of candidate UPRNs, using named motor roads only.
 ownership={}
 overrides=json.loads((DATA/'road-models.json').read_text())
 allmodels={}
 for rn,lines in ways.items():
  for pts in lines:
   for a,b in zip(pts,pts[1:]):
    if dist(a,b)>0:allmodels.setdefault(rn,[]).append((a,b))
 from geo import segment
 def owners(j):
  if j not in ownership:
   p=uprns[j]['p'];ds=[]
   for rn,segments in allmodels.items():
    d=min((segment(p,a,b)[0] for a,b in segments),default=math.inf);ds.append((d,rn))
   ds.sort();ownership[j]=ds
  return ownership[j]
 for r in ROUNDS:
  rows=before[r]
  for road in dict.fromkeys(x[1] for x in rows):
   inds=[i for i,x in enumerate(rows) if x[1]==road];model=models[r,road];rn=roadnorm(road);override=overrides.get(r+':'+road,{})
   pending=[i for i in inds if rows[i][5]!='map' and audit[r][i].get('method') not in ('osm-exact','duplicate-unverified')]
   if not pending:continue
   if not model:
    for i in pending:audit[r][i].update(reason='No named road geometry; nearest real point remains an unverified guess.')
    continue
   # Only UPRNs in this street corridor; reject adjacent streets and remote
   # addresses, and collapse coincident parent/child UPRNs to a single point.
   candidates=[]
   for j,u in enumerate(uprns):
    proj=model.project(u['p'])
    if proj[0]>85:continue
    ds=owners(j)
    aliases={roadnorm(n) for n in override.get('osm_names',[])}|{rn}
    if ds and ds[0][1] not in aliases and ds[0][0]+8<proj[0] and not override.get('unverified_road_name'):continue
    if not available(j):continue
    candidates.append((j,proj))
   anchor=[i for i in inds if result[r][i][5]=='map'];numeric=[i for i in inds if number(rows[i][2])];numanchors=[i for i in numeric if i in anchor]
   ap={i:model.project(xy(*result[r][i][3:5])) for i in anchor}
   sidevotes={p:[1 if ap[i][2]>0 else -1 for i in numanchors if number(rows[i][2])[0]%2==p and abs(ap[i][2])>2] for p in (0,1)}
   sides={p:(1 if sum(v)>=0 else -1) for p,v in sidevotes.items() if v}
   sequential=len(numanchors)>=4 and len(sides)==2 and sides[0]==sides[1]
   if len(sides)==1:
    p=next(iter(sides));sides[1-p]=-sides[p]
   anchored=bool(numanchors)
   if not sides:sides={0:-1,1:1}
   if numeric:road_audits[r].append({'road':road,'confirmed_numeric_anchors':len(numanchors),'numbering':'confirmed-sequential-one-side' if sequential else 'parity-anchored' if anchored else 'unanchored-parity-guess','candidate_points':len(candidates)})
   # Each parity follows road chainage, interpolated between same-parity anchors.
   groups=[sorted(numeric,key=lambda i:number(rows[i][2]))] if sequential else [sorted([i for i in numeric if number(rows[i][2])[0]%2==p],key=lambda i:number(rows[i][2])) for p in (1,0)]
   for group in groups:
    todo=[i for i in group if i in pending]
    if not todo:continue
    comps=collections.Counter(model.project(xy(*rows[i][3:5]))[3] for i in group);component=comps.most_common(1)[0][0]
    anchors=sorted([i for i in group if i in anchor and ap[i][3]==component],key=lambda i:number(rows[i][2]))
    slopes=[]
    for a,b in zip(anchors,anchors[1:]):
     if ap[a][3]==ap[b][3] and number(rows[b][2])[0]!=number(rows[a][2])[0]:slopes.append((ap[b][1]-ap[a][1])/(number(rows[b][2])[0]-number(rows[a][2])[0]))
    direction=1 if not slopes or statistics.median(slopes)>=0 else -1
    p=number(rows[todo[0]][2])[0]%2;side=sides[p]
    pool=[(j,proj) for j,proj in candidates if available(j) and proj[2]*side>1]
    pool.sort(key=lambda v:(direction*v[1][1],v[0]))
    # Do not span disconnected sections of a similarly named street.
    pool=[x for x in pool if x[1][3]==component]
    def target(i):
     n=number(rows[i][2])[0];lo=[a for a in anchors if number(rows[a][2])[0]<=n];hi=[a for a in anchors if number(rows[a][2])[0]>=n]
     if lo and hi:
      a,b=lo[-1],hi[0];na,nb=number(rows[a][2])[0],number(rows[b][2])[0]
      return ap[a][1] if na==nb else ap[a][1]+(ap[b][1]-ap[a][1])*(n-na)/(nb-na)
     if anchors:
      a=min(anchors,key=lambda a:abs(number(rows[a][2])[0]-n));slope=statistics.median(slopes) if slopes else direction*9
      return ap[a][1]+(n-number(rows[a][2])[0])*slope
     # No verified number can establish house identity, side, or direction.
     # Distribute along the actual street, but explicitly keep quality=guess.
     if pool:
      n0=number(rows[group[0]][2])[0];n1=number(rows[group[-1]][2])[0]
      ss=sorted(x[1][1] for x in pool);return ss[0]+(ss[-1]-ss[0])*(n-n0)/max(1,n1-n0) if direction>0 else ss[-1]-(ss[-1]-ss[0])*(n-n0)/max(1,n1-n0)
     return model.project(xy(*rows[i][3:5]))[1]
    def cost(i,c):
     j,proj=c;delta=abs(proj[1]-target(i));old=dist(xy(*rows[i][3:5]),uprns[j]['p'])
     # Anchored assignments cannot jump beyond neighbouring verified numbers.
     n=number(rows[i][2]);low=[a for a in anchors if number(rows[a][2])<n];high=[a for a in anchors if number(rows[a][2])>n]
     if low and direction*(proj[1]-ap[low[-1]][1]) < -3:return 1e9
     if high and direction*(ap[high[0]][1]-proj[1]) < -3:return 1e9
     if delta>180 or old>1000:return 1e9
     return delta*delta+proj[0]*proj[0]*.15+old*old*.015+(0 if uprns[j].get('building',True) else 60000)
    assigned=isotonic_assignment(todo,pool,cost)
    for i,(j,proj) in assigned.items():
     side_ok=bool(sidevotes.get(p)) and abs(sum(sidevotes[p]))==len(sidevotes[p])
     direction_ok=bool(slopes) and all(v*direction>0 for v in slopes)
     confidence=len(anchors)>=2 and direction_ok and side_ok and not sequential and not override.get('unverified_road_name') and uprns[j].get('building',True)
     reason='Ordered UPRN assignment using verified same-road numbering anchors.' if confidence else 'UPRN geometry only: number identity/side/direction lacks independent anchors.'
     if sequential:reason='OSM confirms sequential one-side numbering; UPRN continuation is unverified.'
     if not uprns[j].get('building',True):reason='Real point is outside the available building footprints; postal use and house identity remain unverified.'
     if override.get('unverified_road_name'):reason='The frame road has no named OSM geometry; the local service-road model and number assignment require review.'
     claim(r,i,uprns[j]['p'],'uprn' if confidence else 'guess',{'method':'number-sequence','reason':reason,'target_chainage_m':round(target(i),1),'road_distance_m':round(proj[0],1),'anchors':[a+1 for a in anchors]},j)
   # Names are interpolated only between confirmed neighbours on this same road.
   for i in pending:
    if audit[r][i].get('method') in ('number-sequence','osm-exact'):continue
    p0=xy(*rows[i][3:5]);preceding=[a for a in anchor if a<i];following=[a for a in anchor if a>i];a=preceding[-1] if preceding else None;b=following[0] if following else None
    family=unit_group(rows[i][2]);siblings=[a for a in anchor if family and unit_group(rows[a][2]) and unit_group(rows[a][2])[1]==family[1]]
    if siblings:
     sibling=min(siblings,key=lambda a:abs(unit_group(rows[a][2])[0]-family[0]));target=xy(*result[r][sibling][3:5])
     lo=[a for a in siblings if unit_group(rows[a][2])[0]<family[0]];hi=[a for a in siblings if unit_group(rows[a][2])[0]>family[0]]
     if lo and hi:
      u=max(lo,key=lambda a:unit_group(rows[a][2])[0]);v=min(hi,key=lambda a:unit_group(rows[a][2])[0]);nu,nv=unit_group(rows[u][2])[0],unit_group(rows[v][2])[0]
      pu,pv=xy(*result[r][u][3:5]),xy(*result[r][v][3:5]);fraction=(family[0]-nu)/(nv-nu);target=tuple(pu[k]+(pv[k]-pu[k])*fraction for k in (0,1))
     nearby=[(not uprns[j].get('building',True),d,j) for d,j in space.near(target,100) if available(j)]
     if nearby:
      _,d,j=min(nearby);confidence=uprns[j].get('building',True) and dist(p0,uprns[j]['p'])<300
      claim(r,i,uprns[j]['p'],'uprn' if confidence else 'guess',{'method':'unit-neighbours','reason':'Real point near a confirmed numbered unit in the same named cottage/building group; individual unit identity remains unverified.','anchors':[a+1 for a in siblings]},j);continue
    between=a is not None and b is not None and ap[a][3]==ap[b][3]
    target_p=p0;range_s=None;local_cluster=False
    if between:
     frac=(i-a)/(b-a);target_s=ap[a][1]+(ap[b][1]-ap[a][1])*frac;target_p=model.at(target_s,ap[a][3]);range_s=sorted([ap[a][1],ap[b][1]])
     pa=xy(*result[r][a][3:5]);pb=xy(*result[r][b][3:5])
     local_cluster=max(ap[a][0],ap[b][0])>85 and dist(pa,pb)<350
     if local_cluster:target_p=tuple(pa[k]+(pb[k]-pa[k])*frac for k in (0,1))
    pool=[]
    named_candidates=[(j,model.project(uprns[j]['p'])) for d,j in space.near(target_p,250)] if local_cluster else candidates
    for j,proj in named_candidates:
     if not available(j):continue
     if between and not local_cluster and (proj[3]!=ap[a][3] or not range_s[0]-3<=proj[1]<=range_s[1]+3):continue
     d=dist(target_p,uprns[j]['p'])
     if d>(max(25,dist(pa,pb)*.6) if local_cluster else 250 if between else 140):continue
     pool.append((d*d+dist(p0,uprns[j]['p'])**2*.04+(0 if uprns[j].get('building',True) else 60000),j,proj))
    if pool:
     _,j,proj=min(pool)
     # A failed numbered assignment must not gain confidence through the named
     # fallback: it still lacks an ordered candidate on the required side.
     named=number(rows[i][2]) is None
     confidence=named and between and dist(p0,uprns[j]['p'])<300 and uprns[j].get('building',True) and not override.get('unverified_road_name')
     reason='Free real point between confirmed same-road frame neighbours; house identity unverified.' if between else 'Nearest free real point on this road; insufficient matching neighbours to verify the label.'
     if not named:reason='No supported ordered number assignment; fallback real point still needs number/side review.'
     claim(r,i,uprns[j]['p'],'uprn' if confidence else 'guess',{'method':'frame-neighbours' if between else 'nearest-unverified','reason':reason,'anchors':[a+1,b+1] if between else [],'road_distance_m':round(proj[0],1)},j)
 # Anything still unresolved stays visibly guess. Do not invent offset coordinates.
 for r in ROUNDS:
  for i,row in enumerate(before[r]):
   if row[5]=='map' or audit[r][i].get('method') in ('osm-exact','duplicate-unverified','number-sequence','unit-neighbours','frame-neighbours','nearest-unverified'):continue
   p=xy(*row[3:5]);near=space.near(p,180);near.sort(key=lambda v:(not uprns[v[1]].get('building',True),v[0],v[1]))
   model=models[r,row[1]]
   # Rural addresses can be well back from the named road on a farm drive.
   # A fallback may stay in that existing off-road cluster, always as guess.
   corridor=max(85,model.project(p)[0]+40) if model else math.inf
   candidate=next((j for d,j in near if available(j) and (model is None or model.project(uprns[j]['p'])[0]<corridor)),None)
   info={'method':'fallback-unverified','reason':audit[r][i].get('reason','No supported road/identity assignment; requires driver review.')}
   if near and len(uprns[near[0][1]]['ids'])>1 and near[0][0]<5:
    info['reason']='Coincident UPRNs do not distinguish these addresses. A distinct nearby real point is only an unverified review proposal.'
   if candidate is not None:claim(r,i,uprns[candidate]['p'],'guess',info,candidate)
   else:
    if pointkey(p) in used:raise ValueError(f'No distinct real point for duplicate {r}:{i+1}')
    result[r][i][5]='guess';used.add(pointkey(p));audit[r][i]=info
 return result,audit,models,road_audits

def check_roads(rows,models,r):
 checks=[]
 for road in dict.fromkeys(x[1] for x in rows):
  indices=[i for i,x in enumerate(rows) if x[1]==road and number(x[2])];model=models[r,road]
  record={'road':road,'numbered_houses':len(indices),'parity_status':'not-applicable','gaps_over_60m':[],'order_reversals':[]}
  if indices and not model:record['parity_status']='no-road-geometry'
  if indices and model:
   proj={i:model.project(xy(*rows[i][3:5])) for i in indices};sides={p:[1 if proj[i][2]>0 else -1 for i in indices if number(rows[i][2])[0]%2==p and abs(proj[i][2])>2] for p in (0,1)}
   if all(sides.values()):
    major={p:1 if sum(v)>=0 else -1 for p,v in sides.items()};record['parity_status']='opposite-majorities' if major[0]!=major[1] else 'same-side-needs-review';record['side_exceptions']=[i+1 for i in indices if abs(proj[i][2])>2 and (1 if proj[i][2]>0 else -1)!=major[number(rows[i][2])[0]%2]]
   else:record['parity_status']='insufficient-both-sides'
   for p in (0,1):
    group=sorted([i for i in indices if number(rows[i][2])[0]%2==p],key=lambda i:number(rows[i][2]))
    diffs=[proj[b][1]-proj[a][1] for a,b in zip(group,group[1:]) if proj[a][3]==proj[b][3]];direction=1 if not diffs or statistics.median(diffs)>=0 else -1
    for a,b in zip(group,group[1:]):
     gap=dist(xy(*rows[a][3:5]),xy(*rows[b][3:5]))
     if gap>60:record['gaps_over_60m'].append({'from':a+1,'to':b+1,'labels':[rows[a][2],rows[b][2]],'metres':round(gap,1)})
     if proj[a][3]!=proj[b][3] or direction*(proj[b][1]-proj[a][1])<-5:record['order_reversals'].append([a+1,b+1])
  checks.append(record)
 return checks

def generate(write=False,check=False):
 baseline=json.loads((DATA/'pins-before.json').read_text());before=baseline['rounds'];features,ways,uprns=sources();after,audit,models,roads=place_all(before,features,ways,uprns)
 report={'unique_uprn_coordinates':len(uprns),'uprn_coordinates_on_buildings':sum(u.get('building',True) for u in uprns),'baseline_commit':baseline['source_commit'],'sources':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [DATA/'os-open-uprn.csv',DATA/'osm-addresses.json',DATA/'road-models.json']},'rounds':{}}
 for r in ROUNDS:
  current=json.loads((ROOT/'src'/r/'placed.json').read_text());frame=[line for line in (ROOT/'src'/r/'frame.txt').read_text().splitlines() if line.strip() and not line.lstrip().startswith('#')]
  assert len(current)==len(before[r])==len(frame)
  assert all(a[:3]==b[:3] for a,b in zip(current,before[r])),r+' identity/order changed'
  assert all(line==f'{row[0]}|{row[1]}|{row[2]}' for line,row in zip(frame,before[r])),r+' frame identity mismatch'
  seen=set();entries=[]
  for i,(old,new,info) in enumerate(zip(before[r],after[r],audit[r])):
   assert old[:3]==new[:3]
   assert new[5] in ('map','uprn','guess') and all(math.isfinite(v) for v in new[3:5])
   if old[5]=='map':assert old==new,r+': existing map pin changed'
   key=tuple(new[3:5]);assert key not in seen,(r,i+1,'duplicate point');seen.add(key)
   entries.append({'index':i,'frame':i+1,'shelf':old[0],'road':old[1],'label':old[2],'old':old[3:6],'new':new[3:6],'moved_m':round(dist(xy(*old[3:5]),xy(*new[3:5])),1),**info})
  unresolved=[e['frame'] for e in entries if e['new'][2]!='map' and not e.get('uprn')]
  report['rounds'][r]={'before':counts(before[r]),'after':counts(after[r]),'moved_map':[],'unresolved_no_real_point':unresolved,'entries':entries,'numbering_models':roads[r],'road_checks':check_roads(after[r],models,r)}
  if check:assert current==after[r],r+' output differs: run --write'
  previous=None;previous_file=ROOT/'docs/pin-report.json'
  if previous_file.exists():
   recorded=json.loads(previous_file.read_text())
   if recorded.get('baseline_commit')==baseline['source_commit'] and r in recorded.get('rounds',{}):
    previous=[row[:3]+entry['new'] for row,entry in zip(before[r],recorded['rounds'][r]['entries'])]
  if write and current not in (before[r],after[r],previous):raise ValueError(r+': manual coordinate/quality edits detected; refusing to overwrite them. Review/update the baseline or placement evidence first.')
  print('\n'+r.upper());print('Quality       Before  After')
  for quality in ['map','uprn','approx','guess']:print(f'{quality:12} {counts(before[r]).get(quality,0):6} {counts(after[r]).get(quality,0):6}')
  print('20 biggest moves: metres | label | road')
  for e in sorted(entries,key=lambda e:-e['moved_m'])[:20]:print(f"{e['moved_m']:7.1f} | {e['label']} | {e['road']}")
  problems=[c for c in report['rounds'][r]['road_checks'] if c['gaps_over_60m'] or c['order_reversals'] or c.get('side_exceptions') or c['parity_status'] in ('same-side-needs-review','no-road-geometry')]
  print('Roads requiring review:',len(problems),'(full details in docs/pin-report.json)')
 if write:
  # All rounds must pass identity/coordinate guards before any placement is written.
  for r in ROUNDS:(ROOT/'src'/r/'placed.json').write_text('[\n  '+',\n  '.join(json.dumps(row,ensure_ascii=False) for row in after[r])+'\n]\n')
  (ROOT/'docs/pin-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
  from report import markdown
  (ROOT/'docs/pin-report.md').write_text(markdown(report))
  from review import write_review
  write_review(ROOT,report,before,after)
 return report

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');parser.add_argument('--check',action='store_true');args=parser.parse_args()
 if args.write and args.check:parser.error('Choose --write or --check')
 generate(args.write,args.check)
