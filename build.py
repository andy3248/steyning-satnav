#!/usr/bin/env python3
"""Build both round pages from src/.

  python3 build.py

Writes index.html (Annington round) and ashurst/index.html (Ashurst round).
Edit the app in src/template.html; round data lives in src/annington and src/ashurst.
"""
import json,re,os
ROOT=os.path.dirname(os.path.abspath(__file__));S=os.path.join(ROOT,'src')+'/'
TEMPLATE=open(S+'template.html').read()
HEAD=open(S+'head.html').read()
SW='<script>if("serviceWorker" in navigator)window.addEventListener("load",()=>navigator.serviceWorker.register("sw.js").catch(()=>{}));</script>'

# ---------- Annington round ----------
ann=TEMPLATE.replace('/*DATA*/',open(S+'annington/data.js').read().rstrip('\n')+'\nconst BASEMAP='+json.dumps(open(S+'annington/basemap.txt').read())+';')
open(os.path.join(ROOT,'index.html'),'w').write(HEAD+ann+'\n</body></html>')

# ---------- Ashurst round (frame order, shelves 1-14) ----------
def build_ashurst():
    h=TEMPLATE
    P=json.load(open(S+'ashurst/placed.json'))
    A=[]
    for sh,road,lab,lat,lon,q in P:
        num,name=(lab,"") if re.fullmatch(r'\d+[A-Z]?',lab) else ("",lab)
        A.append([lat,lon,num,name,road,"",sh,q])
    data='const ROUND_CFG={id:"ashurst",name:"Ashurst Round",kind:"van"};\nconst A='+json.dumps(A,separators=(',',':'))+';\nconst B=[],R=[],W=[];\nconst BASEMAP='+json.dumps(open(S+'ashurst/basemap.txt').read())+';'
    def rep(old,new,count=1):
        nonlocal h
        assert h.count(old)>=1,old[:60]
        h=h.replace(old,new) if count==0 else h.replace(old,new,count)
    rep('/*DATA*/',data)
    # items: carry shelf + accuracy
    rep('A.forEach((r,i)=>items.push({id:"a"+i,lat:r[0],lon:r[1],num:r[2],name:r[3],road:r[4],pc:r[5],known:!!(r[2]||r[3])}));',
        'A.forEach((r,i)=>items.push({id:"a"+i,lat:r[0],lon:r[1],num:r[2],name:r[3],road:r[4],pc:r[5],known:true,shelf:r[6],approx:r[7]!=="map"}));')
    rep('if(f){it.lat=f.lat;it.lon=f.lon;it.moved=1;}','if(f){it.lat=f.lat;it.lon=f.lon;it.moved=1;it.approx=false;}')
    # sequence = frame order
    s=h.index('SEG.forEach(([title,f,start,mode,groad,rroad])=>{'); e=h.index('}\nconst seqLabel')
    h=h[:s]+'items.forEach(it=>SEQ.push({seg:it.road,shelf:it.shelf,it,id:it.id,x:it.x,y:it.y,lat:it.lat,lon:it.lon,pc:""}));\n'+h[e:]
    rep('const label=it=>labels[it.id]||[it.num,it.name].filter(Boolean).join(" ");',
        'const label=it=>labels[it.id]||(it.num?it.num+" "+it.road:it.name);')
    # chip for best-guess spots
    rep("""${q.x==null?'<span class="chip warn">Spot not mapped</span>':""}""",
        """${q.x==null?'<span class="chip warn">Spot not mapped</span>':""}${q.it&&q.it.approx?'<span class="chip warn">Pin is a best guess</span>':""}""")
    # storage keys (same github.io origin as Steyning page)
    for k in ['walkLabels','walkPos','hIdx','navMute']:
        h=h.replace('"%s"'%k,'"ash_%s"'%k)
    h=h.replace('STEYNING-FIXES','ASHURST-FIXES').replace('Steyning sat nav fixes','Ashurst round fixes')
    rep('Map of the Annington round','Map of the Ashurst round')
    rep('Addresses without a mapped position come from the GOV.UK energy certificate register, which only lists homes that have had an EPC.',
        'Delivery order is the sorting frame, shelves 1 to 14, left to right. Pins marked “best guess” were placed on the nearest likely building, so check them and use Fix this house.')
    rep('const roadNorm=s=>',
     '// keep only the biggest connected road network, so pins never snap to a cut-off track\n'
     'const MAINE=(()=>{const comp=new Int32Array(NODES.length).fill(-1);let best=-1,bestN=0;for(let s=0;s<NODES.length;s++){if(comp[s]>=0||!ADJ[s].length)continue;const st=[s];comp[s]=s;let n=0;while(st.length){const u=st.pop();n++;for(const [v] of ADJ[u])if(comp[v]<0){comp[v]=s;st.push(v);}}if(n>bestN){bestN=n;best=s;}}return EDGES.map(e=>comp[e.u]===best);})();\n'
     'const roadNorm=s=>')
    rep('EDGES.forEach((e,ei)=>{const a=NODES[e.u]','EDGES.forEach((e,ei)=>{if(!MAINE[ei])return;const a=NODES[e.u]')
    rep('(q.x==null?"Spot not mapped · ":"")+(q.pc||seqRoad(q))','"Shelf "+q.shelf+" · "+seqRoad(q)+(q.it&&q.it.approx?" · pin is a best guess":"")')
    rep('· houses ${s.first+1}–${s.last+1}','· houses ${s.first+1}–${s.last+1} · shelf ${SEQ[s.first].shelf}${SEQ[s.last].shelf!==SEQ[s.first].shelf?"–"+SEQ[s.last].shelf:""}')
    h=h.replace('<title>Annington Round</title>','<title>Ashurst Round</title>')
    rep('<div class="attr">Map data © OpenStreetMap contributors</div>','<div class="attr">Map data © OpenStreetMap contributors · Contains OS data © Crown copyright and database right 2026</div>')
    ASHURST=h

    return ASHURST
os.makedirs(os.path.join(ROOT,'ashurst'),exist_ok=True)
open(os.path.join(ROOT,'ashurst','index.html'),'w').write(HEAD+build_ashurst()+'\n'+SW+'\n</body></html>')
print('built index.html and ashurst/index.html')
