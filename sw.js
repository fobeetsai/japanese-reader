/**
 * AnkiFlash Service Worker - 支援離線使用、PWA 與自動快取更新
 */

const CACHE_NAME = 'ankiflash-v3';
const ASSETS_TO_CACHE = [
  './flashcard.html',
  './manifest.json',
  './static/flashcards/css/app.css',
  './static/flashcards/js/anki_engine.js',
  './static/flashcards/js/sync_manager.js',
  './static/flashcards/js/builtin_data.js',
  './static/flashcards/js/word_enricher.js',
  './static/flashcards/js/app.js',
  './static/flashcards/icons/icon-192.svg'
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] 快取關鍵離線資源...');
      // 容錯快取：單一檔案失敗不中斷其餘資源
      return Promise.allSettled(
        ASSETS_TO_CACHE.map(url => cache.add(url).catch(err => {
          console.warn('[SW] 快取單一項目略過:', url, err.message);
        }))
      );
    })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((name) => {
          if (name !== CACHE_NAME) {
            console.log('[SW] 清理舊版快取:', name);
            return caches.delete(name);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  // 僅處理同源請求
  if (!event.request.url.startsWith(self.location.origin)) {
    return;
  }

  // HTML 檔案採用 Network-First (網路優先，確保用戶隨時獲得最新版，斷網時使用快取)
  if (event.request.headers.get('accept')?.includes('text/html') || event.request.url.endsWith('.html')) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response && response.status === 200) {
            const copy = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
          }
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // 靜態資源 (CSS, JS, SVG) 採用 Stale-While-Revalidate
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      const fetchPromise = fetch(event.request)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const copy = networkResponse.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
          }
          return networkResponse;
        })
        .catch(() => null);

      return cachedResponse || fetchPromise;
    })
  );
});
