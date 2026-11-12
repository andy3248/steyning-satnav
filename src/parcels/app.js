const $=id=>document.getElementById(id);
const store={get(k){try{return JSON.parse(localStorage.getItem("ph_"+k));}catch(e){return null;}},set(k,v){try{localStorage.setItem("ph_"+k,JSON.stringify(v));}catch(e){}}};
const ROUNDNAME={annington:"Annington",wiston:"Wiston",ashurst:"Ashurst",penlands:"Penlands"};
const norm=t=>" "+String(t||"").toLowerCase().replace(/['’`]/g,"").replace(/&/g," and ").replace(/[^a-z0-9]+/g," ").trim()+" ";
const esc=t=>String(t).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

// ---------- address book ----------
// HOUSES rows: [round id, frame index, shelf, road, number, name, lat, lon, confirmed spot]
const H=HOUSES.map(r=>({round:r[0],k:r[1],shelf:r[2],road:r[3],num:r[4],name:r[5],lat:r[6],lon:r[7],sure:!!r[8],opp0:r[9]||"",key:r[0]+":"+r[1]}));
// what is across the road (worked out from the map; the driver can correct it)
const OPPFIX=store.get("opp")||{};
// pins the driver has fixed by standing at the door (kept on this phone, every day)
const PINFIX=store.get("pins")||{};
const oppOf=h=>(h.key in OPPFIX?OPPFIX[h.key]:h.opp0)||"";
const oppSay=h=>{const o=oppOf(h);return o?`, opposite ${o.split(" or ").map(x=>/^\d/.test(x)?"number "+x:x).join(" or ")}`:"";};
const BYKEY=new Map(H.map(h=>[h.key,h]));
const label=h=>h.num?`${h.num} ${h.road}`:h.name;
const shortLab=h=>h.num?h.num:h.name;
const sayHouse=h=>h.num?`number ${h.num}`:h.name;
const ROADV=r=>{const n=norm(r).trim();const v=[n];const ab={street:"st",road:"rd",lane:"ln",close:"cl",place:"pl",square:"sq",drove:"dr"};const w=n.split(" ");const l=w[w.length-1];if(ab[l])v.push(w.slice(0,-1).concat(ab[l]).join(" "));return v;};
const GENERIC=new Set(["cottage","cottages","house","farm","farmhouse","the","barn","lodge","road","lane","street","close","place","west","east","north","south","unit"]);
const ALLROADV=[...new Set(H.map(h=>h.road))].flatMap(ROADV).sort((a,b)=>b.length-a.length);
H.forEach(h=>{h.rv=ROADV(h.road);h.nl=norm(h.name).trim();h.lead=(h.nl.match(/^(\d+[a-z]?) /)||[])[1]||"";h.toks=h.nl.split(" ").filter(w=>w.length>=4&&!GENERIC.has(w));});
// score every house against some text (a scanned label or what was typed)
function match(text,typed){const T=norm(text);let T2=T;ALLROADV.forEach(v=>{T2=T2.split(" "+v+" ").join("  ");});const out=[];
  H.forEach(h=>{let sc=0;const fullRoad=h.rv.some(v=>T.includes(" "+v+" "));
    // typed: "12 charlton" is enough; a whole road name typed beats a part one ("coombe road" is not Coombe Drove)
    const partRoad=typed&&!fullRoad&&h.rv.some(v=>{const w=v.split(" ");return w[0].length>=4&&T.includes(" "+w[0]+" ")&&!T.split(" ").some(x=>x.length>=2&&w.length>1&&x!==w[0]&&!w.includes(x)&&/^(road|rd|lane|ln|way|close|cl|drove|dr|street|st|vale|rise|place|pl|court|avenue|ave|crescent)$/.test(x));});
    const roadHit=fullRoad||partRoad;
    if(h.num){if(roadHit&&T.includes(" "+h.num.toLowerCase()+" "))sc=fullRoad?60:52;}
    else{if(h.nl.length>=4&&T2.includes(" "+h.nl+" "))sc=45+Math.min(15,h.nl.length/2);
      else if(!h.lead||T2.includes(" "+h.lead+" ")){if(h.toks.length&&h.toks.every(w=>T2.includes(" "+w+" ")))sc=30+h.toks.length*4;
        else if(typed&&h.toks.length&&h.toks.some(w=>T2.split(" ").some(x=>x.length>=3&&w.startsWith(x))))sc=20;}
      if(sc&&roadHit)sc+=10;}
    if(sc)out.push({h,sc});});
  out.sort((a,b)=>b.sc-a.sc);return out;}

// ---------- today's list ----------
const today=()=>new Date().toISOString().slice(0,10);
let S=store.get("day");if(!S||S.day!==today())S={day:today(),items:[],rounds:[],pos:0};
// items: {key, n (parcels), l (first class letters), st: "todo"|"done"|"fail", t}
let KIND=store.get("kind")||"parcel";
const tot=i=>(i.n||0)+(i.l||0);
const cntTxt=i=>[i.n?`${i.n} parcel${i.n>1?"s":""}`:"",i.l?`${i.l} letter${i.l>1?"s":""}`:""].filter(Boolean).join(" and ");
const cntShort=i=>[i.n>1||(i.n&&i.l)?"📦"+i.n:"",i.l?"✉"+i.l:""].filter(Boolean).join(" ");
function save(){store.set("day",S);}
function itemOf(key){return S.items.find(i=>i.key===key);}
function addHouse(h,src){let it=itemOf(h.key);if(!it){it={key:h.key,n:0,l:0,st:"todo",t:Date.now()};S.items.push(it);}if(KIND==="letter")it.l=(it.l||0)+1;else it.n=(it.n||0)+1;if(it.st!=="todo")it.st="todo";
  if(!S.rounds.includes(h.round))S.rounds.push(h.round);save();renderList();return it;}
function ordered(){const rk=r=>{const i=S.rounds.indexOf(r);return i<0?99:i;};
  return S.items.filter(i=>BYKEY.has(i.key)).sort((a,b)=>{const A=BYKEY.get(a.key),B=BYKEY.get(b.key);return rk(A.round)-rk(B.round)||A.k-B.k;});}
// stops grouped by road (consecutive in delivery order)
function groups(list){const G=[];list.forEach(it=>{const h=BYKEY.get(it.key);const g=G[G.length-1];if(g&&g.road===h.road&&g.round===h.round)g.items.push(it);else G.push({road:h.road,round:h.round,items:[it]});});return G;}

// ---------- voice ----------
let VOICE=null;const VSET=Object.assign({name:"",rate:0.98},store.get("voice")||{});
function voiceScore(v){const n=v.name;let s=0;if(/en[-_]GB/i.test(v.lang))s+=100;else if(/^en[-_](IE|AU|NZ)/i.test(v.lang))s+=40;else if(/^en/i.test(v.lang))s+=20;else return -1;
  if(/premium/i.test(n))s+=60;if(/enhanced|natural|neural|wavenet|online/i.test(n))s+=45;if(/google/i.test(n))s+=30;if(/siri/i.test(n))s+=35;
  if(/serena|sonia|libby|kate|stephanie|martha|daniel|arthur|oliver|ryan|thomas|female|male/i.test(n))s+=10;
  if(/compact|espeak|robot|novelty|bad news|bells|bubbles|cellos|wobble|whisper|zarvox|trinoids|jester|organ|superstar|albert|fred|junior|ralph|eddy|flo|grandma|grandpa|reed|rocko|sandy|shelley/i.test(n))s-=200;return s;}
function goodVoices(){try{return speechSynthesis.getVoices().filter(v=>voiceScore(v)>0).sort((a,b)=>voiceScore(b)-voiceScore(a));}catch(e){return [];}}
function pickVoice(){const vs=goodVoices();VOICE=(VSET.name&&vs.find(v=>v.name===VSET.name))||vs[0]||null;const sel=$("vcSel");sel.innerHTML="";
  if(!vs.length){sel.innerHTML="<option>Phone's default voice</option>";}
  vs.slice(0,12).forEach(v=>{const o=document.createElement("option");o.value=v.name;o.textContent=v.name.replace(/\s*\(.*?\)\s*/g," ").trim();if(VOICE&&v.name===VOICE.name)o.selected=true;sel.appendChild(o);});$("vcRate").value=VSET.rate;}
try{speechSynthesis.onvoiceschanged=pickVoice;}catch(e){}
let lastSaid="";
function say(t,keep){try{speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(t);if(VOICE){u.voice=VOICE;u.lang=VOICE.lang;}else u.lang="en-GB";u.rate=VSET.rate;speechSynthesis.speak(u);}catch(e){}if(!keep)lastSaid=t;}
function beep(ok){try{const AC=window.__ac||(window.__ac=new (window.AudioContext||window.webkitAudioContext)());const t=AC.currentTime;(ok?[880,1320]:[440,330]).forEach((f,i)=>{const o=AC.createOscillator(),g=AC.createGain();o.frequency.value=f;g.gain.setValueAtTime(0,t+i*.12);g.gain.linearRampToValueAtTime(.2,t+i*.12+.02);g.gain.exponentialRampToValueAtTime(.001,t+i*.12+.3);o.connect(g).connect(AC.destination);o.start(t+i*.12);o.stop(t+i*.12+.35);});}catch(e){}
  try{navigator.vibrate&&navigator.vibrate(ok?[60]:[80,60,80]);}catch(e){}}
$("vcSel").onchange=e=>{VSET.name=e.target.value;store.set("voice",VSET);pickVoice();say("Next, number 12 Charlton Street.",true);};
$("vcRate").oninput=e=>{VSET.rate=+e.target.value;store.set("voice",VSET);};
$("vcTry").onclick=()=>say("Charlton Street done. Next road, Mill Road. 2 parcels: number 4, and Rose Cottage.",true);
$("hearBtn").onclick=()=>{if(lastSaid)say(lastSaid,true);};

// ---------- tabs ----------
function tab(t){$("vLoad").hidden=t!=="load";$("vDel").hidden=t!=="del";$("tLoad").setAttribute("aria-pressed",String(t==="load"));$("tDel").setAttribute("aria-pressed",String(t==="del"));
  store.set("tab",t);if(t==="del"){stopScan();renderDel(true);wake(true);initGoogleMap();if(G.watch==null&&store.get("gps")!==0)gpsOn();}else{wake(false);}}
$("tLoad").onclick=()=>tab("load");$("tDel").onclick=()=>tab("del");
$("goDel").onclick=()=>{if(!ordered().length){flash("Add some parcels first.","");return;}tab("del");};

// ---------- load: list ----------
function renderList(){try{const n=ordered().length;$("goDel").textContent=n?`Start delivering · ${n} ${n>1?"houses":"house"} ›`:"Start delivering ›";}catch(e){}const box=$("list");box.innerHTML="";const L=ordered();const n=L.reduce((s,i)=>s+(i.n||0),0),nl=L.reduce((s,i)=>s+(i.l||0),0);
  $("listH").textContent=L.length?`Today · ${[n?n+" parcel"+(n>1?"s":""):"",nl?nl+" letter"+(nl>1?"s":""):""].filter(Boolean).join(", ")} for ${L.length} ${L.length===1?"house":"houses"}`:"Today's parcels and letters";
  if(!L.length){box.innerHTML='<p class="muted">Nothing yet. Scan or type the first parcel.</p>';return;}
  // compact: one block per road, a chip per house; tap a chip to change its count
  groups(L).forEach(g=>{const d=document.createElement("div");d.className="road";const c=g.items.reduce((s,i)=>s+tot(i),0);
    d.innerHTML=`<div class="rh"><div></div><span></span></div><div class="hchips"></div><div class="ied" hidden></div>`;d.querySelector(".rh div").textContent=g.road;
    d.querySelector(".rh span").textContent=`${ROUNDNAME[g.round]} · ${g.items.length} ${g.items.length>1?"houses":"house"}${c>g.items.length?" · "+c+" items":""}`;
    const box2=d.querySelector(".hchips"),ed=d.querySelector(".ied");
    g.items.forEach(it=>{const h=BYKEY.get(it.key);const b=document.createElement("button");b.className="hc"+(it.st!=="todo"?" "+it.st:"")+(OPENED===it.key?" on":"");
      b.textContent=shortLab(h);if(tot(it)>1||it.l){const x=document.createElement("small");x.textContent=" "+cntShort(it);b.appendChild(x);}
      b.onclick=()=>{OPENED=OPENED===it.key?null:it.key;renderList();};box2.appendChild(b);
      if(OPENED===it.key){ed.hidden=false;ed.innerHTML=`<b></b><div class="row"><span>📦</span><button class="btn">−</button><b class="n"></b><button class="btn">+</button><span style="margin-left:10px">✉</span><button class="btn">−</button><b class="l"></b><button class="btn">+</button></div><div class="row"><button class="btn rm">Remove</button><button class="btn dn">Done</button></div>`;
        ed.querySelector("b").textContent=label(h);ed.querySelector(".n").textContent=it.n||0;ed.querySelector(".l").textContent=it.l||0;
        const bs=ed.querySelectorAll(".row:first-of-type .btn");const chg=(f,dv)=>{it[f]=Math.max(0,(it[f]||0)+dv);if(!tot(it)){S.items=S.items.filter(x=>x!==it);OPENED=null;}save();renderList();};
        bs[0].onclick=()=>chg("n",-1);bs[1].onclick=()=>chg("n",1);bs[2].onclick=()=>chg("l",-1);bs[3].onclick=()=>chg("l",1);
        ed.querySelector(".rm").onclick=()=>{S.items=S.items.filter(x=>x!==it);OPENED=null;save();renderList();};ed.querySelector(".dn").onclick=()=>{OPENED=null;renderList();};}});
    box.appendChild(d);});}
let OPENED=null;
$("clearBtn").onclick=()=>{if(S.items.length)confirmClear();};
let clearArm=0;function confirmClear(){if(Date.now()-clearArm<4000){S={day:today(),items:[],rounds:[],pos:0};save();renderList();flash("List cleared.","");$("clearBtn").textContent="Clear the list";return true;}
  clearArm=Date.now();$("clearBtn").textContent="Tap again to clear";setTimeout(()=>{$("clearBtn").textContent="Clear the list";},4000);return false;}
function flash(main,sub,cls,opts){const f=$("flash");f.className=cls||"";f.hidden=false;f.innerHTML="";const m=document.createElement("div");m.textContent=main;f.appendChild(m);
  if(sub){const s=document.createElement("small");s.textContent=sub;f.appendChild(s);}
  if(opts){const o=document.createElement("div");o.className="opts";opts.forEach(([t,fn])=>{const b=document.createElement("button");b.className="btn";b.textContent=t;b.onclick=fn;o.appendChild(b);});f.appendChild(o);}}
function added(h,how){const it=addHouse(h,how);const pos=ordered().indexOf(it)+1;
  flash(`✓ ${KIND==="letter"?"✉ ":"📦 "}${label(h)}`,`${ROUNDNAME[h.round]} round · shelf ${h.shelf} · ${tot(it)>1?cntTxt(it)+" for this house · ":""}stop ${pos} of ${ordered().length}`,"ok");beep(true);
  say(`${h.num?h.num+" "+h.road:h.name+", "+h.road}${tot(it)>1?". "+cntTxt(it):""}.`);}
// parcels or first class letters: what the next scan counts as
function setKind(k){KIND=k;store.set("kind",k);$("kParcel").setAttribute("aria-pressed",String(k==="parcel"));$("kLetter").setAttribute("aria-pressed",String(k==="letter"));
  $("scanBtn").textContent=SC.on?"Stop scanning":(k==="letter"?"📷 Live scanning (hands-free)":"📷 Live scanning (hands-free)");renderList();}
$("kParcel").onclick=()=>setKind("parcel");$("kLetter").onclick=()=>setKind("letter");

// ---------- load: typing ----------
$("q").addEventListener("input",()=>{const t=$("q").value.trim();const ul=$("sug");ul.innerHTML="";if(t.length<2)return;
  const res=match(t,true).slice(0,6);
  res.forEach(({h})=>{const li=document.createElement("li");li.innerHTML=`<div><b></b><small></small></div><button class="btn primary">Add</button>`;li.querySelector("b").textContent=label(h);li.querySelector("small").textContent=`${h.road} · ${ROUNDNAME[h.round]}`;
    li.querySelector("button").onclick=()=>{added(h,"typed");$("q").value="";ul.innerHTML="";};ul.appendChild(li);});
  if(!res.length){ul.innerHTML='<li><div class="muted">No house on your rounds matches that yet. Try the house number and the first word of the road, like “12 charlton”.</div></li>';}});

// ---------- OCR clean-up: snap misread words to words that exist on our rounds ----------
const DICT=new Set();H.forEach(h=>norm(h.road+" "+h.name).trim().split(" ").forEach(w=>{if(w.length>=4&&!/^\d/.test(w))DICT.add(w);}));
["steyning","ashurst","wiston","sussex","west"].forEach(w=>DICT.add(w));const DICTL=[...DICT];
function ed(a,b,max){if(Math.abs(a.length-b.length)>max)return 9;let p=Array.from({length:b.length+1},(_,i)=>i);for(let i=1;i<=a.length;i++){const c=[i];let lo=i;for(let j=1;j<=b.length;j++){c[j]=Math.min(p[j]+1,c[j-1]+1,p[j-1]+(a[i-1]===b[j-1]?0:1));lo=Math.min(lo,c[j]);}if(lo>max)return 9;p=c;}return p[b.length];}
function fixOCR(t){return norm(t.replace(/[|]/g,"1").replace(/(\d)[oO]/g,"$10").replace(/[oO](\d)/g,"0$1")).trim().split(" ").map(w=>{
    if(/^[0-9]+[a-z]?$/.test(w)||w.length<4||DICT.has(w)||!/[aeiou]/.test(w)||/(.)\1\1/.test(w))return w;const max=w.length>=9?2:1;let best=w,bd=max+1;for(const d of DICTL){const e=ed(w,d,max);if(e<bd){bd=e;best=d;if(e===0)break;}}return best;}).join(" ");}
// ---------- load: camera scanning (reads the label on the phone) ----------
const SC={stream:null,worker:null,loading:null,on:false,busy:false,lastKey:"",lastSeen:0,ask:null,lastFlash:0};
function loadReader(){if(SC.loading)return SC.loading;
  SC.loading=new Promise((ok,bad)=>{if(window.Tesseract)return ok();const s=document.createElement("script");s.src="https://cdn.jsdelivr.net/npm/tesseract.js@5.1.1/dist/tesseract.min.js";s.onload=ok;s.onerror=()=>bad(new Error("load"));document.head.appendChild(s);})
    .then(()=>Tesseract.createWorker("eng")).then(w=>{SC.worker=w;return w;}).catch(e=>{SC.loading=null;throw e;});return SC.loading;}
async function startScan(){if(SC.on){stopScan();return;}$("cam").hidden=false;$("scanBtn").textContent="Stop scanning";SC.on=true;
  flash("Starting the camera…","");
  try{SC.stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:"environment"},width:{ideal:1920},height:{ideal:1080}},audio:false});const v=$("vid");v.srcObject=SC.stream;await v.play().catch(()=>{});}
  catch(e){flash("Can't open the camera","Allow camera access for this page in your browser settings, or type the houses in instead.","ask");stopScan(true);return;}
  if(!SC.worker){flash("Getting the label reader ready…","The first time needs signal and takes about half a minute. After that it works offline.");
    try{await loadReader();}catch(e){flash("Couldn't load the label reader","It needs signal the first time. You can type the houses in instead.","ask");stopScan(true);return;}}
  if(SC.on){flash("Point at an address label","Hold it in the box. It reads it by itself, no need to tap.");scanLoop();}}
function stopScan(keepMsg){SC.on=false;$("scanBtn").textContent=KIND==="letter"?"📷 Live scanning (hands-free)":"📷 Live scanning (hands-free)";$("cam").hidden=true;if(SC.stream){SC.stream.getTracks().forEach(t=>t.stop());SC.stream=null;}}
function grab(){const v=$("vid");const vw=v.videoWidth,vh=v.videoHeight;if(!vw)return null;const box=$("cam").getBoundingClientRect();const sc=Math.max(box.width/vw,box.height/vh);const ox=(vw*sc-box.width)/2,oy=(vh*sc-box.height)/2;
  const gx=(box.width*.07+ox)/sc,gy=(box.height*.14+oy)/sc,gw=box.width*.86/sc,gh=box.height*.72/sc;const k=Math.min(1,1600/gw);const c=document.createElement("canvas");c.width=Math.round(gw*k);c.height=Math.round(gh*k);
  const x=c.getContext("2d");x.filter="grayscale(1) contrast(1.4)";x.drawImage(v,gx,gy,gw,gh,0,0,c.width,c.height);return c;}
async function scanLoop(){while(SC.on){if(SC.ask){await new Promise(r=>setTimeout(r,400));continue;}const c=grab();if(!c){await new Promise(r=>setTimeout(r,300));continue;}
  let text="";try{text=(await SC.worker.recognize(c)).data.text||"";}catch(e){await new Promise(r=>setTimeout(r,500));continue;}
  if(!SC.on)break;const clean=fixOCR(text);const res=match(clean,false);const now=Date.now();
  if(!res.length){if(now-SC.lastSeen>4000)SC.lastKey="";const seen=text.replace(/\s+/g," ").trim().slice(0,60);
    if(!SC.ask&&now-SC.lastFlash>1500){SC.lastFlash=now;flash("Looking for an address…",seen.length>6?`Reading: “${seen}”. Get closer and hold still, or tap 📸 Photo instead.`:"Fill the box with the address, hold still. Or tap 📸 Photo of label.");}continue;}
  const top=res[0],second=res[1];const words=clean.split(" ").filter(w=>w.length>=4&&DICT.has(w)).length;
  const sure=top.sc>=45&&(!second||top.sc-second.sc>=8)&&words>=2&&/steyning|ashurst|wiston|sussex|bn44|bn5|rh13|rh20/.test(clean+" "+text.toLowerCase());
  if(top.h.key===SC.lastKey){SC.lastSeen=now;continue;}// same label still in view
  if(sure){SC.lastKey=top.h.key;SC.lastSeen=now;added(top.h,"scan");}}}
$("scanBtn").onclick=()=>startScan();
$("typeBtn").onclick=()=>{const q=$("q");q.focus();q.scrollIntoView({block:"center",behavior:"smooth"});};
$("photoBtn").onclick=()=>{$("photoIn").value="";$("photoIn").click();};
$("photoIn").onchange=async e=>{const f=e.target.files&&e.target.files[0];if(!f)return;if(SC.on)stopScan();
  flash("Reading the label…",SC.worker?"":"Getting the label reader ready first (needs signal the first time).");
  try{await loadReader();}catch(err){flash("Couldn't load the label reader","It needs signal the first time. Type the house in instead.","ask");return;}
  let bmp;try{bmp=await createImageBitmap(f);}catch(err){const im=new Image();im.src=URL.createObjectURL(f);await im.decode();bmp=im;}
  const W=bmp.width,Hh=bmp.height,k=Math.min(1,2200/Math.max(W,Hh));const c=document.createElement("canvas");c.width=Math.round(W*k);c.height=Math.round(Hh*k);
  const x=c.getContext("2d");x.filter="grayscale(1) contrast(1.5)";x.drawImage(bmp,0,0,c.width,c.height);
  let text="";try{text=(await SC.worker.recognize(c)).data.text||"";}catch(err){}
  const res=match(fixOCR(text),false);const seen=text.replace(/\s+/g," ").trim().slice(0,80);
  if(!res.length){beep(false);flash("Couldn't find a house on your rounds in that",seen?`Read: “${seen}”. Try closer, flatter and in good light, or type it in.`:"Couldn't read any text. Try closer, flatter and in good light.","ask");return;}
  const top=res[0],second=res[1];
  if(top.sc>=45&&(!second||top.sc-second.sc>=8)){added(top.h,"photo");return;}
  beep(false);say("Which house is it?");flash("Which house is it?","Tap the right one.","ask",res.slice(0,4).map(r=>[label(r.h)+" · "+r.h.road,()=>added(r.h,"pick")]).concat([["None of these",()=>flash("Type it in the box below instead.","")]]));};

// ---------- deliver ----------
function current(){return ordered().find(i=>i.st==="todo")||null;}
function speechForNext(prevRoad){const cur=current();if(!cur)return "That's everything delivered. Well done.";const h=BYKEY.get(cur.key);
  const todoHere=ordered().filter(i=>i.st==="todo"&&BYKEY.get(i.key).road===h.road&&BYKEY.get(i.key).round===h.round);
  const what=i=>(i.l||tot(i)>1)?`, ${cntTxt(i)}`:"";
  if(prevRoad&&prevRoad===h.road)return `Next, ${sayHouse(h)}${oppSay(h)}${what(cur)}.`;
  const list=todoHere.map(i=>sayHouse(BYKEY.get(i.key))+((i.l||tot(i)>1)?` (${cntTxt(i)})`:"")).join(", ");const c=todoHere.length;
  return `${prevRoad?prevRoad+" done. ":""}Next road, ${h.road}. ${c>1?`${c} houses: ${list}. First, ${sayHouse(h)}${oppSay(h)}`:`${list}${oppSay(h)}`}.`;}
function renderDel(speak){const L=ordered();const cur=current();const G=groups(L);
  if(!cur){$("dK").textContent=L.length?"All done":"No parcels";$("dRoad").textContent=L.length?"Round complete":"Nothing loaded";$("dChips").innerHTML="";$("dNext").textContent="";
    const f=L.filter(i=>i.st==="fail");$("dCount").textContent=f.length?`${f.length} not delivered: `+f.map(i=>label(BYKEY.get(i.key))).join(", "):(L.length?"Every parcel delivered.":"Go to Load parcels to add today's parcels.");
    $("doneBtn").disabled=true;$("failBtn").disabled=true;$("mapBtn").removeAttribute("href");}
  else{const h=BYKEY.get(cur.key);const gi=G.findIndex(g=>g.items.includes(cur));const g=G[gi];
    $("dK").textContent=`Road ${gi+1} of ${G.length} · ${ROUNDNAME[h.round]} round`;$("dRoad").textContent=h.road;
    const ch=$("dChips");ch.innerHTML="";g.items.forEach(it=>{const s=document.createElement("span");s.className="chip"+(it===cur?" cur":it.st!=="todo"?" done":"");s.textContent=shortLab(BYKEY.get(it.key))+(cntShort(it)?" "+cntShort(it):"");ch.appendChild(s);});
    $("dNext").textContent=`Next: ${label(h)}`;const left=g.items.filter(i=>i.st==="todo").length;
    $("dCount").textContent=`${cntTxt(cur)} · ${left>1?(left-1)+" more on this road after this":"last one on this road"}`;
    const op=oppOf(h);$("dOpp").textContent=op?`Opposite No. ${op}`:"Opposite: not known";$("dOpp").dataset.key=h.key;
    $("doneBtn").disabled=false;$("failBtn").disabled=false;
    $("mapBtn").href="https://www.google.com/maps/dir/?api=1&travelmode=driving&destination="+encodeURIComponent(`${label(h)}${h.num?"":", "+h.road}, ${h.round==="ashurst"?"Ashurst":"Steyning"}, West Sussex`);}
  // coming up
  const up=$("upList");up.innerHTML="";const gi=cur?G.findIndex(g=>g.items.includes(cur)):G.length;
  G.slice(gi+1,gi+9).forEach(g=>{const li=document.createElement("li");li.innerHTML="<b></b><span></span>";li.querySelector("b").textContent=g.road;li.querySelector("span").textContent=g.items.filter(i=>i.st==="todo").map(i=>shortLab(BYKEY.get(i.key))+(cntShort(i)?" "+cntShort(i):"")).join(" · ");up.appendChild(li);});
  if(!up.children.length)up.innerHTML='<li><span>Nothing after this road.</span></li>';
  const dl=$("doneList");dl.innerHTML="";const D=L.filter(i=>i.st!=="todo");$("doneSum").textContent=`Done (${D.length})`;
  D.forEach(i=>{const li=document.createElement("li");li.innerHTML="<b></b><span></span>";li.querySelector("b").textContent=label(BYKEY.get(i.key));li.querySelector("span").textContent=i.st==="fail"?"Not delivered · tap to put back":"Delivered · tap to put back";li.onclick=()=>{i.st="todo";save();renderDel(false);};dl.appendChild(li);});
  updNavBtn();
  if(typeof GM!=="undefined"&&GM.map){$("dSide").hidden=!(cur&&GM.side[cur.key]);if(cur&&GM.side[cur.key])$("dSide").textContent="On your "+GM.side[cur.key];drawPins();updRoute(false);}
  if(speak)say(speechForNext(null));}
function finish(st){const cur=current();if(!cur)return;const h=BYKEY.get(cur.key);cur.st=st;cur.at=Date.now();save();beep(st==="done");renderDel(false);
  const nx=current();say(nx?speechForNext(h.road):`That's everything. ${ordered().filter(i=>i.st==="fail").length?"Some parcels weren't delivered; they're listed on the screen.":"Every parcel delivered. Well done."}`);ALERTED.clear();}
// ---------- hand the list to the full sat nav (map, turn-by-turn voice, follows your GPS) ----------
const NAVPAGE={annington:{id:"steyning",url:"../",pre:"f"},wiston:{id:"wiston",url:"../wiston/",pre:"w"},ashurst:{id:"ashurst",url:"../ashurst/",pre:"a"},penlands:{id:"penlands",url:"../penlands/",pre:"p"}};
const localDay=()=>{const d=new Date();return d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0");};
function navRound(){const cur=current();return cur?BYKEY.get(cur.key).round:null;}
function updNavBtn(){const r=navRound();const b=$("navBtn");if(!r){b.hidden=true;$("navHint").textContent="";return;}b.hidden=false;
  const n=ordered().filter(i=>i.st==="todo"&&BYKEY.get(i.key).round===r).length;const others=[...new Set(ordered().filter(i=>i.st==="todo").map(i=>BYKEY.get(i.key).round))].filter(x=>x!==r);
  b.textContent=`🧭 Start sat nav · ${ROUNDNAME[r]} (${n} ${n===1?"stop":"stops"})`;
  $("navHint").textContent=`Opens the map and talks you to each parcel in order, turn by turn.${others.length?` When ${ROUNDNAME[r]} is done, come back here for ${others.map(x=>ROUNDNAME[x]).join(" and ")}.`:""}`;}
$("navBtn").onclick=()=>{const r=navRound();if(!r)return;const P=NAVPAGE[r];const ids=ordered().filter(i=>i.st==="todo"&&BYKEY.get(i.key).round===r).map(i=>P.pre+BYKEY.get(i.key).k);
  try{localStorage.setItem(P.id+"_parcels",JSON.stringify({ids,day:localDay()}));localStorage.setItem(P.id+"_mode",JSON.stringify("parcels"));localStorage.setItem(P.id+"_pIdx","0");localStorage.setItem(P.id+"_ready","1");localStorage.setItem(P.id+"_fromHelper","1");localStorage.removeItem(P.id+"_pDone");}catch(e){}
  location.href=P.url;};
$("doneBtn").onclick=()=>finish("done");
// training: every house on one road
(function(){const rs=[...new Set(H.map(h=>h.round))];const R=$("trRound"),D=$("trRoad");
  rs.forEach(r=>{const o=document.createElement("option");o.value=r;o.textContent=ROUNDNAME[r];R.appendChild(o);});
  const fill=()=>{D.innerHTML="";const seen=[];H.filter(h=>h.round===R.value).forEach(h=>{if(!seen.includes(h.road))seen.push(h.road);});seen.forEach(n=>{const o=document.createElement("option");o.value=n;o.textContent=n;D.appendChild(o);});};
  R.onchange=fill;fill();
  $("trAdd").onclick=()=>{const L=H.filter(h=>h.round===R.value&&h.road===D.value);const was=KIND;KIND="parcel";L.forEach(h=>{if(!itemOf(h.key))addHouse(h,"train");});KIND=was;
    flash(`Added ${L.length} houses on ${D.value}`,"In frame order. Tap Done loading to start.","ok");beep(true);};})();
// fix a pin: stand at the door and tap
$("pinBtn").onclick=()=>{const cur=current();if(!cur)return;const h=BYKEY.get(cur.key);
  if(!navigator.geolocation){showAlert("No GPS on this phone","",false);return;}
  $("pinBtn").textContent="Getting your position…";
  navigator.geolocation.getCurrentPosition(p=>{const acc=p.coords.accuracy||99;$("pinBtn").textContent="📍 I'm at this house: fix its pin";
    if(acc>25){showAlert("GPS isn't accurate enough yet",`±${Math.round(acc)} m. Wait a few seconds out in the open and try again.`,false);return;}
    PINFIX[cur.key]={lat:+p.coords.latitude.toFixed(6),lng:+p.coords.longitude.toFixed(6)};store.set("pins",PINFIX);
    beep(true);showAlert(`Pin fixed: ${label(h)}`,"Saved on this phone. It'll be right every time from now on.",true);try{drawPins();}catch(e){}},
   ()=>{$("pinBtn").textContent="📍 I'm at this house: fix its pin";showAlert("Couldn't get your position","Allow location for this page.",false);},{enableHighAccuracy:true,maximumAge:0,timeout:20000});};
// correct what's opposite (saved on this phone)
$("dOpp").onclick=()=>{const k=$("dOpp").dataset.key;if(!k)return;const h=BYKEY.get(k);const v=window.prompt(`What's across the road from ${label(h)}? (a number or a house name; leave empty if nothing)`,oppOf(h));if(v===null)return;OPPFIX[k]=v.trim();store.set("opp",OPPFIX);renderDel(false);};$("failBtn").onclick=()=>finish("fail");
$("backBtn").onclick=()=>{const L=ordered();const last=L.filter(i=>i.st!=="todo").sort((a,b)=>(b.at||0)-(a.at||0))[0];if(!last)return;last.st="todo";save();renderDel(false);say(speechForNext(null));};

// ---------- road alerts from GPS ----------
const K=Math.cos(50.9*Math.PI/180),MPD=111320;const xy=(lat,lon)=>({x:lon*MPD*K,y:lat*MPD});
const SEGS=[];ROADGEO.forEach(([name,pieces])=>pieces.forEach(p=>{for(let i=0;i<p.length-1;i++){const a=xy(p[i][0],p[i][1]),b=xy(p[i+1][0],p[i+1][1]);SEGS.push({name,a,b,x0:Math.min(a.x,b.x)-30,x1:Math.max(a.x,b.x)+30,y0:Math.min(a.y,b.y)-30,y1:Math.max(a.y,b.y)+30});}}));
function segD(p,a,b){const dx=b.x-a.x,dy=b.y-a.y,L=dx*dx+dy*dy||1e-9;const t=Math.max(0,Math.min(1,((p.x-a.x)*dx+(p.y-a.y)*dy)/L));return Math.hypot(p.x-a.x-t*dx,p.y-a.y-t*dy);}
function roadAt(p){let best=null,bd=22;for(const s of SEGS){if(p.x<s.x0||p.x>s.x1||p.y<s.y0||p.y>s.y1)continue;const d=segD(p,s.a,s.b);if(d<bd){bd=d;best=s.name;}}return best;}
const mapRoad=h=>MAPROAD[h.road]||h.road;
const G={watch:null,road:null,cand:null,candN:0,prevRoad:null,pos:null};const ALERTED=new Set();
function showAlert(main,sub,info){const a=$("alert");a.className=info?"info":"";a.innerHTML="";const m=document.createElement("div");m.textContent=main;a.appendChild(m);if(sub){const s=document.createElement("small");s.textContent=sub;a.appendChild(s);}a.hidden=false;clearTimeout(G.t);G.t=setTimeout(()=>{a.hidden=true;},9000);}
$("alert").onclick=()=>{$("alert").hidden=true;};
function todoOnRoad(road,p,maxM){return ordered().filter(i=>{if(i.st!=="todo")return false;const h=BYKEY.get(i.key);if(mapRoad(h)!==road)return false;const q=xy(h.lat,h.lon);return Math.hypot(q.x-p.x,q.y-p.y)<maxM;});}
function onRoadChange(newRoad,oldRoad,p){
  // leaving a road with parcels still on it
  // only nag about roads you should already have done (this road or earlier in the order), not ones you're just driving through
  if(oldRoad){const cur=current();const L=ordered();const ci=cur?L.indexOf(cur):L.length;const left=todoOnRoad(oldRoad,p,900).filter(i=>{const curH=cur&&BYKEY.get(cur.key);return L.indexOf(i)<=ci||(curH&&mapRoad(curH)===oldRoad);});const key="leave:"+oldRoad;if(left.length&&!ALERTED.has(key)){ALERTED.add(key);
      const names=left.map(i=>sayHouse(BYKEY.get(i.key))).join(", ");beep(false);showAlert(`Still to deliver on ${oldRoad}`,left.map(i=>label(BYKEY.get(i.key))).join(" · "));
      say(`Wait. You've left ${oldRoad} with ${left.length} parcel${left.length>1?"s":""} still to deliver: ${names}.`);return;}}
  if(!newRoad)return;const here=todoOnRoad(newRoad,p,700);if(!here.length)return;const key="on:"+newRoad;if(ALERTED.has(key))return;ALERTED.add(key);
  const cur=current();const curH=cur&&BYKEY.get(cur.key);const isCurrent=curH&&mapRoad(curH)===newRoad;const names=here.map(i=>sayHouse(BYKEY.get(i.key))).join(", ");
  showAlert(`${isCurrent?"":"Don't miss: "}${here.length} parcel${here.length>1?"s":""} on ${newRoad}`,here.map(i=>label(BYKEY.get(i.key))).join(" · "),isCurrent);
  if(!isCurrent)beep(false);say(`${isCurrent?"You're on":"Heads up, you're on"} ${newRoad}. Parcel${here.length>1?"s":""} here: ${names}.`);}
function onFix(pos){const p=xy(pos.coords.latitude,pos.coords.longitude);G.pos=p;const acc=pos.coords.accuracy||99;try{gmFix(pos.coords.latitude,pos.coords.longitude,acc);}catch(e){}if(acc>40){$("gpsT").textContent=`Road alerts on · weak GPS (±${Math.round(acc)} m)`;return;}
  const r=roadAt(p);if(r===G.cand)G.candN++;else{G.cand=r;G.candN=1;}
  if(G.candN>=2&&r!==G.road){const old=G.road;G.road=r;onRoadChange(r,old,p);}
  $("gpsT").textContent=G.road?`Road alerts on · you're on ${G.road}`:"Road alerts on · not on a road with parcels";}
function gpsOn(){if(G.watch!=null){navigator.geolocation.clearWatch(G.watch);G.watch=null;$("gpsBtn").textContent="Turn on";$("gpsT").textContent="Road alerts are off";store.set("gps",0);return;}
  if(!navigator.geolocation){$("gpsT").textContent="This phone can't share its location here.";return;}
  G.watch=navigator.geolocation.watchPosition(onFix,e=>{$("gpsT").textContent=e&&e.code===1?"Location is blocked. Allow it for this page in your browser settings.":"Waiting for GPS…";},{enableHighAccuracy:true,maximumAge:2000,timeout:30000});
  $("gpsBtn").textContent="Turn off";$("gpsT").textContent="Road alerts on · finding you…";store.set("gps",1);}
$("gpsBtn").onclick=gpsOn;

// keep the screen on while delivering
let WL=null;async function wake(on){try{if(on&&"wakeLock" in navigator&&!WL){WL=await navigator.wakeLock.request("screen");WL.addEventListener("release",()=>{WL=null;});}else if(!on&&WL){await WL.release();WL=null;}}catch(e){}}
document.addEventListener("visibilitychange",()=>{if(document.visibilityState==="visible"&&!$("vDel").hidden)wake(true);});

// bring back progress from the sat nav: parcels before the one it's on now count as delivered
function syncFromNav(){let changed=false;for(const r in NAVPAGE){const P=NAVPAGE[r];try{if(!localStorage.getItem(P.id+"_fromHelper"))continue;const par=JSON.parse(localStorage.getItem(P.id+"_parcels")||"null");const idx=+JSON.parse(localStorage.getItem(P.id+"_pIdx")||"0");
    if(!par||!Array.isArray(par.ids))continue;const done=localStorage.getItem(P.id+"_pDone")==="1";par.ids.slice(0,done?par.ids.length:idx).forEach(id=>{const k=+id.slice(1);const it=S.items.find(i=>i.key===r+":"+k);if(it&&it.st==="todo"){it.st="done";it.at=Date.now();changed=true;}});}catch(e){}}
  if(changed){save();renderList();if(!$("vDel").hidden)renderDel(false);}}
document.addEventListener("visibilitychange",()=>{if(document.visibilityState==="visible")syncFromNav();});
window.addEventListener("pageshow",syncFromNav);
// ---------- start ----------
pickVoice();syncFromNav();setKind(KIND);renderList();
if(store.get("tab")==="del"&&S.items.length)tab("del");

if("serviceWorker" in navigator)window.addEventListener("load",()=>navigator.serviceWorker.register("sw.js").catch(()=>{}));
window.__ph={ROADGEO,H,match,S:()=>S,ordered,groups,addHouse,finish,onRoadChange,roadAt,xy,speechForNext,current};
