// Keeps a copy of the Ashurst sat nav on the phone so it opens with no signal.
// Online: fetch fresh and update the copy. Offline: use the saved copy.
const CACHE = "ashurst-v11";
self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(["./", "./index.html"])).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith("ashurst-") && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  e.respondWith(
    fetch(req).then(res => {
      if (res && (res.ok || res.type === "opaque")) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
      return res;
    }).catch(() => caches.match(req, { ignoreSearch: true }).then(r => r || caches.match("./")))
  );
});
