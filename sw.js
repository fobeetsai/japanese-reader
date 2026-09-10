/**
 * AnkiFlash Service Worker - 支援 100% 離線使用與極速快取
 */

const CACHE_NAME = 'ankiflash-cache-v1';
const ASSETS_TO_CACHE = [
  'flashcard.html',
  'manifest.json',
  'static/flashcards/css/app.css',
  'static/flashcards/js/anki_engine.js',
  'static/flashcards/js/sync_manager.js',
  'static/flashcards/js/builtin_data.js',
  'static/flashcards/js/app.js',
  'static/flashcards/icons/icon-192.svg'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] 正在預先快取關鍵離線資源...');
      return cache.addAll(ASSETS_TO_CACHE);
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((name) => {
          if (name !== CACHE_NAME) {
            console.log('[SW] 清理舊快取:', name);
            return caches.delete(name);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  // 只攔截同源 HTTP/HTTPS 請求，忽視 chrome-extension 或 API
  if (!event.request.url.startsWith(self.location.origin)) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        // 快取優先，背景靜默更新 (Stale-While-Revalidate)
        fetch(event.request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, networkResponse);
            });
          }
        }).catch(() => {});
        return cachedResponse;
      }
      return fetch(event.request);
    })
  );
});
