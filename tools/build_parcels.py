#!/usr/bin/env python3
"""Build parcels/index.html (the Parcel helper) from src/parcels/app.html.

Bakes in every address from all three rounds (frame order) and the named road shapes,
so the page works with no signal.  Run from the repo root:  python3 tools/build_parcels.py
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from opposite import opposites
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, 'src') + '/'
AL = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
IX = {c: i for i, c in enumerate(AL)}
LAT0, LON0 = 50.87, -0.35

def dec(s):
    out, i, a, b = [], 0, 0, 0
    def rd():
        nonlocal i
        r = sh = 0
        while True:
            if i >= len(s): return None
            c = IX.get(s[i]); i += 1
            if c is None: return None
            r |= (c & 0x1f) << sh; sh += 5
            if c < 0x20: break
        return ~(r >> 1) if r & 1 else r >> 1
    while i < len(s):
        da, db = rd(), rd()
        if da is None or db is None: break
        a += da; b += db
        out.append((round(LAT0 + a * 1e-5, 5), round(LON0 + b * 1e-5, 5)))
    return out

def simplify(pts, tol=4.0):
    # Douglas-Peucker in metres
    if len(pts) < 3: return pts
    k = 0.63
    def xy(p): return ((p[1] - LON0) * 111320 * k, (p[0] - LAT0) * 111320)
    P = [xy(p) for p in pts]
    keep = [False] * len(pts); keep[0] = keep[-1] = True
    st = [(0, len(pts) - 1)]
    while st:
        a, b = st.pop()
        ax, ay = P[a]; bx, by = P[b]; dx, dy = bx - ax, by - ay; L = (dx * dx + dy * dy) or 1e-9
        best, bi = -1, -1
        for i in range(a + 1, b):
            px, py = P[i]; t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L))
            d = ((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2) ** .5
            if d > best: best, bi = d, i
        if best > tol:
            keep[bi] = True; st += [(a, bi), (bi, b)]
    return [p for p, k2 in zip(pts, keep) if k2]

ROUNDS = [('annington', 'Annington'), ('wiston', 'Wiston'), ('ashurst', 'Ashurst'), ('penlands', 'Penlands')]
TOWN = {'annington': 'Steyning', 'wiston': 'Steyning', 'ashurst': 'Ashurst', 'penlands': 'Steyning'}
# frame road name -> road name on the map (for "you're on this road" alerts)
MAPROAD = {"Sir Georges Place": "Sir George's Place", "Stocks Hill": "Spithandle Lane", "Maudlyn Park Way": "Maudlyn Parkway",
           "Penlands Close": "Penland's Close", "Botolphs Road": "Annington Road", "Mount Park": "Bostal Road"}
houses, roads = [], {}
for rid, rname in ROUNDS:
    P = json.load(open(S + rid + '/placed.json'))
    OPP = opposites([(p[1], p[2], p[3], p[4], p[5] == 'map') for p in P], open(S + rid + '/basemap.txt').read(), MAPROAD)
    for k, (sh, road, lab, lat, lon, q) in enumerate(P):
        num = lab if re.fullmatch(r'\d+[A-Za-z]?', lab) else ''
        houses.append({'r': rid, 'k': k, 's': str(sh), 'road': road, 'mr': MAPROAD.get(road, road), 'num': num,
                       'name': '' if num else lab, 'lat': lat, 'lon': lon, 'q': q, 'town': TOWN[rid], 'opp': OPP[k]})
    for line in open(S + rid + '/basemap.txt'):
        p = line.rstrip('\n').split('|')
        if p[0] != 'R' or len(p) < 4 or not p[2]: continue
        pts = simplify(dec(p[3]))
        if len(pts) > 1: roads.setdefault(p[2], []).append(pts)
# de-duplicate identical road pieces that appear in more than one round's map
for n in roads:
    seen, keep = set(), []
    for pts in roads[n]:
        key = (pts[0], pts[-1], len(pts))
        if key in seen or (pts[-1], pts[0], len(pts)) in seen: continue
        seen.add(key); keep.append(pts)
    roads[n] = keep
H = [[h['r'], h['k'], h['s'], h['road'], h['num'], h['name'], h['lat'], h['lon'], 1 if h['q'] == 'map' else 0, h['opp']] for h in houses]
R = [[n, pcs] for n, pcs in sorted(roads.items())]
data = ('const HOUSES=' + json.dumps(H, separators=(',', ':')) + ';\nconst ROADGEO=' + json.dumps(R, separators=(',', ':')) +
        ';\nconst MAPROAD=' + json.dumps(MAPROAD) + ';')
app = open(S + 'parcels/app.html').read()
assert '/*DATA*/' in app
js = open(S + 'parcels/app.js').read()
assert '// ---------- start ----------' in js
js = js.replace('// ---------- start ----------', open(S + 'parcels/google.js').read() + '\n// ---------- start ----------')
app = app.replace('/*DATA*/', data).replace('/*APP*/', js)
os.makedirs(os.path.join(ROOT, 'parcels'), exist_ok=True)
open(os.path.join(ROOT, 'parcels', 'index.html'), 'w').write(app)
open(os.path.join(ROOT, 'parcels', 'sw.js'), 'w').write(open(S + 'parcels/sw.js').read())
print('parcels/index.html:', len(H), 'houses,', len(R), 'named roads,', round(len(data) / 1024), 'KB data')
