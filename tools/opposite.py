"""Work out which house is directly across the road from each house.

Uses the real house positions (only pins that came from address data, quality "map") and the
road lines in the round's basemap.  For each house: find where it sits along its road and which
side it is on, then pick the house on the other side of the same road that is closest along the
road.  Roads where numbers don't pair up neatly (e.g. 2 opposite 11) come out right because this
goes by position, not by number.
"""
import math

AL = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_'
IX = {c: i for i, c in enumerate(AL)}
LAT0, LON0 = 50.87, -0.35
K = math.cos(math.radians(50.9)); M = 111320.0


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
        out.append((LAT0 + a * 1e-5, LON0 + b * 1e-5))
    return out


def xy(lat, lon): return ((lon - LON0) * M * K, (lat - LAT0) * M)


def road_lines(basemap_text):
    roads = {}
    for line in basemap_text.split('\n'):
        p = line.split('|')
        if p[0] == 'R' and len(p) >= 4 and p[2]:
            pts = [xy(*q) for q in dec(p[3])]
            if len(pts) > 1: roads.setdefault(p[2], []).append(pts)
    return roads


def project(p, pieces):
    best = None
    for pi, pts in enumerate(pieces):
        run = 0.0
        for i in range(len(pts) - 1):
            (ax, ay), (bx, by) = pts[i], pts[i + 1]
            dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy or 1e-9; L = math.sqrt(L2)
            t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
            qx, qy = ax + t * dx, ay + t * dy; d = math.hypot(p[0] - qx, p[1] - qy)
            if best is None or d < best[0]:
                best = (d, pi, run + t * L, 1 if dx * (p[1] - ay) - dy * (p[0] - ax) > 0 else -1)
            run += L
    return best  # (distance to road, piece, distance along, side)


def opposites(entries, basemap_text, maproad=None, max_road=45.0, max_along=30.0):
    """entries: list of (road, label, lat, lon, sure).  Returns a list of opposite labels ('' if unknown)."""
    maproad = maproad or {}
    roads = road_lines(basemap_text)
    info = []
    for road, label, lat, lon, sure in entries:
        pcs = roads.get(maproad.get(road, road))
        if not sure or not pcs: info.append(None); continue
        pr = project(xy(lat, lon), pcs)
        info.append(pr if pr and pr[0] <= max_road else None)
    pos = [xy(e[2], e[3]) for e in entries]
    out = []
    for i, (road, label, lat, lon, sure) in enumerate(entries):
        me = info[i]
        if not me: out.append(''); continue
        cands = []
        for j, (road2, label2, *_r) in enumerate(entries):
            o = info[j]
            if j == i or not o or road2 != road or o[1] != me[1] or o[3] == me[3]: continue
            if abs(o[2] - me[2]) > max_along * 1.6: continue
            cands.append((math.dist(pos[i], pos[j]), label2))
        cands.sort()
        if not cands or cands[0][0] > 70: out.append(''); continue
        best = cands[0][1]
        # two houses almost equally close: give both, nearest first
        if len(cands) > 1 and cands[1][0] - cands[0][0] < 2.5: best += ' or ' + cands[1][1]
        out.append(best)
    # only keep pairs that agree both ways (A is across from B and B is across from A), so a
    # house never gets a wrong "opposite" just because the road bends or ends there
    idx = {}
    for i, e in enumerate(entries): idx.setdefault((e[0], e[1]), i)
    final = []
    for i, e in enumerate(entries):
        if not out[i]: final.append(''); continue
        keep = [c for c in out[i].split(' or ') if (e[0], c) in idx and e[1] in out[idx[(e[0], c)]].split(' or ')]
        final.append(' or '.join(keep))
    # on odd/even roads, a same-parity "opposite" is a mistake (a bend or a spur), so drop it
    par = lambda t: int(t) % 2 if t.isdigit() else None
    for road in set(e[0] for e in entries):
        ii = [i for i, e in enumerate(entries) if e[0] == road and final[i] and par(e[1]) is not None]
        diff = sum(1 for i in ii for c in final[i].split(' or ') if par(c) is not None and par(c) != par(entries[i][1]))
        same = sum(1 for i in ii for c in final[i].split(' or ') if par(c) is not None and par(c) == par(entries[i][1]))
        if diff > same * 2:
            for i in ii:
                final[i] = ' or '.join(c for c in final[i].split(' or ') if par(c) is None or par(c) != par(entries[i][1]))
    return final
