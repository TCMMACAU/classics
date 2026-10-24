// 經典原文 service worker：殼同索引先裝，睇過嘅頁面自動快取，搜尋索引行 network-first
const CACHE='classics-v6';
const SHELL=['./','index.html','assets/style.css','assets/app.js','manifest.webmanifest','search.html','patient.html','fangji/index.html','yao/index.html','bingmen/index.html','clinical/index.html','icons/icon-192.png','icons/icon-512.png'];
self.addEventListener('install',e=>{
  e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting()));
});
self.addEventListener('activate',e=>{
  e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));
});
self.addEventListener('fetch',e=>{
  const req=e.request;
  if(req.method!=='GET') return;
  const url=new URL(req.url);
  if(url.origin!==location.origin) return;
  if(url.pathname.endsWith('search-index.json')){
    e.respondWith(fetch(req).then(res=>{const copy=res.clone(); caches.open(CACHE).then(c=>c.put(req,copy)); return res;}).catch(()=>caches.match(req)));
    return;
  }
  e.respondWith(caches.match(req).then(hit=>{
    if(hit) return hit;
    return fetch(req).then(res=>{
      if(res.ok){const copy=res.clone(); caches.open(CACHE).then(c=>c.put(req,copy));}
      return res;
    }).catch(()=>caches.match('index.html'));
  }));
});
