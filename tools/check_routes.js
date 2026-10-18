#!/usr/bin/env node
// Exercise the actual built app's snap() and route(), without reimplementing them.
// Only the initial data/graph section is evaluated; rendering is a no-op Path2D.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),rounds={annington:'index.html',ashurst:'ashurst/index.html',wiston:'wiston/index.html'};
let failed=false,results={};
for(const [round,file] of Object.entries(rounds)){
 const html=fs.readFileSync(path.join(root,file),'utf8');const script=html.match(/<script>\s*(const ROUND_CFG=[\s\S]*?)<\/script>/)[1];
 const marker=script.indexOf('\nbuildSeq();');if(marker<0)throw new Error('Cannot locate graph section');
 const code=script.slice(0,marker)+`\nbuildSeq();
 const checks=[];
 for(let i=1;i<SEQ.length;i++){
  const a=SEQ[i-1],b=SEQ[i],s0=snap(a.x,a.y,a.it.road),s1=snap(b.x,b.y,b.it.road);
  const leg=s0&&s1?route(s0,s1):null;
  checks.push({from:i,to:i+1,labels:[seqLabel(a),seqLabel(b)],reachable:leg!==null,snap_metres:[s0?Math.hypot(a.x-s0.x,a.y-s0.y):null,s1?Math.hypot(b.x-s1.x,b.y-s1.y):null]});
 }
 JSON.stringify({houses:SEQ.length,pairs:checks.length,null_routes:checks.filter(c=>!c.reachable),max_snap_m:Math.max(...checks.flatMap(c=>c.snap_metres).filter(x=>x!==null)),pins:items.map(it=>({id:it.id,lat:it.lat,lon:it.lon,approx:it.approx})),checks});`;
 class Path2D {moveTo(){}lineTo(){}closePath(){}}
 const context={Path2D,localStorage:{getItem(){return null}},location:{search:''},URLSearchParams,console};
 const result=JSON.parse(vm.runInNewContext(code,context,{timeout:120000}));const placed=JSON.parse(fs.readFileSync(path.join(root,'src',round,'placed.json'),'utf8')),prefix={annington:'f',ashurst:'a',wiston:'w'}[round];
 if(result.pins.length!==placed.length)throw new Error(round+': built entry count differs');
 placed.forEach((row,i)=>{const p=result.pins[i];if(p.id!==prefix+i||p.lat!==row[3]||p.lon!==row[4]||p.approx!==(row[5]!=='map'))throw new Error(round+': built identity/position/quality differs at '+(i+1))});
 delete result.pins;result.built_identity_position_quality_checked=true;result.built_sha256=crypto.createHash('sha256').update(html).digest('hex');results[round]=result;
 console.log(`${round}: ${result.pairs-result.null_routes.length}/${result.pairs} consecutive pairs reachable; max snap ${result.max_snap_m.toFixed(1)} m`);
 if(result.null_routes.length){failed=true;console.error(result.null_routes)}
}
fs.writeFileSync(path.join(root,'docs/route-checks.json'),JSON.stringify(results,null,2)+'\n');
if(failed)process.exitCode=1;
