# Pin placement review

These are source-based proposals, not a claim that every label has been located. `map` pins are confirmed/preserved; `uprn` and `guess` still require review. No original `map` pin was moved.

| Round | Before map | Before approx | Before uprn | Before guess | After map | After uprn | After guess |
|---|---:|---:|---:|---:|---:|---:|---:|
| annington | 75 | 213 | 0 | 9 | 76 | 6 | 215 |
| ashurst | 142 | 74 | 0 | 0 | 148 | 10 | 58 |
| wiston | 211 | 223 | 0 | 3 | 226 | 24 | 187 |

There are no `approx` entries after placement: constrained real-point assignments use `uprn`; unsupported identity/numbering assignments use `guess`. Both keep the app’s best-guess warning.

The open sources do not supply address anchors on every road. In particular, unanchored numbered roads cannot have their true odd/even side or numbering direction verified from unlabeled UPRN coordinates alone. Geometry checks must not be mistaken for address confirmation.

## Annington

### 20 biggest moves

| House | Road | Move (m) | Result | Method |
|---|---|---:|---|---|
| 2 | Mount Park | 220.3 | guess | number-sequence |
| 4 | Mount Park | 196.5 | guess | number-sequence |
| 7 | Maudlyn Park Way | 192.0 | guess | number-sequence |
| Woodpeckers | Maudlin Lane | 186.8 | uprn | frame-neighbours |
| 26 | Maudlyn Park Way | 175.2 | guess | number-sequence |
| 27 | Maudlyn Park Way | 168.7 | guess | number-sequence |
| Nether Maudlin | Maudlin Lane | 167.1 | uprn | frame-neighbours |
| 4A | Mount Park | 167.0 | guess | number-sequence |
| 1 Maudlin Farm Cottages | Maudlin Lane | 165.8 | guess | fallback-unverified |
| 8 | Mount Park | 163.3 | guess | number-sequence |
| 22 | Coombe Drove | 161.7 | guess | number-sequence |
| Loxwood | Maudlin Lane | 161.0 | uprn | frame-neighbours |
| 3 | Mount Park | 146.7 | guess | number-sequence |
| 21 | Coombe Drove | 143.5 | guess | number-sequence |
| 8 | Kingsmead Close | 143.4 | guess | number-sequence |
| 3A | Mount Park | 140.4 | guess | number-sequence |
| Pear Tree Cottage | Botolphs Road | 133.6 | guess | nearest-unverified |
| 15 | Coombe Drove | 133.1 | guess | number-sequence |
| 2 Maudlin Farm Cottages | Maudlin Lane | 130.6 | guess | nearest-unverified |
| 5 | Kingsmead Close | 128.3 | guess | number-sequence |

### Every-road numbering checks

Counts flag geometry for review. Rural drives may legitimately exceed 60 m; confirmed sequential terraces can legitimately use the same side. No confirmed pin was moved to make a check pass.

| Road | Numbered | Parity | Side exceptions | Same-parity gaps >60m | Order reversals |
|---|---:|---|---:|---:|---:|
| Laines Road | 48 | opposite-majorities | 0 | 0 | 0 |
| Bostal Road | 0 | not-applicable | 0 | 0 | 0 |
| Mount Park | 31 | opposite-majorities | 0 | 2 | 0 |
| Little Drove | 0 | not-applicable | 0 | 0 | 0 |
| Penlands Close | 0 | not-applicable | 0 | 0 | 0 |
| Maudlin Lane | 0 | not-applicable | 0 | 0 | 0 |
| Coombe Drove | 40 | opposite-majorities | 7 | 14 | 7 |
| Maudlyn Close | 0 | not-applicable | 0 | 0 | 0 |
| Maudlyn Park | 0 | not-applicable | 0 | 0 | 0 |
| Maudlyn Park Way | 11 | opposite-majorities | 0 | 2 | 0 |
| The Ridings | 19 | opposite-majorities | 0 | 4 | 3 |
| Kingsmead Close | 7 | opposite-majorities | 1 | 1 | 1 |
| Sopers Lane | 0 | not-applicable | 0 | 0 | 0 |
| Annington Road | 0 | not-applicable | 0 | 0 | 0 |
| Botolphs Road | 0 | not-applicable | 0 | 0 | 0 |

### Numbering evidence

| Road | Verified number anchors | Model |
|---|---:|---|
| Mount Park | 0 | unanchored-parity-guess |
| Coombe Drove | 7 | parity-anchored |
| Maudlyn Park Way | 1 | parity-anchored |
| The Ridings | 0 | unanchored-parity-guess |
| Kingsmead Close | 0 | unanchored-parity-guess |

Moved original map pins: **none**.

### Still without a distinct local real-point proposal

6 entries retain their old position as `guess`; the script did not find an available nearby UPRN within its limits.

- Frame #276: High Hobby — Botolphs Road
- Frame #277: Annington Old Farmhouse — Botolphs Road
- Frame #281: The Granary — Botolphs Road
- Frame #284: Annexe, Pear Tree Cottage — Botolphs Road
- Frame #287: Old Barn Cottage — Botolphs Road
- Frame #288: Botolphs Cottage — Botolphs Road

## Ashurst

### 20 biggest moves

| House | Road | Move (m) | Result | Method |
|---|---|---:|---|---|
| The Barn Cottage, The Capite | Honeybridge Lane | 279.1 | uprn | frame-neighbours |
| 2 Huddlestone Farm Cottages | Horsham Road | 165.9 | guess | fallback-unverified |
| 2 | School Lane | 153.4 | guess | number-sequence |
| 1 Wyckham Dale Cottages | Wyckham Lane | 136.3 | guess | nearest-unverified |
| 13 | Coxham Lane | 119.4 | guess | number-sequence |
| 15 | Coxham Lane | 111.6 | guess | number-sequence |
| 22 | Coxham Lane | 89.7 | guess | number-sequence |
| 11 | Coxham Lane | 87.5 | guess | number-sequence |
| 2 Kings Barn Farm Cottages | Peppers Lane | 84.7 | uprn | unit-neighbours |
| 9 | Coxham Lane | 83.1 | guess | number-sequence |
| 20 | Coxham Lane | 83.0 | guess | number-sequence |
| Clock House | Honeybridge Lane | 81.7 | guess | fallback-unverified |
| 9A | Coxham Lane | 81.1 | guess | number-sequence |
| 2 Wyckham Dale Cottages | Wyckham Lane | 78.9 | guess | fallback-unverified |
| 18 | Coxham Lane | 73.5 | guess | number-sequence |
| Annexe, Old House | Church Lane | 72.4 | uprn | frame-neighbours |
| 7 | Coxham Lane | 67.7 | guess | number-sequence |
| 16 | Coxham Lane | 65.3 | guess | number-sequence |
| 3 Digital Oyster, Chanctonfold | Horsham Road | 61.5 | guess | nearest-unverified |
| Ashurst Primary School | School Lane | 55.2 | uprn | frame-neighbours |

### Every-road numbering checks

Counts flag geometry for review. Rural drives may legitimately exceed 60 m; confirmed sequential terraces can legitimately use the same side. No confirmed pin was moved to make a check pass.

| Road | Numbered | Parity | Side exceptions | Same-parity gaps >60m | Order reversals |
|---|---:|---|---:|---:|---:|
| Kings Barn Lane | 0 | not-applicable | 0 | 0 | 0 |
| Wyckham Lane | 0 | not-applicable | 0 | 0 | 0 |
| Horsham Road | 0 | not-applicable | 0 | 0 | 0 |
| Steyning Road | 0 | not-applicable | 0 | 0 | 0 |
| Coxham Lane | 20 | opposite-majorities | 0 | 0 | 0 |
| Washington Road | 0 | not-applicable | 0 | 0 | 0 |
| Wappingthorn Farm Lane | 0 | not-applicable | 0 | 0 | 0 |
| Horsebridge Common | 0 | not-applicable | 0 | 0 | 0 |
| The Village | 0 | not-applicable | 0 | 0 | 0 |
| School Lane | 4 | same-side-needs-review | 0 | 1 | 0 |
| Golden Lane | 0 | not-applicable | 0 | 0 | 0 |
| Ford Lane | 0 | not-applicable | 0 | 0 | 0 |
| Church Lane | 0 | not-applicable | 0 | 0 | 0 |
| Peppers Lane | 0 | not-applicable | 0 | 0 | 0 |
| Honeybridge Lane | 0 | not-applicable | 0 | 0 | 0 |

### Numbering evidence

| Road | Verified number anchors | Model |
|---|---:|---|
| Coxham Lane | 0 | unanchored-parity-guess |
| School Lane | 2 | parity-anchored |

Moved original map pins: **none**.

### Still without a distinct local real-point proposal

2 entries retain their old position as `guess`; the script did not find an available nearby UPRN within its limits.

- Frame #129: Baybridge House — Horsham Road
- Frame #130: Heron Farm — Horsham Road

## Wiston

### 20 biggest moves

| House | Road | Move (m) | Result | Method |
|---|---|---:|---|---|
| 1 Wheelers Common Cottage | Spithandle Lane | 1589.9 | map | osm-exact |
| 2 Wheelers Common Cottage | Spithandle Lane | 1585.4 | guess | unit-neighbours |
| Adur Brewery | Mouse Lane | 1414.4 | map | osm-exact |
| 2 Middle Barn Cottages | Spithandle Lane | 438.4 | guess | unit-neighbours |
| 1 Middle Barn Cottages | Spithandle Lane | 434.0 | map | osm-exact |
| 2 Model Cottages | Steyning Road | 307.0 | guess | unit-neighbours |
| 1 Model Cottages | Steyning Road | 296.4 | map | osm-exact |
| Wilton Park | Steyning Road | 294.5 | uprn | frame-neighbours |
| 28 | Sir Georges Place | 214.3 | guess | number-sequence |
| 39 | Charlton Street | 212.5 | guess | number-sequence |
| 26 | Sir Georges Place | 187.9 | guess | number-sequence |
| Newham Lane Farm | Newham Lane | 187.1 | uprn | frame-neighbours |
| 40 | Charlton Street | 184.1 | guess | number-sequence |
| 9 | Sir Georges Place | 175.0 | guess | number-sequence |
| 5 Pompeys Terrace | Mouse Lane | 173.2 | guess | fallback-unverified |
| 18 | Sir Georges Place | 169.7 | guess | number-sequence |
| 24 | Sir Georges Place | 168.5 | guess | number-sequence |
| 14 | Sir Georges Place | 167.6 | guess | number-sequence |
| 11 | Sir Georges Place | 164.7 | guess | number-sequence |
| 13 | Sir Georges Place | 163.7 | guess | number-sequence |

### Every-road numbering checks

Counts flag geometry for review. Rural drives may legitimately exceed 60 m; confirmed sequential terraces can legitimately use the same side. No confirmed pin was moved to make a check pass.

| Road | Numbered | Parity | Side exceptions | Same-parity gaps >60m | Order reversals |
|---|---:|---|---:|---:|---:|
| Spithandle Lane | 0 | not-applicable | 0 | 0 | 0 |
| Stocks Hill | 6 | no-road-geometry | 0 | 0 | 0 |
| Hole Street | 3 | same-side-needs-review | 0 | 0 | 0 |
| North Lane | 2 | same-side-needs-review | 0 | 0 | 0 |
| Water Lane | 0 | not-applicable | 0 | 0 | 0 |
| Chanctonbury Ring Road | 0 | not-applicable | 0 | 0 | 0 |
| Steyning Road | 0 | not-applicable | 0 | 0 | 0 |
| Mouse Lane | 0 | not-applicable | 0 | 0 | 0 |
| Mill Road | 26 | opposite-majorities | 0 | 0 | 0 |
| Sir Georges Place | 28 | opposite-majorities | 0 | 3 | 0 |
| Fairs Field | 20 | opposite-majorities | 3 | 0 | 1 |
| Charlton Street | 39 | same-side-needs-review | 0 | 2 | 0 |
| White Horse Square | 5 | same-side-needs-review | 0 | 0 | 1 |
| Dukes Lane | 2 | opposite-majorities | 0 | 0 | 0 |
| Dukes Yard | 8 | opposite-majorities | 1 | 0 | 0 |
| Newham Lane | 34 | same-side-needs-review | 0 | 2 | 0 |
| Newham Close | 30 | same-side-needs-review | 14 | 0 | 9 |
| Godstalls Lane | 12 | same-side-needs-review | 4 | 0 | 2 |
| Perrots Lane | 9 | opposite-majorities | 0 | 0 | 0 |
| Chandlers Way | 29 | opposite-majorities | 13 | 0 | 8 |

### Numbering evidence

| Road | Verified number anchors | Model |
|---|---:|---|
| Hole Street | 3 | parity-anchored |
| Mill Road | 0 | unanchored-parity-guess |
| Sir Georges Place | 0 | unanchored-parity-guess |
| Fairs Field | 0 | unanchored-parity-guess |
| Charlton Street | 23 | confirmed-sequential-one-side |
| White Horse Square | 2 | parity-anchored |
| Dukes Lane | 1 | parity-anchored |
| Dukes Yard | 6 | parity-anchored |
| Newham Lane | 31 | confirmed-sequential-one-side |
| Chandlers Way | 28 | parity-anchored |

Moved original map pins: **none**.

### Still without a distinct local real-point proposal

8 entries retain their old position as `guess`; the script did not find an available nearby UPRN within its limits.

- Frame #85: 2 Garden Cottage — Steyning Road
- Frame #92: 2 Charlton Court Cottages — Mouse Lane
- Frame #93: 1 Charlton Court Cottages — Mouse Lane
- Frame #94: 3 Charlton Court Cottages — Mouse Lane
- Frame #97: Mouse Cottage — Mouse Lane
- Frame #98: Ivy Cottage — Mouse Lane
- Frame #99: Whispers — Mouse Lane
- Frame #101: 4 Pompeys Terrace — Mouse Lane

## Reproduce and inspect

See `data/README.md` for sources, licences, limitations and commands. `docs/pin-review.html` embeds the old/new pins, labels and basemaps for offline phone review. `docs/pin-report.json` contains every placement decision, source identifier, confidence reason and detailed road exception. `node tools/check_routes.js` checks the actual generated app’s `snap()`/`route()` for every consecutive frame pair and writes `docs/route-checks.json`.
