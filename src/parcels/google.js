// ---------- Google Maps (optional: only when the driver has added their own key) ----------
// The key is the driver's own, typed in on this phone and kept only on this phone.
// Google positions are looked up for today's houses only and kept with today's list (cleared each day).
const GM={key:store.get("gkey")||"",ready:null,map:null,me:null,acc:null,pins:new Map(),line:null,routeFor:"",routeAt:0,lastLL:null,follow:true,side:{},err:""};
const TOWNOF=r=>r==="ashurst"?"Ashurst":"Steyning";
function gmStatus(t,bad){const e=$("gmStatus");if(e){e.textContent=t;e.style.color=bad?"var(--bad)":"";}}
function loadGoogle(){if(!GM.key)return Promise.reject(new Error("nokey"));if(GM.ready)return GM.ready;
  GM.ready=new Promise((ok,bad)=>{window.__gmOk=()=>ok();window.gm_authFailure=()=>{GM.err="Google didn't accept that key. Check it's copied in full, that the Maps JavaScript API is switched on, and that the key allows andy3248.github.io.";gmStatus(GM.err,true);$("gmBox").hidden=true;};
    const s=document.createElement("script");s.async=true;s.src=`https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(GM.key)}&v=weekly&libraries=geometry&language=en-GB&region=GB&callback=__gmOk&loading=async`;
    s.onerror=()=>{GM.ready=null;bad(new Error("load"));};document.head.appendChild(s);});
  return GM.ready;}
// where to aim for each house: Google's spot if we have one for today, else the app's own pin
// priority: the driver's own fixed pin > Google's exact match > the app's own pin
function spot(it){const h=BYKEY.get(it.key);const f=PINFIX[it.key];if(f)return {lat:f.lat,lng:f.lng};return it.g?{lat:it.g.lat,lng:it.g.lng}:{lat:h.lat,lng:h.lon};}
async function geocodeToday(){const gc=new google.maps.Geocoder();const L=ordered().filter(i=>i.st==="todo"&&!i.g&&!PINFIX[i.key]);
  for(const it of L){const h=BYKEY.get(it.key);const q=`${h.num?h.num+" "+h.road:h.name+", "+h.road}, ${TOWNOF(h.round)}, West Sussex, UK`;
    try{const r=await gc.geocode({address:q,componentRestrictions:{country:"GB"}});const best=(r.results||[])[0];
      if(best){const lt=best.geometry.location_type;const exact=lt==="ROOFTOP"||lt==="RANGE_INTERPOLATED";const ll=best.geometry.location;
        // only trust it if it's a real house match and not miles from where the app thinks the house is
        const far=google.maps.geometry.spherical.computeDistanceBetween(ll,new google.maps.LatLng(h.lat,h.lon));
        it.g=exact&&far<700?{lat:ll.lat(),lng:ll.lng(),src:"google"}:{lat:h.lat,lng:h.lon,src:"app"};}
      else it.g={lat:h.lat,lng:h.lon,src:"app"};}
    catch(e){if(String(e).includes("REQUEST_DENIED")){GM.err="Google refused the address lookup. Switch on the Geocoding API for your key.";gmStatus(GM.err,true);break;}
      it.g={lat:h.lat,lng:h.lon,src:"app"};}
    save();drawPins();await new Promise(r=>setTimeout(r,120));}}
// show the road you're on (plus the start of the next one); "Whole list" shows everything
function pinText(h){if(h.num)return h.num;const w=h.name.replace(/^the /i,"").split(/[ ,]+/)[0];return w.length>6?w.slice(0,5)+"…":w;}
function drawPins(){if(!GM.map)return;const L=ordered();const cur=current();const live=new Set();
  const curH=cur&&BYKEY.get(cur.key);const G2=groups(L.filter(i=>i.st==="todo"));const gi=cur?G2.findIndex(g=>g.items.includes(cur)):-1;
  const shown=new Set();if(GM.showAll)L.forEach(i=>i.st==="todo"&&shown.add(i.key));else if(gi>=0){G2[gi].items.forEach(i=>shown.add(i.key));if(G2[gi+1])G2[gi+1].items.slice(0,3).forEach(i=>shown.add(i.key));}
  L.forEach(it=>{if(it.st!=="todo"||!shown.has(it.key))return;live.add(it.key);let m=GM.pins.get(it.key);const p=spot(it);const isCur=it===cur;const h=BYKEY.get(it.key);
    const onRoad=curH&&h.road===curH.road;const col=isCur?"#1a73e8":(PINFIX[it.key]?"#e37400":(it.g&&it.g.src==="google"?"#188038":"#80868b"));
    const txt=pinText(h);const wide=txt.length>3;
    const icon={path:wide?"M -22,-11 L 22,-11 Q 26,-11 26,-7 L 26,7 Q 26,11 22,11 L -22,11 Q -26,11 -26,7 L -26,-7 Q -26,-11 -22,-11 Z":google.maps.SymbolPath.CIRCLE,
      scale:wide?(isCur?1.15:0.95):(isCur?17:13),fillColor:col,fillOpacity:onRoad?1:0.55,strokeColor:"#fff",strokeWeight:2,labelOrigin:new google.maps.Point(0,0)};
    const lab={text:txt,color:"#fff",fontSize:isCur?"15px":(wide?"11px":"13px"),fontWeight:"700"};
    if(!m){m=new google.maps.Marker({map:GM.map,position:p,icon,label:lab,title:label(h),zIndex:isCur?999:(onRoad?10:1)});
      m.addListener("click",()=>{const it2=ordered().find(x=>x.key===it.key);showAlert(label(h),(it2?cntTxt(it2):"")+(PINFIX[it.key]?" · your pin":it.g&&it.g.src==="google"?" · Google's position":" · best guess: fix it when you're there"),true);});GM.pins.set(it.key,m);}
    else{m.setPosition(p);m.setIcon(icon);m.setLabel(lab);m.setZIndex(isCur?999:(onRoad?10:1));}});
  for(const [k,m] of GM.pins)if(!live.has(k)){m.setMap(null);GM.pins.delete(k);}
  // new road: zoom to it
  if(curH&&GM.zoomRoad!==curH.road&&!GM.showAll){GM.zoomRoad=curH.road;const b=new google.maps.LatLngBounds();G2[gi].items.forEach(i=>b.extend(spot(i)));if(GM.lastLL&&GM.follow)b.extend(GM.lastLL);GM.map.fitBounds(b,50);if(GM.map.getZoom&&GM.map.getZoom()>18)GM.map.setZoom(18);}}
const label2=h=>label(h);
function fitAll(){if(!GM.map)return;const b=new google.maps.LatLngBounds();let n=0;ordered().forEach(it=>{if(it.st==="todo"){b.extend(spot(it));n++;}});if(GM.lastLL){b.extend(GM.lastLL);n++;}if(n)GM.map.fitBounds(b,40);}
async function initGoogleMap(){if(!GM.key){$("gmBox").hidden=true;$("gmHint").hidden=false;return;}$("gmHint").hidden=true;
  try{await loadGoogle();}catch(e){$("gmBox").hidden=true;gmStatus("Couldn't load Google Maps. It needs signal; the rest of the app still works.",true);return;}
  if(GM.err)return;$("gmBox").hidden=false;
  if(!GM.map){GM.map=new google.maps.Map($("gmap"),{center:{lat:50.886,lng:-0.33},zoom:15,disableDefaultUI:true,zoomControl:true,gestureHandling:"greedy",clickableIcons:false});
    GM.map.addListener("dragstart",()=>{GM.follow=false;$("gmCentre").hidden=false;});}
  GM.zoomRoad="";drawPins();geocodeToday().then(()=>{drawPins();updRoute(true);});}
// you-are-here, follow, and the route to the next house
function gmFix(lat,lng,acc){GM.lastLL={lat,lng};if(!GM.map)return;const p=GM.lastLL;
  if(!GM.me){GM.me=new google.maps.Marker({map:GM.map,position:p,zIndex:1000,icon:{path:google.maps.SymbolPath.CIRCLE,scale:9,fillColor:"#4285f4",fillOpacity:1,strokeColor:"#fff",strokeWeight:3}});
    GM.acc=new google.maps.Circle({map:GM.map,center:p,radius:acc||20,strokeOpacity:0,fillColor:"#4285f4",fillOpacity:.12,clickable:false});}
  else{GM.me.setPosition(p);GM.acc.setCenter(p);GM.acc.setRadius(acc||20);}
  if(GM.follow)GM.map.panTo(p);
  // off the route by more than ~60 m: work it out again (at most every 25 s)
  if(GM.line&&!google.maps.geometry.poly.isLocationOnEdge(new google.maps.LatLng(p),GM.line,0.0006)&&Date.now()-GM.routeAt>25000)updRoute(true);
  else if(!GM.line)updRoute(false);}
function decodeLine(enc){return google.maps.geometry.encoding.decodePath(enc);}
async function updRoute(force){const cur=current();if(!GM.map||!cur||!GM.lastLL)return;if(!force&&GM.routeFor===cur.key)return;if(Date.now()-GM.routeAt<4000&&GM.routeFor===cur.key)return;
  GM.routeFor=cur.key;GM.routeAt=Date.now();const to=spot(cur);
  try{const r=await fetch("https://routes.googleapis.com/directions/v2:computeRoutes",{method:"POST",headers:{"Content-Type":"application/json","X-Goog-Api-Key":GM.key,"X-Goog-FieldMask":"routes.polyline.encodedPolyline,routes.distanceMeters,routes.duration"},
      body:JSON.stringify({origin:{location:{latLng:{latitude:GM.lastLL.lat,longitude:GM.lastLL.lng}}},destination:{location:{latLng:{latitude:to.lat,longitude:to.lng}}},travelMode:"DRIVE",languageCode:"en-GB",units:"IMPERIAL"})});
    const j=await r.json();if(j.error){gmStatus("Google route: "+(j.error.status==="PERMISSION_DENIED"?"switch on the Routes API for your key.":j.error.message),true);return;}
    const rt=(j.routes||[])[0];if(!rt)return;const path=decodeLine(rt.polyline.encodedPolyline);
    if(GM.line)GM.line.setMap(null);GM.line=new google.maps.Polyline({map:GM.map,path,strokeColor:"#1a73e8",strokeOpacity:.85,strokeWeight:7});
    // which side of the road: compare the road's direction at the end with the direction to the house
    if(path.length>=2){const end=path[path.length-1];let k=path.length-2;while(k>0&&google.maps.geometry.spherical.computeDistanceBetween(path[k],end)<12)k--;
      const hr=google.maps.geometry.spherical.computeHeading(path[k],end),hh=google.maps.geometry.spherical.computeHeading(end,new google.maps.LatLng(to));
      const d=((hh-hr+540)%360)-180;const dist=google.maps.geometry.spherical.computeDistanceBetween(end,new google.maps.LatLng(to));
      const side=dist<4||Math.abs(d)<25||Math.abs(d)>155?"":(d<0?"left":"right");
      if(side&&GM.side[cur.key]!==side){GM.side[cur.key]=side;const h=BYKEY.get(cur.key);sayQueued(`${uc(sayHouse(h))} is on your ${side}.`);}
      $("dSide").textContent=side?`On your ${side}`:"";$("dSide").hidden=!side;}
    const mi=rt.distanceMeters/1609.34;$("gmInfo").textContent=`${mi<0.2?Math.round(rt.distanceMeters*1.094)+" yards":mi.toFixed(1)+" miles"} · ${Math.max(1,Math.round(parseInt(rt.duration)/60))} min`;}
  catch(e){gmStatus("Couldn't get a Google route (no signal?). The app's alerts still work.",true);}}
const uc=t=>t.charAt(0).toUpperCase()+t.slice(1);
// Street View of the next house's front
async function openStreet(){const cur=current();if(!cur||!GM.map)return;const to=spot(cur);$("svBox").hidden=false;$("svMsg").textContent="Finding the street view…";
  try{const sv=new google.maps.StreetViewService();const r=await sv.getPanorama({location:to,radius:60,source:google.maps.StreetViewSource.OUTDOOR,preference:google.maps.StreetViewPreference.NEAREST});
    const pl=r.data.location.latLng;const heading=google.maps.geometry.spherical.computeHeading(pl,new google.maps.LatLng(to));
    $("svMsg").textContent=label(BYKEY.get(cur.key));
    new google.maps.StreetViewPanorama($("svPano"),{pano:r.data.location.pano,pov:{heading,pitch:5},zoom:0.6,addressControl:false,fullscreenControl:false,motionTracking:false,motionTrackingControl:false});}
  catch(e){$("svMsg").textContent="No street view near this house.";}}
$("svClose").onclick=()=>{$("svBox").hidden=true;$("svPano").innerHTML="";};
$("svBtn").onclick=openStreet;
$("gmCentre").onclick=()=>{GM.follow=true;$("gmCentre").hidden=true;if(GM.lastLL)GM.map.panTo(GM.lastLL);};
$("gmFit").onclick=()=>{GM.showAll=!GM.showAll;$("gmFit").textContent=GM.showAll?"This road":"Whole list";GM.follow=false;$("gmCentre").hidden=false;drawPins();if(GM.showAll)fitAll();else{GM.zoomRoad="";drawPins();}};
// settings: the driver's own key
$("gmKey").value=GM.key;
$("gmSave").onclick=()=>{const k=$("gmKey").value.trim();GM.key=k;store.set("gkey",k);GM.err="";
  if(!k){gmStatus("Google Maps is off.");$("gmBox").hidden=true;return;}
  if(GM.ready&&window.google&&google.maps){gmStatus("Saved. Reload the page to use the new key.");return;}
  gmStatus("Saved. Testing…");loadGoogle().then(()=>new google.maps.Geocoder().geocode({address:"High Street, Steyning, UK"})).then(()=>{if(!GM.err)gmStatus("Working. The Deliver screen now shows the Google map.");if(!$("vDel").hidden)initGoogleMap();})
    .catch(e=>gmStatus(String(e).includes("REQUEST_DENIED")?"The key works for the map but the Geocoding API isn't switched on.":"Couldn't use that key: "+(GM.err||String(e.message||e)),true));};
// queue a line after whatever is being said (don't cut off "Next road…")
function sayQueued(t){try{const u=new SpeechSynthesisUtterance(t);if(VOICE){u.voice=VOICE;u.lang=VOICE.lang;}else u.lang="en-GB";u.rate=VSET.rate;speechSynthesis.speak(u);}catch(e){}}
