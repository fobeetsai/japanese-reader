/** Versioned flashcard assets: never combine cached controllers with newer HTML. */
const CACHE_NAME = 'ankiflash-v13-moji-companion';
const VERSION = '20260916-13';
const ASSETS_TO_CACHE = [
  './flashcard.html', './manifest.json',
  './static/cross_nav.css', './static/flashcards/css/app.css',
  './static/flashcards/js/anki_engine.js', './static/flashcards/js/sync_manager.js',
  './static/flashcards/js/builtin_data.js', './static/flashcards/js/word_enricher.js',
  './static/flashcards/js/ankiflash_bridge.js', './static/flashcards/js/photo_ocr_engine.js',
  './static/flashcards/js/moji_bridge.js', './static/flashcards/js/app.js', './static/flashcards/js/excel_import.js',
  './static/flashcards/vendor/xlsx.full.min.js', './static/flashcards/icons/icon-192.svg'
].map(path => /\.(js|css)$/.test(path) ? `${path}?v=${VERSION}` : path);

self.addEventListener('install', event => {
  self.skipWaiting();
  event.waitUntil(caches.open(CACHE_NAME).then(cache =>
    Promise.allSettled(ASSETS_TO_CACHE.map(url => cache.add(new Request(url, {cache: 'reload'}))))));
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(names => Promise.all(
    names.filter(name => name.startsWith('ankiflash-') && name !== CACHE_NAME)
      .map(name => caches.delete(name))
  )).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  // Also stop old controlled tabs before their cached code can contact paid AI.
  if (/(^|\.)(generativelanguage\.googleapis\.com|aiplatform\.googleapis\.com|openai\.com|anthropic\.com)$/.test(url.hostname)) {
    event.respondWith(Promise.resolve(new Response(JSON.stringify({code: 'PAID_AI_DISABLED'}), {status: 410, headers: {'Content-Type': 'application/json'}})));
    return;
  }
  const scope = new URL(self.registration.scope);
  if (event.request.method !== 'GET' || url.origin !== scope.origin || !url.pathname.startsWith(scope.pathname)) return;
  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    try {
      const response = await fetch(event.request, {cache: 'no-cache'});
      if (response.ok) {
        await cache.put(event.request, response.clone());
        return response;
      }
      return await cache.match(event.request) || response;
    } catch (error) {
      return await cache.match(event.request) || Response.error();
    }
  })());
});
