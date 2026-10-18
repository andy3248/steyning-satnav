"""Small, dependency-free local geometry helpers (metres near Steyning)."""
import collections,heapq,math,re,unicodedata
K=math.cos(math.radians(50.9));M=111320

def xy(lat,lon):return ((lon+.35)*M*K,(lat-50.9)*M)
def ll(p):return [round(p[1]/M+50.9,7),round(p[0]/(M*K)-.35,7)]
def dist(a,b):return math.hypot(a[0]-b[0],a[1]-b[1])
def norm(s):return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',str(s)).lower())
def roadnorm(s):return norm(s).replace('maudlyn','maudlin')
def number(s):
 m=re.fullmatch(r'(\d+)([a-zA-Z]?)',str(s).strip());return (int(m[1]),m[2].lower()) if m else None

def center(e):
 if 'lat' in e:return xy(e['lat'],e['lon'])
 g=e.get('geometry',[])
 if not g and e.get('members'):
  rings=[m.get('geometry',[]) for m in e['members'] if m.get('role')=='outer'];g=max(rings,key=len,default=[])
 pts=[xy(p['lat'],p['lon']) for p in g if 'lat' in p]
 if not pts:return None
 if len(pts)>3 and pts[0]==pts[-1]:
  area=sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(pts,pts[1:]))
  if abs(area)>1e-6:return tuple(sum((a[k]+b[k])*(a[0]*b[1]-b[0]*a[1]) for a,b in zip(pts,pts[1:]))/(3*area) for k in [0,1])
 return tuple(sum(p[k] for p in pts)/len(pts) for k in [0,1])

def decode(s):
 alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_';ix={c:i for i,c in enumerate(alphabet)};i=0;a=b=0;pts=[]
 def read():
  nonlocal i
  v=shift=0
  while True:
   c=ix[s[i]];i+=1;v|=(c&31)<<shift;shift+=5
   if c<32:break
  return ~(v>>1) if v&1 else v>>1
 while i<len(s):
  a+=read();b+=read();pts.append(xy(50.87+a*1e-5,-.35+b*1e-5))
 return pts

def segment(p,a,b):
 dx=b[0]-a[0];dy=b[1]-a[1];length=math.hypot(dx,dy)
 if not length:return (dist(p,a),0,0)
 t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(length*length)))
 q=(a[0]+t*dx,a[1]+t*dy);cross=(dx*(p[1]-a[1])-dy*(p[0]-a[0]))/length
 return dist(p,q),t,cross

class Spatial:
 def __init__(self,points,cell=80):
  self.points=points;self.cell=cell;self.grid=collections.defaultdict(list)
  for i,p in enumerate(points):self.grid[self.key(p)].append(i)
 def key(self,p):return (math.floor(p[0]/self.cell),math.floor(p[1]/self.cell))
 def near(self,p,radius):
  x,y=self.key(p);n=math.ceil(radius/self.cell);out=[]
  for u in range(x-n,x+n+1):
   for v in range(y-n,y+n+1):
    for i in self.grid.get((u,v),[]):
     d=dist(p,self.points[i])
     if d<=radius:out.append((d,i))
  return sorted(out)

class Road:
 """Dijkstra chainage on a named road; segments oriented away from a real endpoint."""
 def __init__(self,name,ways,reference):
  self.name=name;self.segs=[];self.adj=collections.defaultdict(list)
  for pts in ways:
   for a,b in zip(pts,pts[1:]):
    a=tuple(round(v,2) for v in a);b=tuple(round(v,2) for v in b)
    if a==b:continue
    self.segs.append((a,b));d=dist(a,b);self.adj[a].append((b,d));self.adj[b].append((a,d))
  self.s={};component=0;left=set(self.adj)
  # Components get separate chainages; never interpolate across disconnected roads.
  self.components={}
  while left:
   seed=min(left);stack=[seed];nodes=set()
   while stack:
    u=stack.pop()
    if u in nodes:continue
    nodes.add(u);stack.extend(v for v,d in self.adj[u] if v not in nodes)
   endpoints=[u for u in nodes if len(self.adj[u])==1] or list(nodes)
   origin=min(endpoints,key=lambda u:(dist(u,reference),u));queue=[(0,origin)];ds={origin:0}
   while queue:
    d,u=heapq.heappop(queue)
    if d!=ds[u]:continue
    for v,w in self.adj[u]:
     if d+w<ds.get(v,math.inf):ds[v]=d+w;heapq.heappush(queue,(d+w,v))
   self.s.update(ds);self.components.update({u:component for u in nodes});left-=nodes;component+=1
 def project(self,p):
  best=None
  for a,b in self.segs:
   if self.s[a]>self.s[b]:a,b=b,a
   d,t,side=segment(p,a,b);value=(d,self.s[a]+t*dist(a,b),side,self.components[a])
   if best is None or value[0]<best[0]:best=value
  return best
 def at(self,s,component=0):
  best=None
  for a,b in self.segs:
   if self.components[a]!=component:continue
   if self.s[a]>self.s[b]:a,b=b,a
   d=dist(a,b);t=max(0,min(1,(s-self.s[a])/d));error=abs(self.s[a]+t*d-s)
   if best is None or error<best[0]:best=(error,(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t))
  return best[1] if best else None

class Buildings:
 """Point-in-footprint lookup, allowing 2m for basemap coordinate quantisation."""
 def __init__(self,polygons,cell=80):
  self.polygons=polygons;self.cell=cell;self.grid=collections.defaultdict(list)
  for i,poly in enumerate(polygons):
   if len(poly)<3:continue
   xs=[p[0] for p in poly];ys=[p[1] for p in poly]
   for x in range(math.floor((min(xs)-2)/cell),math.floor((max(xs)+2)/cell)+1):
    for y in range(math.floor((min(ys)-2)/cell),math.floor((max(ys)+2)/cell)+1):self.grid[x,y].append(i)
 def contains(self,p):
  for i in self.grid.get((math.floor(p[0]/self.cell),math.floor(p[1]/self.cell)),[]):
   poly=self.polygons[i];inside=False
   for a,b in zip(poly,poly[1:]+poly[:1]):
    if segment(p,a,b)[0]<=2:return True
    if (a[1]>p[1])!=(b[1]>p[1]) and p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:inside=not inside
   if inside:return True
  return False
