const CACHE='snu-2026-trainers-2026-11-02-v3-arbitration';
const ASSETS=['/','/index.html','/memory/','/memory/index.html','/manifest.webmanifest'];
self.addEventListener('install', event => {event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(ASSETS)).then(()=>self.skipWaiting()));});
self.addEventListener('activate', event => {event.waitUntil(Promise.all([caches.keys().then(keys => Promise.all(keys.filter(k=>k.startsWith('snu-2026-trainers-')&&k!==CACHE).map(k=>caches.delete(k)))),self.clients.claim()]));});
self.addEventListener('fetch',event => {const req=event.request;if(req.method!=='GET'||new URL(req.url).origin!==self.location.origin)return;
event.respondWith(fetch(req).then(res=>{if(res.ok){const copy=res.clone();caches.open(CACHE).then(cache=>cache.put(req,copy)).catch(()=>{});}return res;}).catch(()=>caches.match(req).then(hit=>hit||Response.error())));});
