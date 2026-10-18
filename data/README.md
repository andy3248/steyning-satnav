# Local placement source snapshots

The app does not download these files at runtime. `tools/place.py` uses them locally, and `build.py` embeds the resulting coordinates and basemap in each round page.

- `os-open-uprn.csv`: the local subset of OS Open UPRN, September 2026, downloaded via the official [OS Downloads API](https://api.os.uk/downloads/v1/products/OpenUPRN/downloads). The national ZIP is streamed with bounded HTTP range read-ahead, decompressed in memory, and checked against OS's complete-archive MD5 and each ZIP member's CRC/size. It is not saved. The CSV keeps the original five columns: UPRN, British National Grid X/Y and ETRS89 latitude/longitude. No coordinates have been manufactured.
- `os-open-uprn.source.json`: release filename, source metadata, full-archive checksum, local file SHA-256, retrieval date and filter bounds.
- `osm-addresses.json`: complete Overpass response including address tags, named features and highway geometry. Nodes use their location; closed ways use an area centroid. A named building centroid is not necessarily its door.
- `osm-addresses.source.json` and `addresses.overpassql`: endpoint, OSM base timestamp, query and snapshot checksum. The main German and Private.coffee instances returned errors, so the OSM-documented VK Maps public Overpass mirror was used.
- `pins-before.json`: immutable frame-entry baseline at the recorded Git commit. Existing `map` coordinates remain untouched. This makes reruns reproducible and the review comparison permanent.
- `road-models.json`: explicit, documented geometry aliases/local unnamed-road selections. These do not verify house numbers or names.

The filter is **50.86–50.955 N, −0.40–−0.29 E**. Its north edge extends the requested approximate box to include Ashurst's existing northern stops at 50.948 N.

## Reproduce without downloading anything

```sh
python3 -m unittest discover -s tools
python3 tools/place.py --write
python3 build.py
python3 tools/place.py --check
node tools/check_routes.js
node tools/check_practice.js
python3 -m http.server 8765 --bind 127.0.0.1
```

Open `/docs/pin-review.html` and the three built pages through the local server. The review page is self-contained: no tiles, fonts, libraries, fetches or external scripts. It can also be opened as a local file.

`--write` checks all frame identities and refuses to overwrite later manual coordinate edits. It always computes from the immutable baseline, so a repeat run cannot successively drift the pins. The four service-worker copies must be versioned together for future page changes.

Explicitly refreshing the sources requires network access:

```sh
python3 tools/fetch_addresses.py --uprn --osm
```

Changing a source snapshot can change placements. Review the generated movement/road checks before committing another run.

## Limits of the source data

OS Open UPRN is a set of real **addressable-location** points. It has **no street names, house numbers, house names or residential/postal classification**. Some points describe non-postal objects; parent/child UPRNs can share a coordinate. Coincident coordinates are collapsed for this task's one-pin-per-point rule. A selected UPRN is not evidence that a particular label belongs there.

The two Station Cottages at Wappingthorn Farm illustrate this limit: OS assigns two UPRNs to one coordinate. The script cannot recover two house locations from that. A distinct nearby point can only be a `guess` proposal, explicitly flagged for review. Rural fallback points may remain in the existing off-road farm cluster rather than being forced onto a different property beside the named public road.

`map` means a preserved existing confirmed pin or an exact, street-compatible OSM name/number match. `uprn` means a geometrically constrained assignment using verified neighbours/numbering anchors, **not** a confirmed label. `guess` means the identity, side/direction, road model or assignment is still unsupported. Both `uprn` and `guess` retain the app's “Pin is a best guess” warning. No approximate/guess location is promoted to confirmed merely because a UPRN is nearby.

Unanchored numbered streets cannot have their numbering direction or odd/even side established from these two sources. Their assignments remain `guess`. Some real streets, notably the OSM-confirmed Charlton Street terrace, use consecutive numbers on the same side. The script preserves those confirmed pins and reports the exception rather than moving them to fabricate an odd/even pattern.

The report includes every entry's chosen source/method, remaining uncertainty, road parity/order/gap checks, and all moves. Distances use a local tangent-plane approximation suitable for the road-scale checks. A non-null app route proves graph connectivity, not the identity of a house or legal vehicle access. Review and driver confirmation remain necessary for unresolved entries.

`tools/check_practice.js` executes the generated app's actual simulation, arrival, numbered-road advancement and speech functions in both modes, using a virtual clock and stubbed rendering/device APIs. It checks completion and en-GB speech calls, and writes `docs/practice-checks.json`. It does not claim to test audible playback on a physical phone; the browser smoke check covers the visible Practice drive controls separately.

## Licences and attribution

OS Open UPRN: [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). **Contains OS data © Crown copyright and database right 2026.**

OpenStreetMap: **© OpenStreetMap contributors**, [Open Database Licence 1.0](https://www.openstreetmap.org/copyright). The OSM snapshot, derived placement data and combined review database are made available under ODbL; OS data retains its OGL attribution. The app and offline review page display both attributions.

UPRN points on existing OSM/basemap building footprints are preferred over points outside buildings. This reduces street-furniture assignments but does not establish postal status or house identity. Points outside the available footprints cannot receive `uprn` quality from a heuristic assignment.
