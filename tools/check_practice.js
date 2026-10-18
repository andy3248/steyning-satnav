#!/usr/bin/env node
// Run the built app's real Practice drive loop with a virtual clock and speech
// sink. Rendering/device APIs are stubbed; this does not test audible playback.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),files={annington:'index.html',ashurst:'ashurst/index.html',wiston:'wiston/index.html'};
const results={};
for(const [round,file] of Object.entries(files)){
 const html=fs.readFileSync(path.join(root,file),'utf8'),script=html.match(/<script>\s*(const ROUND_CFG=[\s\S]*?)<\/script>/)[1];
 const prefix=script.slice(0,script.indexOf('// ---------------- canvas view'));
 const streets=script.slice(script.indexOf('const STREETS=[];'),script.indexOf('function renderStreets()'));
 const nav=script.slice(script.indexOf('// ================= SAT NAV'),script.indexOf('// ================= FIX THIS HOUSE'));
 for(const mode of ['learn','parcels']){
  let now=0;const spoken=[],elements=new Map(),saved=new Map();
  const config=JSON.parse(script.match(/const ROUND_CFG=(.*?);/)[1]);
  const rows=JSON.parse(fs.readFileSync(path.join(root,'src',round,'placed.json'),'utf8'));
  const ids=rows.map((_,i)=>({annington:'f',ashurst:'a',wiston:'w'}[round])+i).filter((_,i)=>i%7===0);
  saved.set(config.id+'_mode',JSON.stringify(mode));
  if(mode==='parcels')saved.set(config.id+'_parcels',JSON.stringify({ids,day:'2026-10-18'}));
  function el(id){if(!elements.has(id))elements.set(id,{hidden:false,style:{setProperty(){}},classList:{add(){},remove(){},toggle(){}},setAttribute(){},querySelector(s){return el(id+s)}});return elements.get(id)}
  class Path2D{moveTo(){}lineTo(){}closePath(){}}
  const context={Path2D,URLSearchParams,location:{search:''},console,
   localStorage:{getItem:k=>saved.get(k)||null,setItem:(k,v)=>saved.set(k,v)},
   document:{getElementById:el,querySelector:el},navigator:{},window:{},
   performance:{now:()=>now},requestAnimationFrame:()=>1,cancelAnimationFrame(){},setTimeout:()=>1,clearTimeout(){},
   ResizeObserver:class{observe(){}},SpeechSynthesisUtterance:class{constructor(text){this.text=text}},
   speechSynthesis:{getVoices:()=>[{lang:'en-GB',name:'Test en-GB'}],cancel(){},speak:u=>spoken.push({text:u.text,lang:u.lang}),speaking:false,pending:false}};
  const setup=`
   const view={s:1,rot:0};const pop={hidden:true};const mapEl={style:{setProperty(){}}};let navPanelHeight=0,navBannerHeight=0;
   function resize(){}function render(){}function draw(){}function render_ui(){}function focusLeg(){}function svgI(){return ''}
   const esc=s=>String(s),navLink=()=>'';
  `;
  const loop=`
   hIdx=0;startNav('sim');NAV.speed=40;const visited=[];let last=-1,ticks=0;
   while(!NAV.finished&&ticks++<100000){
    if(hIdx!==last){if(hIdx<last)throw new Error('Practice moved backwards');visited.push(hIdx);last=hIdx;}
    navTick(ticks*1000);__advanceClock();
   }
   if(!NAV.finished||hIdx!==SEQ.length-1)throw new Error('Practice did not finish');
   if(document.getElementById('nbDone').textContent!=='All done')throw new Error('Completion control not updated');
   JSON.stringify({houses:SEQ.length,visited_stops:visited.length,ticks,finished:NAV.finished,last_frame_index:hIdx,numbered_road_runs:RUNS.length});
  `;
  context.__advanceClock=()=>{now+=1000};
  const result=JSON.parse(vm.runInNewContext(prefix+streets+setup+nav+loop,context,{timeout:120000}));
  if(spoken.some(u=>u.lang!=='en-GB'))throw new Error('Wrong speech language');
  const completion=spoken.find(u=>/round is complete|last parcel.*All done/.test(u.text));
  if(!completion)throw new Error('Missing spoken completion');
  result.speech_utterances=spoken.length;result.direction_utterances=spoken.filter(u=>/turn|Continue onto|Slight|In .*yards/i.test(u.text)).length;
  result.completion_speech=completion.text;result.speech_language='en-GB';
  result.built_sha256=crypto.createHash('sha256').update(html).digest('hex');results[round+'_'+mode]=result;
  console.log(`${round} ${mode}: finished ${result.visited_stops} stops / ${result.houses} houses; ${spoken.length} en-GB speech calls`);
 }
}
fs.writeFileSync(path.join(root,'docs/practice-checks.json'),JSON.stringify(results,null,2)+'\n');
