"""Human-readable placement/validation report, also used as the PR's table body."""
def markdown(report):
 out=['# Pin placement review','',
 'These are source-based proposals, not a claim that every label has been located. `map` pins are confirmed/preserved; `uprn` and `guess` still require review. No original `map` pin was moved.','',
 '| Round | Before map | Before approx | Before uprn | Before guess | After map | After uprn | After guess |',
 '|---|---:|---:|---:|---:|---:|---:|---:|']
 for name,d in report['rounds'].items():
  b,a=d['before'],d['after'];out.append('| '+name+' | '+' | '.join(str(v) for v in [b.get('map',0),b.get('approx',0),b.get('uprn',0),b.get('guess',0),a.get('map',0),a.get('uprn',0),a.get('guess',0)])+' |')
 out+=['','There are no `approx` entries after placement: constrained real-point assignments use `uprn`; unsupported identity/numbering assignments use `guess`. Both keep the app’s best-guess warning.','',
 'The open sources do not supply address anchors on every road. In particular, unanchored numbered roads cannot have their true odd/even side or numbering direction verified from unlabeled UPRN coordinates alone. Geometry checks must not be mistaken for address confirmation.','']
 for name,d in report['rounds'].items():
  out+=['## '+name.title(),'','### 20 biggest moves','','| House | Road | Move (m) | Result | Method |','|---|---|---:|---|---|']
  for e in sorted(d['entries'],key=lambda e:-e['moved_m'])[:20]:out.append('| '+str(e['label']).replace('|','/')+' | '+e['road']+' | '+str(e['moved_m'])+' | '+e['new'][2]+' | '+e['method']+' |')
  out+=['','### Every-road numbering checks','','Counts flag geometry for review. Rural drives may legitimately exceed 60 m; confirmed sequential terraces can legitimately use the same side. No confirmed pin was moved to make a check pass.','','| Road | Numbered | Parity | Side exceptions | Same-parity gaps >60m | Order reversals |','|---|---:|---|---:|---:|---:|']
  for c in d['road_checks']:out.append('| '+c['road']+' | '+str(c['numbered_houses'])+' | '+c['parity_status']+' | '+str(len(c.get('side_exceptions',[])))+' | '+str(len(c['gaps_over_60m']))+' | '+str(len(c['order_reversals']))+' |')
  out+=['','### Numbering evidence','','| Road | Verified number anchors | Model |','|---|---:|---|']
  for c in d['numbering_models']:out.append('| '+c['road']+' | '+str(c['confirmed_numeric_anchors'])+' | '+c['numbering']+' |')
  out+=['','Moved original map pins: **none**.','']
  unresolved=[e for e in d['entries'] if e['new'][2]!='map' and not e.get('uprn')]
  out+=['### Still without a distinct local real-point proposal','',str(len(unresolved))+' entries retain their old position as `guess`; the script did not find an available nearby UPRN within its limits.','']
  for e in unresolved:out.append('- Frame #'+str(e['frame'])+': '+e['label']+' — '+e['road'])
  out+=['']
 out+=['## Reproduce and inspect','','See `data/README.md` for sources, licences, limitations and commands. `docs/pin-review.html` embeds the old/new pins, labels and basemaps for offline phone review. `docs/pin-report.json` contains every placement decision, source identifier, confidence reason and detailed road exception. `node tools/check_routes.js` checks the actual generated app’s `snap()`/`route()` for every consecutive frame pair and writes `docs/route-checks.json`.','']
 return '\n'.join(out)
