// 앱으로 설치했을 때 인터넷 없이도 열리게: 온라인이면 새로 받아 저장해 두고, 끊기면 저장해 둔 것을 씀
const CACHE = "sqld";
self.addEventListener("install", e => e.waitUntil(caches.open(CACHE).then(c => c.addAll(["./", "index.html", "questions.js", "manifest.webmanifest", "icon-192.png", "icon-512.png"]))));
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  e.respondWith(fetch(e.request, { cache: "no-cache" }) // 휴대폰에 남은 옛 파일 대신 늘 새 버전을 확인
    .then(r => { if (r.ok) { const copy = r.clone(); caches.open(CACHE).then(c => c.put(e.request, copy)); } return r; })
    .catch(() => caches.match(e.request)));
});
